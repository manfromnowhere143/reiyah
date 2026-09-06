# Result V: the deployed monitor - a coupling-corrected risk estimator from outputs alone

Document ID: `reiyah.result-v-deployed-monitor`

Version: `0.1.0`

Lifecycle status: `proposed`

## From a study to an instrument

The program measured that redundant channels fail together, and that agreement is therefore an
over-trusted signal. This is the instrument that follows: a monitor that reads only the channels'
outputs on an item, with no ground truth, and returns a calibrated probability that the ensemble is
wrong, having learned the coupling from a labeled calibration set. It is held to the standard a
deployed instrument must meet, not just demonstrated once.

Instance: a seven-model LLM jury on MMLU. The features are channel-agnostic - agreement fraction,
per-model confidence margins and their spread, the plurality voters' confidence, vote entropy, and
the number of distinct answers - so the same monitor form applies to any redundant channels whose
outputs carry a choice and a confidence, including two sensors or a human and a machine.

## The standard it is held to, and meets

Calibrated on a training split (8,362 items), evaluated on a held-out test split (5,575 items), with
no test label seen at fit time. Compared against the naive baseline that is the ensemble's own
implicit assumption: risk equals one minus the agreement fraction.

| estimator | ROC AUC (higher) | Brier (lower) | ECE (lower) |
|---|---|---|---|
| naive: risk = 1 - agreement | 0.719 | 0.204 | 0.045 |
| **Reiyah monitor: coupling-aware, calibrated** | **0.845** | **0.155** | **0.015** |

The monitor beats the naive assumption on discrimination, on the Brier score, and is three times
better calibrated.

## The blind spot it fixes

The naive ensemble treats unanimity as certainty. On the held-out unanimous items, that is a
dangerous assumption, and the monitor corrects it:

| held-out unanimous items (326 of 5,575) | value |
|---|---|
| actual wrong rate | 9.5% |
| naive risk (1 - agreement) | 0.0% |
| **Reiyah monitor risk** | **11.6%** |

Where a diverse seven-model jury is unanimous, it is still wrong about one time in ten, and the
naive assumption assigns that case zero risk. The monitor, having learned the coupling from
calibration data, assigns it the risk it actually carries. That is the coupled-failure blind spot,
detected from outputs alone.

## Calibration on held-out data

Predicted risk against the realized wrong rate, in five bands of the held-out set:

| monitor risk band | predicted | actual | n |
|---|---|---|---|
| 1 | 1.6% | 3.0% | 1,115 |
| 2 | 12.1% | 12.0% | 1,115 |
| 3 | 38.5% | 39.7% | 1,115 |
| 4 | 62.7% | 61.6% | 1,115 |
| 5 | 77.4% | 75.9% | 1,115 |

The predicted risk tracks the realized failure rate across the whole range. The monitor is not only
discriminative, it is honest about its own probabilities.

## What this completes

The program's arc is now closed end to end:

- **measure** (the automation program, the human channel, the LLM jury): redundancy across similar
  kinds fails together;
- **correct** (Result S): the required validation evidence, understated by the coupling;
- **generalize** (Result T): one law across sensors, humans, and AI;
- **predict** (Result U): agreement is an over-trusted signal, quantified;
- **monitor** (this result): a calibrated, output-only risk estimator that corrects the
  over-confidence, validated out of sample.

This is the instrument the architecture pointed at: not a study of joint failure after the fact, but
a live estimate of it, ground-truth-free, that a system reads from its own channels.

## Non-claims

A demonstration instrument on public MMLU outputs, retained as `proposed`. The features are
channel-agnostic, but this is calibrated and evaluated on one benchmark and one jury; it is not a
deployed product, not a safety determination, and not a driving result. The naive baseline is the
ensemble's own implicit assumption, shown for contrast. No released `1.2` byte is involved.
