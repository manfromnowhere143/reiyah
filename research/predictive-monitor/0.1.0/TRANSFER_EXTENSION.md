# Collection-log separation declared before fitting

Document ID: `reiyah.predictive-monitor-log-extension.0.1.0`

Version: `0.1.0`

Lifecycle status: `exploratory`

This extension is retained before any real-data monitor fit, alongside the
[initial plan](PLAN.md). Scene separation does not imply separation of the
underlying collection drives. The same log can contribute multiple scenes.

Repeat the primary approximately one-second, original-cache comparison
(`joint_history` versus `marginal_history`) with **all scenes from a collection
log assigned to the same outer and inner fold**. Use the same five outer folds,
three inner folds, seeded mapping, three candidate models, feature definitions,
loss and controls. If fewer than five independent log IDs are available, mark
this extension unavailable rather than silently falling back to scene folds.

Selection still minimizes equal-scene loss; the split group changes to logs.
Retain the original scene-separated result regardless of its sign. Report
the number of logs shared across training/test folds in both analyses. The
extension has zero shared logs by construction; this is tested explicitly.

Add a log-clustered paired sensitivity interval, using the same 3,000 seeded
resamples, alongside the original scene interval. Its estimand is an equal-log
mean of per-frame losses. It is not numerically interchangeable with the
equal-scene estimand; report both denominators. Neither accounts for refitting
uncertainty or makes the data independent across locations or sensor setups.

An increment that disappears under log separation is evidence against robust
transfer of this rule. An increment that survives still requires a new detector,
geography and independently checked reference. No outcome of this experiment
establishes physical hazard prediction or actual one-second warning lead time.
