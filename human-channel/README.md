# Human channel

The camera-lidar workstream measured coupling between two automation channels. This thread
begins the other side of the windshield: the human, and eventually the joint human-automation
failure that is HARBOR's actual target, the moment two channels stop being independent.

## Source

100-Car Naturalistic Driving Study, VTTI, CC0 1.0 public domain. DOI `10.15787/VTT1/CEU6RB`.
Custody for every source in this thread, with retained publisher records and verified checksums, is
in [`evidence/public-data-custody-2026-09-06.json`](../evidence/public-data-custody-2026-09-06.json).
828 crash and near-crash events, ~5,000 baseline epochs, frame-by-frame driver eyeglance
reduction, glances timed in syncs (1/10 s).

## Reproduce the data (not committed; CC0, fetched from the dataverse)

```
mkdir -p human-channel/data && cd human-channel/data
for id in 574 578 577 571; do curl -sL "https://dataverse.vtti.vt.edu/api/access/datafile/$id" -o "$id.txt"; done
# 574 event eyeglance, 578 event reduced (69 cols), 577 event timestamp, 571 baseline eyeglance
# dictionaries: 586 eyeglance, 587 timestamp, 589 video reduction
```

The tools expect `eventEyeglance.txt`, `eventVideoReduced.txt`, `baselineEyeglance.txt` in
`human-channel/data/`.

## Results

- [`H1_DRIVER_OBSERVATION.md`](H1_DRIVER_OBSERVATION.md) - the driver's observation state in real
  conflicts, against a normal-driving baseline. Off-road gaze is only modestly elevated on average
  (crashes 28.3% vs baseline 17.3%), the real signal is that eyes-forward-throughout collapses from
  39% in normal driving to under 5% in conflicts, and a residual of conflicts happened with the
  driver looking forward the entire window: observation is not sufficiency.
- [`H2_GLANCE_AT_CONFLICT.md`](H2_GLANCE_AT_CONFLICT.md) - the gaze at the conflict instant, anchored
  to event_end. In about two thirds of crashes (67.8%) the driver was looking forward at the moment
  it happened. Eyes-on-road is necessary, not sufficient: a channel being on is not the channel
  succeeding, the human-side twin of the camera-lidar result.
- [`H3_OBSERVATION_RESPONSE_JOINT.md`](H3_OBSERVATION_RESPONSE_JOINT.md) - the first joint
  measurement. The same Definition 32 coefficient applied to the human's two channels, observation
  and response: c = 1.46, they fail together beyond independence, and 23% of crashes had the driver
  looking forward yet doing nothing. The redundancy fails on both sides of the windshield.
- [`H4_DCPT_TAKEOVER.md`](H4_DCPT_TAKEOVER.md) - a modern L3 counterpart (DCPT, CC BY 4.0). Visual-
  manual distraction (game, messaging, reading, eating) slows the automation-to-human takeover by
  +0.47 s (+24%) versus no task; cognitive-only load costs almost nothing. The kind of distraction
  is what matters, and the human-as-backup assumption is weakest for the tasks people do on a phone.
- [`H5_CROSS_AGENT_JOINT.md`](H5_CROSS_AGENT_JOINT.md) - the cross-agent joint (BDD-A, research-use):
  a validated detector on the frames (automation) against the driver gaze heatmap (human) over
  13,904 objects. Cross-agent c = 0.97, approximately independent, in contrast to same-kind
  redundancy (two sensors 1.15, one human's eyes-x-hands 1.46). Same-kind redundancy is a trap;
  different-kind (human x machine) roughly holds - on detectable objects, with an engaged human.
- [`H6_TOTAL_BOTH_MISS.md`](H6_TOTAL_BOTH_MISS.md) - the deepest version, with an interval. A strong
  reference detector defines objects present, a realistic edge detector is the deployed automation
  (totally blind to 84.5% of them), and the total joint miss with human neglect is c = 0.981,
  clip-clustered 95% CI [0.962, 0.998]. Even at total blindness the human-machine pairing is not
  worse than independent, in sharp contrast to same-kind redundancy.
- [`H5B_CROSS_AGENT_INTERVAL.md`](H5B_CROSS_AGENT_INTERVAL.md) - H5 re-measured with the clip
  id per object: c = 0.962, clip-clustered band [0.927, 0.993], upper bound below 1. The
  human-machine cell now carries a band at both depths (H5b, H6).
- [`H6B_BLINDNESS_CHECK.md`](H6B_BLINDNESS_CHECK.md) - the edge detector's 84 percent total-miss
  rate in H6 is genuine and size-driven (100 percent on the smallest quarter of boxes, 42.6 on the
  largest), not a matching or class-mapping defect; the marginals still cap H6's coefficient near
  1.18, so the human-machine cell rests on H5 and H5b.
- [`H7_INTERVALS.md`](H7_INTERVALS.md) - bands on every human-channel headline. The eyes x hands
  coefficient is 1.46 [1.04, 1.90] over all events (event-resampled, not driver-clustered) and does
  not exclude 1 in either severity subgroup; the visual-manual takeover delay is +0.47 s [+0.21,
  +0.73] participant-clustered. The human same-kind cell holds narrowly and is quoted with its band.

## Discipline

Every result descriptive and `proposed`, `No Video` kept as unknown, never a causal or safety
claim, no released `1.2` byte involved. H5 and H6 execute pretrained torchvision detectors on the
BDD-A frames to produce the automation channel's outputs; nothing is trained, and the word silent
is not used for a both-channel miss. The next steps are anchoring the glance to the
precipitating instant, driver-level clustering, and the first joint human-automation measurement.
