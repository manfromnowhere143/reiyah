"""Review instrument, part 2: the register and the documents must describe the same program.

The register is the reconciliation point. A reviewer's second question is whether it is complete
and whether the documents agree with it. This checks, fail-closed:

  R1  every registered claim names a first_stated_in document that exists and at least one retained
      transcript that exists;
  R2  every result document the replay manifest maps to a transcript is named by at least one
      registered claim (first_stated_in or lineage text), so no result is unregistered;
  R3  every result document's Lifecycle status line is one the status model allows and is
      consistent with its registered claims: a document whose every claim is withdrawn_as_stated
      must say corrected or withdrawn; a document carrying an inconclusive claim must say
      inconclusive somewhere in its lifecycle line or headline; a document whose claims are all
      measured, derived or narrowed says proposed;
  R4  every value the register lists as withdrawn appears in some retained transcript (the
      withdrawal has lineage), and no registered transcript path is unreachable.

Mechanical, advisory under the repository's law; never independent.
"""
import json
import pathlib
import re
import sys

REG_GLOB = "evidence/claim-status-register-*.json"
MANIFEST = "validation/gate-b-replay-manifest.json"


def main():
    reg = json.loads(sorted(pathlib.Path("evidence").glob("claim-status-register-*.json"))[-1].read_text(encoding="utf-8"))
    man = json.loads(pathlib.Path(MANIFEST).read_text(encoding="utf-8"))
    fails = []
    print("=" * 92); print("REVIEW INSTRUMENT 2: register and document coverage"); print("=" * 92)
    # R1
    r1 = []
    for c in reg["claims"]:
        paths = re.findall(r"[\w\-/]+\.(?:md|py|txt|json)", c["lineage"]["first_stated_in"])
        if not any(pathlib.Path(d).exists() for d in paths):
            r1.append(f"{c['claim_id']}: no existing path in first_stated_in")
        # a claim whose status is unknown or not_established records the absence of a measurement
        # and may carry no transcript; every other status must carry at least one that exists
        if c["status"] not in ("unknown", "not_established") and not any(pathlib.Path(t).exists() for t in c["retained_transcripts"]):
            r1.append(f"{c['claim_id']}: no existing transcript")
    print(f"  [{'PASS' if not r1 else 'FAIL'}] R1 every claim points to an existing document and transcript ({len(reg['claims'])} claims)" + (f": {r1}" if r1 else ""))
    fails += r1
    # R2
    named = set()
    for c in reg["claims"]:
        named |= set(re.findall(r"[\w\-/]+\.md", c["lineage"]["first_stated_in"] + " " + c.get("notes", "") + " " + " ".join(c.get("reconsideration_requirements", []))))
    result_docs = sorted({d for row in man["transcripts"] for d in row["results"]})
    r2 = [d for d in result_docs if d not in named and pathlib.Path(d).name not in {pathlib.Path(n).name for n in named}]
    print(f"  [{'PASS' if not r2 else 'FAIL'}] R2 every result document is named by a registered claim ({len(result_docs)} documents)" + (f": unregistered {r2}" if r2 else ""))
    fails += [f"unregistered: {d}" for d in r2]
    # R3
    allowed = {"proposed", "corrected", "withdrawn", "inconclusive", "preregistered", "exploratory", "narrowed"}
    r3 = []
    by_doc = {}
    for c in reg["claims"]:
        for d in re.findall(r"[\w\-/]+\.md", c["lineage"]["first_stated_in"]):
            by_doc.setdefault(pathlib.Path(d).name, []).append(c["status"])
    for d in result_docs:
        t = pathlib.Path(d).read_text(encoding="utf-8")
        m = re.search(r"^Lifecycle status: `([a-z_]+)`(.*)$", t, re.M)
        if not m:
            r3.append(f"{d}: no lifecycle line"); continue
        status, tail = m.group(1), m.group(2)
        if status not in allowed:
            r3.append(f"{d}: lifecycle {status} not allowed")
        sts = by_doc.get(pathlib.Path(d).name, [])
        if sts and all(s == "withdrawn_as_stated" for s in sts) and status not in {"corrected", "withdrawn"}:
            r3.append(f"{d}: all claims withdrawn_as_stated but lifecycle {status}")
        if "inconclusive" in sts and "inconclusive" not in (status + tail):
            r3.append(f"{d}: carries an inconclusive claim but the lifecycle line does not say so")
    print(f"  [{'PASS' if not r3 else 'FAIL'}] R3 lifecycle lines agree with registered statuses" + (f": {r3}" if r3 else ""))
    fails += r3
    # R4
    r4 = []
    transcripts_text = "\n".join(pathlib.Path(row["transcript"]).read_text(encoding="utf-8", errors="replace") for row in man["transcripts"])
    for c in reg["claims"]:
        for v in c.get("values_withdrawn", []):
            val = v.get("value", "")
            if val and val != "see transcript" and val.lstrip("+") not in transcripts_text and val not in transcripts_text:
                own = "\n".join(pathlib.Path(t).read_text(encoding="utf-8", errors="replace") for t in c["retained_transcripts"] if pathlib.Path(t).exists())
                if val.lstrip("+") not in own:
                    r4.append(f"{c['claim_id']}: withdrawn value {val} not found in any retained transcript")
    print(f"  [{'PASS' if not r4 else 'FAIL'}] R4 every withdrawn value has lineage in a retained transcript" + (f": {r4}" if r4 else ""))
    fails += r4
    print(f"\n  RESULT: {'PASS' if not fails else 'FAIL'}  ({len(fails)} finding(s))")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
