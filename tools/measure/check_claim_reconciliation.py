"""Fail closed if any live prose artifact asserts a withdrawn Gate B figure.

Two checks, both deterministic and offline.

  1. SCHEMA     the claim status register validates against its declared schema.
  2. RECONCILE  every value string listed under `values_withdrawn` for a claim whose
                `current_scientific_use` is `forbidden` may appear in a live prose
                artifact ONLY on a line that also carries a withdrawal marker.

Retained evidence transcripts and the scripts that produced them are HISTORICAL BYTES.
They record what a script printed at a moment in time and are never edited to match a
later correction, so they are exempt by path. Editing them would destroy the lineage the
repository exists to preserve, and would break byte-identical reproduction.

The exemption is by path prefix and is deliberately narrow. A new prose document does
not inherit it.

Usage:
  python3 tools/measure/check_claim_reconciliation.py
Exit 0 if reconciled, 1 if any live artifact asserts a forbidden figure, 2 on a
structural failure.
"""

import json
import pathlib
import re
import sys

REGISTER = "evidence/claim-status-register-2026-08-29.json"
SCHEMA = "schemas/v1.3/claim-status-register.schema.json"

# Historical bytes: transcripts of what a script printed, and the scripts themselves.
HISTORICAL_PREFIXES = ("evidence/measurement/", "tools/measure/")

# A line asserting a withdrawn figure must also carry one of these.
WITHDRAWAL_MARKERS = (
    "withdrawn", "WITHDRAWN", "superseded", "SUPERSEDED",
    "historical", "HISTORICAL", "not for current use", "forbidden",
)

LIVE_GLOBS = ("docs/*.md", "*.md")



def surface_variants(text: str) -> list[str]:
    """Every surface form a withdrawn figure can take in prose.

    A register entry writes "+26.0%" but a document may write "26.0%", "26%", or
    "**163.5%**". Matching only the register's own spelling is a false-negative
    hole, so each value is expanded. Expansion never drops a digit: it only
    removes a leading sign and, for a value whose fraction is a single trailing
    zero, adds the integer spelling that a summary sentence tends to use.
    """
    seen: list[str] = []

    def add(candidate: str) -> None:
        if candidate and candidate not in seen:
            seen.append(candidate)

    add(text)
    bare = text.lstrip("+")
    add(bare)
    match = re.fullmatch(r"(\d+)\.0%", bare)
    if match:
        add(f"{match.group(1)}%")
    return seen


def live_files() -> list[pathlib.Path]:
    out: list[pathlib.Path] = []
    root = pathlib.Path(".")
    for pattern in LIVE_GLOBS:
        for path in sorted(root.glob(pattern)):
            rel = path.as_posix()
            if rel.startswith(HISTORICAL_PREFIXES):
                continue
            out.append(path)
    return out


def main() -> int:
    try:
        register = json.loads(pathlib.Path(REGISTER).read_text(encoding="utf-8"))
        schema = json.loads(pathlib.Path(SCHEMA).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"STRUCTURAL FAILURE: {type(exc).__name__}: {exc}")
        return 2

    print("=" * 92)
    print("GATE B CLAIM RECONCILIATION CHECK")
    print("=" * 92)

    try:
        import jsonschema
        jsonschema.validate(register, schema)
        print("  [1] SCHEMA     register validates against its declared schema        PASS")
    except Exception as exc:  # noqa: BLE001 - report any validator failure verbatim
        first = str(exc).splitlines()[0]
        print(f"  [1] SCHEMA     {type(exc).__name__}: {first}")
        return 2

    forbidden: list[tuple[str, str]] = []
    for claim in register["claims"]:
        if claim["current_scientific_use"] != "forbidden":
            continue
        for value in claim.get("values_withdrawn", []):
            for field in ("value", "interval"):
                text = value.get(field)
                if not text or text == "see transcript":
                    continue
                for variant in surface_variants(text):
                    forbidden.append((claim["claim_id"], variant))

    print(f"  [2] RECONCILE  forbidden value strings to police: {len(forbidden)}")
    print(f"                 live prose artifacts scanned:      {len(live_files())}")
    print(f"                 historical paths exempt by prefix: {', '.join(HISTORICAL_PREFIXES)}")

    violations: list[str] = []
    for path in live_files():
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for lineno, line in enumerate(lines, start=1):
            if any(marker in line for marker in WITHDRAWAL_MARKERS):
                continue
            for claim_id, text in forbidden:
                if re.search(re.escape(text), line):
                    violations.append(
                        f"    {path.as_posix()}:{lineno}  asserts '{text}'  "
                        f"({claim_id.rsplit('.', 1)[-1]})"
                    )

    print()
    if violations:
        print(f"  RESULT: FAIL - {len(violations)} live assertion(s) of a forbidden figure")
        print("  A live artifact must not assert a figure the register forbids. Either mark")
        print("  the line as withdrawn or superseded, or change the register with evidence.")
        print()
        for row in sorted(set(violations)):
            print(row)
        return 1

    print("  RESULT: PASS - no live artifact asserts a forbidden figure")
    print("  Withdrawn values remain present in retained transcripts, with lineage intact.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
