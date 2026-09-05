# Human channel H1: the driver's observation state in real conflicts

Document ID: `reiyah.human-channel.h1-driver-observation`

Version: `0.1.0`

Lifecycle status: `proposed`

## Why this exists

The camera-lidar workstream measured coupling between two *automation* channels. HARBOR's
actual target is the human and the automation as one encounter, and the moment their failures
stop being independent. This is the first empirical brick of the human side: how well was the
driver observing during real safety-critical events, measured on public data.

Source: 100-Car Naturalistic Driving Study (CC0), frame-by-frame eyeglance reduction for the
crash and near-crash events, glances timed in syncs (1/10 s). The on-road state is a `Forward`
glance out the windshield; off-road is any glance to mirrors, windows, the center stack, a cell
phone, an interior object, or eyes closed. `No Video` is kept as unknown time and never folded
into either, per Reiyah's status discipline.

## What was measured

For each event, the proportion of the observed window the driver's gaze was off the forward
roadway, and how often the driver looked forward for the entire observed window yet was still in
a conflict. The same statistic is computed on the baseline (normal-driving) epochs, because the
conflict number only has meaning against normal driving.

| Group | n | off-road, mean | eyes forward the entire window |
|---|---|---|---|
| Baseline (normal driving) | 4,950 | 17.3% | 39.1% |
| Near-crashes | 726 | 18.2% | 4.7% |
| Crashes | 59 | 28.3% | 1.7% |

(On-road defined as strict `Forward`. Folding in the peripheral `Left/Right Forward` glances
lowers every off-road figure by about three points and does not change the pattern.)

## What it says, stated as measured

1. **The average is only modestly elevated.** Near-crash off-road time (18.2%) is barely above
   normal driving (17.3%). Only crashes (28.3%) separate clearly, about 1.6 times baseline. The
   dramatic reading, that drivers in conflicts were simply looking away, is not what the average
   supports.

2. **The real signal is in the extreme, not the mean.** In normal driving 39% of windows are
   eyes-forward the whole time; in conflicts that collapses to about 5%, and to 1.7% in crashes.
   Almost every conflict involved *some* eyes-off-road, which normal driving frequently does not.

3. **Observation is not sufficiency.** A residual of conflicts, 4.5% overall and 1.7% of crashes,
   occurred with the driver looking forward for the entire observed window. The human observation
   channel was on and the event happened anyway. This is the human-side analogue of a channel
   that observed and still missed, and it is exactly what a driver-monitoring safety case that
   equates eyes-on-road with attentive-and-safe has to reckon with.

## What this is not

It is the observed-window proportion, not the glance at the precipitating instant, which needs
the reaction sync from the 69-column reduced file and is the next refinement. Events cluster
within about 100 drivers; proper inference on the crash-versus-baseline difference needs
driver-level clustering, which needs the driver mapping and is not done here, so the table is
descriptive, not an inferential test. It is 2003-2004 naturalistic data, and it is the human
channel alone, not yet the joint human-automation failure that is the mission's target.

## Next

- Anchor the glance to the precipitating instant using the reduced-file reaction sync.
- Cluster on driver and put an interval on the crash-versus-baseline difference.
- Bring in the automation-proxy channel (event sensor status) and measure the first joint
  human-automation failure, the actual HARBOR construct.

## Non-claims

Descriptive statistics on a public CC0 dataset, retained as `proposed`. Not a causal claim, not
a safety determination, and not a claim about any modern driver-monitoring product. No released
`1.2` byte is involved; this is a separate measurement thread.
