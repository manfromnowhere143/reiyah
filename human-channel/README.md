# Human channel

The camera-lidar workstream measured coupling between two automation channels. This thread
begins the other side of the windshield: the human, and eventually the joint human-automation
failure that is HARBOR's actual target, the moment two channels stop being independent.

## Source

100-Car Naturalistic Driving Study, VTTI, CC0 1.0 public domain. DOI `10.15787/VTT1/CEU6RB`.
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

## Discipline

Every result descriptive and `proposed`, `No Video` kept as unknown, never a causal or safety
claim, no released `1.2` byte involved. The next steps are anchoring the glance to the
precipitating instant, driver-level clustering, and the first joint human-automation measurement.
