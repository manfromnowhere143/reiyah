# Consistency and reference agreement favor different saved runs

Document ID: `reiyah.motion-consistency-audit`. Version: `0.1.0`.
Lifecycle status: `exploratory`. Date: 11 October 2026.

**On two released EgoDyn-Bench answer files, the run labeled as using trajectory
information has higher reference agreement but lower physics-consistency score.**
Both files reproduce their published metric records exactly. A separate
implementation reconstructs all 28,000 answers, every per-clip rule trace and
both complete metric reports.

This is a saved-file audit of the Qwen3-VL-8B vision-only and trajectory-labeled
runs. It establishes a difference between two evaluation targets. It does not
establish a causal trajectory effect, physical truth, a defect in the benchmark,
or a performance advantage for Reiyah.

## What the two metrics say

Each file covers the same 1,000 clips and 14 questions per clip, with 500 clips
from nuScenes and 500 from CARLA. Every expected pair appears exactly once;
all embedded reference labels agree with the separate released clip roster.
All 28,000 saved answer strings normalize directly to declared labels.

| Quantity | Vision file | Trajectory file |
| --- | ---: | ---: |
| Correct relative to released oracle, out of 14,000 answers | 6,969 | 8,905 |
| Native answer accuracy | 49.78% | 63.61% |
| Native balanced accuracy | 38.86% | 54.69% |
| Native macro F1 | 0.3301 | 0.5270 |
| Native weighted physics consistency, WPCR | 97.87% | 89.66% |
| Unparsed answers | 0 | 0 |
| Clips with all 14 answers matching the oracle | 9 | 87 |

Accuracy and WPCR have different units and denominators. Accuracy counts
individual answers. WPCR derives from clips with at least one triggered rule,
then multiplies by the fraction of rule types triggered anywhere in the run.
All ten rule types trigger in each file, so that weight is one here.
The different scores must not be treated as two accuracy estimates.

The exact paired answer table preserves regressions as well as improvements:

| Vision answer versus trajectory answer | Opportunities |
| --- | ---: |
| Both agree with the oracle | 6,338 |
| Vision agrees, trajectory disagrees | 631 |
| Vision disagrees, trajectory agrees | 2,567 |
| Both disagree | 4,464 |
| Total | 14,000 |

The net agreement difference is 1,936/14,000, about 13.83 percentage points.
The published WPCR moves in the opposite direction by 8.21 percentage points.
These are descriptive paired records, not independent trials or a causal
estimate. The trajectory-labeled run receives additional information; it is
not an equal-information competitor to the vision file or to Reiyah.

## What a passed consistency check establishes

The [frozen protocol](protocol.json) asks whether a fully parsed clip with no
rule violations nevertheless disagrees with the released oracle on a question
that occurs in the rules. The rules involve nine of the fourteen questions.
This restriction avoids attributing errors on unrelated questions to the check.

| Clip-level quantity | Vision file | Trajectory file |
| --- | ---: | ---: |
| No rule applicable | 154 | 91 |
| At least one rule violated | 18 | 94 |
| At least one rule applicable, none violated | 828 | 815 |
| Among that last group: disagreement on a rule-involved question | **791/828 (95.53%)** | **686/815 (84.17%)** |
| Among that last group: disagreement on any of the 14 questions | 819/828 | 728/815 |

Clips without an applicable rule remain a separate state. They are not counted
as successful consistency checks. Every clip in these two files is fully parsed;
the implementation keeps unparsed responses separate from incorrect ones and
reports agreement bounds if responses are unavailable.

The primary finding appears in both source strata:

| Source | Vision: reference disagreement among rule-consistent clips | Trajectory: same quantity |
| --- | ---: | ---: |
| nuScenes | 403/406 | 387/416 |
| CARLA | 388/422 | 299/399 |

These denominators condition on each run's rule applicability and outputs.
They are not population error rates, driving-risk estimates or confidence
intervals. Every source and all fourteen question-level count summaries remain
in the [result](result.json).

The released oracle itself violates none of the rules: 966 clips have at least
one applicable rule and 34 have none. This checks consistency of this roster
with the rules, not the physical validity of its telemetry or thresholds.

The reason for the distinction is visible in the scorer. Its implication rules
compare one predicted answer with another; they do not compare those answers
with the oracle. Compatible answers can therefore disagree with the reference.
The benchmark already reports both accuracy and consistency. We are measuring
the limits of using the latter as decision evidence, not claiming the authors
advertise it as a safety guarantee.

## Why this is the next scientific step

