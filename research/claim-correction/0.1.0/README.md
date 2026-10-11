# Correction of selected-population and independence interpretations

Document ID: `reiyah.claim-correction`

Version: `0.1.0`

Lifecycle status: `corrected`

Date: 2026-10-10. Corrects the interpretation of retained measurements; it does
not replace their original transcripts or constitute a new empirical experiment.

## Decision

Withdraw the inference that detector-selected coincidence coefficients bound
population dependence. Withdraw the general same-kind/cross-kind independence
law and its derived human-machine safety-evidence credit. Preserve the
descriptive measurements, their sampling limits and every historical record.
The [successor register](../../../evidence/claim-status-register-2026-10-10.json)
separates permitted selected-sample descriptions from these forbidden inferences.

## Exact falsification of the population bound

Write the selected coefficient as `c = n * n_both / (n_auto * n_gaze)`.
Both the marginal counts and the joint count change when omitted objects are
added. A sample-relative median can change which original objects count as
below-threshold too. None of these operations is generally monotone in `c`.

Four selected objects have automation flags `[true,false,true,false]` and gaze
`[2/5,9/20,11/20,3/5]`. Their median is `1/2`, each cell count is one, and `c=1`.
Add four automation-missed objects. These are two alternative completions of
the same selected data, not additional observations from BDD-A.

| Completion | Added gaze | Recompute population median | Keep selected threshold |
| --- | --- | --- | --- |
| Higher gaze | `[16/20,17/20,18/20,19/20]` | `2/3` | `2/3` |
| Lower gaze | `[1/20,2/20,3/20,4/20]` | `4/3` | `10/9` |

Both threshold conventions permit movement in either direction. Changing the
threshold convention cannot rescue the claimed general lower bound. Nor does
this construction identify the true unobserved population or its coefficient.
An unnormalized count of additional joint events would be a different quantity.

## What the original results still say

H5's cells `[1821,1927,5131,5025]` reproduce the rounded coefficient `0.972` on
13,904 selected objects. H5b's `[1434,1547,4118,4005]` reproduce `0.962` on
11,104 selected objects. Their populations differ. H5b's historical interval
`[0.927,0.993]` resampled clips with the sample median fixed; this correction
does not rerun it or extend its coverage to selection, reference error,
observer variability or unseen objects.

The operational variables are low detector score and below-median heatmap
intensity. They do not identify human belief, awareness, recoverability or joint
silent misses. A small descriptive departure from the product of marginals
does not provide an equivalence test or independence certificate. H6 uses
another detector as reference and inherits the population limitation.

LLM jury results remain benchmark-specific descriptions. A shared arithmetic
formula does not identify the same latent construct across sensors, gaze and
language models. The homogeneous-equivalent model count is not a literal
number of independent models. Residuals after adjustment for a difficulty
proxy do not isolate lineage causality. The previously withdrawn Result S
evidence-cost interpretation supplies no safety credit to these studies.

## Reproduction and scope

From the repository root, using existing CPU resources and the Python standard
library:

```sh
python3 -B research/claim-correction/0.1.0/probe.py
python3 -B -m unittest discover -s research/claim-correction/0.1.0 -p 'test_*.py' -v
```

[probe.py](probe.py) checks exact rational counterexamples and the retained
point-estimate arithmetic. [test_probe.py](test_probe.py) adds malformed-input,
undefined-denominator, transcript-forgery and changed-byte controls.
[bindings.json](bindings.json) identifies the preserved predecessor, scripts,
transcripts and value-study results. This is an explicit finite check, not a
general semantic validator of every scientific sentence.

The research consistency command remains
`python3 -B tools/measure/gate_b_check.py --json /new/path/report.json`.
Without replay flags it checks historical bindings and current documents; it
replays no historical experiment. The correction probe and perception unit
tests have separate scopes. None is the locked Gate A release procedure.

## Remaining work and investment gate

Historical H5/H5b extraction still ignores ffmpeg exit status and can omit
inputs without a complete disposition ledger. Its occurrence in the retained
runs is unknown. These scripts remain historical artifacts; before reuse, a
new consumer must use complete failure accounting. The separate
[extraction helper](../../extraction-accounting/0.1.0/README.md) now records
expected, processed, absent and failed inputs and blocks incomplete consumption.
It is not integrated into the historical model scripts and does not qualify
physical synchronization. No original cohort is silently repaired.

Broad product expansion remains stopped under the
[research stopping point](../../../docs/RESEARCH_STOP_POINT_2026-09-21.md).
A genuine chronological revision, accountable decision criterion, qualified
adjudication and complete measured conventional-versus-Reiyah workflow costs
are still required. This correction establishes no competitive advantage.
