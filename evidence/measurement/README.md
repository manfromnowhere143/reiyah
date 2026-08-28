# Measurement evidence

Retained transcripts from the Gate B offline measurement work defined in
[`docs/GATE_B_MEASUREMENT_CONTRACT.md`](../../docs/GATE_B_MEASUREMENT_CONTRACT.md).

These are derived measurements over publicly licensed data. No dataset payload bytes are
redistributed here, because the nuScenes licence is CC BY-NC-SA 4.0 and non-commercial. Inputs are
retained as pointers with verified digests; only the outputs of computation over them are retained
as bytes.

| File | Contents |
|---|---|
| `result_a_exact.txt` | Ground-truth objects removed by the official evaluation filter, by class, range, visibility and scene condition |
| `audit_result_a.txt` | Ten adversarial audits of Result A, including the external check that reproduces nuScenes' published 6,019 validation samples |
| `replication_independent_copy.txt` | Result A re-derived on a separately obtained copy of the dataset, on different hardware, with independently written code |
| `result_b.txt` | Recall inflation granted by the filter, stratified |
| `result_d.txt` | Joint camera/lidar miss table and the marginal RSS lift, on both denominators |
| `result_e.txt` | The same lift conditioned on scene difficulty, with Mantel-Haenszel and CMH statistics |
| `result_f.txt` | Whether zero keyframe lidar return implies non-detection, tested directly |
| `result_g.txt` | Evidence cost of the measured dependence, with the square-root scaling derivation |
| `result_h.txt` | Pairwise lift across four detectors and six pairs, same-modality against cross-modality |

## Reading these

Every transcript states its own denominator and its own operating point. None of them should be
quoted without both.

Two results are superseded by later ones and are retained anyway: Result D's marginal figure is
contextualised by Result E, and Result B's upper bound is closed by Result F. A superseded result
is not a deleted one.

## Status

All of these are `proposed`. Nothing here has passed the evidence admission process, been accepted
by an operator, or been independently reviewed. A measurement that has been audited is still not an
accepted claim.
