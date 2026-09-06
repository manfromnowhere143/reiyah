# Human channel H3: the first joint measurement, and it fails the same way

Document ID: `reiyah.human-channel.h3-observation-response-joint`

Version: `0.1.0`

Lifecycle status: `proposed`

## The same question, asked of the human

The camera-lidar workstream asked whether two automation channels fail together more than
independence predicts. This asks it of the human's own two channels on the same encounter:
**observation** (gaze at the conflict instant) and **response** (evasive action). It uses the
identical estimand, the coincidence coefficient of RSS Definition 32:

```
c = P(both channels fail) / [ P(observation fails) * P(response fails) ]
```

`c = 1` is independence. `c > 1` means the two channels fail together beyond independence.

Channels from the data: observation fails when the climax gaze is not `Forward`; response fails
when `driver_reaction` is `No reaction`, the driver did nothing.

## The result

| Group | n | P(both fail) | expected if independent | **c** | looked forward yet no reaction |
|---|---|---|---|---|---|
| All events | 770 | 3.1% | 2.1% | **1.46** | 4.3% (33) |
| Crashes | 56 | 14.3% | 11.4% | 1.25 | **23.2% (13)** |
| Near-crashes | 714 | 2.2% | 1.4% | 1.55 | 2.8% (20) |

## What it says

1. **The human's redundancy is not independent either.** (Band added 2026-09-06 by H7: 1.46 with an
   event-resampled 95% interval of [1.04, 1.90] over all events; the crash and near-crash subgroups
   do not exclude 1.) Observation and response fail together
   about 1.46 times more than independence predicts. This is the same shape, and nearly the same
   magnitude, as the conditional camera-lidar coefficient. The assumption that a driver who is
   looking will also act does not hold cleanly.

2. **The non-trivial cell is the damning one.** Part of `c > 1` is the obvious causal link, eyes
   off means no chance to react. But that does not touch the eyes-forward-yet-no-reaction cell,
   which is 4.3% of all events and **23% of crashes**. In nearly a quarter of crashes the driver
   was looking forward and still did nothing: observed, and did not respond. Looking is not acting.

3. **The thesis, unified.** Two automation channels fail together beyond independence. The human's
   two channels fail together beyond independence. The redundancy a safety case leans on is
   violated on both sides of the windshield, wherever it has been measured.

## What this is not

This is the **within-agent** joint, the human's own two channels, which is the honest joint this
dataset supports. It is **not** the cross-agent human-automation joint, because the 100-Car study
has no modern automation channel; that measurement needs conditional-automation takeover data with
eye tracking and is the next acquisition. The coefficients on the crash subset rest on small counts
(n=56, both-fail 8, looked-no-act 13) and are illustrative, not an inferential test. It is
descriptive, not driver-clustered, on 2003-2004 CC0 data. `c > 1` here includes a causal component
(not looking impairs reacting) and is not claimed as pure latent dependence.

## Non-claims

Descriptive statistics on a public CC0 dataset, retained as `proposed`. Not a causal effect, not a
safety determination, not a claim about any product. No released `1.2` byte is involved.
