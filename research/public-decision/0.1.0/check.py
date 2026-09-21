"""Reconstruct source sums and endpoint completions without either arm."""

from collections import Counter
import copy
from decimal import Decimal
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import sys

EXPECTED = {
    "UniAD-Base.json": "ab07b2b9ab3bfe614bf7bc15c70ad9e4543ab664448dba98641b33fe6aa4dfac",
    "UniAD-Tiny.json": "b0f60431dc667ae692787c9ee11dc7911d1f6bc39f30fabe518007a37888c900",
}
SCOPE = "Conditional recorded-score completion; official cohort and execution binding unresolved"


def load_source(directory):
    data = []
    for name, digest in EXPECTED.items():
        raw = (directory / name).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == digest
        rows = json.loads(raw, parse_float=Decimal)["_checkpoint"]["records"]
        assert len({r["route_id"] for r in rows}) == len(rows) <= 220
        assert all(
            F(r["scores"]["score_composed"]) >= 0
            and F(r["scores"]["score_composed"]) <= 100
            for r in rows
        )
        assert all(
            r["status"] in ("Completed", "Perfect", "Crashed")
            or r["status"].startswith("Failed")
            for r in rows
        )
        data.append(rows)
    return data


def reference(rows):
    a, b = rows
    aa, bb = {r["route_id"]: r for r in a}, {r["route_id"]: r for r in b}
    shared = sorted(aa.keys() & bb.keys())
    assert len(aa.keys() | bb.keys()) <= 220
    for k in shared:
        assert [aa[k][f] for f in ("scenario_name", "weather_id", "town_name")] == [
            bb[k][f] for f in ("scenario_name", "weather_id", "town_name")
        ]
    values = [[F(r["scores"]["score_composed"]) for r in arm] for arm in rows]
    sums = [sum(arm, F(0)) for arm in values]
    counts = [len(a), len(b)]
    missing = [220 - n for n in counts]
    # Explicitly complete two 220-member vectors, then subtract their means.
    low_a = values[0] + [F(0)] * missing[0]
    low_b = values[1] + [F(100)] * missing[1]
    high_a = values[0] + [F(100)] * missing[0]
    high_b = values[1] + [F(0)] * missing[1]
    assert all(len(x) == 220 for x in (low_a, low_b, high_a, high_b))
    lower = sum(low_a) / 220 - sum(low_b) / 220
    upper = sum(high_a) / 220 - sum(high_b) / 220
    state = "supported" if lower > 0 else "excluded" if upper <= 0 else "unresolved"
    expected = {
        "n": 220,
        "base_count": counts[0],
        "tiny_count": counts[1],
        "shared_count": len(shared),
        "union_count": len(aa.keys() | bb.keys()),
        "original_complete_pair": "supported"
        if len(shared) == counts[0] == counts[1] == 220
        else "blocked",
        "base_sum": str(sums[0]),
        "tiny_sum": str(sums[1]),
        "zero_fill_means": [str(x / 220) for x in sums],
        "difference_bounds": [str(lower), str(upper)],
        "conditional_aggregate_decision": state,
        "missing": missing,
        "scope": SCOPE,
    }
    blocks = []
    for i, label in enumerate(("base", "tiny")):
        if counts[i]:
            val = 2 * sums[i] / (100 * counts[i]) - 1
            if i == 1:
                val = -val
            blocks.append(
                (label + "_observed", F(counts[i], 440), val, val, "observed")
            )
    for i, label in enumerate(("base", "tiny")):
        if missing[i]:
            blocks.append(
                (label + "_missing", F(missing[i], 440), F(-1), F(1), "missing")
            )
    assert sum(x[1] for x in blocks) == 1
    return expected, blocks


