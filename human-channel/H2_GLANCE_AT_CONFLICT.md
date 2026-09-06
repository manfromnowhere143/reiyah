# Human channel H2: the driver was usually looking forward when it happened

Document ID: `reiyah.human-channel.h2-glance-at-conflict`

Version: `0.1.0`

Lifecycle status: `proposed`

## The anchor H1 lacked

H1 measured the whole observed window. This anchors to the conflict itself. In the 100-Car data
the eyeglance sequence ends exactly at the reduced file's `event_end` for every event (verified,
offset 0), so `event_end` is the conflict climax and `[event_start, event_end]` is the
few-second reaction window. That lets the gaze be read at the moment that matters.

## What was measured

For each crash and near-crash, the off-road gaze proportion during the reaction window, and the
gaze location at the climax, the driver's gaze at the instant of the conflict.

| Group | n | reaction-window off-road (mean) | gaze forward at the conflict instant |
|---|---|---|---|
| All events | 783 | 23.9% | **70.2%** |
| Crashes | 59 | 36.0% | **67.8%** |
| Near-crashes | 724 | 22.9% | 70.4% |

## What it says

1. **In about two thirds of crashes, the driver was looking straight ahead at the moment of the
   conflict.** Eyes on the road, and it happened anyway. Only about 30% were looking away at the
   instant. This is the human-side twin of the camera-lidar result: a channel being *on* is not the
   same as the channel *succeeding*. Gaze direction is a weak proxy for detection.

2. **The reaction window sharpens the severity gradient.** Crashes carry 36.0% off-road time in the
   reaction window against 22.9% for near-crashes, a wider separation than the whole-window
   figures in H1 (28.3% vs 18.2%). Focusing on the seconds that matter strengthens the
   inattention-severity relationship, as it should.

3. **The consequence for driver monitoring.** A safety argument that treats eyes-on-road as
   attentive-and-safe is contradicted here: two thirds of crashes occurred with the driver's gaze
   forward. Eyes-on-road is necessary, not sufficient. This is the same shape of error the
   camera-lidar work found in the automation channels, now on the human side.

This independently reproduces the direction of Victor et al. (2018), that a substantial share of
drivers are looking toward the conflict and still fail, from a different derivation on public data.

## What this is not

`Forward` means a glance ahead through the windshield, not provably at the specific hazard, so
"looking forward" does not mean "saw the hazard"; it means gaze direction did not prevent the
event. It is descriptive, not driver-clustered, and 2003-2004 naturalistic data. It is the human
channel alone. The mission's target, the joint human-automation failure, is next.

## Adversarial reading, 2026-09-06

A context-free reader (model-assisted, advisory, same model family as the author) read this document against its transcript alone. The points below are the ones that changed a sentence; the full record is `evidence/review-model-assisted-2026-09-06.json`.

1. The conflict instant is `event_end`, the last sync of the reduced window. Nothing in the
   transcript establishes that this is the precipitating moment rather than the end of the
   evasive maneuver, by which time a driver who looked away may have re-oriented forward. The
   70.2 percent figure may therefore measure post-recognition gaze and overstate looking forward
   when it happened. This is the strongest open objection to H2 and it is not answered here.
2. The table shows no unknown column; the unknown-gaze share at the instant is 1.1 percent of
   events and 1.7 percent of crashes in the transcript.
3. Result H7 reports the same rates on a smaller denominator (775 and 58 events with known gaze
   against 783 and 59 here, which include unknown gaze); the two agree within a point and the
   denominators are now stated in both.

## Non-claims

Descriptive statistics on a public CC0 dataset, retained as `proposed`. Not a causal claim, not a
safety determination, not a claim about any modern driver-monitoring product. No released `1.2`
byte is involved.
