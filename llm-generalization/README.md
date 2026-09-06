# LLM generalization

The camera-lidar and human-channel work measured the independence assumption in driving. This
thread shows the estimand is not about driving at all: it applies to any two channels a system
calls independent. The largest unmeasured such assumption in AI is the LLM jury, self-consistency,
majority vote, and multi-model cross-checking, all of which assume the models err independently.

## Source

Public v1 Open LLM Leaderboard per-question results (`open-llm-leaderboard-old` on Hugging Face),
MMLU 5-shot, per-question correctness, joined across models by a hash of the example. Same method as
the sensor work: public per-item predictions and the Definition 32 coefficient. No LLM inference.
Result V fits and calibrates a logistic-regression monitor on those outputs, the only model fitting
in this thread, and reports it on a held-out split.

Reproduce: `bdda-venv/bin/python llm-generalization/tools/result_t_llm_independence.py` (downloads
the per-question parquet files from Hugging Face).

## Result

- [`RESULT_T_LLM_INDEPENDENCE.md`](RESULT_T_LLM_INDEPENDENCE.md) - seven models, five families,
  13,937 MMLU questions. LLM juries fail together (marginal c = 1.32, every pair above 1); the
  same-kind-vs-cross-kind law replicates (same family 1.52 vs cross family 1.29); the coupling
  survives difficulty conditioning (conditional c = 1.10); and a seven-model jury has the effective
  diversity of 3.6 independent models. The independence assumption is a load-bearing fiction
  wherever redundancy is claimed, in sensors, in the human, and in AI juries alike.
- [`RESULT_U_AGREEMENT_RELIABILITY.md`](RESULT_U_AGREEMENT_RELIABILITY.md) - from measuring joint
  failure to predicting it from outputs alone. When two models agree, they are correct only 64.8% of
  the time (both wrong together 35% of the time), and when all seven agree they are still wrong 10.4%
  of the time. Agreement is a systematically over-trusted signal, and the amount is measurable from
  the outputs with no ground truth, the seed of a live monitor.
- [`RESULT_V_DEPLOYED_MONITOR.md`](RESULT_V_DEPLOYED_MONITOR.md) - the instrument itself. A
  coupling-aware risk estimator, calibrated on a training split and evaluated on a held-out test
  split from outputs alone, beats the naive agreement heuristic on every metric (AUC 0.845 vs 0.719,
  ECE 0.015 vs 0.045). On held-out unanimous items the naive ensemble assigns 0% risk while the true
  wrong rate is 9.5%; the monitor assigns 11.6%, catching the coupled-failure blind spot. Its
  features are channel-agnostic, so the same form applies to two sensors or a human and a machine.
- [`RESULT_W_SECOND_BENCHMARK.md`](RESULT_W_SECOND_BENCHMARK.md) - the red-team. The whole law
  replicates on ARC-Challenge, a different domain: marginal c 1.76 (same 1.87 > cross 1.73),
  conditional 1.05, a six-model jury with the effective diversity of 1.6, and unanimous-yet-wrong
  37% (against 10% on MMLU). On harder material the coupling sharpens. The findings are not an MMLU
  artifact.

## Discipline

Public data, descriptive, retained as `proposed`, the marginal coefficient includes shared question
difficulty (the conditional removes the measurable part), a generalization demonstration and not a
driving result. No released `1.2` byte involved.
