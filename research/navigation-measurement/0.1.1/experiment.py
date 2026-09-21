"""Frozen source selector and fixed, explicitly charged acquisition experiment."""

from fractions import Fraction as F

from common import require
import conventional
import residual
from responses import response_status

TOLERANCE = F(1, 20)
RATE = F(5)


def segments(selected):
    require(len(selected) == 101, "selection_count")
    require(
        all(b["time_ms"] - a["time_ms"] == 10 for a, b in zip(selected, selected[1:])),
        "selection_clock",
    )
    result = []
    for start in range(0, 100, 20):
        rows = selected[start : start + 21]
        times = [F(i, 100) for i in range(21)]
        values = [F(r["north_velocity_units"], 10000) for r in rows]
        knots = [(times[i], values[i]) for i in (0, 10, 20)]
        slopes = [abs((b[1] - a[1]) / (b[0] - a[0])) for a, b in zip(knots, knots[1:])]
        result.append(
            dict(
                id=f"segment-{start // 20}",
                source_indices=[r["index"] for r in rows],
                times=times,
                values=values,
                knots=knots,
                residual_rate=RATE + max(slopes),
            )
        )
    return result


class Oracle:
    def __init__(self, values):
        require(len(values) == 21, "oracle_allocation")
        self.values = tuple(values)
        self.calls = []

    def acquire(self, index):
        require(
            type(index) is int and 0 <= index < 21 and index not in (0, 10, 20),
            "oracle_query",
        )
        require(index not in self.calls, "oracle_repeated_query")
        self.calls.append(index)
        return self.values[index]


def run_segment(segment, arm):
    require(arm in ("reiyah", "conventional"), "arm")
    times, values, knots = segment["times"], segment["values"], segment["knots"]
    oracle = Oracle(values)
    seen = {i: values[i] for i in (0, 10, 20)}
    records, witnesses = [], []
    for step in range(19):
        original = [(times[i], seen[i]) for i in sorted(seen)]
        remaining = [i for i in range(21) if i not in seen]
        if arm == "reiyah":
            observed = [(t, v - conventional.baseline(knots, t)) for t, v in original]
            state, proof = residual.evaluate(
                observed, segment["residual_rate"], TOLERANCE
            )
            witnesses.append(dict(step=step, margins=proof))
        else:
            observed = original
            state = conventional.error_bounds(observed, knots, RATE, TOLERANCE)
            witnesses.append(dict(step=step, bound=state))
        if step == 0:
            initial = state
        if state["status"] != "unresolved" or not remaining:
            final = state
            break
        if arm == "reiyah":
            index = residual.next_index(
                observed, segment["residual_rate"], remaining, times
            )
            prediction, components = residual.response_plan(
                observed, segment["residual_rate"], TOLERANCE, times[index]
            )
        else:
            index = conventional.next_index(observed, knots, RATE, remaining, times)
            prediction = conventional.response_plan(
                observed, knots, RATE, TOLERANCE, times[index]
            )
            components = None
        value = oracle.acquire(index)
        reply = (
            value - conventional.baseline(knots, times[index])
            if arm == "reiyah"
            else value
        )
        records.append(
            dict(
                step=step,
                query_index=index,
                source_index=segment["source_indices"][index],
                time_s=str(times[index]),
                before=state,
                predicted=prediction,
                margin_partitions=components,
                observed_north_velocity_mps=str(value),
                response_mps=str(reply),
                response_status=response_status(prediction, reply),
            )
        )
        seen[index] = value
    for i, row in enumerate(records):
        after = records[i + 1]["before"] if i + 1 < len(records) else final
        row["after"] = after
        require(row["response_status"] == after["status"], "actual_reply_recomputation")
    return dict(
        id=segment["id"],
        arm=arm,
        initial=initial,
        final=final,
        oracle_calls=len(oracle.calls),
        query_indices=oracle.calls,
        coarse_indices=[0, 10, 20],
        unqueried_indices=[i for i in range(21) if i not in seen],
        workflow_status="exhausted"
        if final["status"] == "unresolved"
        else final["status"],
        records=records,
    ), witnesses


def full_reference(segment):
    values, times, knots = segment["values"], segment["times"], segment["knots"]
    slopes = [
        abs((b - a) / (t1 - t0))
        for a, b, t0, t1 in zip(values, values[1:], times, times[1:])
    ]
    errors = [abs(v - conventional.baseline(knots, t)) for t, v in zip(times, values)]
    bad = [i for i, s in enumerate(slopes) if s > RATE]
    peak = max(errors)
    return dict(
        id=segment["id"],
        native_intervals=20,
        original_rate_premise="rejected"
        if bad
        else "supported_for_declared_recorded_reconstruction",
        violating_interval_indices=bad,
        maximum_recorded_slope_mps2=str(max(slopes)),
        maximum_affine_error_mps=str(peak),
        maximum_error_source_index=segment["source_indices"][errors.index(peak)],
        recorded_fidelity_decision="supported" if peak <= TOLERANCE else "contradicted",
        physical_qualification="unresolved",
    )
