# Evaluator population report to the upstream maintainer

Document ID: `reiyah.maintainer-report.evaluator-populations`

Version: `0.1.0`

Lifecycle status: `exploratory`

Posted by `manfromnowhere143` on 11 October 2026 at 09:18:35 UTC:
[upstream issue #1](https://github.com/JonathanKlees/Uncertainty-aware-Object-Detection/issues/1).
The operator explicitly authorized this prepared report in reply to the posting
request. All-state preflight found no existing issues, and upstream main still
matched the tested commit. A public GET confirmed the exact title, body and
author after posting. The issue was open with zero comments at that read.
The [action receipt](../../evidence/upstream-evaluator-report-2026-10-11.json)
is publisher-authored; it is not independent transport or scientific review.

This requests the intended averaging population and original run coverage,
plus a shareable original comparison packet. No maintainer response, upstream
correction or impact on published results is established. The two authored
controls remain separate from an empirical value comparison. No new experiment
was run for this contact. Retain both conventional corrections in any future
comparison.

## Next evidence decision

When a response arrives, inspect it in this existing thread before replying or
opening another issue. Treat the response as a source to verify. A useful
packet needs complete paired outputs, expected image membership, explicit
successful empty versus missing/failed run status, applicable reference bytes,
and the original evaluator configuration. Obtain access and redistribution
terms before accepting payloads. Freeze the empirical question and comparator
before running the original and corrected calculations. Preserve unavailable
fields explicitly; do not infer them from absent detection rows.

A packet may establish scoring impact without establishing a product advantage.
The latter still needs a consequential decision, a qualified resolution action
and complete measured work. A reply alone does not admit a case. Do not repeat
the closed local audit, tune either exposed pair or create an unattended poll.

## Submitted body

Thank you for making the evaluation implementation available. At commit
f793379ad7a9760f71c18ba57b7ed71fa76a5e6c, I reproduced two population-accounting
behaviors in evaluate_soft.py using small constructed examples.

1. **Successful empty detection images disappear from the AUSRC reference
   denominator.** A two-image example with one perfect detection and one empty
   output scores 1 with a denominator of 1. Preserving both references gives
   51/101. Another arm detecting both objects with class probability 0.8 stays
   at 0.8, so the comparison reverses.
2. **Auxiliary means depend on chunk size and image order.** process_chunk
   returns the last image's metric arrays; the outer evaluator averages those
   arrays. With two matched detections having TV distances 0 and 1/2, chunk size
   1 reports the expected mean 1/4. Chunk size 2 reports 1/2, or 0 when the image
   order is reversed. A comparison arm with mean 3/8 therefore changes order.

The first research wrapper adds empty prediction tensors for annotated images
with explicit successful empty outputs. The second collects every per-image
auxiliary array before the existing global mean. The aggregation checks cover
90 execution configurations, including unequal detection counts, matched versus
all predictions, empty populations and area filtering. A separate scalar
calculation verifies the means, and AUSRC is unchanged by the second wrapper.

Reproducers, authored fixes, protocols and complete control results:

- [Empty-output scoring control](https://github.com/manfromnowhere143/reiyah/tree/7a3fe332369dc463c2322fbd4558854acb944155/research/empty-output-score-control/0.1.0)
- [Auxiliary aggregation control](https://github.com/manfromnowhere143/reiyah/tree/a810dc0f448c0bd3ed91dacf55f84df0aaa73e93/research/metric-aggregation-control/0.1.0)

These execute the exact scoring function bodies with real CPU tensors; they
are not full CLI replications. I have not established whether either behavior
affects your published results, and no upstream source payload is redistributed.

Are the auxiliary means intended to pool all eligible detections, and does the
original prediction inventory distinguish successful empty outputs from missing
or failed runs? If a small shareable original comparison packet is available,
I would like to measure actual impact before making any empirical claim.
