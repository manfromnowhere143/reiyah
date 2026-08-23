# Gate A Standards and Guidance Crosswalk

## Decision statement

**As of:** 2026-08-23

**Lifecycle status:** `proposed`

**Compliance claimed:** `false`

This is a dated evidence-and-gap map, not a legal opinion, safety case, conformance analysis,
certification, compliance claim, or scientific result. Reiyah has no product runtime and has not
implemented or been assessed against any source below. The current machine-readable map is
[`evidence/standards-crosswalk-1.1.0.json`](../evidence/standards-crosswalk-1.1.0.json);
current custody is in
[`evidence/source-ledger-1.1.0.json`](../evidence/source-ledger-1.1.0.json). The unversioned
1.0 files are historical predecessor artifacts only.

## Retained source inventory

| Source ID | Exact version and issue/publication date | Evidence class | Retained artifact | Decisive limitation |
|---|---|---|---|---|
| `src.iso.26262-1.2018.open-data` | ISO 26262-1:2018, edition 2; 2018-12-17 | Official catalog metadata | [`iso-open-data-68383-20260819.jsonl`](../evidence/sources/iso-open-data-68383-20260819.jsonl) | Part 1 metadata only; full series and clauses absent; record lists a successor project. |
| `src.iso.21448.2022.open-data` | ISO 21448:2022, edition 1; 2022-06-30 | Official catalog metadata | [`iso-open-data-77490-20260819.jsonl`](../evidence/sources/iso-open-data-77490-20260819.jsonl) | Scope summary only; 181-page normative text absent; record reports revision activity. |
| `src.iso-tr.21959-1.2020.open-data` | ISO/TR 21959-1:2020, edition 2; 2020-01-09 | Official catalog metadata | [`iso-open-data-78088-20260819.jsonl`](../evidence/sources/iso-open-data-78088-20260819.jsonl) | Scope says the report is informative; definitions, protocol, and report text absent. |
| `src.iso-pas.8800.2024.open-data` | ISO/PAS 8800:2024, edition 1; 2024-12-13 | Official catalog metadata | [`iso-open-data-83303-20260819.jsonl`](../evidence/sources/iso-open-data-83303-20260819.jsonl) | Scope summary only; 172-page PAS absent; two successor identifiers are unreviewed. |

## Historical pointer-only records

These records preserve former local identities and hashes but no current payload. They are
ineligible for positive mapping evidence.

| Source ID | Recorded identity | Current custody | Consequence |
|---|---|---|---|
| `src.nist.ai-100-1.2023.pdf` | NIST AI RMF 1.0; report NIST AI 100-1; 2023-01-26 | Pointer only | The prior PDF bytes are excluded because the general NIST rights statement leaves a document-specific third-party-material caveat unresolved. No positive NIST mapping is admitted. |
| `src.nist.ai-100-1.2023.publication-page` | NIST AI RMF 1.0 publication page, 2023-01-26 | Pointer only | The old mutable HTML capture is excluded and supplies no current mapping evidence. |
| `src.unece.r157.rev1.2025.documentation` | E/ECE/TRANS/505/Rev.3/Add.156/Rev.1, 2025-03-27 | Pointer only | No document scope or clause proposition is admitted. |
| `src.unece.wp29.2022-59-rev1.authentic-text` | ECE/TRANS/WP.29/2022/59/Rev.1, 2022-05-30 | Pointer only | Both UN mappings are explicit evidence gaps until lawful current bytes and qualified review exist. |

The four ISO files are exact complete-record byte ranges from the official ISO Open Data JSON
Lines object, pinned by ETag and `Content-Range`. They are not transcriptions and not standards
text. See [`SOURCE_POLICY.md`](SOURCE_POLICY.md) for the range-retention rule.

Every machine-readable mapping names one versioned `identity_source_ref`. Its publisher, full
title, document identifier, exact version, and publication date must match that source-ledger
record exactly. Fuzzy, substring, or composite identity matching is prohibited. Positive
`evidence_source_refs` may name eligible retained payloads only. Pointer-only identities may
appear only in `discovery_source_refs` and cannot silently replace or broaden evidence.

The offline validator freezes four retained-payload identities and digests plus four historical
pointer records. It derives ISO identity fields from the retained JSON Lines objects. NIST PDF
identity remains prior digest-pinned custody metadata rather than current retained evidence or a
claim of independent machine interpretation. Pointer metadata is structurally ineligible as
positive evidence.

## Proposed mappings

