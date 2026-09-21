"""Manufacturer input check, separate protocol calculation and strong baseline."""

import argparse
import csv
from fractions import Fraction as F
import io
import math
from pathlib import Path
import resource
import subprocess
import time

from binding import bind
from common import load, require, write_new
import conventional as cv
from decode import decode, population, select
from experiment import RATE, TOLERANCE, full_reference, run_segment, segments
from linear_check import check as check_witness
from response_check import plan as margin_reference
from responses import response_status


def short(state):
    return {k: state[k] for k in ("status", "uniform_error_range_mps") if k in state}


def interp(knots, t):
    for left, right in zip(knots, knots[1:]):
        if left[0] <= t <= right[0]:
            return ((right[0] - t) * left[1] + (t - left[0]) * right[1]) / (
                right[0] - left[0]
            )
    raise AssertionError("reference_interpolation_domain")


def margin_model(points, rate, sign):
    return dict(
        id="residual-positive" if sign == 1 else "residual-negative",
        horizon_s=["0", "1/5"],
        threshold_mps="0",
        quantity=dict(
            kind="recorded_north_velocity_margin",
            unit="m/s",
            provenance="conditional_recorded_reconstruction",
        ),
        motion=dict(kind="global_lipschitz", rate_mps2=str(rate)),
        clock=dict(kind="common_offset", radius_s="0"),
        observations=[
            dict(
                id=f"sample-t-{t.numerator}-{t.denominator}",
                time_s=str(t),
                interval_mps=[str(TOLERANCE + sign * v)] * 2,
            )
            for t, v in sorted(points)
        ],
    )


def verify_reiyah_segment(segment, actual, proof):
    times, values, knots, rate = (
        segment["times"],
        segment["values"],
        segment["knots"],
        segment["residual_rate"],
    )
    zero_knots = [(t, F(0)) for t, _ in knots]
    seen = {i: values[i] - interp(knots, times[i]) for i in (0, 10, 20)}
    expected_records, calls, model_count, partition_count = [], [], 0, 0
    for step in range(19):
        points = [(times[i], seen[i]) for i in sorted(seen)]
        state = short(cv.error_bounds(points, zero_knots, rate, TOLERANCE))
        if step == 0:
            initial = state
        require(step < len(proof["stages"]), "missing_proof_stage")
        native = proof["stages"][step]
        require(
            set(native) == {"step", "margins"}
            and native["step"] == step
            and len(native["margins"]) == 2,
            "proof_membership",
        )
        models = [margin_model(points, rate, sign) for sign in (1, -1)]
        for model, witness in zip(models, native["margins"]):
            require(
                set(witness) == {"model", "result"} and witness["model"] == model,
                "native_model",
            )
            check_witness(model, witness["result"])
            model_count += 1
        remaining = [i for i in range(21) if i not in seen]
        if state["status"] != "unresolved" or not remaining:
            final = state
            break
        index = cv.next_index(points, zero_knots, rate, remaining, times)
        prediction = cv.response_plan(points, zero_knots, rate, TOLERANCE, times[index])
        query = dict(
            id="next-sample",
            time_s=str(times[index]),
            error_mps="0",
            clock_registration="same_recording_axis",
            available=True,
        )
        margins = [margin_reference(m, query) for m in models]
        value = values[index]
        reply = value - interp(knots, times[index])
        expected_records.append(
            dict(
                step=step,
                query_index=index,
                source_index=segment["source_indices"][index],
                time_s=str(times[index]),
                before=state,
                predicted=prediction,
                margin_partitions=margins,
                observed_north_velocity_mps=str(value),
                response_mps=str(reply),
                response_status=response_status(prediction, reply),
            )
        )
        seen[index] = reply
        calls.append(index)
        partition_count += 3
    require(len(proof["stages"]) == step + 1, "extra_proof_stage")
    for i, row in enumerate(expected_records):
        row["after"] = (
            expected_records[i + 1]["before"]
            if i + 1 < len(expected_records)
            else final
        )
        require(
            row["response_status"] == row["after"]["status"],
            "independent_reply_recomputation",
        )
    expected = dict(
        id=segment["id"],
        arm="reiyah",
        initial=initial,
        final=final,
        oracle_calls=len(calls),
        query_indices=calls,
        coarse_indices=[0, 10, 20],
        unqueried_indices=[i for i in range(21) if i not in seen],
        workflow_status="exhausted"
        if final["status"] == "unresolved"
        else final["status"],
        records=expected_records,
    )
    require(actual == expected, "complete_reiyah_protocol")
    return dict(
        native_model_witness_stages=model_count,
        complete_response_partitions=partition_count,
    )


