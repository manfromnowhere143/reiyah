# Research intake

Interface version `0.1.0`. An offline, standard-library prototype for checking
whether a research proposal has the records needed for review. It does not
retrieve papers, judge scientific truth, run a model or authorize a build.

Research needs two different kinds of checking. Exact source identity and quoted
bytes can be checked mechanically. Whether those words support a claim in the
actual engineering setting needs a substantive review. This helper checks the
first and preserves the supplied assessment of the second.

## Use

From the repository root, with Python 3.10 or newer on a POSIX system:

```sh
python3 -B -m tools.research_intake assess \
  --mission research/decision-research/0.1.0/compatible-augrc.mission.json \
  --dossier research/decision-research/0.1.0/compatible-augrc.dossier.json \
  --sources .
```

The result is deterministic JSON on stdout. `--output /path/to/new.json`
atomically creates a new result and refuses to replace an existing file. Exit
code zero means a well-formed assessment was produced, including an unresolved
or incompatible assessment; inspect `status`. Invalid records exit with code
two and a JSON diagnostic on stderr. The Python entry point is
`assess(mission, dossier, source_root)`.

## Record contract

The [four complete examples](../../research/decision-research/0.1.0/cases.json)
show every field. Unknown properties are rejected. Stable artifact IDs and
`schema_version` identify the typed contract; the executable validator is its
current specification. This version has no separate JSON Schema or migration
layer.

| Record | Required content |
| --- | --- |
| Mission | Project, versioned decision, explicit assumptions, observation requirements, closure reason and prior source identities. |
| Proposal | Technique, competent comparator, expected decision impact, falsifier and proposed next-test resource caps. These caps are not measured costs or automatically enforced execution budgets. |
| Retrieval | Completed or incomplete **declared scope**, with limitations. This never means exhaustive literature coverage. |
| Sources | Canonical work ID, pinned version, exact digest, size, root-relative UTF-8 path, role, UTC capture time, access/terms assertions and inclusion/exclusion/unavailability reason. |
| Evidence | Source identity, literal UTF-8 byte interval `[start_byte,end_byte)`, exact text, and method/observation/limitation role. |
| Assessment | One supplied interpretation per assumption: compatible, incompatible or unknown; referenced evidence; observation qualification state. |
| Reopening | An explicit proposal, changed source references and rationale. A later capture date alone is insufficient. |

Mission binding is SHA-256 of UTF-8 JSON with sorted keys, compact separators,
non-ASCII characters preserved, no nonfinite numbers, and one trailing newline.
`digest(mission)` implements it. Source hashes cover exact file bytes.
The host must select the current authorized mission. A self-consistent older
mission/dossier pair remains self-consistent; this helper has no authoritative
mission registry. Capture timestamps are checked for syntax and calendar
validity, not verified against an external clock or an admissible source cutoff.
Supported work identities are `arxiv:YYMM.NNNNN`, lower-case `doi:10.…`,
`repo:github.com/owner/repository` and `local:project/artifact`. Identity spelling
is checked; remote resolution and equivalence are not.

Each input JSON is capped at 1 MiB, each source at 4 MiB, all source entries at
16 MiB. Collection and text lengths are bounded. Source-relative paths reject
traversal and symlinks, and are opened relative to a directory descriptor.
The explicit source root is the operator-selected boundary. The CLI reads
regular files, rejects duplicate JSON keys and refuses floating/nonfinite
numbers. Source contents are data and are never executed.

## Meaning of the result

| Status | Meaning |
| --- | --- |
| `ready_for_review` | Required structure and literal source bindings are present for the supplied positive assessments. Semantic review remains necessary. |
| `needs_evidence` | An assumption, full-text support, required observation record or declared retrieval scope is incomplete. |
| `incompatible` | At least one supplied assessment says the method does not fit. This is not an automatically proven mathematical conclusion; missing evidence is still reported. |
| `closed_no_new_basis` | A closed mission has no explicit proposal with changed source bytes used in an assessment. |

Abstract-only evidence cannot make a positive method assessment ready. A method
paper cannot substitute for a required observation record. Calling an observation
`qualified` is still a reviewer assertion. A correctly quoted but irrelevant
sentence can pass structural checking: a dedicated control demonstrates that
limitation. No false claim of automated entailment checking is made.

Changed bytes are only candidates for reopening review. The output distinguishes
new work, changed version and changed bytes under the same work/version. A
repository can contain several files under one commit, and an HTML page can
change without its scientific content changing. The helper does not verify
material novelty, current upstream versions, capture timestamps, access rights,
rights compliance, physical validity or scientific support. Its authority flags
remain false.

## Integration and validation

An agent or analyst supplies these records after inspecting primary methods,
code, negative evidence and assumptions. The host project retains authority,
budgets and acceptance criteria. Sentinel, Nisayon, Etzio, Telos and Inbar are
future adapter targets; no sibling integration or shared unattended service is
implemented. The interface is dependency-light, but portability beyond the
tested local POSIX environment is not established.

```sh
python3 -B -m unittest discover -s tests -p test_research_intake.py
python3 -B research/decision-research/0.1.0/reproduce.py
```

Read the [research decision](../../docs/research-decisions/research-to-build-2026-10-12.md)
for the current-system comparison and the
[development pilot](../../research/decision-research/0.1.0/README.md) for the
distinction between checking this interface and demonstrating useful research.