| Mapping ID | Exact external scope and locator | Proposed Reiyah relevance | Exact comparator | Evidence | Open gap | State |
|---|---|---|---|---|---|---|
| `map.iso.26262-1.2018.scope-boundary` | ISO 26262-1:2018 metadata record 68383: malfunctioning behaviour of safety-related road-vehicle E/E systems; catalog `scope` field only. | Preserve a candidate boundary between malfunction evidence and intended-function/model-insufficiency evidence. | ISO 21448:2022 metadata scope and proposed protocol `reiyah.protocol.harbor-gate-a@1.1.0`; no conformance comparator. | `src.iso.26262-1.2018.open-data@1.1.0` | Full series, clauses, interpretation, applicability, and successor absent. | `partial_mapping` / `proposed` |
| `map.iso.21448.2022.scope-boundary` | ISO 21448:2022 metadata record 77490: intended-function specification/performance insufficiency, complex sensing/processing, foreseeable misuse, and exclusions; catalog `scope` only. | Keep intended-function insufficiency, unknown scenario, validity boundary, and misuse concepts distinct from faults and outcomes. | ISO 26262-1:2018 metadata scope and proposed Gate A protocol; no implementation target. | `src.iso.21448.2022.open-data` | Normative clauses and pending successor absent; no independent SOTIF review. | `partial_mapping` / `proposed` |
| `map.iso-pas.8800.2024.ai-safety-scope` | ISO/PAS 8800:2024 metadata record 83303: AI output insufficiency, systematic error, random hardware error, external-element interaction, and safety properties; catalog `scope` only. | Preserve candidate evidence categories for AI-related errors and interactions without authorizing AI runtime or an assurance claim. | ISO 21448:2022 scope at metadata level and proposed Gate A protocol. | `src.iso-pas.8800.2024.open-data` | PAS text, safety properties, exact clauses, and successor projects absent. | `partial_mapping` / `proposed` |
| `map.iso-tr.21959-1.2020.human-state-concepts` | ISO/TR 21959-1:2020 metadata record 78088: informative driver performance/state concepts for engagement, fallback readiness, resumption, and evaluation contexts. | Prevent “driver state,” “fallback-ready,” and Reiyah's protocol-bound readiness estimand from becoming unreviewed synonyms. | Proposed Reiyah readiness estimand in `reiyah.protocol.harbor-gate-a@1.1.0`; constructs are non-equivalent. | `src.iso-tr.21959-1.2020.open-data@1.1.0` | Full report, definitions, research gaps, experiment guidance, and human-factors review absent. | `partial_mapping` / `proposed` |
| `map.unece.r157.driver-availability` | No clause locator is admitted in 1.1 because both UN records are pointer-only. | Preserve a future review question about separating availability observation, readiness belief, transition decision, intervention, and outcome. | Unmeasured pending eligible exact evidence. | None; two discovery references only | Lawful current text, amendments, applicability, regulatory review, and construct validation absent. | `evidence_gap` / `proposed` |
| `map.unece.r157.transition-recoverability` | No clause locator is admitted in 1.1 because both UN records are pointer-only. | Preserve a future review question about transition, response, fallback, and recovery without equating these constructs. | Unmeasured pending eligible exact evidence. | None; two discovery references only | Lawful current text, tests, jurisdictional context, human-factors review, and empirical mapping absent. | `evidence_gap` / `proposed` |
| `map.nist.ai-rmf-1.0.risk-governance` | No section or appendix locator is admitted because both NIST records are pointer-only. | Preserve a future review question about comparing general AI risk-governance vocabulary with Gate A evidence inventory and change control. | Proposed Gate A 1.1 protocol; no current NIST content comparator. | None; two discovery references only | Document-specific rights, eligible current bytes, later versions, a selected profile, automotive tailoring, and independent assessment absent. | `evidence_gap` / `proposed` |

Every row is governed by this required interpretation:

> This mapping is not a legal, safety, conformance, certification, or compliance conclusion.

## Cross-source boundaries retained by Gate A

These are architecture decisions, not findings about the external documents:

1. Evidence about malfunctioning behaviour is not silently merged with intended-function or AI
   output insufficiency evidence.
2. A driver-availability observation or rule is not latent readiness ground truth.
3. Transition demand, delivered warning, driver response, minimum-risk manoeuvre, and outcome are
   separate objects with separate provenance and time.
4. Generic risk-governance guidance does not establish vehicle-specific validity or safety.
5. Publisher metadata, full text, documentation copies, guidance, generated summaries, digests,
   validation, consensus, and operator acceptance remain distinct evidence and authority classes.

## Unresolved coverage

Gate A does not retain full ISO normative text, the broader ISO 26262 series, relevant companion
parts of ISO/TR 21959, successor drafts, later R157 amendments, jurisdictional adoption evidence,
SAE taxonomy text, current NHTSA human-factors guidance bytes, empirical readiness or takeover
literature, benchmark protocols, datasets, or independent reviews. No inference is made from those
absences.

Closing a gap requires retained exact bytes, provenance, qualified independent review, a separately
authorized falsifiable protocol where relevant, and explicit operator review. Architecture
completion or a passing validator cannot close a scientific, legal, standards, or acceptance gap.
