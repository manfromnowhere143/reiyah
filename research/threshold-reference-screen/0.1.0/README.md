# Reference policies can reverse a threshold choice

Document ID: `reiyah.threshold-reference-screen`. Version: `0.1.0`.
Status: exploratory retrospective study. Date: 11 October 2026.

**The preferred confidence threshold reverses between two released references.**
For one fixed prediction file covering all 5,000 COCO validation images,
threshold 0.50 has lower equal-weight false-positive/false-negative loss under
COCO 2017. Threshold 0.25 has lower loss under COCO-ReM. Conventional evaluation
and integer bounds establish this result; no Reiyah advantage is demonstrated.

A follow-up also bounds the opportunity for choosing which image policies to
resolve. A conventional order needs 204 simulated disclosures. An ideal method
with advance knowledge needs at least 148, limiting the possible reduction in
disclosure count to **204/148 = 51/37, about 1.38×**, in that declared model.
That is at most about 27.5% fewer disclosures. This is not measured human work
or a general lower bound on evaluation effort.

## The comparison packet

The source is the author-released `data/predictions_yolov10x.json` member of the
archive linked by Llerena and Jung's
[WACV 2025 paper](https://openaccess.thecvf.com/content/WACV2025/papers/Llerena_Noise-Aware_Evaluation_of_Object_Detectors_WACV_2025_paper.pdf)
and [official repository](https://github.com/Artcs1/Error-Aware/tree/6b299e2ac9bd0f3473df35a3f570f428c92ac224).
It contains 1,500,000 rows: 300 for each of the exact 5,000 reference image IDs.
Its 80 category IDs match the references. This is saved-file coverage, not
authenticated model execution. The exact checkpoint and inference configuration
remain unverified; the comparison is bound to file bytes.

Two deterministic configurations retain scores at least 0.25 (A) or 0.50 (B).
Both retain every image opportunity. A has 31,602 prediction rows and 54 derived
empty images; B has 22,208 rows and 102 derived empty images. These empty outputs
are calculated from a present raw record, so they are distinguishable from
unobserved or failed historical inference.

The raw file includes 466 zero-size boxes, all at scores at most 0.00048. Our
initial positive-extent gate rejected that raw file, and the rejection remains
retained. Both specified output configurations have positive extents. The
thresholds are declared transformations; no source row was repaired or clipped.
A separate native COCO diagnostic kept every raw row, including all 466, and
computed 54.433798 bbox AP points. All thirteen metrics in the paper's Table 2
YOLOv10 X row match within its printed rounding. This supports numerical
consistency; it does not authenticate the inference run or reproduce the paper's
noise-adjusted evaluator. See [source qualification](source-qualification.json).

The references are the exact original COCO 2017 and released COCO-ReM files in
[inputs.json](inputs.json). Their image IDs, dimensions and category IDs/names
match. The COCO-ReM work is by Singh, Yadav, Jain, Shi, Johnson and Desai,
[ECCV 2024](https://github.com/kdexd/coco-rem). Neither reference is established
here as physical truth. Both were already exposed during prior work. The
previous R50/R101 prediction pair is not reused or tuned.

## Metric and observed reversal

Use native COCO score-greedy, class-aware matching at IoU 0.50, the standard
crowd/ignore rules, all object areas, and at most 100 detections per image and
category. Preserve native stable score ordering. This is not Reiyah's
maximum-cardinality matcher and these counts are not AP.

```text
L = FP + FN
Delta = L(A: threshold 0.25) - L(B: threshold 0.50)
Positive Delta favors B; negative Delta favors A.
```

| Reference | A: FP | A: FN | A: loss | B: FP | B: FN | B: loss | Delta |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| COCO 2017 | 6,545 | 12,566 | 19,111 | 2,223 | 16,740 | 18,963 | +148 |
| COCO-ReM | 6,235 | 16,005 | 22,240 | 2,080 | 20,448 | 22,528 | −288 |

Equal error weights are a research choice. They are not an owner-approved
driving loss or a recommendation for a production threshold. This is one fixed
comparison, with no threshold or cost-weight sweep. The [primary protocol](protocol.json)
was frozen before these calculations, after the source and one-model AP were
observed. It is exploratory, not blinded or preregistered.

## Exact conditional reference bounds

For each image, allow its entire annotation set to be either the original set
or the revised set. Choices are independent in the declared family. This
includes hypothetical mixtures of two annotation policies, not only the two
released datasets; it is not an empirical model of physical uncertainty.

Let `d_i(original)` and `d_i(revised)` be the two per-image differences. Then:

```text
lower = sum_i min(d_i(original), d_i(revised)) = -572
upper = sum_i max(d_i(original), d_i(revised)) = +432
```

Each bound is attainable within this family by choosing its minimizing or
maximizing policy separately for every image. The bounds are exact integer
sums of native evaluator counts; this is not exact rational geometry or a
statistical confidence interval. Both choices remain possible. Only 434 images
have a reference-sensitive difference; the other 4,566 need no policy disclosure
to settle this comparison. Conventional methods get the same cancellation.

## Conventional process and optimistic ceiling

The primary protocol specified a hindsight lower bound in the completed world
where every image uses COCO-ReM. A query hypothetically discloses one image's
policy at unit cost. No human annotation action or physical adjudication is
claimed to implement that query.

To certify A, the initial upper endpoint of 432 must fall strictly below zero.
The 147 largest realized endpoint reductions sum to 431; the 148 largest sum to
433. Therefore even a method that knows all answers in advance needs at least
148 such disclosures. The oracle may use advance knowledge to choose queries;
its final certificate may use only disclosed answers and the declared family,
and must remain valid for every compatible completion. This is an oracle bound,
not a deployable selector. If a workflow chooses one policy globally instead,
it has a different observation model and this disclosure bound does not apply.

After the primary result, a separately [frozen exploratory follow-up](conventional-protocol.json)
tested the ordinary largest-potential-change policy: descending interval width,
ties by image ID. Ordering uses known bounds, never the realized answer. It
stops after 204 disclosures, moving from `[-423, +1]` to `[-423, -1]` on the last
one. All 434 sensitive images would also suffice, but that is a weaker baseline.

The resulting 1.38× ceiling rules out both twofold and threefold reductions in
**this simulated disclosure count** relative to that conventional policy.
It does not rule out every possible improvement in CPU time or complete work.
Complete review, integration and engineering costs remain unmeasured. Because
the original and revised files are already available, this replay purchases no
new evidence at all. Do not present its hypothetical disclosures as actual
review savings. The [follow-up result](conventional-result.json) preserves the
strict stopping boundary and oracle minimality counts.

## Verification and reproduction

The producer evaluates the full score file once per reference and counts the
two score prefixes. A separate verifier instead filters the input first and
runs all four native evaluations afresh. All **20,000 per-image count records**,
5,000 sharp endpoint pairs, witness choices, aggregate totals and reported
derived empty counts agree. Four numeric-type, value and membership rejection
controls pass. Both implementations use the same pinned native evaluator; this
is not independent scientific replication. [Verification](verification.json)
and [provenance](provenance.json) distinguish measurements and scope.

Use Python 3.10 or newer with the pinned [requirements](requirements.txt). The
retained run uses Python 3.13.5 on arm64 macOS. Exact evaluator Python source
hashes are checked; the native binary identity is recorded. Cross-platform
numerical replication has not been performed.

Obtain the three [input files](inputs.json) outside Git under their applicable
terms. For the prediction file, download the author-linked archive and extract
only `data/predictions_yolov10x.json`. A complete matching cached copy may be
reused. No images, weights or model inference are needed. The original reference
reproduction guide provides the [COCO and COCO-ReM routes](../../reference-revision/0.1.0/README.md#reproduce-on-cpu).

```sh
python3 -m venv /tmp/reiyah-threshold-env
/tmp/reiyah-threshold-env/bin/python -m pip install \
  -r research/threshold-reference-screen/0.1.0/requirements.txt

reiyah_study=research/threshold-reference-screen/0.1.0
reiyah_inputs=/absolute/path/to/inputs
reiyah_run=/absolute/path/to/new-run

/tmp/reiyah-threshold-env/bin/python -B "$reiyah_study/reproduce.py" \
  --predictions "$reiyah_inputs/predictions_yolov10x.json" \
  --original "$reiyah_inputs/instances_val2017.json" \
  --revised "$reiyah_inputs/instances_valrem.json" --output "$reiyah_run"
/tmp/reiyah-threshold-env/bin/python -B "$reiyah_study/verify.py" \
  --predictions "$reiyah_inputs/predictions_yolov10x.json" \
  --original "$reiyah_inputs/instances_val2017.json" \
  --revised "$reiyah_inputs/instances_valrem.json" --run "$reiyah_run"
/tmp/reiyah-threshold-env/bin/python -B "$reiyah_study/conventional_screen.py" \
  --run "$reiyah_run"
cmp "$reiyah_run/result.json" "$reiyah_study/result.json"
cmp "$reiyah_run/conventional-result.json" "$reiyah_study/conventional-result.json"
```

The output directory must be new. Keep the generated image-level counts and
witnesses outside public Git. Only authored code and aggregate results are
distributed here; third-party inputs are not relicensed or bundled.

## Research decision

A reproducible reference-sensitive configuration case now exists. Two
deterministic operating points from one complete raw file qualify this narrower
retrospective question. They do not supply a second independent model run or
resolve the original inference-provenance gap. A prospective detector-value
packet still requires an actual consequential decision, a qualified
reference-resolution action and complete cost records.

Do not build or tune a Reiyah selector on this exposed case. Standard methods
already leave little disclosure-count headroom in its declared simulation.
The broader HARBOR mission remains open, and broad product investment remains
stopped pending demonstrated value. No state-of-the-art, safety, novelty,
commercial-value or halved-complete-work claim follows from this result.
