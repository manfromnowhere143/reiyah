"""Separate association and algebraic checker; never calls decision.run/case."""

import argparse
import bisect
from fractions import Fraction
import json
import math
from pathlib import Path

from contract import (
    COUNTS,
    FRAME,
    MODES,
    QUESTION_SHA256,
    SEQUENCES,
    SCOPE,
    Refusal,
    bind_sources,
    read_case,
    require,
    vendor_modules,
)


def near(actual, expected, name):
    require(
        isinstance(actual, (int, float))
        and not isinstance(actual, bool)
        and math.isfinite(actual),
        "numeric:" + name,
    )
    require(
        math.isclose(actual, expected, rel_tol=1e-10, abs_tol=1e-12), "metric:" + name
    )


def reconstruct(gt, rows, origin, coords):
    times = [row[0] for row in rows]
    matches = []
    for visit, g in enumerate(gt):
        cursor = bisect.bisect_left(times, g["t"])
        candidates = [j for j in (cursor - 1, cursor) if 0 <= j < len(times)]
        chosen = sorted(candidates, key=lambda j: (abs(times[j] - g["t"]), j))[0]
        offset = abs(times[chosen] - g["t"])
        if offset <= 2:
            position = coords.convert_extracted_points_to_utm(
                [{"position": rows[chosen][1:4]}], origin
            )[0]["position"]
            matches.append(
                {
                    "visit": visit,
                    "id": g["id"],
                    "source_row": chosen,
                    "dt": offset,
                    "position": list(map(float, position)),
                    "q": g["q"],
                }
            )
    return matches


def pairwise_delta(online, offline):
    require(len(online) == len(offline) and bool(online), "pair_count")
    total = Fraction(0)
    for a, b in zip(online, offline):
        require(a["id"] == b["id"] and a["q"] == b["q"], "pair_identity")
        for av, bv, qv in zip(a["position"], b["position"], a["q"]):
            av, bv, qv = map(Fraction, (av, bv, qv))
            total += (bv - av) * (bv + av - 2 * qv)
    return total / len(online)


def check(record, traces, root):
    revision = bind_sources(root)
    coords = vendor_modules(root)[0]
    require(
        set(record)
        == {
            "document_id",
            "version",
            "arm",
            "question_sha256",
            "source_revision",
            "scope",
            "frame",
            "physical_claim",
            "cases",
            "workflow_seconds",
        },
        "record_fields",
    )
    require(
        record["document_id"] == "reiyah.decision-value.result"
        and record["version"] == "0.1.0",
        "record_identity",
    )
    require(record["arm"] in ("reiyah", "conventional"), "arm")
    require(
        record["question_sha256"] == QUESTION_SHA256
        and record["source_revision"] == revision,
        "result_binding",
    )
    require(
        record["scope"] == SCOPE and record["physical_claim"] == "unresolved",
        "claim_scope",
    )
    require(record["frame"] == FRAME, "frame_contract")
    require(
        math.isfinite(record["workflow_seconds"]) and record["workflow_seconds"] >= 0,
        "cost_value",
    )
    require([c["sequence"] for c in record["cases"]] == list(SEQUENCES), "case_cohort")
    require(set(traces) == set(SEQUENCES), "trace_cohort")
    checked, nominal = 0, []
    for item, seq, count in zip(record["cases"], SEQUENCES, COUNTS):
        require(item["expected_visits"] == count, "expected_cohort")
        try:
            gt, poses, origin = read_case(root, seq, count)
        except (Refusal, OSError, ValueError) as exc:
            require(
                item
                == {
                    "sequence": seq,
                    "expected_visits": count,
                    "status": "invalid",
                    "reason": str(exc),
                    "delta_m2": None,
                },
                "invalid_case",
            )
            require(traces[seq] == {}, "invalid_trace")
            nominal.append({"sequence": seq, "status": "invalid", "reason": str(exc)})
            continue
        require(
            set(item)
            == {
                "sequence",
                "expected_visits",
                "status",
                "modes",
                "delta_m2",
                "exact_delta_ratio",
            },
            "case_fields",
        )
        require(
            set(item["modes"]) == set(MODES) and set(traces[seq]) == set(MODES),
            "mode_cohort",
        )
        expected = {}
        for mode in MODES:
            matches = reconstruct(gt, poses[mode], origin, coords)
            expected[mode] = matches
            require(traces[seq][mode] == matches, "association_trace")
            checked += len(matches)
            md = item["modes"][mode]
            require(
                set(md)
                == {
                    "matched",
                    "missing_ids",
                    "max_dt_seconds",
                    "available_cohort_mse",
                    "available_cohort_rmse",
                },
                "mode_fields",
            )
            missing = [g["id"] for g in gt if g["id"] not in {m["id"] for m in matches}]
            require(
                md["matched"] == len(matches) and md["missing_ids"] == missing,
                "coverage",
            )
            require(
                md["max_dt_seconds"] == max((m["dt"] for m in matches), default=None),
                "association_offset",
            )
            if matches:
                # Separate floating reference for each published mode metric.
                squared = [
                    math.fsum((x - y) ** 2 for x, y in zip(m["position"], m["q"]))
                    for m in matches
                ]
                mse = math.fsum(squared) / len(matches)
                near(md["available_cohort_mse"], mse, mode + "_mse")
                near(md["available_cohort_rmse"], math.sqrt(mse), mode + "_rmse")
            else:
                require(
                    md["available_cohort_mse"] is None
                    and md["available_cohort_rmse"] is None,
                    "empty_metric",
                )
        complete = all(len(expected[m]) == count for m in MODES)
        if not complete:
            require(
                item["status"] == "blocked"
                and item["delta_m2"] is None
                and item["exact_delta_ratio"] is None,
                "partial_cohort_decision",
            )
            nominal.append({"sequence": seq, "status": "blocked"})
            continue
        delta = pairwise_delta(expected["online"], expected["offline"])
        status = "supported" if delta < 0 else "contradicted" if delta > 0 else "null"
        require(item["status"] == status, "decision_sign")
        near(item["delta_m2"], float(delta), "delta")
        reported_sign = (item["delta_m2"] > 0) - (item["delta_m2"] < 0)
        require(reported_sign == (delta > 0) - (delta < 0), "numeric_sign_unresolved")
        ratio = (
            [str(delta.numerator), str(delta.denominator)]
            if record["arm"] == "reiyah"
            else None
        )
        require(item["exact_delta_ratio"] == ratio, "exact_ratio")
        nominal.append({"sequence": seq, "status": status, "delta_m2": float(delta)})
    return {
        "status": "passed",
        "arm": record["arm"],
        "cases": len(record["cases"]),
        "associations_checked": checked,
        "nominal": nominal,
        "physical_claim": "unresolved",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("vendor", type=Path)
    parser.add_argument("results", type=Path, nargs="+")
    args = parser.parse_args()
    results = []
    for folder in args.results:
        record = json.loads((folder / "result.json").read_text())
        traces = json.loads((folder / "trace.json").read_text())
        results.append(check(record, traces, args.vendor))
    print(json.dumps(results, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
