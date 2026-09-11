# Common analysis inputs, 0.1.0

Question: does retaining the existing detector and adding the declared candidate improve the
declared weighted false-negative/false-positive loss on these comparison anchors?

This folder prepares the same inputs for both analysts. It contains no human reference judgments.
Use it only at the agreed later assistance stage, after both independent discoveries have been
preserved and exposure order recorded. Preparation does not authorize disclosure or run a study.

`comparison.json` is a valid input to the existing offline comparison interface. It contains the
exact loss penalties, tolerance, common population weights, retained detections, explicit output
availability and open reference. `operands.json` binds that file, the complete source assistance
and `rules.json` by SHA-256. Its configuration roles identify the existing configuration and the
candidate; the augmented output retains every normalized base detection and adds only the
retained candidate detections. These roles are necessary to define the decision.

Each comparison anchor ID is its observation window ID. `frame_id` identifies its keyframe in
`assistance.json`, at time offset zero. Other keyframes are inspection context, not additional loss
opportunities or independent samples. Window-relative clocks, nominal global transforms and source
coordinates remain in the unchanged source assistance. No absolute clock or source-token mapping
is required to locate a comparison row within this package.

For every original prediction row at a comparison frame, the trace states score eligibility,
range eligibility, retention and any suppressing detection. A trace `row_id` is the exact source
row ID in that frame and configuration in `assistance.json`. Equal-valued duplicate rows still
have different IDs. A qualified record contains exact normalized class, XY and score; its record
digest is computed over that neutral record. The original source-record digests and identity
mapping remain with the operator. No source row is deleted from the assistance because it failed
an eligibility or suppression rule.

`rules.json` specifies the unchanged normalization, loss and decision conventions. Score 0.30 is
included; nominal XY range 50 metres is included. Suppression is same-class and strictly below
2 metres, using descending candidate score and source-row order to break ties. Every qualifying
base row survives, including duplicate base predictions. A suppressed candidate cannot suppress
another candidate. Missing base output makes candidate retention unknown. Unknown detector classes
are invalid inputs. Only XY, class and score participate here; source Z, size, orientation,
velocity and attributes do not silently acquire 3D validity.

All supplied references are open. An empty source annotation list, an uninspected capture or an
unassigned reviewer cannot establish an empty physical world. The current interval follows only
from the retained-addition count and penalties. It does not constitute physical coverage or prove
non-identifiability. Later reviewed alternatives require the separately bound admission workflow,
including shared interpretations across both configurations and anchors. This preparation refuses
finite references and nonempty joint models; it never strips them to reopen a comparison.

Both analysts may use the same mathematics, matching algorithms and public Engine/checker code.
A conventional analyst may calculate the loss or exact count bound directly. The Engine's
separate checker verifies matching certificates without calling the producer's matcher. Its
shared trusted contract, parser and edge semantics remain explicit. Record each method, initial
conclusion, corrections, unresolved evidence and effort using the rehearsal materials. Do not
count a machine's projection replay as human review or an independent scientific assessment.

From a checked Engine checkout, the prepared file can be processed with:

```sh
python -B -m tools.perception_decision run \
  --input /private/common/comparison.json \
  --input-sha256 EXPECTED_COMPARISON_SHA256 \
  --output /private/new-packet.json
```

Read expected comparison bytes from the separately supplied preparation identity, not a report
allowed to select its own inputs. The producer command also invokes the checker. Both analysts
must receive the same eventual admitted reference evidence and mappings before a later comparison.

This is private material. Structured source IDs are renamed, but original assumption and reason
text is preserved verbatim so substantive conditions remain visible. Text, coordinates, patterns
and source values can identify configurations or scenes. Masking is not anonymity or demonstrated
blindness. `SOURCE_READER.md` governs the unchanged assistance. Keep operator custody private and
record all prior exposure; no absence of prior knowledge is inferred.
