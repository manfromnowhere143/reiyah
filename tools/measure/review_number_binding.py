"""Review instrument, part 1: every number in a result document must be bound to retained bytes.

A result document is prose about a transcript. The first thing a reviewer does is check that every
number in the document is real. This does that mechanically for every document the replay manifest
maps to a transcript, and classifies every numeric token into one of five states:

  own        the value appears in one of the document's own transcripts (the transcript may carry
             more decimals; a percentage may appear as a fraction; thousands separators ignored)
  elsewhere  the value appears in another retained transcript in the manifest: a real number, quoted
             from another result; reported so the reader can see the document leans on it
  derived    the value is one arithmetic step from two values in the document's own transcripts
             (a + b, a - b, 100 - a, 1 - a, a / b, a * b, a * 100), reported with the derivation:
             this is the arithmetic a reviewer would check by hand
  exempt     identity lines, dates, list markers, section and definition references, arXiv and DOI
             identifiers, confidence levels (95%, 2.5%, 97.5%), bootstrap and seed parameters, run
             counts, or a value the document lists in a `<!-- review-exempt: value=reason -->`
             comment with a stated reason
  UNBOUND    none of the above: a number the retained bytes do not support

The check fails closed on any UNBOUND token. It cannot judge whether the prose reads the numbers
correctly; it shows that the numbers are real and where they come from. Advisory under the
repository's law; never independent.
"""
import itertools
import json
import pathlib
import re
import sys

MANIFEST = "validation/gate-b-replay-manifest.json"
# a number may be followed by a short unit (2.03s, 15 m, 1.6x) but not by a digit, a slash or a word
NUM = re.compile(r"(?<![\w.\-])[-+]?\d{1,3}(?:,\d{3})+(?:\.\d+)?%?(?![\d/])(?![A-Za-z]{3})|(?<![\w.\-/])[-+]?\d+(?:\.\d+)?%?(?![\d/])(?![A-Za-z]{3})")
SKIP_LINE = re.compile(r"^(Document ID|Version|Lifecycle status):|^#|^\| *-+ *\|")
EXEMPT_INLINE = [r"\b20\d\d-\d\d-\d\d\b", r"\barXiv:\d+\.\d+", r"\bdoi:[\d./A-Za-z-]+", r"\b10\.\d{4,}/[^\s)]+", r"\bsection \d+(\.\d+)?", r"\bDefinition \d+", r"\bCorollary \d+",
                  r"\b95 ?%|\b2\.5%|\b97\.5%", r"\bB = \d[\d,]*", r"\bK = \d+", r"\bseed \d+", r"\b(two|three|four|five) runs\b", r"\(\d+ runs?\)", r"\b(19|20)\d\d\b(?! objects| items| questions| rows| frames| clips| trials| events| models)",
                  r"\b\d+-shot\b", r"\bResult [A-Z]{1,2}\d?\b", r"\bH\d[a-z]?\b", r"\bP\d\b", r"\bX\d-\d\b", r"\bv?1\.[0-9]\b(?= schema| register| architecture)", r"`1\.2`", r"1\.2 byte", r"schema `?v1\.[0-9]`?", r"register `?0\.\d+\.\d+`?", r"Version: `[\d.]+`", r"\b10\^\d+\b", r"\bcv=\d\b", r"\bIoU `?>= ?0\.\d+`?"]
DERIVE_TOL = 0.0051


def tokens(text):
    out = set()
    for m in NUM.finditer(text):
        s = m.group(0).replace(",", "")
        pct = s.endswith("%"); s = s.rstrip("%")
        try:
            out.add((round(float(s), 6), pct))
        except ValueError:
            pass
    return out


def values(tset):
    return sorted({v for v, _ in tset} | {v / 100.0 for v, p in tset if p} | {v * 100.0 for v, p in tset if not p and abs(v) <= 1.0})


def match(c, tv):
    for d in range(0, 7):
        if abs(round(tv, d) - c) < 1e-9:
            return True
    return False


def bound_in(v, pct, vals):
    cands = {v, v / 100.0} if pct else {v, v * 100.0}
    return any(match(c, tv) for tv in vals for c in cands)


