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

A refutation and a bound are different things and are registered separately. An
artifact that contradicts a headline blocks it. An artifact that limits its scope
does not block it, and has to be cited anyway, because a standing headline with no
stated limit is the shape most of this lane's withdrawn claims arrived in.

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
    {
        "headline": ("the decision waits on a far shorter list of reading facts than the disputed "
                     "set, and both ends of that list are checkable in linear time"),
        "checkpoint": "comparator-0.1.0",
        "assumptions": ["the admitted readings are the readings on offer",
                        "an atom is an object presence or an admitted same class edge",
                        "the verdict depends on a reading only through the declared loss "
                        "and tolerance",
                        "the measured rates come from a generator written in this lane"],
        "refuted_by": [],
        "bounded_by": [
            {"artifact": "tools/measure/conventional_comparator.py",
             "limits": ("the list is a function of the shared readings, so an analyst holding "
                        "them could compute it too. Shorter and checkable, not exclusive"),
             "published_in": "conventional-comparator-0.1.0"},
            {"artifact": "research/cohort-packet/0.1.0/bracketed-observation-case.json",
             "limits": ("39 disputed atoms whose shortest list is not pinned. The packing forces "
                        "1 and a cover of 2 is exhibited, so the report brackets rather than "
                        "claims"),
             "published_in": "comparator-0.1.0"},
            {"artifact": "research/comparator/0.1.0/verification-cost.json",
             "limits": ("checking rather than recomputing is measured slower on every retained "
                        "case, and only overtakes recomputation between 30 and 90 detections"),
             "published_in": "comparator-0.1.0"},
            {"artifact": "research/comparator/0.2.0/end-to-end.json",
             "limits": ("checking a supplied cover is linear in the supplied sets. The "
                        "implemented checker recomputes those sets and performs one comparison "
                        "per pair of admitted readings: 36, 136 and 528 on the 8, 16 and 32 pair "
                        "controls. The unqualified linear time wording is withdrawn"),
             "published_in": "comparator-0.2.0"}],
        "status": "standing, bounded",
    },
    {
        "headline": "386 of the generated cases carry a minimum size certificate",
        "checkpoint": "comparator-0.1.0",
        "assumptions": ["that a shortest list found by search is a certificate result"],
        "refuted_by": [
            {"artifact": "research/comparator/0.2.0/end-to-end.json",
             "shows": ("replaying the same 1400 cases gives 386 with a shortest list, of which "
                       "378 have a packing that meets the cover and 8 do not. The first is "
                       "size 4, seed 9, where the search finds 2 and the packing forces 1"),
             "published_in": "comparator-0.2.0"}],
        "status": "withdrawn",
        "successor": "378 of 717 cases needing a list carry a minimum size certificate",
    },
    {
        "headline": "an open reference means the decision is waiting on that reference",
        "checkpoint": "comparator-0.1.0",
        "assumptions": ["that an open interval always leaves the criterion open"],
        "refuted_by": [
            {"artifact": "research/cohort-packet/0.1.0/settled-with-open-reference-case.json",
             "shows": ("a cohort whose enclosure is 4/5 to 1 at tolerance 1/10. The criterion is "
                       "supported across the whole open interval, so nothing is waiting, yet "
                       "0.1.0 reported waits_on_a_reference and both checkers accepted it"),
             "published_in": "comparator-0.2.0"}],
        "status": "withdrawn",
        "successor": ("the criterion is read first. An open reference is preserved without being "
                      "turned into an outstanding question"),
    },
    {
        "headline": "the grid's 48 labels name 33 distinct preparations",
        "checkpoint": "preparation-robustness-0.3.0",
        "assumptions": ["that equal population and equal kept counts establish equal members"],
        "refuted_by": [],
        "bounded_by": [
            {"artifact": "tools/measure/premise_corrections.py",
             "limits": ("0.3.0 grouped on aggregate counts alone, which two different row sets "
                        "can share. 0.4.0 evaluates the declared predicates against the exact "
                        "source rows, digests each selected index sequence, and carries a "
                        "control with equal counts and disjoint members. The 33 survives on "
                        "membership; the 0.3.0 grouping did not establish it"),
             "published_in": "preparation-robustness-0.4.0"}],
        "status": "standing, bounded",
    },
    {
        "headline": ("the benchmark verdict on this cohort rests on six of its 106 labels, and is "
                     "fragile to a spurious label but not to a missed one"),
        "checkpoint": "label-dependence-0.1.0",
        "assumptions": [
            "the declared loss, tolerance, class map, geometry, suppression rule and weights",
            "a deletion is a hypothetical spurious label correction and nothing else",
            "an insertion is placed at an unmatched retained detection's own position",
            "two previously exposed development frames and one supplied benchmark interpretation"],
        "refuted_by": [],
        "bounded_by": [
            {"artifact": "research/label-dependence/0.2.0/insertion-family.json",
             "limits": ("the insertion family tested singles and pairs under one insertion rule. "
                        "Localization error, class error and other insertion geometries are "
                        "untested, so the asymmetry is established for these families only"),
             "published_in": "label-dependence-0.2.0"},
            {"artifact": "research/label-dependence/0.1.0/deletion-family.json",
             "limits": ("no deletion made the addition harmful. The weighted delta range is 0 to "
                        "1, so six deletions stop it helping and none makes it hurt. Six of 106 "
                        "is a count, not a probability"),
             "published_in": "label-dependence-0.1.0"},
            {"artifact": "research/annotation-case/0.1.0/source-reconstruction.json",
             "limits": ("the reconstruction establishes that the number follows from the declared "
                        "rules on the declared bytes. It establishes nothing about whether any "
                        "annotation is correct, and the closest excluded label sits 0.28 metres "
                        "outside the range boundary"),
             "published_in": "annotation-case-0.1.0"}],
        "status": "standing, bounded",
    },
    {
        "headline": "every decisive verdict is carried entirely by the admission decision",
        "checkpoint": "admission-sensitivity-0.2.0",
        "assumptions": ["that a decisive verdict pins the enclosure to a point",
                        "that the asserted share is one whenever the verdict is decisive"],
        "refuted_by": [
            {"artifact": "research/cohort-packet/0.1.0/decisive-interval-case.json",
             "shows": ("every anchor finite, both readings supported at different values, "
                       "enclosure [1, 3] against a coarse bound of [-3, 3] and an asserted share "
                       "of 2/3. An open reference is not the explanation"),
             "published_in": "comparator-0.2.0"},
            {"artifact": "research/cohort-packet/0.1.0/settled-with-open-reference-case.json",
             "shows": "decisive at [4/5, 1] with an asserted share of 9/10",
             "published_in": "comparator-0.2.0"}],
        "status": "withdrawn",
        "successor": ("removing readings can only narrow and admitting more can only widen, so a "
                      "decisive verdict rests on the completeness of the admitted set. The share "
                      "of one was a property of the four cases then retained"),
    },
]


class AuditError(Exception):
    """The registered headline or artifact is not one this audit can check."""


def artifacts_present(entry, root=ROOT):
    """Every artifact a refutation or a bound cites must actually exist in the tree."""
    missing = []
    for citation in list(entry["refuted_by"]) + list(entry.get("bounded_by", [])):
        path = os.path.join(root, citation["artifact"])
        if not os.path.exists(path):
            missing.append(citation["artifact"])
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
            "bounds": len(entry.get("bounded_by", [])),
            "cited_artifacts_missing": missing,
            "publishable": not blocked and not missing,
            "reason": ("a retained artifact refutes this standing headline" if blocked else
                       f"cited artifacts are absent: {missing}" if missing else "clear")})
    return {
        "artifact_id": "reiyah.headline-audit.report", "version": VERSION,
        "registered": len(findings),
        "withdrawn": sum(1 for f in findings if f["status"] == "withdrawn"),
        "standing_with_no_stated_bound": [f["headline"] for f, entry in zip(findings, register)
                                          if entry["status"].startswith("standing")
                                          and not entry.get("bounded_by")],
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
