# Audit method and limits

Document ID: `reiyah.roadmap-audit.method`. Version: `0.1.0`.
Lifecycle status: `exploratory`. Dated 19 September 2026.

This retrospective audit has two jobs: reconcile execution with the existing
roadmap, and identify published comparators or assumptions that materially change
the next decision. Parent outcomes were known. This is not preregistration, a
systematic literature review, external peer review or a new empirical experiment.

## Local execution audit

The canonical controller was verified clean at
`74fbacc77a3c74d3a4962f488b589ee614a4c575`. Normal fetch and remote readout agreed
with local main at `23db0b322707e7e3d2e93efbb33d4e0127070c47`. A new owned
same-repository candidate uses branch
`research/2026-09-19-roadmap-audit-tgwsxrpn`; its common Git directory and remote
match the controller. No closed checkout or experiment is edited.

The selected roadmap, mission, thesis, charter, workflow brief, source terms,
negative monitor result and current research artifacts are hash-bound in
[audit.json](audit.json). Their historical statuses are read as written. Source
bindings refer to the selected base commit, so updating the current handoff does
not pretend that its new bytes were the audited historical text.

A separate audit script recounts the published operating CSV and full-answer
comparison CSV; compares decisions, target identities, witnessed unresolved rows,
query-floor counts and candidate wins/losses; and checks the resulting summary.
This is fresh aggregate reconciliation, not a rerun of geometry, matching,
scientific proof verification or outcome-reserve access. Engine perception code
is compared with its retained source revision. The documented default
`tools/measure/gate_b_check.py` runs using the existing pinned runtime after
the macOS network-denial policy is entered. Historical Gate A replay is not
substituted for this research check.

No tests are added for the documentation change. Integrity, source coverage,
local links, actual aggregate reconciliation, current research consistency and
public scope are the relevant checks. The new proposed sequential methods task
has not been executed; its mathematics and implementation still require their
own frozen controls and verification.

## Literature selection

The private audit plan was recorded after the first eight discovery queries.
It set a cutoff of 19 September 2026, at most 32 search queries, 48 retained
direct retrieval attempts, 250 MiB of new non-checkout artifacts, and a 5 GiB
free-space floor. All 32 queries were used. Forty direct retrievals produced
37 successful bodies and three failures. Source retrieval is reading only:
no downloaded code, model, package or paper command is executed.

Select primary papers, publisher/proceedings records and official technical
reports relevant to: adaptive evaluation; finite-population and sequential
inference; prediction-assisted efficiency; exact optimization proofs; reference
and noise assumptions; downstream autonomous-system evaluation; and the
human-automation construct boundary. Include foundational work when it is a
serious comparator. Distinguish source assertions from independently reproduced
results, preprints from publication records, and full-text section inspection
from abstract-only discovery. Dates are taken from the retained primary record,
not the search engine's relative dates or secondary summaries.

Twenty primary works are selected: thirteen have full HTML with relevant method,
assumption or limitation sections inspected; seven have only the primary
abstract/metadata record reviewed. Relevant full-text section inspection is not
a complete proof audit. No external implementation or paper experiment was run.

Secondary generated summaries, unofficial leaderboards, unrelated training
papers, and uninspected methodological assertions are not evidence for the
recommendation. The small eight-method driving correlation preprint stays a
limited diagnostic. An unavailable situation-awareness paper is excluded from
the retained substantive source set; the human channel's qualification gap stays
explicit. This targeted review does not establish exhaustive coverage of human
factors, causal inference, standards, every competitor or every 2026 paper.

## Retention, failures and corrections

[sources.json](sources.json) binds every successful or failed response body,
retrieval time, selected source version, metadata and extraction. Author/publisher
claims are evidence only for their bounded statements. They do not become Reiyah
performance evidence. Payloads stay private under [DISTRIBUTION.md](DISTRIBUTION.md).

- The SCIP documentation endpoint returned HTTP 429. It is not cited as retained
  content. The openly available authors' versioned technical report supplies the
  exact-mode description; no challenge or rate-limit bypass was attempted.
- The situation-awareness publisher endpoint returned HTTP 403. Its retained
  failure is not promoted to a reviewed paper or a substantive conclusion.
- A guessed PMLR noisy-label PDF route returned HTTP 404. That source remains an
  abstract-only record; no full-text review is claimed.
- The AAAI response used gzip despite the identity encoding request. An initial
  text-only inspection was unreadable. The original compressed bytes are intact;
  the explicit gzip decoding and corrected extraction are separately recorded.
- Search metadata initially surfaced an older abstract for Bayes-assisted PPI.
  The retained v2 explicitly says its time-uniform intervals are asymptotic. This
  audit uses the versioned primary text, not the stronger cached wording.
- A later verification-summary assembly initially rejected the consistency
  checker's explicit optional attack-suite skip. The failed assembly is retained.
  The corrected summary requires nine passing checks and exactly that one
  declared skip. The checker is unchanged; its skipped suite is not called passed.

Rights links are recorded where present. The retained PMLR FAQ does not supply a
blanket redistribution permission. Unknown permissions remain unknown, and none
of these payloads is put in public Git. Copies of third-party figures, tables and
abstracts are unnecessary for the public synthesis.

## Exact search queries

Each group was one four-query call; full returns and UTC intervals are retained
privately as `web-search-01.json` through `web-search-08.json`.

- "active testing" model evaluation label efficient 2025 2026
- "prediction powered" adaptive evaluation sequential 2025 2026
- "Sim2Val" NVIDIA paper 2025
- SCIP 10 exact rational proof logging VIPR 2025 2026

- site:arxiv.org "Prediction-Powered Active Testing"
- site:arxiv.org "Stop Guessing When to Stop Testing"
- site:proceedings.mlr.press "Active Statistical Inference"
- site:arxiv.org autonomous driving evaluation perception metric planning "2026" benchmark

- site:arxiv.org confidence sequences active evaluation noisy labels 2025 2026
- site:proceedings.mlr.press conformal risk control noisy labels 2025
- site:arxiv.org "NAVSIM v2"
- site:openaccess.thecvf.com perception evaluation planning "2025" detection

- "NAVSIM v2" autonomous driving benchmark
- "confidence sequences" "active" "model evaluation"
- "A No Free Lunch Theorem for Human-AI Collaboration"
- "perception" "planning" "evaluation" "2026" "Waymo"

- "Prediction-Powered Inference" "Science" 2023
- "Confidence sequences for sampling without replacement"
- "Anytime-valid" "prediction-powered"
- "BridgeSim" "arxiv"

- "Prediction-Powered E-Values"
- "BridgeSim: Unveiling"
- "How to assess situation awareness while driving with automation"
- "Prediction-Powered Risk Monitoring of Deployed Models"

- "confidence sequences" "partial identification"
- "active testing" "noisy labels" "2026"
- "prediction-powered" "imperfect" "labels" "2026"
- "risk-limiting" "audits" "side information"

- "No Free Lunch: Non-Asymptotic Analysis of Prediction-Powered Inference"
- "Risk-limiting Financial Audits" "2305.06884"
- "Debiased Inference for AI-Generated Data without Gold-Standard Labels"
- "Calibeating Prediction-Powered Inference"