def derive(v, pct, vals):
    """One arithmetic step from two transcript values. Returns a derivation string or None."""
    targets = {v, v / 100.0} if pct else {v}
    small = [x for x in vals if abs(x) <= 1e6]
    for t in targets:
        for a in small:
            if abs((100 - a) - t) < DERIVE_TOL or abs((1 - a) - t) < DERIVE_TOL * 0.01:
                return f"100 - {a:g}" if abs((100 - a) - t) < DERIVE_TOL else f"1 - {a:g}"
        for a, b in itertools.combinations(small, 2):
            for name, val in (("+", a + b), ("-", a - b), ("-", b - a)):
                if abs(val - t) < DERIVE_TOL:
                    return f"{a:g} {name} {b:g}" if name == "+" or val == a - b else f"{b:g} - {a:g}"
            if b and abs(a / b - t) < DERIVE_TOL:
                return f"{a:g} / {b:g}"
            if a and abs(b / a - t) < DERIVE_TOL:
                return f"{b:g} / {a:g}"
    return None


def main():
    man = json.loads(pathlib.Path(MANIFEST).read_text(encoding="utf-8"))
    docs, all_vals = {}, set()
    for row in man["transcripts"]:
        tt = tokens(pathlib.Path(row["transcript"]).read_text(encoding="utf-8", errors="replace"))
        all_vals |= tt
        for d in row["results"]:
            docs.setdefault(d, set()).add(row["transcript"])
    all_values = values(all_vals)
    fails, report, totals = 0, [], {"own": 0, "elsewhere": 0, "derived": 0, "exempt": 0, "UNBOUND": 0}
    print("=" * 92); print("REVIEW INSTRUMENT 1: number binding, every result document against retained transcripts"); print("=" * 92)
    for doc in sorted(docs):
        text = pathlib.Path(doc).read_text(encoding="utf-8")
        own = set()
        for tr in docs[doc]:
            own |= tokens(pathlib.Path(tr).read_text(encoding="utf-8", errors="replace"))
        own_values = values(own)
        exempt_listed = {}
        for m in re.finditer(r"<!-- review-exempt: ([^>]*) -->", text):
            for item in m.group(1).split(";"):
                if "=" in item:
                    val, reason = item.split("=", 1)
                    for tv in tokens(val.strip()):
                        exempt_listed[tv] = reason.strip()
        states, unbound = {"own": 0, "elsewhere": 0, "derived": 0, "exempt": 0, "UNBOUND": 0}, []
        for ln, line in enumerate(text.splitlines(), 1):
            if SKIP_LINE.search(line) or line.startswith("<!--"):
                continue
            work = re.sub(r"^\s*\d+\.\s", " ", line)
            for pat in EXEMPT_INLINE:
                work = re.sub(pat, " ", work)
            for v, pct in tokens(work):
                if v == 0.0:
                    continue
                if (v, pct) in exempt_listed:
                    states["exempt"] += 1; continue
                if bound_in(v, pct, own_values):
                    states["own"] += 1; continue
                if bound_in(v, pct, all_values):
                    states["elsewhere"] += 1; continue
                d = derive(v, pct, own_values)
                if d:
                    states["derived"] += 1; continue
                states["UNBOUND"] += 1; unbound.append((ln, f"{v:g}{'%' if pct else ''}"))
        for k in totals:
            totals[k] += states[k]
        report.append({"document": doc, "states": states, "unbound": [{"line": l, "value": s} for l, s in unbound]})
        tag = "bound" if not unbound else "UNBOUND"
        print(f"  [{tag:<7}] {doc}: own {states['own']}, elsewhere {states['elsewhere']}, derived {states['derived']}, exempt {states['exempt']}"
              + (f", UNBOUND {unbound}" if unbound else ""))
        fails += bool(unbound)
    print(f"\n  totals: {totals}")
    print(f"  RESULT: {'PASS' if not fails else 'FAIL'}  ({fails} document(s) with unbound numbers of {len(docs)})")
    if "--json" in sys.argv:
        pathlib.Path(sys.argv[sys.argv.index("--json") + 1]).write_text(json.dumps({"totals": totals, "documents": report}, indent=2) + "\n", encoding="utf-8")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
