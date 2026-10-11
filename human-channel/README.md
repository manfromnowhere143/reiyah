# Human channel

Current interpretation, 10 October 2026: the
[dated correction](../research/claim-correction/0.1.0/README.md) and successor
claim register withdraw the population-bound and general independence inferences.
H5/H5b/H6 retain descriptive detector-selected gaze measurements. Their original
transcripts are unchanged. A checked [extraction-accounting helper](../research/extraction-accounting/0.1.0/README.md)
is available; historical cohort replay, consumer integration and timing qualification remain open.

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
- [`H5_CROSS_AGENT_JOINT.md`](H5_CROSS_AGENT_JOINT.md): low detector score and low
  gaze on 13,904 selected boxes, c = 0.972. No population bound or awareness claim.
- [`H5B_CROSS_AGENT_INTERVAL.md`](H5B_CROSS_AGENT_INTERVAL.md): a different sampled
  cohort, c = 0.962 with historical clip-bootstrap interval [0.927, 0.993].
- [`H6_TOTAL_BOTH_MISS.md`](H6_TOTAL_BOTH_MISS.md): reference-detector unmatched
  boxes and low gaze, c = 0.981 [0.962, 0.998]; marginals constrain its range.
- [`H6B_BLINDNESS_CHECK.md`](H6B_BLINDNESS_CHECK.md): size and matching diagnostics
  on H6's reference-defined misses, without independent physical ground truth.

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
