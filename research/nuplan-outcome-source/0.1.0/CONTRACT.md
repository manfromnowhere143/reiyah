# Record obligations before a sampled outcome can be interpreted

Document ID: `reiyah.nuplan-outcome-source.contract`. Version: `0.1.0`.
Lifecycle status: `proposed`. 16 October 2026.

These are proposed admission requirements for a future simulator-only study.
They are not a new runtime, accepted protocol or permission to acquire trials.
The exact source and qualification limits are in [inputs.json](inputs.json) and
[qualification.json](qualification.json).

1. Bind the source commit, resolved configuration, planner identity, controller,
   observation mode, map version, metric dependencies and runtime libraries.
   Preserve the distinction between code version and actual run provenance.
2. Freeze every expected scenario/planner/log key, its inclusion rule, intended
   window and comparator before opening outcomes. Duplicate keys must be rejected;
   the inspected executor indexes reports by that key. Count absent and failed
   rows in the roster instead of dropping them from the denominator.
3. Retain scenario timestamps, actual history indices, iteration timestamps and
   ego timestamps. Check their units, ordering, identity, gaps and membership.
   For the selected normal path with `N≥2`, expected history is `0…N−2`, not all
   `N` scenario points. Prespecify the common observed window from that contract.
   A requested duration or nominal 10 Hz setting is insufficient.
4. Retain terminal reason, final executor status and traceback when present;
   account for synchronous errors and every metric/log callback future. A missing
   report, externally killed process or unavailable completion is unknown. A short
   log can end normally while failing the planned follow-up requirement.
5. Prove the requested metric was enabled and delivered for the exact run.
   Keep all first-track collision events, their sampled times and classifications
   separately from the at-fault subset and aggregate score. A score alone has no
   timestamp series and cannot attest complete monitoring.
6. State which contacts count, the first-track de-duplication rule, any map/geometry
   assumptions and the consequences of missing objects. A positive scalar score,
   no-at-fault flag and successful execution are three distinct observations.
7. Keep failed, invalid, missing, excluded and insufficient-follow-up cases
   explicit. A future censoring analysis must justify its assumptions; source
   truncation does not establish independent censoring or successful recovery.
8. Interpret a negative result only as no eligible sampled event in the admitted
   window. No continuous-contact guarantee, physical clock-error bound or human
   readiness label follows from this source contract.

| Observed state in a future record | Permitted interpretation |
| --- | --- |
| Complete expected history, enabled metric, final successful execution and no eligible sampled events | No eligible sampled event over the verified discrete window. |
| Eligible sampled collision with completed reporting | That source-defined event was observed, irrespective of the run-success flag. |
| Run success without metric/history receipts | Outcome monitoring remains unqualified. |
| Failed run or metric/log callback | Execution failed; retain any verified observations separately from an unknown complete-window outcome. |
| Normal end with shortened/gapped source coverage | Complete for the available local sequence may still be insufficient for the planned common window. |
| Missing run or terminal receipt | Unknown completion and outcome; never encode zero collisions. |

The native control stage must test these distinctions before trial selection.
No empirical row currently satisfies or fails this contract because no trial
records were acquired in this audit. Population coverage remains unmeasured.
