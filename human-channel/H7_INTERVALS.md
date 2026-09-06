# Human channel H7: intervals, and the human same-kind cell is weaker than it read

Document ID: `reiyah.human-channel.h7-intervals`

Version: `0.1.0`

Lifecycle status: `proposed`; one prior statement is `narrowed` by it

## Why

H1 to H4 report point estimates, and the law table quotes the human's eyes-by-hands coefficient
beside sensor coefficients that carry bands. This puts a band on every human-channel headline: an
event-resampled bootstrap for the 100-Car quantities (the public files carry no driver id, so these
are not driver-clustered and understate uncertainty if events cluster within drivers) and a
participant-clustered bootstrap for the DCPT contrast (trials cluster within 40 people). B = 2000,
seeded. Parsing and definitions are imported from the H3 and H4 tools unchanged.

## The intervals

| quantity | point | 95% band |
|---|---|---|
| gaze forward at the conflict instant, all events (H2) | 0.711 | [0.680, 0.742] |
| gaze forward at the instant, crashes (H2) | 0.690 | [0.569, 0.810] |
| eyes x hands coefficient `c`, all events (H3) | **1.460** | **[1.036, 1.897]** |
| eyes x hands `c`, crashes (H3) | 1.255 | [0.693, 1.867] |
| eyes x hands `c`, near-crashes (H3) | 1.548 | [0.990, 2.139] |
| looked forward yet no reaction, all events (H3) | 0.043 | [0.030, 0.057] |
| looked forward yet no reaction, crashes (H3) | 0.232 | [0.125, 0.357] |
| visual-manual minus no task, takeover time (H4) | +0.474 s | [+0.214, +0.732] |
| cognitive-only minus no task (H4) | +0.094 s | [-0.107, +0.277] |
| visual-manual relative to no task (H4) | +23.9% | [+10.3%, +39.9%] |

## What it says

1. **The human same-kind cell holds, narrowly.** The eyes-by-hands coefficient of 1.46 excludes
   independence over all events, with a lower bound of 1.04, and does not exclude it in either
   severity subgroup. The law table has quoted this cell next to sensor coefficients whose bands sit
   at plus or minus 0.01; that comparison is now stated with the band. The claim "the human's two
   channels fail together beyond independence" is supported at the 95 percent level on 770 events
   and is not a precise coefficient.

2. **The observational statements are solid.** Two thirds of conflicts with the driver looking
   forward at the instant has a band of a few points, and the looked-forward-yet-no-reaction cell
   in crashes, 23 percent, has a band of [12, 36] percent.

3. **The Level 3 distraction effect survives participant clustering.** Visual-manual tasks slow
   the takeover by 0.47 s with a band that excludes zero; cognitive-only tasks do not.

## Adversarial reading, 2026-09-06

A context-free reader (model-assisted, advisory, same model family as the author) read this document against its transcript alone. The points below are the ones that changed a sentence; the full record is `evidence/review-model-assisted-2026-09-06.json`.

1. The 100-Car bands are event-resampled; any intra-driver correlation widens them, and the
   near-crash subgroup already reaches 0.990. The lower bound of 1.036 is therefore the
   least-clustered reading, and H3's adversarial reading adds the selection-on-outcome objection.
2. The H2 rates here (0.711 on 775 events, 0.690 on 58) use events with known gaze; the H2
   document's 70.2 and 67.8 percent use 783 and 59 events including unknown gaze. Both are now
   stated.

## Non-claims

Descriptive intervals on public CC0 and CC BY 4.0 data, retained as `proposed`. The 100-Car
intervals are not driver-clustered; H3's coefficient includes a causal component. Not a causal
claim, not a safety determination, not a claim about any product. Transcript
`evidence/h7_intervals.txt` re-runs byte-identically (three runs). No released `1.2` byte is
involved.
