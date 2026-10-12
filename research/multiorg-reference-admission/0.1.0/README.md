# Repeated references: a complete annotation audit

Study ID: `reiyah.multiorg.reference-admission`, version `0.1.0`.
12 October 2026. Completed source-specific structural qualification.

**All 165 reference files were acquired and checked. None of the 55 images fits
the first protocol's direct, source-qualified union representation.** The
smallest union contains 135 objects; the current native cap is 128. This is an
encoding limitation, not a defect in MultiOrg or proof that the source cannot
be evaluated by another exact representation.

| Recorded reference procedure | Verified boxes | Images exceeding 128 boxes |
| --- | ---: | ---: |
| Initial `t0` procedure, expert A or B | 7,523 | 27 |
| Repeated `t1_A` procedure | 4,729 | 13 |
| Repeated `t1_B` procedure | 4,956 | 11 |
| All three source-qualified sets | 17,208 | 55 |

The [result](result.json) preserves every image and all three counts. Every
annotation is a finite, nondegenerate, axis-aligned rectangle; no negative
coordinates were found. These checks do not establish image bounds or physical
correctness. No object was merged, cropped, dropped or repaired.

## What was frozen and what changed

The [protocol](protocol.json) and its source inventory were frozen before raw
annotation acquisition. It required a complete census, retained source identity
for each box, and selected pilot images by a fixed hash order only if the
source-qualified union fit the existing object cap. Zero images qualified, so
**this protocol admitted no image or model inference**.

The first download pass returned 120 valid payloads followed by 45 HTTP 404
responses. A later request for the same failed path succeeded. A prospective
transport-budget amendment permitted retrying the remaining failed paths, with
lower concurrency. All 165 payloads then matched the listed lengths. The 45
original failures and incomplete-census result remain retained. A transient
transport issue is supported; its server-side cause is not established.

The annotation bytes total 2,710,742. A separately authored checker rebuilt the
55-image/165-file roster from the original listing responses and verified exact
geometry, source-qualified identity hashes, counts and selection. Its first
complete comparison rejected a report-shape mismatch; the original checker and
failure remain retained. The correction reconstructs the extra declared fields
and preserves strict equality. This is one assisted investigation with separate
implementations, not independent scientific replication.

## The exact alternative

Twenty-eight images have at most 128 objects in **each individual procedure**.
For an additive image loss with no cross-image matching, the procedures can be
checked separately and combined exactly. A
[separate version 0.2.0 pilot](../0.2.0/README.md) was frozen after these counts,
before images, weights or predictions. The original refusal remains unchanged.

For detector difference `d(i,r) = loss_A(i,r) − loss_B(i,r)`, the whole-procedure
interval is the minimum and maximum of the three procedure totals. The enlarged
imagewise interval sums the per-image minima and maxima. Divide both intervals
by the number of evaluated images to obtain mean loss differences. The first interval is
contained in the second. A resolved preference may remain resolved or become
unresolved; it cannot switch directly to the opposite resolved preference.

This composition uses ordinary exact matching and arithmetic. It is not a novel
statistical estimator, a monolithic native certificate, or evidence of reduced
human review work. [The methods decision](../../../docs/research-decisions/owned-reference-trial-2026-10-12.md)
explains why a complete conventional comparison is the appropriate baseline.

## Reproduction and evidence

The source is [MultiOrg](https://arxiv.org/html/2410.14612v2), Kaggle dataset
[`christinabukas/mutliorg`](https://www.kaggle.com/datasets/christinabukas/mutliorg),
platform version 6, internal prefix `MultiOrg_v2/test/`. The full platform bundle
was not enumerated or downloaded. The complete current-prefix test roster was
reconstructed from the retained listing pages and cross-checked against the
paper's 55-image cohort.

Acquire the exact annotation paths in [source-manifest.json](source-manifest.json)
from that version, retaining their recorded bytes under a private directory's
`raw/` prefix. No images are required for this structural audit. Then run:

```sh
python3 -B research/multiorg-reference-admission/0.1.0/audit.py \
  --manifest research/multiorg-reference-admission/0.1.0/source-manifest.json \
  --manifest-sha256 937b74145d113c9823a7c497dbedc018808b8f9cde7231c1765d053d9ec52cdb \
  --sources /absolute/path/to/private/annotations \
  --output /absolute/path/to/new-audit-result.json
python3 -B research/multiorg-reference-admission/0.1.0/tests.py
```

The separately authored [checker](check_annotations.py) additionally consumes the five
original listing responses. [Verification](verification.json),
[source descriptors](sources.json), [provenance](provenance.json) and
[terms](NOTICE.md) distinguish retained private payloads, public derived counts,
authored code, failure records and scientific limits.

Three procedures are not three independent raters. Both experts began with
pseudolabels, one changed input equipment between rounds, and `t0` informed
checkpoint selection. This study does not authenticate physical truth, demonstrate
automotive transfer, reproduce the paper's benchmark scores, or establish a
Reiyah decision or work advantage. Gate A remains operator-unaccepted.
