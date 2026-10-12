# A conditional high-score projection, not a completed storage output

This is an authored qualification of a proposed **new endpoint contract**, developed after the retained diagnostic exposed a low-score nonpositive box. It does not amend, complete or reverse any failed original computation. No model or empirical input was executed in this qualification.

## Proposition and proof

Let S be the complete, ordered population of storage-eligible detections for one image, with fixed observed float32 scores. Set H = {r in S : score(r) > float32(0.5)}. Rows retain their original tile/row order. Greedy hard NMS sorts by descending fixed score and breaks ties by that original order. It decides each row using only already-kept rows and a fixed, defined pairwise IoU predicate. No score updates, box fusion or other population-dependent transformation follows.

All H rows precede every S-minus-H row. Restricting the full sorted sequence to H gives exactly the sequence obtained by sorting H alone, including ties. Before the first high row there are no kept rows in either computation. Inductively, suppose the previously kept high rows agree. The next high row compares with exactly those same kept rows, using the same coordinates, float32 IoU arithmetic and threshold; its keep/suppress decision therefore agrees. This proves, for every numerically admitted full geometry:

`NMS(S) restricted to H = NMS(H)`.

Thus the high result is identical over every valid completion of low coordinates, with high coordinates, scores, classes, row identities and transformation fixed. “Valid completion” means the full algorithm's numerical domain, including its coordinate/area bounds and defined pairwise arithmetic. This statement does **not** assign an NMS result to malformed full input. In particular, the old program's global/retained-geometry refusal remains a refusal.

The proof concerns a fixed algorithm and finite endpoint. It establishes no sampling guarantee, physical truth, model quality, independent human reference, efficiency advantage or new NMS method.

## New contract prerequisites

1. Every frozen image tile must be observed exactly once in its declared order. Missing, failed, skipped and empty are different states. All returned raw rows count toward original per-image caps before any score filter.
2. Both output arrays, shape, real floating detections, integer labels, every original score and score range must be observed. All original coordinates must be finite, and conversion of any coordinate to float32 must remain finite, including excluded low and zero-score rows. Unknown/NaN/infinite scores fail; they cannot be classified low. Only low positive-extent requirements are relaxed; nonfinite inputs and conversion overflow are not admitted. The required original one-class condition remains on every row with float32 score at least float32(0.05). Below-floor padded labels retain their original allowance.
3. The analysis population uses the **converted float32** score strictly greater than 0.5. Original and converted membership can differ at rounding boundaries. No threshold is chosen from outcomes.
4. Every high row must have finite, positive raw and converted coordinate extents and pass the unchanged decoder's scale/offset/floor checks and the unchanged NMS validation. A high-row failure refuses this new endpoint. Each coordinate transform is row-local and unchanged.
5. Low nonpositive-extent conditions are retained as observations, with original row identity and source arrays. Nonfinite raw or converted coordinates instead refuse the entire endpoint; successful-return nonfinite anomaly lists are necessarily empty. The helper distinguishes all-low anomalies from storage-eligible-low anomalies because nonpositive zero-score padding is normally allowed. Neither list is a model-bug label. Low transformed geometry is not evaluated or claimed valid by this helper.
6. Whole-image ordering preserves original tile then row order; the original fixed-score hard NMS and float32 arithmetic remain bound. The downstream reference loss consumes only the high survivors. No storage export, low-quality guarantee or physical interpretation is asserted.

## Authored qualification and comparator

`projection.py` contains pure functions. `project_tile` validates all-row obligations, counts before projection, selects H and invokes a supplied exact-bound original `decode_output` on that subset. Its returned subset count is never used as the original work count. It reports low anomalies and explicitly says no storage output is defined/exported. `complete_projection` is an in-memory composition check on canonical helper outputs, not a parser or verifier for arbitrary externally supplied serialized records. A future worker must bind actual source, tile and raw-array provenance separately.

The controls hash-bind the original worker before compiling its exact bytes. They do not call its execute or any model/session. A separately implemented scalar full NMS supplies the comparator, using the same declared float32 pairwise arithmetic. Full valid geometry is decoded with the shared original coordinate function, then the scalar comparator's high survivors are compared to the projected original NMS. This qualifies projection/NMS behavior; shared decoding is not an independent geometry validation.

The tests cover 500 deterministic authored arrays with mixed score levels and stable ties, 256 distinct valid low-coordinate completions, exact float32 0.5 neighbors and a raw-above-half value that rounds to half, cross-tile tie order, complete coverage, raw-row caps before/after composition, low anomalies and padding distinction, required labels, malformed outputs, nonfinite/invalid scores, all-row raw/conversion finiteness (including zero-score padding), high raw/cast/floor failures, and raw-array immutability.

Two counterexamples delimit the assumptions. Low-first traversal lets an overlapping score-0.4 row suppress a score-0.9 row. A specific global score-renormalization step changes a fixed high score from above to below 0.5 when low rows are present. The latter is a counterexample for that stated score-updating rule, **not** a claim that every Soft-NMS variant violates prefix invariance. No mathematical proof relies on the finite test count.

## Minimal future worker option; not implemented here

A separate prospectively frozen adapter can reuse the unchanged source-bound input preparation, model execution, decoder and NMS. It must bind a new analysis-only contract before execution, preserve the closed original protocols/failures, and retain all raw tile arrays privately before projecting. NPY/NPZ must forbid object pickle; raw retention must be byte/count bounded and verified. Failure to retain required raw evidence must stop the attempt.

For each observed tile, save input/output identities, exact raw arrays, all-row counts, high membership and anomaly dispositions. Pass the remaining **all-row** budget to the qualified helper. After complete roster checks, concatenate high results in original order and use the original NMS. Return an explicit `complete_analysis_projection` endpoint with analysis predictions and row provenance. Do not populate `storage_predictions`, relabel it full storage completion, or reuse the old result/comparison schema without a separately explicit adaptation and checker review.

A qualified complete first pair would still establish only the new source-specific conditional benchmark endpoint. It would not undo original failures, establish upstream behavior on malformed inputs, justify cohort extension automatically, or show Reiyah beats a competent ordinary high-score NMS and matching baseline. No empirical retry is authorized by this qualification artifact.
