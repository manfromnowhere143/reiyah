# Concrete prediction packet checklist

Document ID: `reiyah.research.release-source-packet`

Version: `0.1.0`

Lifecycle status: `proposed`

This is a local acquisition checklist, not a message sent to a publisher or a
frozen experiment. Read the [source findings](README.md) and
[candidate records](candidates.json) first. Cached outputs are preferred; missing
inputs remain missing and never become successful empty detections.

## Next source actions

1. Inspect the linked public EdgeFirst sessions
   [v-e89](https://edgefirst.studio/public/validation/v-e89/details?mode=charts),
   [v-e93](https://edgefirst.studio/public/validation/v-e93/details?mode=charts) and
   [v-e9c](https://edgefirst.studio/public/validation/v-e9c/details?mode=charts).
   Record whether complete prediction files and their provenance are publicly
   available. Retain bytes and terms privately before admission. The current
   browser-availability failure establishes no access or authentication policy.
2. Seek corresponding per-image outputs for the three pinned RT-DETR candidates.
   Preserve the original R18 conversion, v2 rerun and v4 backbone distinctions.
   Do not download model binaries expecting them to contain per-image predictions.
3. If no cached packet qualifies, specify a small local export feasibility experiment
   with fixed candidate bytes, existing exposed development IDs, exact runtime and
   numerical settings, wall-time limits and all failures retained. Establish the
   applicable inference authority before execution. Do not silently turn this
   metadata inventory into a broad inference campaign.

## Minimum contents of a usable packet

| Required item | Why it changes admission |
|---|---|
| Model identity and chronology | Exact checkpoint bytes/digest and source commit, plus the publisher's relationship between versions; package tags and size variants are insufficient |
| Prediction file and terms | Retained bytes/digest, creator, run time, dataset use and prediction redistribution rights; publisher tables alone are insufficient |
| Complete image index | Every allocated image ID with source/dimension identity, processing status and explicit empty outputs; absent rows do not imply zero detections |
| Common comparison population | Same image identities and category mapping across candidates, with missing/failed images retained in the denominator and reported separately |
| Inference contract | Runtime/export version, numerical precision, resizing/letterboxing, coordinate mapping, score threshold, NMS or end-to-end mode, top-k/max detections, rounding and batch settings |
| Reference and exposure boundary | Reference version/digest, what has already been inspected, uncertain eligible corrections, reserved membership, and distinct observation versus outcome access |
| Decision and observation contract | Metric and strict decision threshold, allowed uncertainty, requested observation, returned precision/error, applicability and unresolved status |
| Cost and workflow evidence | Preparation, integration, review, repairs, observation, computation and verification costs; actual agreed rates or explicit unmeasured fields |

A packet may support a public development comparison without establishing real
customer revision economics. Keep those conclusions separate. Model predictions
provide the fixed competing outputs; they do not validate a reference correction
or make a reviewer's answer infallible. Do not inspect reserved corrections to choose
thresholds, uncertainty bounds, selectors or stopping rules. A later protocol must
freeze those choices and preserve every allocated case, including unresolved cases.
