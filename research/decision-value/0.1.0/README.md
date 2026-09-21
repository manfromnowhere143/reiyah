# Completed-map decision audit, 0.1.0

Status: exploratory recorded-data reproduction. **Three sequence decisions
support replacement; one remains blocked. Reiyah and the competent conventional
method agree on every case. No comparative advantage is established.**

The decision was frozen before deliberate numeric inspection: should a completed
map use the published offline trajectory when its mean squared global error is
strictly smaller than the stored online trajectory's on the entire checkpoint
cohort? Published aggregate outcomes were already exposed. This is not a blind
benchmark, a driving result, a causal online comparison or physical certification.

## Observed results

All four FAST-LIO-SAM sequences at publisher revision
f2921a58caf5a87c1f4f73b48c6f2a5e35f92924 were retained. No sequence or visit was
removed to improve the result. The3D RMSE values below concern the recorded
reference under the pinned publisher coordinate transformation.

| Sequence | Online visits / expected | Offline visits / expected | Online RMSE, m | Offline RMSE, m | Complete-cohort decision |
| --- | --- | --- | --- | --- | --- |
| Construction1 |16/16|16/16|0.255856|0.247573|Supported|
| Construction2 |16/16|16/16|0.438971|0.373861|Supported|
| Stadtgarten1 |36/36|35/36|0.162473|0.068066|Blocked|
| Stadtgarten2 |19/19|19/19|0.149656|0.099170|Supported|

**The Stadtgarten1 RMSE columns cover different cohorts.** Their comparison
cannot decide the frozen36-visit question. The original publisher entry point
prints both numbers without exposing visit counts. C1 adds the same full-cohort
check as Reiyah and reaches the same refusal. Do not attribute a decision to
the paper's authors that their artifact never explicitly made.

The missing offline visit is checkpoint4300. Its closest available pose is
23.527828s away, beyond the frozen2s association limit; the trajectory ends
that far before the visit. Raising the limit or substituting another method's
pose would change the frozen evidence contract. Neither was done.

A separately frozen **post-result diagnostic** expresses the complete nominal
loss difference as (-0.7881582637 + e²)/36, where e is the unknown missing
position error in metres. Its sign changes at about0.88778278m. Authored
completions with0m and2m missing error produce opposite decisions. They are
counterexamples to claiming resolution, not observed or imputed positions.

Exactly what would resolve this narrow gap: a provenance-bearing offline
base-center position at that frozen checkpoint time, using the same reference
and timestamp convention. For example, a valid record whose resulting error
is0.5m would support replacement; one with2m would contradict it. This example
does not assert that Daniel or a private team possesses such a record.

## Evidence boundaries and comparison

The [primary dataset paper](https://arxiv.org/html/2604.07151v1), submitted
8April2026, describes independently surveyed checkpoints for handheld mapping.
Its reported accuracy estimates do not establish deterministic per-row bounds.
The [pinned evaluation source](https://github.com/Willyzw/rtk-slam-eval/tree/f2921a58caf5a87c1f4f73b48c6f2a5e35f92924)
and all selected source bytes are identified in [sources](sources.json) and
[references](references.json), retained privately with access receipts.

All paths share the publisher's coordinate conversion, including a48.22m ENU
height correction. Its physical provenance remains unresolved here. Native and
checker arithmetic validate rounded nominal operands, not that common backend
or physical reality. All recorded online associations have zero timestamp
offset; offline maxima are0.536814,0,0.920657,0.896218s in sequence order.
These are observed offsets, not motion-error guarantees.

C0 is unmodified publisher code. C1 is a same-author strict wrapper around
publisher parsing, matching, conversion and RMSE. Reiyah enumerates matches and
uses exact rational loss differences. A separate checker uses neighboring-time
search and the identity (B-A) dot (B+A-2Q). No arm's final answers are constants
or expectations supplied to the other. Shared checks/conversion and authorship
preclude claims of independent replication.

One printed reproduction discrepancy remains: Construction2 offline rounds
to0.374m in this pinned artifact, while the exposed paper figure was0.373m.
The cause is unresolved. There was no calibration change or rounding adjustment
to force agreement. Other quoted three-decimal global values reproduce.
The frozen question has not been changed in response.

## Verification, failures and costs

[Verification](check.json) checks173associations per arm,346across both
executions. [Authored controls](controls-authored.json) cover17cases;
[source controls](controls-source.json) cover3custody substitutions;
[result mutations](controls-mutations.json) reject26alterations.
The [post-result diagnostic](missing-diagnostic.json) rejects six attempts
to promote or numerically fill the blocked case. Counts are software checks,
not scientific replications or evidence of superiority.

The first conventional execution computed its cases but failed saving because
the output parent directory was absent. Its receipt/stderr remain retained;
its unsaved outputs are not successful measurements. Creating the parent and
rerunning unchanged frozen code succeeded. The earlier supervisor parent-path
failure and a pre-freeze diagnostic lint failure also remain in
[the failure record](failures.json). No frozen numerical code was changed.

Successful whole-process times were0.293534s for C1 and0.240490s for Reiyah;
internal workflows0.133771s and0.087141s. Each ran once in fixed order.
This is not a speed benchmark; no speed superiority follows. The failed C1
attempt also cost0.242334s and stays in total accounting. See
[costs](costs.json) for acquisition, preparation, checking, failures and storage.
Engineering effort, economic value, charges, energy, network overhead and peak
workflow memory remain unknown. Final integration/readback costs are retained
in the private owner after the public cutoff.

## Investment decision and reproduction

**Modify the investment thesis:** complete-cohort decision auditing is useful,
but this experiment supplies no advantage over a competent conventional
implementation. It does not justify expanding a new monitoring framework.
A further value experiment needs a decision the conventional method leaves
wrong or unresolved, with an obtainable discriminating observation and all
acquisition/checking costs included. Do not repeat this exposed case as a
novelty benchmark or ask for unspecified private-team records.

[Method](METHOD.md), [question](QUESTION.md), [protocol](protocol.json),
[original freeze](freeze.json) and [diagnostic freeze](diagnostic-freeze.json)
separate before-outcome commitments from post-result explanation.

To reproduce, supply the24exact private source files in the layout named by
sources.json using their public pinned URLs. The broader sensor archives and
images are unnecessary. Use the existing pinned Python/NumPy environment,
offline, with the two-second policy unchanged:

```sh
python -B controls.py authored
python -B source_controls.py /path/to/private/vendor
python -B /path/to/private/vendor/eval/eval.py --method fast_lio_sam
mkdir -p /path/to/private/results
python -B decision.py conventional /path/to/private/vendor /path/to/private/results/conventional
python -B decision.py reiyah /path/to/private/vendor /path/to/private/results/reiyah
python -B verify.py /path/to/private/vendor /path/to/private/results/conventional /path/to/private/results/reiyah
```

Those example commands are development reproduction, not the byte-bound
monitored execution used here. Exact owned commands and receipts remain under
~/.codex/reports/reiyah/decision-value-2026-09-21-9xm9fu4f/private/commands/.
The publisher code requires available NumPy for this slice; no dependencies
were installed. [Distribution boundaries](DISTRIBUTION.md) exclude all
third-party payloads and full per-visit traces.

All1,433reserved images remain closed. Historical controller and earlier
negative findings remain unchanged. Gate A remains operator-unaccepted.
The original ten-hour assignment is complete; no clock was restarted or padded.

