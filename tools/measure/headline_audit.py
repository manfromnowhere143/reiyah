"""Check a headline against its own assumptions and the counterexamples already retained.

This lane published three claims in `review-cost-0.1.0` that did not survive
consumer review, and the third is the one that matters for process: **it
contradicted an artifact this lane had itself published four checkpoints
earlier**. `resolution-plan-0.3.0` retains a case where two adaptive questions beat
the smallest fixed set of three, with no prior anywhere in the calculation. Then
`review-cost-0.1.0` concluded that no ordering helps without a prior. Both are in
this repository.

A lane that cannot keep its own results consistent across five days cannot be
relied on, so the repair is mechanical rather than an intention to be careful. Every
headline is registered here with the assumptions it needs and the retained artifacts
that could refute it, and the check runs before a checkpoint is published.

What this does NOT do: it cannot know a counterexample nobody registered, it does not
verify the arithmetic behind a claim, and a headline passing here is unexamined
rather than confirmed. It catches one specific failure, which is a claim that
contradicts evidence this lane already holds.
"""
import json
import os
import sys

VERSION = "0.1.0"
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Every headline this lane has published that a retained artifact bears on.
REGISTER = [
    {
        "headline": "no ordering of the review reduces the worst case without a prior",
        "checkpoint": "review-cost-0.1.0",
        "assumptions": ["the unknown state is r independent unrestricted binary facts",
                        "one query reveals exactly one fact",
                        "the target is a threshold on an unweighted sum"],
        "refuted_by": [
            {"artifact": "research/cohort-packet/0.1.0/adaptive-beats-fixed-varying-edges-case.json",
             "shows": "adaptive depth 2 against a smallest fixed set of 3, with no prior",
             "published_in": "resolution-plan-0.3.0"}],
        "status": "withdrawn",
    },
    {
        "headline": "the worst case review count is invariant to the anchor weights",
        "checkpoint": "review-cost-0.1.0",
        "assumptions": ["weights were swept over three settings"],
        "refuted_by": [
            {"artifact": "tools/measure/review_cost.py",
             "shows": "at weights (99/100, 1/100) the same function returns 9, not 16",
             "published_in": "this lane's own code, never run at that weighting"}],
        "status": "withdrawn",
    },
    {
        "headline": "deciding the sign costs one judgement per retained addition",
        "checkpoint": "review-cost-0.1.0",
        "assumptions": ["each retained addition carries an independently observable label"],
        "refuted_by": [
            {"artifact": "research/cohort-packet/0.1.0/matching-trap.json",
             "shows": ("the addition is identical in both worlds and only the disputed base "
                       "neighbour differs, yet the loss moves from -1 to +1. Matching competition "
                       "is global, so an addition carries no local truth bit"),
             "published_in": "decision-packet and cohort-packet, retained since 2026-09-11"}],
        "status": "withdrawn",
    },
    {
        "headline": "the modality claim is not robust to evaluation scope, with five close range flip witnesses",
        "checkpoint": "preparation-robustness-0.1.0",
        "assumptions": ["each preparation changes only the evaluation scope"],
        "refuted_by": [
            {"artifact": "research/preparation-robustness/0.2.0/preparation-grid.json",
             "shows": ("every preparation also moved each detector's score cutoff, by up to +0.521. "
                       "Holding the cutoffs fixed, all five failing cells hold by +0.151 to +1.512"),
             "published_in": "preparation-robustness-0.2.0"}],
        "status": "withdrawn",
    },
    {
        "headline": "same modality pairs are more coupled than cross modality pairs",
        "checkpoint": "modality-coupling-0.1.0",
        "assumptions": ["matched miss rates", "one annotated population", "one match rule",
                        "five public detectors sharing a training split",
                        "and, discovered later, ONE evaluation scope"],
        "refuted_by": [
            {"artifact": "research/preparation-robustness/0.1.0/preparation-grid.json",
             "shows": ("an audit across 48 pre-registered evaluation scopes could not be "
                       "completed. The matched rate arm moves the operating point with the scope; "
                       "the fixed cutoff arm never matches marginals, in 0 of 48. No preparation "
                       "isolates the scope effect for a marginal dependent estimand"),
             "published_in": "preparation-robustness-0.2.0"}],
        "status": "qualified",
        "qualification": ("holds at full scope with matched marginals. The audit across sub scopes "
                          "is obstructed rather than adverse, and the scope is part of the claim"),
    },
]


class AuditError(Exception):
    """The registered headline or artifact is not one this audit can check."""


def artifacts_present(entry, root=ROOT):
    """Every artifact a refutation cites must actually exist in the tree."""
    missing = []
    for refutation in entry["refuted_by"]:
        path = os.path.join(root, refutation["artifact"])
        if not os.path.exists(path):
            missing.append(refutation["artifact"])
    return missing


def audit(register=None, root=ROOT):
    """Refuse to publish a standing headline that a retained artifact refutes."""
    register = register if register is not None else REGISTER
    findings = []
    for entry in register:
        missing = artifacts_present(entry, root)
        blocked = entry["status"].startswith("standing") and entry["refuted_by"]
        findings.append({
            "headline": entry["headline"], "checkpoint": entry["checkpoint"],
            "status": entry["status"], "assumptions": entry["assumptions"],
            "refutations": len(entry["refuted_by"]),
            "cited_artifacts_missing": missing,
            "publishable": not blocked and not missing,
            "reason": ("a retained artifact refutes this standing headline" if blocked else
                       f"cited artifacts are absent: {missing}" if missing else "clear")})
    return {
        "artifact_id": "reiyah.headline-audit.report", "version": VERSION,
        "registered": len(findings),
        "withdrawn": sum(1 for f in findings if f["status"] == "withdrawn"),
        "blocked": [f for f in findings if not f["publishable"]],
        "all_clear": all(f["publishable"] for f in findings),
        "findings": findings,
        "what_this_does_not_do": [
            "it cannot know a counterexample nobody registered",
            "it does not verify the arithmetic behind any claim",
            "a headline passing here is unexamined, not confirmed",
        ],
    }


def main(argv):
    report = audit()
    json.dump(report, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0 if report["all_clear"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