def verify(result, expected, blocks, arm):
    required = {
        "summary",
        "document_id",
        "version",
        "arm",
        "source_sha256",
        "internal_seconds_through_computation",
        "scope",
    } | ({"population"} if arm == "native" else set())
    assert set(result) == required
    assert result["document_id"] == "reiyah.public-decision.arm-result"
    assert result["version"] == "0.1.0" and result["arm"] == arm
    assert result["source_sha256"] == EXPECTED
    assert result["summary"] == expected
    assert (
        result["scope"]
        == "Post-structure conditional diagnostic; original complete-group question blocked"
    )
    assert type(result["internal_seconds_through_computation"]) in (float, int)
    assert result["internal_seconds_through_computation"] >= 0
    if arm == "native":
        p = result["population"]
        assert set(p) == {"id", "version", "threshold", "purpose", "units"}
        assert p["id"] == "recorded-score-completion" and p["version"] == "0.1.0"
        assert p["threshold"] == "0"
        assert p["purpose"] == "conditional missing-score diagnostic"
        assert len(p["units"]) == len(blocks) <= 6
        for u, (identity, weight, lo, hi, state) in zip(p["units"], blocks):
            assert u == {
                "id": identity,
                "weight": str(weight),
                "lower": str(lo),
                "upper": str(hi),
                "proxy": "0",
                "status": state,
                "cluster": identity,
            }
        assert (
            str(100 * sum(w * lo for _, w, lo, _, _ in blocks))
            == expected["difference_bounds"][0]
        )
        assert (
            str(100 * sum(w * hi for _, w, _, hi, _ in blocks))
            == expected["difference_bounds"][1]
        )


def main():
    directory, cpath, npath, output = map(Path, sys.argv[1:])
    rows = load_source(directory)
    expected, blocks = reference(rows)
    actual = {
        "conventional": json.loads(cpath.read_text()),
        "native": json.loads(npath.read_text()),
    }
    for arm, result in actual.items():
        verify(result, expected, blocks, arm)
    changes = [
        (
            "lower_endpoint",
            lambda x: x["summary"]["difference_bounds"].__setitem__(0, "0"),
        ),
        (
            "upper_endpoint",
            lambda x: x["summary"]["difference_bounds"].__setitem__(1, "0"),
        ),
        ("count", lambda x: x["summary"].__setitem__("tiny_count", 220)),
        (
            "zero_fill_mean",
            lambda x: x["summary"]["zero_fill_means"].__setitem__(0, "0"),
        ),
        ("missing_to_zero", lambda x: x["summary"].__setitem__("missing", [0, 0])),
        (
            "decision",
            lambda x: x["summary"].__setitem__(
                "conditional_aggregate_decision", "excluded"
            ),
        ),
        (
            "unblock_original",
            lambda x: x["summary"].__setitem__("original_complete_pair", "supported"),
        ),
        (
            "binding",
            lambda x: x["source_sha256"].__setitem__("UniAD-Base.json", "0" * 64),
        ),
        ("unknown_property", lambda x: x.__setitem__("extra", True)),
        ("scope", lambda x: x.__setitem__("scope", "real_world_safety")),
    ]
    controls = []
    for arm, result in actual.items():
        for name, edit in changes:
            forged = copy.deepcopy(result)
            edit(forged)
            try:
                verify(forged, expected, blocks, arm)
            except AssertionError:
                controls.append(arm + ":" + name)
            else:
                raise AssertionError("mutation_accepted:" + name)
    for field, bad in (("weight", "0"), ("status", "observed"), ("lower", "0")):
        forged = copy.deepcopy(actual["native"])
        missing = next(
            u for u in forged["population"]["units"] if u["status"] == "missing"
        )
        missing[field] = bad
        try:
            verify(forged, expected, blocks, "native")
        except AssertionError:
            controls.append("native:block_" + field)
        else:
            raise AssertionError("block_mutation_accepted")
    report = {
        "document_id": "reiyah.public-decision.check",
        "version": "0.1.0",
        "status": "passed",
        "source_records_checked": [len(x) for x in rows],
        "summary": expected,
        "actual_result_mutations_rejected": controls,
        "extreme_completions_checked": 2,
        "endpoint_completions_are_observations": False,
        "producer_imported": False,
        "independent_replication": False,
        "missing_only_from_tiny": sorted(
            {r["route_id"] for r in rows[0]} - {r["route_id"] for r in rows[1]}
        ),
        "base_group_counts": dict(
            sorted(Counter(r["scenario_name"] for r in rows[0]).items())
        ),
        "tiny_group_counts": dict(
            sorted(Counter(r["scenario_name"] for r in rows[1]).items())
        ),
    }
    assert not output.exists()
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: report[k]
                for k in (
                    "status",
                    "source_records_checked",
                    "summary",
                    "extreme_completions_checked",
                )
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
