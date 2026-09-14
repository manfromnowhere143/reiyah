"""One end to end comparison between this lane's instrument and an ordinary analyst.

The decision is the Engine's, unchanged:

    delta = (a + b) * (TP_augmented - TP_base) - b * r

over a weighted cohort, with maximum same class one to one matching, matching
competition preserved, complete joint reference alternatives, nonnegative
penalties and a declared tolerance. Neither a coefficient, an excess nor an
overlap share replaces it here.

The comparator is a competent analyst holding the same evidence, the same loss,
the same tolerance and the same admitted readings, using ordinary tools. They may
run their own matcher, diff their own readings and abstain. Nothing is withheld
from them, so the comparison can come out against this lane, and in two of the
five measured dimensions it does.

Each case is reported with:

  identity        the exact bytes compared, by digest.
  decision        the declared loss, tolerance and what is being asked.
  conventional    what the analyst concludes, both readings of the reference.
  instrument      the enclosure and its criterion.
  witness         for a decided case, the certificates that force it; for an
                  unresolved case, the two readings that obstruct it.
  observations    the shortest checkable list of reading facts that would settle
                  it, bracketed between a packing bound and a greedy cover.
  costs           preparation, computation, verification, interpretation,
                  integration and repair, each with its unit and its basis.

Human effort is not measured anywhere in this file. No person has run either
method on this cohort, and no number here stands in for that.

Standard library only, no data read, exact rational arithmetic throughout.
"""
from fractions import Fraction
import hashlib
import json
import os
import platform
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_cohort_packet as packet_checker  # noqa: E402
import check_observation_cover as cover_checker  # noqa: E402
import cohort_packet as packet  # noqa: E402
import conventional_comparator as conventional  # noqa: E402
import observation_cover as cover  # noqa: E402

VERSION = "0.2.0"
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CASES = os.path.join(ROOT, "research", "cohort-packet", "0.1.0")

SELECTED = (
    ("open-two-anchor.json", "the live two window comparison, with no admitted reading"),
    ("matching-trap.json", "one addition, one disputed object, opposite losses"),
    ("oppositely-coupled.json", "two anchors constrained to disagree"),
    ("worst-group-flip-case.json", "a cohort whose worst group changes with the reading"),
    ("three-copies-plan-case.json", "three weighted copies of one ambiguity"),
    ("adaptive-beats-fixed-varying-edges-case.json", "readings that disagree about edges, not presence"),
    ("sixteen-candidates-plan-case.json", "a disputed set past the exact search budget"),
    ("ghost-burden-three.json", "a settled cohort carrying three unmatched additions"),
)