def vendor_values(data, text, own_rows):
    decoded = {}
    for row in csv.reader(io.StringIO(text)):
        require(len(row) == 7, "vendor_output_columns")
        (
            end,
            mode,
            packet_type,
            time_valid,
            value_time,
            velocity_valid,
            value_velocity,
        ) = row
        end = int(end)
        require(end % 72 == 71 and end // 72 not in decoded, "vendor_packet_offsets")
        index = end // 72
        require(0 <= index < len(own_rows), "vendor_membership")
        item = dict(
            mode=int(mode),
            packet_type=int(packet_type),
            time_valid=int(time_valid),
            velocity_valid=int(velocity_valid),
        )
        if item["time_valid"]:
            t = float(value_time)
            require(math.isfinite(t), "vendor_nonfinite_time")
            item["time_ms"] = round(t * 1000)
            require(
                abs(F.from_float(t) - F(item["time_ms"], 1000))
                <= F.from_float(math.ulp(t)),
                "vendor_time_rounding",
            )
        if item["velocity_valid"]:
            v = float(value_velocity)
            require(math.isfinite(v), "vendor_nonfinite_velocity")
            item["north_velocity_units"] = round(v * 10000)
            require(
                abs(F.from_float(v) - F(item["north_velocity_units"], 10000))
                <= 2 * F.from_float(math.ulp(v)),
                "vendor_velocity_rounding",
            )
        decoded[index] = item
    require(len(decoded) == len(own_rows), "vendor_complete_prefix_packets")
    vendor_eligible = []
    for i, item in decoded.items():
        p = data[72 * i : 72 * (i + 1)]
        integrity = p[0] == 0xE7 and all(
            sum(p[1:j]) % 256 == p[j] for j in (22, 61, 71)
        )
        if (
            integrity
            and p[21] == 4
            and item["mode"] == 4
            and item["time_valid"]
            and item["velocity_valid"]
            and item["time_ms"] >= 60000000
            and int.from_bytes(p[1:3], "little") < 60000
        ):
            vendor_eligible.append(i)
    require(
        vendor_eligible == [r["index"] for r in own_rows if r["status"] == "eligible"],
        "vendor_eligible_membership",
    )
    eligible = []
    for source in own_rows:
        i = source["index"]
        vendor = decoded[i]
        if source["status"] == "eligible":
            require(
                data[i * 72 + 21] == vendor["mode"] == 4
                and vendor["time_valid"] == vendor["velocity_valid"] == 1,
                "vendor_validity",
            )
            require(
                source["time_ms"] == vendor["time_ms"]
                and source["north_velocity_units"] == vendor["north_velocity_units"],
                "vendor_numeric_disagreement",
            )
            eligible.append(
                dict(
                    source,
                    time_ms=vendor["time_ms"],
                    north_velocity_units=vendor["north_velocity_units"],
                )
            )
    return eligible, decoded


def check_original_bounds(segment, report):
    seen = {i: segment["values"][i] for i in (0, 10, 20)}
    count = 0
    states = [r["before"] for r in report["records"]] + [report["final"]]
    for step, state in enumerate(states):
        points = [(segment["times"][i], seen[i]) for i in sorted(seen)]
        if state["status"] != "inconsistent_premises":
            low, high = map(F, state["uniform_error_range_mps"])
            require(
                low == max(abs(v - interp(segment["knots"], t)) for t, v in points),
                "minimum_error_witness",
            )
            witness = state["maximum_witness"]
            t = F(witness["time_s"])
            # Different proof route: the declared upper error must admit no
            # unsafe world, checked by strict two-variable projection at a fixed reply.
            certification = cv.response_plan(
                points, segment["knots"], RATE, high, points[0][0]
            )
            require(
                certification["possible_statuses"] == ["supported"],
                "conventional_upper_bound",
            )
            lower = max(v - RATE * abs(t - s) for s, v in points)
            upper = min(v + RATE * abs(t - s) for s, v in points)
            value = lower if witness["envelope"] == "lower" else upper
            require(
                str(value) == witness["value_mps"]
                and abs(value - interp(segment["knots"], t)) == high,
                "conventional_maximum_attainment",
            )
            count += 1
        if step < len(report["records"]):
            i = report["records"][step]["query_index"]
            seen[i] = segment["values"][i]
    return count


def main():
    parser = argparse.ArgumentParser()
    for arg in (
        "freeze-sha256",
        "sources",
        "vendor",
        "results",
        "proofs",
        "decoded",
        "output",
        "baseline",
        "vendor-output",
        "timing",
    ):
        parser.add_argument("--" + arg, required=True)
    args = parser.parse_args()
    tick = time.perf_counter()
    cpu = resource.getrusage(resource.RUSAGE_SELF)
    data = bind(Path(__file__).parent, args.sources, args.vendor, args.freeze_sha256)
    actual, proofs, original = load(args.results), load(args.proofs), load(args.decoded)
    require(
        actual["freeze_sha256"] == proofs["freeze_sha256"] == args.freeze_sha256,
        "result_identity",
    )
    rows = decode(data)
    require(
        original["rows"] == rows and original["population"] == population(rows),
        "decoded_complete_population",
    )
    vendor_tick = time.perf_counter()
    process = subprocess.run(
        [args.vendor, str(Path(args.sources) / "ncom-sample-prefix.bin")],
        capture_output=True,
        text=True,
    )
    with Path(args.vendor_output).open("x") as stream:
        stream.write(process.stdout)
    require(process.returncode == 0, "vendor_exit:" + process.stderr)
    eligible, vendor = vendor_values(data, process.stdout, rows)
    selection = select(rows)
    require(
        actual["selection"]
        == original["selection"]
        == (None if selection is None else [r["index"] for r in selection]),
        "selection_identity",
    )
    vendor_by_index = {r["index"]: r for r in eligible}
    if selection:
        selection = [vendor_by_index[r["index"]] for r in selection]
    vendor_seconds = time.perf_counter() - vendor_tick
    prepared = time.perf_counter()
    reports, reference, comparison = [], [], []
    counts = dict(
        native_model_witness_stages=0,
        complete_response_partitions=0,
        conventional_bound_stages=0,
    )
    if selection:
        cases = segments(selection)
        require(
            len(actual["dependent_segments"]) == len(proofs["segments"]) == 5,
            "case_allocation",
        )
        for case, result, proof in zip(
            cases, actual["dependent_segments"], proofs["segments"]
        ):
            require(proof["id"] == case["id"], "proof_id")
            checked = verify_reiyah_segment(case, result, proof)
            for key, value in checked.items():
                counts[key] += value
            baseline_result, _ = run_segment(case, "conventional")
            counts["conventional_bound_stages"] += check_original_bounds(
                case, baseline_result
            )
            reports.append(baseline_result)
            truth = full_reference(case)
            reference.append(truth)
            comparison.append(
                dict(
                    id=case["id"],
                    reiyah=result["final"]["status"],
                    conventional=baseline_result["final"]["status"],
                    reiyah_queries=result["oracle_calls"],
                    conventional_queries=baseline_result["oracle_calls"],
                    original_rate_premise=truth["original_rate_premise"],
                    reference_decision=truth["recorded_fidelity_decision"],
                )
            )
            write_new(
                str(args.output) + "." + case["id"] + ".json",
                dict(
                    status="completed_segment_only",
                    comparison=comparison[-1],
                    full_reference=truth,
                    baseline=baseline_result,
                    cumulative_counts=counts,
                ),
            )
    else:
        require(
            actual["status"] == "blocked_no_eligible_run"
            and actual["dependent_segments"] == proofs["segments"] == [],
            "blocked_selection",
        )
    require(
        actual["source_population"] == population(rows)
        and actual["total_oracle_calls"]
        == sum(r["oracle_calls"] for r in actual["dependent_segments"]),
        "reported_population_cost",
    )
    errors = []
    for row in comparison:
        if row["original_rate_premise"] == "rejected":
            continue
        for arm in ("reiyah", "conventional"):
            if (
                row[arm] in ("supported", "contradicted")
                and row[arm] != row["reference_decision"]
            ):
                errors.append(
                    dict(
                        segment=row["id"],
                        arm=arm,
                        kind="false_acceptance"
                        if row[arm] == "supported"
                        else "false_refusal",
                    )
                )
    calculated = time.perf_counter()
    write_new(
        args.baseline,
        dict(
            document_id="reiyah.navigation-measurement.conventional",
            version="0.1.1",
            freeze_sha256=args.freeze_sha256,
            dependent_segments=reports,
            total_oracle_calls=sum(r["oracle_calls"] for r in reports),
            full_reference=reference,
            comparison=comparison,
        ),
    )
    report = dict(
        document_id="reiyah.navigation-measurement.check",
        version="0.1.1",
        status="failed_incorrect_recorded_decision" if errors else "passed",
        freeze_sha256=args.freeze_sha256,
        source_packets_checked=len(rows),
        vendor_packet_outputs=len(vendor),
        eligible_values_checked=len(eligible),
        selected_samples=0 if selection is None else len(selection),
        dependent_segments=len(reports),
        counts=counts,
        comparison=comparison,
        false_acceptances=[r for r in errors if r["kind"] == "false_acceptance"],
        false_refusals=[r for r in errors if r["kind"] == "false_refusal"],
        rejected_empirical_bindings=[
            r["id"] for r in comparison if r["original_rate_premise"] == "rejected"
        ],
        physical_cases=0,
        physical_qualification="unresolved",
        independent_replication=False,
        authorship="Manufacturer decoder separately authored; decision methods, wrappers and study same author.",
    )
    write_new(args.output, report)
    end = resource.getrusage(resource.RUSAGE_SELF)
    write_new(
        args.timing,
        dict(
            arm="strong_conventional_and_independent_check",
            preparation_seconds=prepared - tick,
            vendor_seconds_nested=vendor_seconds,
            calculation_seconds=calculated - prepared,
            process_through_output_seconds=time.perf_counter() - tick,
            cpu_seconds=end.ru_utime + end.ru_stime - cpu.ru_utime - cpu.ru_stime,
            child_vendor_cpu_in_supervisor_only=True,
            source_bytes_loaded=len(data),
            logical_queries=sum(r["oracle_calls"] for r in reports),
        ),
    )
    print(
        dict(
            status=report["status"],
            selected_samples=report["selected_samples"],
            counts=counts,
            comparison=comparison,
        )
    )
    require(not errors, "incorrect_recorded_decision")


if __name__ == "__main__":
    main()