The [EgoDyn-Bench paper](https://arxiv.org/abs/2604.22851v2), v2 dated 7 July 2026
and described by its authors as accepted at ECCV 2026, studies grounding motion
judgments in visual and trajectory information. Its released answer files make
this particular reproduction possible without model inference. The retained
abstract supplies research context; the arithmetic here derives from the exact
code and records listed in [input bindings](inputs.json).

The official [AlpaSim 2026 challenge](https://opendrivelab.com/alpasim2026),
inspected on 11 October, illustrates the complementary need to evaluate
successive actions and their simulated consequences. No AlpaSim experiment,
challenge participation or simulator validity claim is made here. A motion-VQA
result is not a closed-loop driving result.

For HARBOR, this audit supports preserving distinct evidence for internal
coherence, agreement with a declared measurement reference, and downstream
outcomes. A decision contract must specify which property it requires.
A higher coherence score cannot silently replace the reference-agreement
obligation. The new code is an offline research auditor, not an integrated
runtime or a demonstrated product advantage.

## Reproduction and checks

GitHub source: `TUM-AVS/EgoDyn-Bench` at
`a0c9c01a424cbeb5aa5471a6156354f21111436d` (commit dated 26 June 2026).
Dataset: `fnc1901/EgoDyn-Bench` at
`70032aa156d06c5bff24e0f1a4532973ca09ee0d` (updated 8 July 2026).
The clip roster has the same Git blob identity in both distributions.
The exact two answer files were selected and the protocol frozen before their
payloads or pair-specific metrics were inspected. The paper's general claim
of trajectory benefits was known; this is exploratory, not blinded research.

The producer executes the complete unchanged, digest-checked native parser and
metrics modules from private source custody. Its strict gate joins each answer
to the separate clip roster before scoring. All 234 recomputed metric fields
per run match the corresponding released result, including confusion matrices.
Extra stored inference-timing fields are not reproduced.

The checker imports neither native implementation nor producer. It reads the
declared rules as data, reconstructs implications with truth tables, rebuilds
confusion counts and metrics with rational arithmetic, and compares every
private clip row and public aggregate. All saved answers here are canonical
labels; it rejects unsupported free-text cases rather than asserting a general
independent check of the native parser's fallback heuristics.

Twenty-four negative controls reject missing, duplicate and unknown membership,
reference/category substitutions, malformed fields, forged witnesses and scores,
numeric type coercion, duplicate JSON properties and nonfinite values. Six
state controls preserve unknown responses and distinguish untriggered rules
from satisfied implications. Two final runs have identical public results,
private rows and native metric bytes. See [controls](controls.json),
[verification](verification.json) and [provenance](provenance.json).
These are checks by one investigator, not independent scientific review.

Use Python 3.10 or newer with [PyYAML 6.0.3](requirements.txt); the retained
execution used Python 3.14.2. No package installation or model execution was
needed. Obtain the eight named files at the exact URLs in [inputs.json](inputs.json)
under their terms and place them in a private directory using its local filenames.
Keep the source and identifier-bearing results outside public Git:

```sh
reiyah_sources=/absolute/path/to/private/source-files
reiyah_run=$(mktemp -d)/run
reiyah_study=research/motion-consistency-audit/0.1.0
python3 -B "$reiyah_study/reproduce.py" \
  --sources "$reiyah_sources" --output "$reiyah_run" \
  --expected "$reiyah_study/result.json"
python3 -B "$reiyah_study/verify.py" \
  --sources "$reiyah_sources" --run "$reiyah_run"
python3 -B "$reiyah_study/check_controls.py" \
  --sources "$reiyah_sources" --run "$reiyah_run"
```

The retained executions denied network access before starting Python. Public
scripts perform no network retrieval. Source digests, access records, scope and
rights are retained in [sources.json](sources.json). Third-party source code,
answer payloads, clip identities, telemetry, images and weights are not published.
The code license is Apache-2.0; the dataset card applies CC BY-NC-SA 4.0 to its
nuScenes-derived portion and calls its CARLA portion permissive without naming
an exact license there. No commercial-use entitlement is inferred.

Credit for the benchmark and released records belongs to Finn Rasmus Schäfer,
Yuan Gao, Dingrui Wang, Thomas Stauner, Stephan Günnemann, Mattia Piccinini,
Sebastian Schmidt and Johannes Betz. The saved files do not authenticate historical
weights, full prompts, inference settings or any earlier output processing.
The audit does not rerun the models or validate raw-sensor labels.

This fixed paired audit is complete. No 49-model sweep, tuning or larger compute
campaign follows automatically. A product-value claim still requires a useful
engineering decision and complete measured work against an equally equipped
conventional process. Gate A remains operator-unaccepted.