def digest(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def roundtrip(value):
    """Through JSON, the way a consumer receives it, so the checker sees what they see."""
    return json.loads(json.dumps(value, sort_keys=True))


def witness_or_obstruction(report, listing):
    """What forces the verdict, or what stands in its way."""
    criterion = report["decision"].get("improvement_criterion")
    if report.get("state") == "open_reference_only":
        return {"kind": "obstruction", "name": "no admitted reading",
                "detail": ("every anchor is open, so the enclosure is the weighted count bound "
                           "and no certificate applies"),
                "enclosure": report["enclosure"]}
    certificates = []
    for world in report["joint_worlds"]:
        for entry in world["anchors"]:
            certificates.append({
                "world": world["world_id"], "anchor": entry["anchor"],
                "tp_base": entry["tp_base"], "tp_augmented": entry["tp_augmented"],
                "base_matching": len(entry["base_certificate"]["matching"]),
                "base_cover": (len(entry["base_certificate"]["cover"]["detections"])
                               + len(entry["base_certificate"]["cover"]["objects"])),
                "augmented_matching": len(entry["augmented_certificate"]["matching"]),
                "augmented_cover": (len(entry["augmented_certificate"]["cover"]["detections"])
                                    + len(entry["augmented_certificate"]["cover"]["objects"]))})
    equal_sizes = all(row["base_matching"] == row["base_cover"]
                      and row["augmented_matching"] == row["augmented_cover"]
                      for row in certificates)
    if criterion == "unresolved":
        sets = (listing.get("observation_list") or {}).get("separating_sets") or []
        return {"kind": "obstruction", "name": "readings with opposite verdicts",
                "detail": "no reading is wrong, and they do not agree on the verdict",
                "discordant_pairs": [entry["worlds"] for entry in sets],
                "certificates": certificates,
                "every_matching_meets_a_cover_of_equal_size": equal_sizes}
    return {"kind": "witness", "name": "matching and cover of equal size at every anchor",
            "detail": ("every matching is at most every cover, so equal sizes force optimality "
                       "without rerunning a matcher"),
            "certificates": certificates,
            "every_matching_meets_a_cover_of_equal_size": equal_sizes}


def measure(case, report, listing, repeats=200):
    """Command time for each path on this machine. Not human effort."""
    def timed(action):
        start = time.perf_counter()
        for _ in range(repeats):
            action()
        return round((time.perf_counter() - start) / repeats * 1000, 5)
    return {
        "build_ms": timed(lambda: packet.build(case)),
        "packet_check_ms": timed(lambda: packet_checker.verify(case, report)),
        "cover_build_ms": timed(lambda: cover.analyse(case)),
        "cover_check_ms": timed(lambda: cover_checker.verify(report, listing)),
        "analyst_readings_ms": timed(lambda: conventional.single_interpretation_readings(case)),
    }


def one(name, why):
    path = os.path.join(CASES, name)
    with open(path, "r", encoding="utf-8") as handle:
        case = json.load(handle)
    report = roundtrip(packet.build(case))
    listing = roundtrip(cover.analyse(case))
    comparison = conventional.compare(case)
    packet_result = packet_checker.verify(case, report)
    cover_result = cover_checker.verify(report, listing)

    anchors = case["anchors"]
    entry = {
        "case": name, "why_selected": why,
        "identity": {
            "path": os.path.join("research", "cohort-packet", "0.1.0", name),
            "sha256": digest(path), "cohort_id": case["cohort_id"],
            "anchors": len(anchors),
            "open_anchors": sum(1 for a in anchors if a["reference_state"] == "open"),
            "admitted_readings": len(case.get("joint_worlds", [])),
            "retained_additions": sum(len(a.get("added_detections", [])) for a in anchors),
            "base_detections": sum(len(a.get("base_detections", [])) for a in anchors)},
        "declared_decision": {
            "loss": case["loss"],
            "formula": "delta = (a + b) * (TP_augmented - TP_base) - b * r",
            "question": "does the added detector improve the weighted cohort beyond the tolerance"},
        "instrument": {"state": report.get("state"), "enclosure": report.get("enclosure"),
                       "improvement_criterion": report["decision"].get("improvement_criterion"),
                       "preference": report["decision"].get("preference")},
        "conventional": {
            "single_interpretation": comparison.get("conventional_single_interpretation"),
            "complete_annotation": comparison.get("conventional_complete_annotation"),
            "equivalence": comparison.get("equivalence"),
            "what_the_instrument_adds": comparison.get("what_the_instrument_adds")},
        "witness_or_obstruction": witness_or_obstruction(report, listing),
        "observations_that_would_change_the_decision": {
            "state": listing["state"],
            "diff_the_analyst_gets_free": (listing.get("disputed_atoms") or {}).get("count"),
            "certified_list": (listing.get("observation_list") or {}).get("count"),
            "lower_bound": (listing.get("observation_list") or {}).get("lower_bound"),
            "checkable_cover": ((listing.get("observation_list") or {}).get("checkable_cover") or {}
                                ).get("count"),
            "atoms": ((listing.get("observation_list") or {}).get("atoms")
                      or ((listing.get("observation_list") or {}).get("checkable_cover") or {}
                          ).get("atoms")),
            "note": listing.get("reason")},
        "checked_by_separate_checkers": {
            "cohort_packet": packet_result.get("established", packet_result),
            "observation_cover": cover_result.get("established", cover_result)},
        "command_time_ms": measure(case, report, listing),
    }
    return entry


def synthetic_case(size, seed):
    """A finite cohort with explicit joint worlds, built from a fixed seed.

    The generator is this lane's own construction. Every rate measured over it
    describes the construction, not any field population, and it is reported that
    way wherever it appears.
    """
    rng = random.Random(seed)
    base = [{"id": "b%d" % i, "class": "car"} for i in range(3)]
    added = [{"id": "c0", "class": "car"}]
    objects = [{"id": "o%d" % i, "class": "car"} for i in range(size)]
    joint = []
    for index in range(size):
        present = [o["id"] for o in objects if rng.random() < 0.6]
        edges = [[d["id"], o] for d in base + added for o in present if rng.random() < 0.5]
        joint.append({"world_id": "w%d" % index,
                      "per_anchor": {"A": {"objects_present": present, "edges": edges}}})
    return {"schema_id": "reiyah.cohort-packet.case", "cohort_id": "conformance",
            "anchors": [{"id": "A", "weight": "1", "reference_state": "finite",
                         "base_detections": base, "added_detections": added,
                         "objects": objects}],
            "joint_worlds": joint,
            "loss": {"false_negative": "1", "false_positive": "1", "tolerance": "0"}}


def conformance(sizes=(4, 6, 8, 10, 12, 16, 20), per_size=200):
    """Exercise every state on synthetic joint worlds, checking each one."""
    names = ("already_decided", "certified_shortest", "searched_shortest", "bracketed",
             "waits_on_a_reference", "no_admitted_reading", "not_evaluated")
    rows, totals = [], {name: 0 for name in names}
    diffs, lengths, checked = [], [], 0
    for size in sizes:
        states = {name: 0 for name in names}
        local_diff, local_length = [], []
        for seed in range(per_size):
            case = synthetic_case(size, seed)
            report = roundtrip(packet.build(case))
            listing = roundtrip(cover.analyse(case))
            packet_checker.verify(case, report)
            cover_checker.verify(report, listing)
            checked += 1
            state = listing["state"]
            states[state] = states.get(state, 0) + 1
            totals[state] = totals.get(state, 0) + 1
            declared = listing.get("disputed_atoms") or {}
            entry = listing.get("observation_list") or {}
            if not declared.get("count"):
                continue
            length = entry.get("count")
            if length is None:
                length = (entry.get("checkable_cover") or {}).get("count")
            if length is None:
                continue
            local_diff.append(declared["count"])
            local_length.append(length)
        diffs.extend(local_diff)
        lengths.extend(local_length)
        rows.append({"objects": size, "readings": size, "instances": per_size,
                     "states": states,
                     "mean_disputed": round(sum(local_diff) / len(local_diff), 3) if local_diff else None,
                     "mean_list": round(sum(local_length) / len(local_length), 3) if local_length else None})
    needing = totals["certified_shortest"] + totals["searched_shortest"] + totals["bracketed"]
    return {
        "instances": len(sizes) * per_size,
        "instances_both_checkers_accepted": checked,
        "by_size": rows,
        "states": totals,
        "corrects": ("0.1.0 counted every case with a shortest list as certified. A searched "
                     "optimum whose packing does not meet it is not a certificate, and is now "
                     "counted as its own state"),
        "cases_needing_a_list": needing,
        "certified_shortest_share": ("%d of %d" % (totals["certified_shortest"], needing)
                                     if needing else None),
        "searched_but_not_certified": totals["searched_shortest"],
        "mean_disputed": round(sum(diffs) / len(diffs), 3) if diffs else None,
        "mean_list": round(sum(lengths) / len(lengths), 3) if lengths else None,
        "scope": ("a generator written in this lane. The shares describe these instances only. "
                  "No claim is made about how often a real cohort is already decided"),
    }


def star_case(discordant):
    """One centre reading and k satellites, each disagreeing with the centre.

    A control for the checking cost. It has k discordant pairs and k+1 readings, so
    it separates the size of the supplied certificate from the number of comparisons
    the implemented checker performs.
    """
    base = [{"id": "b0", "class": "car"}]
    added = [{"id": "c0", "class": "car"}]
    objects = [{"id": "o%d" % i, "class": "car"} for i in range(discordant + 1)]
    present = [o["id"] for o in objects]
    joint = [{"world_id": "centre",
              "per_anchor": {"A": {"objects_present": present, "edges": [["c0", "o0"]]}}}]
    for index in range(discordant):
        name = "o%d" % (index + 1)
        joint.append({"world_id": "s%d" % index,
                      "per_anchor": {"A": {"objects_present": present,
                                           "edges": [["b0", name], ["c0", name]]}}})
    return {"schema_id": "reiyah.cohort-packet.case", "cohort_id": "star-%d" % discordant,
            "anchors": [{"id": "A", "weight": "1", "reference_state": "finite",
                         "base_detections": base, "added_detections": added,
                         "objects": objects}],
            "joint_worlds": joint,
            "loss": {"false_negative": "1", "false_positive": "1", "tolerance": "0"}}


def checking_cost(sizes=(8, 16, 32)):
    """What the implemented checker actually does, in traced operations.

    0.1.0 said the list is checked in linear time. That is true of the mathematics and
    false of this implementation. Checking a supplied cover against supplied separating
    sets is linear in their total size. The implemented checker does not trust the
    supplied sets: it recomputes them from the packet, which compares every pair of
    admitted readings, discordant or not. These are traced counts, not timings.
    """
    rows = []
    for count in sizes:
        case = star_case(count)
        report = roundtrip(packet.build(case))
        listing = roundtrip(cover.analyse(case))
        cover_checker.verify(report, listing)
        worlds = len(report["joint_worlds"])
        entry = listing["observation_list"]
        pack = len(entry["packing"])
        rows.append({
            "discordant_pairs": count, "admitted_readings": worlds,
            "pair_verdict_comparisons": worlds * (worlds - 1) // 2,
            "packing_overlap_comparisons": pack * (pack - 1) // 2,
            "separating_sets_recomputed": len(entry["separating_sets"]),
            "supplied_certificate_atoms": entry["checkable_cover"]["count"]})
    return {
        "what_is_linear": ("checking a supplied cover against supplied separating sets, in the "
                           "total size of those sets"),
        "what_this_implementation_costs": ("one comparison per pair of admitted readings, because "
                                           "it recomputes the separating sets instead of trusting "
                                           "them, plus one overlap test per pair of packing members"),
        "why_it_is_not_a_defect": ("a checker that trusted the reported separating sets would "
                                   "accept a report that omitted a discordant pair, which is a "
                                   "forgery this lane already retains. The quadratic cost buys "
                                   "independence and is stated rather than optimised away"),
        "traced": rows,
        "note": "traced operation counts on constructed controls, not timing measurements",
        "corrects": "the unqualified linear time claim in comparator 0.1.0",
    }


ENGINE_CASE_SHA256 = "8e79f3636ef337d7ea2f12ec213e67106d7d4afce55bdafb6c63ba10d667f299"


def compatibility(path=None, expected=ENGINE_CASE_SHA256):
    """Acknowledge the Engine's source bound comparison without copying it in.

    The case is another owner's private export and its detection identifiers are
    source derived row references. They are not copied into this repository. What is
    recorded here is the digest that binds the bytes, the structure in counts, and
    the result both checkers accept. If the file is not supplied the record says so
    and names the digest it would need.
    """
    if not path or not os.path.exists(path):
        return {"state": "unavailable", "expected_sha256": expected,
                "reason": ("the Engine's source bound case is private to its owner and was not "
                           "supplied to this run. Its digest is recorded so the result can be "
                           "reproduced against the exact bytes")}
    found = digest(path)
    if found != expected:
        return {"state": "digest_mismatch", "expected_sha256": expected, "found_sha256": found,
                "reason": "the supplied bytes are not the case this record is about"}
    with open(path, "r", encoding="utf-8") as handle:
        case = json.load(handle)
    report = roundtrip(packet.build(case))
    listing = roundtrip(cover.analyse(case))
    packet_result = packet_checker.verify(case, report)
    cover_result = cover_checker.verify(report, listing)
    return {
        "state": "checked",
        "sha256": found,
        "cohort_id": case["cohort_id"],
        "custody": ("read only from the owner's sealed outbox. No byte of it is copied into this "
                    "repository, and no detection identifier is reproduced here"),
        "structure": [{"anchor": a["id"], "weight": a["weight"],
                       "reference_state": a["reference_state"],
                       "base_detections": len(a["base_detections"]),
                       "added_detections": len(a["added_detections"]),
                       "declared_objects": len(a.get("objects", []))} for a in case["anchors"]],
        "admitted_readings": len(case.get("joint_worlds", [])),
        "loss": case["loss"],
        "result": {"packet_state": report["state"], "enclosure": report["enclosure"],
                   "coarse_bound": report["coarse_bound"],
                   "improvement_criterion": report["decision"]["improvement_criterion"],
                   "preference": report["decision"]["preference"],
                   "observation_state": listing["state"],
                   "open_anchors": listing["open_anchors"],
                   "observation_list": listing["observation_list"]},
        "checked_by_separate_checkers": {
            "cohort_packet": packet_result.get("established", packet_result),
            "observation_cover": cover_result.get("established", cover_result)},
        "what_this_does_not_do": [
            "it admits no reading, invents no object and creates no human reference",
            "an open reference is preserved, not replaced by a fixture",
            "the enclosure is a count bound over an open reference, not a measurement"],
    }


def costs(entries):
    """Six named costs. Each states its unit and what it was read from."""
    decided = [e for e in entries
               if e["instrument"]["improvement_criterion"] in ("supported", "excluded")]
    unresolved = [e for e in entries
                  if e["instrument"]["improvement_criterion"] == "unresolved"]
    shortening = []
    for entry in entries:
        row = entry["observations_that_would_change_the_decision"]
        diff = row["diff_the_analyst_gets_free"]
        if diff is None:
            continue
        length = row["certified_list"]
        if length is None:
            length = row["checkable_cover"]
        if length is None:
            continue
        shortening.append((length, diff))
    return {
        "preparation": {
            "unit": "case files written and retained before any result",
            "value": len(entries),
            "basis": "each case is a committed JSON file with a digest recorded above",
            "against_the_analyst": ("the analyst prepares the same readings. The preparation is "
                                    "shared and this lane earns nothing here")},
        "computation": {
            "unit": "milliseconds of command time per case on one machine",
            "value": {e["case"]: e["command_time_ms"]["build_ms"] for e in entries},
            "basis": "mean over repeated builds, machine dependent",
            "against_the_analyst": ("the analyst runs one matcher per reading. Building the "
                                    "enclosure runs the same matchers over the same readings, so "
                                    "the work is the same order and the measured times are close")},
        "verification": {
            "unit": "milliseconds of command time per case, checker against recomputation",
            "value": {e["case"]: {"packet_check": e["command_time_ms"]["packet_check_ms"],
                                  "analyst_recompute": e["command_time_ms"]["analyst_readings_ms"]}
                      for e in entries},
            "basis": "see research/comparator/0.1.0/verification-cost.json for the scaling",
            "against_the_analyst": ("on these retained cases the certificate is slower than "
                                    "recomputing. It overtakes recomputation between 30 and 90 "
                                    "detections and reaches about 4.7 times faster at 900")},
        "interpretation": {
            "unit": "reading facts the lead is handed to go and settle",
            "value": {"diff_the_analyst_gets_free": sum(d for _c, d in shortening),
                      "certified_or_checkable_list": sum(c for c, _d in shortening),
                      "cases_counted": len(shortening),
                      "per_case": {entry["case"]: {
                          "diff": entry["observations_that_would_change_the_decision"][
                              "diff_the_analyst_gets_free"],
                          "list": (entry["observations_that_would_change_the_decision"][
                              "certified_list"]
                              if entry["observations_that_would_change_the_decision"][
                                  "certified_list"] is not None
                              else entry["observations_that_would_change_the_decision"][
                                  "checkable_cover"])}
                          for entry in entries}},
            "basis": "the disputed set against the checkable cover, both recomputed by the checker",
            "against_the_analyst": ("this is where the lane earns something measurable. The list "
                                    "is shorter, and a supplied cover with its separating sets is "
                                    "checked in time linear in their total size. The implemented "
                                    "checker recomputes those sets from the packet rather than "
                                    "trusting them, which costs one comparison per pair of "
                                    "admitted readings. See checking_cost below")},
        "integration": {
            "unit": "modules a consumer must trust, and what they share",
            "value": {"producer_modules": ["cohort_packet", "observation_cover"],
                      "checker_modules": ["check_cohort_packet", "check_observation_cover"],
                      "checkers_import_from_producers": [],
                      "shared_trusted_surface": ["the json module", "Fraction and integer arithmetic",
                                                 "the identifier and rational string conventions",
                                                 "the atom string convention"]},
            "basis": "read from the import statements of the four modules",
            "against_the_analyst": ("the analyst integrates nothing and trusts their own matcher. "
                                    "Four modules is a real cost this lane imposes and does not "
                                    "recover unless the checking is wanted")},
        "repair": {
            "unit": "claims this lane has withdrawn or qualified after retained counterexamples",
            "value": {"withdrawn": 4, "qualified": 1,
                      "register": "tools/measure/headline_audit.py"},
            "basis": "the standing headline register, which blocks a headline its own evidence refutes",
            "against_the_analyst": ("an analyst carries the same risk without a register. The "
                                    "register is a cost here and a discipline, not an advantage "
                                    "claimed over anyone")},
        "human_effort": {
            "unit": "person minutes",
            "value": None,
            "state": "unmeasured",
            "basis": ("no person has run either method on this cohort. Command time is not human "
                      "effort and is not offered as a proxy for it")},
        "summary": {
            "decided": len(decided), "unresolved": len(unresolved),
            "where_this_lane_is_ahead": ["the observation list, shorter and checkable both ways"],
            "where_it_is_level": ["the verdict itself, which the equivalence makes identical on a "
                                  "finite cohort", "preparation", "computation"],
            "where_it_is_behind": ["verification on a small cohort, measured slower than "
                                   "recomputation below about 60 detections",
                                   "integration, four modules against none"]},
    }


def report():
    entries = [one(name, why) for name, why in SELECTED]
    return {
        "artifact_id": "reiyah.ordinary-comparator.end-to-end", "version": VERSION,
        "decision": "delta = (a + b) * (TP_augmented - TP_base) - b * r over a weighted cohort",
        "comparator": ("a competent analyst with the same anchors, detections, loss, tolerance and "
                       "admitted readings, an ordinary matcher, the freedom to abstain and the "
                       "freedom to ask adaptive questions"),
        "runtime": {"platform": platform.platform(), "python": platform.python_version(),
                    "note": "command timings on one machine. No human effort is measured here"},
        "cases": entries,
        "synthetic_conformance": conformance(),
        "checking_cost": checking_cost(),
        "engine_case_compatibility": compatibility(os.environ.get("REIYAH_ENGINE_CASE")),
        "costs": costs(entries),
        "limits": [
            "every verdict here is over admitted readings, never over the physical world",
            "the live comparison remains open at [-8, 8] and no reading is invented for it",
            "no person has run the comparator, so every human cost stays unmeasured",
            "the observation list is a function of the shared readings, so the analyst could "
            "compute it too. What is measured is its length and its checkability, not exclusivity",
            "the exact shortest list is only searched below a declared budget; past it the report "
            "brackets rather than claims",
        ],
    }


def main(argv):
    destination = argv[1] if len(argv) > 1 else None
    result = report()
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if destination:
        with open(destination, "w", encoding="utf-8") as handle:
            handle.write(text)
        return 0
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
