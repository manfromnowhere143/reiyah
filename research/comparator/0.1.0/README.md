# Ordinary comparator

Version: `0.1.0`

Lifecycle status: `proposed`

One end to end comparison between this lane's instrument and a competent conventional analyst
holding the same evidence, on the Engine's actual additive decision. Written so the answer can
come out unfavourable, and in two of five measured dimensions it does.

| artifact | what it holds |
|---|---|
| `end-to-end.json` | eight selected cases with input digests, the declared decision, the conventional result, a witness or a named obstruction, the observation list, and six measured costs. Plus 1400 synthetic conformance instances, each accepted by both checkers |
| `verification-cost.json` | checking a reported enclosure by certificate against an analyst rerunning a maximum matcher, on retained cases and at five synthetic scales |

Read [`docs/ORDINARY_COMPARATOR_2026-09-14.md`](../../../docs/ORDINARY_COMPARATOR_2026-09-14.md)
for the result and its limits.

## The short version

The verdict is a draw and this lane proved it a draw. The measurable difference is the list of
reading facts a validation lead is sent to settle: 56 disputed atoms across the eight cases
reduce to 7 certified atoms, and both ends of the list are checkable in linear time. Against
that, the certificate is slower than recomputation on every retained case and only overtakes it
between 30 and 90 detections, and this lane costs four modules to integrate where the analyst
costs none.

## Producers and checkers

Produced by [`tools/measure/ordinary_comparator.py`](../../../tools/measure/ordinary_comparator.py)
and [`tools/measure/observation_cover.py`](../../../tools/measure/observation_cover.py).
Checked by [`check_cohort_packet.py`](../../../tools/measure/check_cohort_packet.py) and
[`check_observation_cover.py`](../../../tools/measure/check_observation_cover.py), which import
nothing from the producers and run neither a matcher nor a search.

Command timings are machine dependent and are not human effort. No person has run either method
on this cohort, so every human cost is recorded `unmeasured`.

## Scope

Every verdict is over admitted readings, never over the physical world. The live two window
comparison remains open at `[-8, 8]` with no admitted reading and no human reference, and is
reported as waiting on a reference rather than on any atom.
