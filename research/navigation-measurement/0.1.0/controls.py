"""Directed parser, continuum and retained-result rejection controls."""

import argparse
import copy
from fractions import Fraction as F
from pathlib import Path
import shutil
import tempfile

from binding import bind
from common import Invalid, load, parse_case, require, write_new
import conventional as cv
from decode import decode, select
from experiment import Oracle, TOLERANCE, segments
from residual import evaluate, model, response_plan
from responses import response_status


def packet(ms=0, velocity=0, mode=4, channel=1, minute=20000000):
    p = bytearray(72)
    p[0], p[21], p[62] = 0xE7, mode, channel
    p[1:3] = ms.to_bytes(2, "little")
    p[43:46] = velocity.to_bytes(3, "little", signed=True)
    if channel == 0:
        p[63:67] = minute.to_bytes(4, "little", signed=True)
    for i in (22, 61, 71):
        p[i] = sum(p[1:i]) % 256
    return bytes(p)


ANCHOR = packet(mode=10, channel=0)


def main():
    parser = argparse.ArgumentParser()
    for arg in ("mode", "freeze-sha256", "sources", "vendor", "output"):
        parser.add_argument("--" + arg, required=True)
    for arg in ("results", "proofs", "decoded"):
        parser.add_argument("--" + arg)
    args = parser.parse_args()
    bind(Path(__file__).parent, args.sources, args.vendor, args.freeze_sha256)
    records = []

    def test(name, condition):
        require(condition, "control_failed:" + name)
        records.append(dict(id=name, status="passed"))

    def rejects(name, call, needle=None):
        try:
            call()
        except (Invalid, ValueError, AssertionError) as exc:
            require(needle is None or needle in str(exc), "wrong_rejection:" + name)
            records.append(dict(id=name, status="rejected_as_expected"))
            return
        raise AssertionError("accepted_bad_control:" + name)

    if args.mode == "pre":
        rows = decode(ANCHOR + packet())
        test(
            "exact-recorded-zero",
            rows[1]["status"] == "eligible" and rows[1]["north_velocity_units"] == 0,
        )
        test("missing-clock-not-zero", decode(packet())[0]["time_ms"] is None)
        test(
            "status-only-not-measurement",
            rows[0]["time_ms"] is None and rows[0]["north_velocity_units"] is None,
        )
        test(
            "sentinel-not-zero",
            decode(ANCHOR + packet(velocity=-(2**23)))[1]["reason"]
            == "invalid_velocity_sentinel",
        )
        corrupt = bytearray(packet())
        corrupt[45] ^= 1
        test(
            "checksum-corruption-retained",
            decode(ANCHOR + bytes(corrupt))[1]["status"] == "invalid",
        )
        wrap = decode(ANCHOR + packet(ms=59990) + packet(ms=0))
        test("minute-wrap", wrap[2]["time_ms"] - wrap[1]["time_ms"] == 10)
        test(
            "unexplained-clock-rewind",
            decode(ANCHOR + packet(ms=30000) + packet(ms=20000))[2]["time_ms"] is None,
        )
        test(
            "invalid-minute-anchor",
            decode(packet(mode=10, channel=0, minute=999) + packet())[1]["time_ms"]
            is None,
        )
        test(
            "asynchronous-not-synchronous",
            decode(ANCHOR + packet(mode=22))[1]["status"] != "eligible",
        )
        sequence = ANCHOR + b"".join(packet(ms=i * 10) for i in range(102))
        test(
            "first-eligible-run",
            [r["index"] for r in select(decode(sequence))] == list(range(1, 102)),
        )
        gap = ANCHOR + b"".join(
            packet(ms=i * 10 + (10 if i >= 50 else 0)) for i in range(101)
        )
        test("native-gap-breaks-run", select(decode(gap)) is None)
        rejects("unaligned-prefix", lambda: decode(sequence[:-1]), "packet_alignment")
        base = [(F(0), F(0)), (F(1, 5), F(0))]
        typed = model(base, F(1), TOLERANCE, 1)
        wrong = copy.deepcopy(typed)
        wrong["quantity"]["unit"] = "m"
        rejects("wrong-quantity-unit", lambda: parse_case(wrong), "quantity_scope")
        many = [(F(i, 100), F(0)) for i in range(21)]
        test(
            "21-native-observations",
            len(parse_case(model(many, F(1), TOLERANCE, 1))[5]) == 21,
        )
        rejects(
            "22-observations-excluded",
            lambda: parse_case(model(many + [(F(21, 100), F(0))], F(1), TOLERANCE, 1)),
            "observation_cap",
        )
        prediction, _ = response_plan(base, F(1), TOLERANCE, F(1, 10))
        expected = cv.response_plan(base, base, F(1), TOLERANCE, F(1, 10))
        test(
            "joint-continuum-partition",
            prediction == expected
            and prediction["possible_statuses"]
            == ["contradicted", "supported", "unresolved"],
        )
        test(
            "singleton-support-and-open-neighbors",
            response_status(prediction, F(0)) == "supported"
            and all(
                response_status(prediction, v) == "unresolved"
                for v in (F(-1, 1000), F(1, 1000), -TOLERANCE, TOLERANCE)
            ),
        )
        test(
            "fidelity-equality-included",
            evaluate(base + [(F(1, 10), F(0))], F(1), TOLERANCE)[0]
            == dict(status="supported", uniform_error_range_mps=["0", "1/20"]),
        )
        test(
            "inconsistent-is-distinct",
            evaluate([(F(0), F(0)), (F(1, 5), F(1))], F(1), TOLERANCE)[0]["status"]
            == "inconsistent_premises",
        )
        slope_knots = [(F(0), F(0)), (F(1, 10), F(1, 10)), (F(1, 5), F(1, 5))]
        original = cv.error_bounds(slope_knots, slope_knots, F(1), TOLERANCE)
        relaxed = evaluate([(t, F(0)) for t, _ in slope_knots], F(2), TOLERANCE)[0]
        test(
            "strong-baseline-retains-slope",
            original["status"] == "supported"
            and original["uniform_error_range_mps"] == ["0", "0"]
            and relaxed["status"] == "unresolved",
        )
        bent = [(F(0), F(0)), (F(1, 10), F(1, 40)), (F(1, 5), F(0))]
        plan = cv.response_plan(bent, bent, F(1), TOLERANCE, F(1, 20))
        values = {
            F(cell[k])
            for cell in plan["response_partition"]
            for k in ("lower", "upper")
        }
        values |= {
            (F(cell["lower"]) + F(cell["upper"])) / 2
            for cell in plan["response_partition"]
        }
        test(
            "original-coordinate-response-cells",
            all(
                response_status(plan, y)
                == cv.error_bounds(bent + [(F(1, 20), y)], bent, F(1), TOLERANCE)[
                    "status"
                ]
                for y in values
            ),
        )
        negative = [(t, -v) for t, v in bent]
        mirror = cv.response_plan(negative, negative, F(1), TOLERANCE, F(1, 20))
        test(
            "two-sided-sign-symmetry",
            all(
                response_status(plan, y) == response_status(mirror, -y) for y in values
            ),
        )
        oracle = Oracle([F(0)] * 21)
        oracle.acquire(1)
        rejects(
            "repeat-acquisition", lambda: oracle.acquire(1), "oracle_repeated_query"
        )
        rejects(
            "freeze-tamper",
            lambda: bind(Path(__file__).parent, args.sources, args.vendor, "0" * 64),
            "freeze_identity",
        )
        with tempfile.TemporaryDirectory(prefix="source-tamper-") as path:
            altered = Path(path)
            for name in load(Path(__file__).parent / "freeze.json")["sources"]:
                shutil.copyfile(Path(args.sources) / name, altered / name)
            p = altered / "ncom-sample-prefix.bin"
            data = bytearray(p.read_bytes())
            data[43] ^= 1
            p.write_bytes(data)
            rejects(
                "source-byte-tamper",
                lambda: bind(
                    Path(__file__).parent, altered, args.vendor, args.freeze_sha256
                ),
                "source_identity",
            )
        require(len(records) == 25, "pre_control_allocation")
    elif args.mode == "post":
        from check import verify_reiyah_segment

        actual, proofs, decoded = (
            load(args.results),
            load(args.proofs),
            load(args.decoded),
        )
        require(actual["dependent_segments"], "post_controls_need_executed_case")
        selected = [decoded["rows"][i] for i in decoded["selection"]]
        case = segments(selected)[0]
        original = actual["dependent_segments"][0]
        proof = proofs["segments"][0]
        mutations = []
        x = copy.deepcopy(original)
        x["final"]["status"] = (
            "contradicted" if x["final"]["status"] != "contradicted" else "supported"
        )
        mutations.append(("wrong-final-decision", x))
        x = copy.deepcopy(original)
        x["oracle_calls"] += 1
        mutations.append(("wrong-query-cost", x))
        x = copy.deepcopy(original)
        x["records"][0]["source_index"] += 1
        mutations.append(("wrong-source-association", x))
        x = copy.deepcopy(original)
        x["records"][0]["response_mps"] = "999"
        mutations.append(("wrong-acquired-value", x))
        x = copy.deepcopy(original)
        x["records"][0]["predicted"]["guaranteed_resolution"] = not x["records"][0][
            "predicted"
        ]["guaranteed_resolution"]
        mutations.append(("false-resolution-guarantee", x))
        x = copy.deepcopy(original)
        x["records"][0]["predicted"]["response_partition"].pop()
        mutations.append(("omitted-response-cell", x))
        x = copy.deepcopy(original)
        x["records"][0]["predicted"]["response_partition"][0]["lower_closed"] = not x[
            "records"
        ][0]["predicted"]["response_partition"][0]["lower_closed"]
        mutations.append(("changed-strict-boundary", x))
        x = copy.deepcopy(original)
        x["records"].pop()
        mutations.append(("omitted-acquisition-stage", x))
        for name, mutant in mutations:
            rejects(
                name,
                lambda mutant=mutant: verify_reiyah_segment(case, mutant, proof),
                "complete_reiyah_protocol",
            )
        require(len(records) == 8, "post_control_allocation")
    else:
        raise Invalid("control_mode")
    write_new(
        args.output,
        dict(
            document_id="reiyah.navigation-measurement.controls",
            version="0.1.0",
            mode=args.mode,
            status="passed",
            count=len(records),
            records=records,
            scope="Directed authored controls and actual-result mutations; not empirical coverage or additional independent cases.",
        ),
    )
    print(dict(mode=args.mode, status="passed", controls=len(records)))


if __name__ == "__main__":
    main()
