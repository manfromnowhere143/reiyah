# Label dependence

Version: `0.2.0` (insertions), alongside `0.1.0` (deletions)

Lifecycle status: `proposed`

Two declared families over one annotation conditional case, each preregistered before it was run
and each reported as its own family.

| family | cases | result |
|---|---:|---|
| deletions, `0.1.0` | 107 | six single deletions change the criterion from `supported` to `excluded`. Breakdown number **1** |
| insertions, `0.2.0` | 20 singles then all 190 pairs | none changes the criterion. Singles range `[1, 2]`, pairs range `[1, 3]` |

The verdict is fragile to a spurious label and not to a missed one. Read
[`docs/LABEL_DEPENDENCE_2026-09-14.md`](../../../docs/LABEL_DEPENDENCE_2026-09-14.md).

Each of the six witnesses is confirmed by
[`check_label_dependence.py`](../../../tools/measure/check_label_dependence.py), which imports
nothing from the producer and writes its own matcher. Witnesses are named by anchor, class and the
label's local index; no benchmark identifier appears in any retained artifact.

`insertion-family.json` is the original run and is retained unchanged.
`insertion-family-corrected.json` is the successor under two corrections the consumer found: the
pair extrema are now recorded, and the insertion rule applies the declared strict 2 metre distance
to the supplied coordinates instead of a graph neighbourhood. The conclusion is unchanged. See
[`docs/LABEL_DEPENDENCE_SECOND_CASE_2026-09-14.md`](../../../docs/LABEL_DEPENDENCE_SECOND_CASE_2026-09-14.md).

A deletion is a hypothetical spurious label correction and an insertion a hypothetical missed one.
Neither is an observed error, a probability, a physical reading or a human admission. The same
detector change under open physical references remains `[-8, 8]` and is untouched by this work.
