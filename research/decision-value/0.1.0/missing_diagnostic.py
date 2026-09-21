"""Post-result diagnostic: no imputation, no new empirical decision."""

from copy import deepcopy
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import sys

from contract import HERE, bind_sources, read_case, require
from controls import refusal
from verify import check, pairwise_delta

root, vendor = map(Path, sys.argv[1:])
binding = json.loads((HERE / "diagnostic-freeze.json").read_text())
require(
    hashlib.sha256(Path(__file__).read_bytes()).hexdigest() == binding["code_sha256"],
    "diagnostic_code_identity",
)
bind_sources(vendor)
reference = json.loads((root / "private/outputs/reiyah/result.json").read_text())
trace = json.loads((root / "private/outputs/reiyah/trace.json").read_text())
diagnostics = []
mutations = []
for arm in ("conventional", "reiyah"):
    record = json.loads((root / "private/outputs" / arm / "result.json").read_text())
    original = json.loads((root / "private/outputs" / arm / "trace.json").read_text())
    for i, item in enumerate(record["cases"]):
        if item["status"] != "blocked":
            continue
        for name, changes in (
            ("false_support", {"status": "supported", "delta_m2": -1.0}),
            ("numeric_imputation", {"delta_m2": 0.0}),
            ("false_refusal", {"status": "contradicted", "delta_m2": 1.0}),
        ):
            altered = deepcopy(record)
            altered["cases"][i].update(changes)
            refusal(
                arm + ":" + name,
                "partial_cohort_decision",
                lambda a=altered: check(a, original, vendor),
                mutations,
            )

for item in reference["cases"]:
    if item["status"] != "blocked":
        continue
    seq, count = item["sequence"], item["expected_visits"]
    gt, poses, _ = read_case(vendor, seq, count)
    a, b = trace[seq]["online"], trace[seq]["offline"]
    require(len(a) == count and len(b) == count - 1, "single_missing_offline_required")
    missing = next(g for g in gt if g["id"] not in {m["id"] for m in b})
    sums = {}
    for mode, matches in (("online", a), ("offline", b)):
        sums[mode] = sum(
            (Fraction(x) - Fraction(q)) ** 2
            for m in matches
            for x, q in zip(m["position"], m["q"])
        )
    constant = sums["offline"] - sums["online"]
    target = -constant
    worlds = []
    for distance in (0.0, 2.0):
        added = {
            "id": missing["id"],
            "q": missing["q"],
            "position": [missing["q"][0] + distance, *missing["q"][1:]],
        }
        by_id = {m["id"]: m for m in [*b, added]}
        completed = [by_id[m["id"]] for m in a]
        delta = pairwise_delta(a, completed)
        independently_summed = (
            sum(
                (Fraction(x) - Fraction(q)) ** 2
                for m in completed
                for x, q in zip(m["position"], m["q"])
            )
            - sums["online"]
        ) / count
        require(delta == independently_summed, "completion_algebra")
        worlds.append(
            {
                "authored_missing_error_m": distance,
                "delta_m2": float(delta),
                "decision": "supported"
                if delta < 0
                else "contradicted"
                if delta > 0
                else "null",
                "observed": False,
            }
        )
    nearest = min(poses["offline"], key=lambda row: abs(row[0] - missing["t"]))
    diagnostics.append(
        {
            "sequence": seq,
            "missing_checkpoint_id": missing["id"],
            "nearest_available_offline_offset_seconds": abs(nearest[0] - missing["t"]),
            "offline_trajectory_ends_seconds_before_visit": missing["t"]
            - poses["offline"][-1][0],
            "observed_online_visits": len(a),
            "observed_offline_visits": len(b),
            "known_loss_difference_sum_m2": float(constant),
            "missing_squared_error_boundary_exact": [
                str(target.numerator),
                str(target.denominator),
            ],
            "missing_error_boundary_m_approx": math.sqrt(float(target))
            if target > 0
            else None,
            "complete_nominal_delta_formula": "(known_loss_difference_sum_m2 + missing_squared_error_m2) / 36",
            "condition": "strictly smaller than boundary supports; equality ties; larger contradicts",
            "physical_claim": "unresolved",
            "counterfactual_completions": worlds,
            "actual_full_cohort_status": "blocked",
            "additional_record": "published offline base-center position at this frozen checkpoint time, with the same coordinate and association provenance",
        }
    )
require(bool(diagnostics), "no_missing_case_diagnostic")
output = {
    "document_id": "reiyah.decision-value.missing-diagnostic",
    "version": "0.1.0",
    "status": "exploratory_post_result",
    "study_freeze_sha256": binding["study_freeze_sha256"],
    "diagnostics": diagnostics,
    "partial_case_mutations": mutations,
    "new_observed_positions": 0,
    "new_physical_evidence": False,
}
(root / "private/outputs/missing-diagnostic.json").write_text(
    json.dumps(output, indent=2, allow_nan=False) + "\n"
)
print(json.dumps(output, indent=2, allow_nan=False))
