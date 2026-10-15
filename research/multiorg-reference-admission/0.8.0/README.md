# The complete four-image reference comparison

Document ID: `reiyah.multiorg.cohort-completion`. Version: `0.8.0`.
Lifecycle status: `exploratory`. 15 October 2026.

The detector preference survives allowing a different recorded reference
procedure for each image. The frozen contrast found **no observed
reference-composition fragility**.

All four selected image pairs and all twelve reference cases are now complete.
Two earlier pairs were rechecked and reused without inference; the two remaining
images completed 624 new forwards. Their 10,920 retained arrays passed the
unchanged numerical checker and qualified resource consumer. The prior failures
remain visible in [0.6.0](../0.6.0/README.md) and [0.7.0](../0.7.0/README.md).

The table reports `(FP + FN)_Faster - (FP + FN)_YOLO`. Positive values favor
YOLO under this particular equal-cost loss; they do not mean better recall.
Both arms use the same complete outputs, corrections and reference information.

| Image | t0 | t1_A | t1_B |
| --- | ---: | ---: | ---: |
| Plate 4 / image 7 | 78 | 138 | 120 |
| Plate 23 / image 0 | 134 | 206 | 110 |
| Normal Plate 31 / image 6 | 143 | 215 | 141 |
| Plate 23 / image 1 | 149 | 245 | 155 |


With equal image weights, one procedure shared across all images gives
**G = [126, 201]**, `prefer_b`. Allowing imagewise procedure choices gives
**P = [119.5, 201]**, `prefer_b`. Here A is the exact corrected Faster
observation variant and B is the released YOLO variant. Zero boundaries remain
unresolved. The native engine, competent conventional census and separate
Edmonds–Karp checker agree in all twelve cases.

This completes the original fixed question. It establishes no complete-work
advantage over conventional evaluation, general detector superiority or physical
truth. The images are microscopy data; no automotive or human-readiness claim
follows. The three annotation procedures come from two experts and shared initial
pseudolabels, and the original reference informed checkpoint selection. The
imagewise family is a declared stress test, not an observed workflow.

## Execution and verification

The new owner changed owned input paths and explicitly bound a mixed composition
of historical and new complete receipts. Matching source changes are limited to
version metadata and the new contract digest. Numerical algorithms, selected
images, model bytes, thresholds, NMS, IoU, unit loss and native limits are
unchanged. [Preservation checks](NUMERICAL_PRESERVATION.json) record that boundary.
[Recorded corrections](packaging-notes.json) retain an inherited plan-prose count
and a documentation-only packaging-check error; neither changed execution or
the frozen scientific question.

Fresh capacity windows covered the full remaining retention allowance above the
4 GiB reserve and 3 GiB margin. Both attempts passed without cleanup, downloads,
retries or stitched partial files. Each stayed within the 600-second/3-GiB sampled
worker limits. Available storage remains shared; sampled observations do not
reserve capacity or explain the previous owner's sudden drop.

There are 64 matching controls, eight harmless launcher controls and four new
budget-boundary controls. Both historical pairs were numerically rechecked,
including their 10,920 arrays. Inference runtime auditing covers 17 distributions
and 5,926 hashed entries; matching auditing covers five distributions and 134
hashed entries. Explicit unhashed exclusions, system libraries and independent
supply-chain verification remain outside those checks. [Verification](verification.json)
and [accounting](result.json) distinguish actual execution from retained history.

## Reproduce the authored qualification

From this repository root with the existing JSON-schema dependencies:

```sh
python -B research/multiorg-reference-admission/0.8.0/matching/test_matching.py --repository . --output /absolute/fresh/matching-controls.json
python -B research/multiorg-reference-admission/0.8.0/matching/test_resource_matching.py --repository . --output /absolute/fresh/resource-controls.json
python -B research/multiorg-reference-admission/0.8.0/consumer-review/test_budget.py
```

Use fresh output paths. These authored tests do not rerun the empirical study.
Raw model, image, annotation and inference payloads remain private under their
original custody. The public matching [producer](matching/match_analysis.py) and
[checker](matching/check_matching.py) accept exact bound source packets. Their
[contract](matching/contract.json), [aggregate result](matching-result.json),
[checked result](matching-check.json) and [provenance](provenance.json) identify
this calculation. The retained inference launcher is source evidence for a
closed owner, not permission to relaunch it.

Close this exposed cohort. Further value work needs a fresh consequential
decision, a justified observation process and complete measured costs against
the strongest applicable conventional method. Do not tune thresholds, replace
images or broaden this cohort to manufacture a positive contrast. Preserve the
full HARBOR mission; Gate A remains operator-unaccepted.
