# Label dependence

Version: `0.2.0` (insertions), alongside `0.1.0` (deletions)

Lifecycle status: `proposed`

Two declared families over one annotation conditional case, each preregistered before it was run
and each reported as its own family.

| family | cases | result |
|---|---:|---|
| deletions, `0.1.0` | 107 | six single deletions change the criterion from `supported` to `excluded`. Breakdown number **1** |
| insertions, `0.2.0` | 20 singles then every pair | none changes the criterion. The weighted delta only rises, 1 to 2 |

The verdict is fragile to a spurious label and not to a missed one. Read
[`docs/LABEL_DEPENDENCE_2026-09-14.md`](../../../docs/LABEL_DEPENDENCE_2026-09-14.md).

Each of the six witnesses is confirmed by
[`check_label_dependence.py`](../../../tools/measure/check_label_dependence.py), which imports
nothing from the producer and writes its own matcher. Witnesses are named by anchor, class and the
label's local index; no benchmark identifier appears in any retained artifact.

A deletion is a hypothetical spurious label correction and an insertion a hypothetical missed one.
Neither is an observed error, a probability, a physical reading or a human admission. The same
detector change under open physical references remains `[-8, 8]` and is untouched by this work.
