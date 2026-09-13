# Real comparison and autonomous-window checkpoint, 13 September 2026

Document ID: `reiyah.engine.window-checkpoint`. Version: `0.1.0`. Status: `exploratory`.

The actual two-window comparison remains **[-8,8]**. Current Engine code reproduces its retained
packet byte for byte, and a conventional calculation rechecks all 648 original comparison-row
dispositions. The engineering improvements have not supplied the missing reference observations
or changed the detector decision. More synthetic architecture does not discharge that obligation.

This final verification starts from main `172ff2d82b4a74a1d9aa7389e9707171cfebabdf`, tree
`43cd90373ad92ad7ee333e9afa7f402b7f5e532d`. Its [machine evidence](../research/engine-window-verification/0.1.0/verification.json)
binds the commands, original inputs, outputs, controls, limitations and measured costs. The private
packet is `~/.codex/reports/reiyah/engine-window-verification-2026-09-13/`; its exact resulting
commit, normal push and publisher readback are recorded there. No production code changes here.

## What the real check establishes

The retained [common operands](PERCEPTION_OPERANDS_CHECKPOINT_2026-09-11.md) preparation is
6,213 bytes, SHA-256 `4853a8ce959422f819795e86bf7a36b7fce9d43444ec7bdf2250f33c4885bf0a`.
Its comparison is 14,147 bytes, SHA-256
`fbb2610aef00687e429bb71d805c4c1f321ec14978005e9fbdf44048bb5547b4`.
All seven preparation files and all 158 files in that historical closeout are rechecked. Input
selection comes from the committed preparation checkpoint, not a packet choosing its own source.
The selected input remains private; neither source payloads nor reviewer assistance are published.

| Anchor | Retained base | Retained additions | Weight | Reference | Count enclosure |
|---|---:|---:|---:|---|---|
| window-0001 | 48 | 9 | 1/2 | open | [-9,9] |
| window-0002 | 37 | 7 | 1/2 | open | [-7,7] |

For a maximum matching on the same reference interpretation and graph, retaining every base
detection implies gain `g >= 0`. Deleting the at most `r` added detections and their matched edges from an augmented matching leaves a feasible
base matching, so `g <= r`. With nonnegative miss and false-detection penalties `a,b`,
`delta = (a+b)*g - b*r` therefore lies in `[-b*r,a*r]`. Here both penalties are 1, so equal
anchor weights give `[-(9+7)/2,(9+7)/2] = [-8,8]`. Tolerance remains 1/10. This ordinary bound
is conservative under open references; it does not show that either endpoint is attained in the
physical scene or prove physical non-identifiability. Open references are never finite empty sets.

Two current producer runs create identical packets and match the earlier entire packet, including
its producer identity. The current checker accepts the honest packet with producer and producer
matching functions disabled. Seven rehashed forgeries are rejected: each of three non-unresolved
preferences, supported improvement, established physical coverage, exact finite enclosure and a
changed lower bound. These controls check consumed verdicts; they do not authenticate observation.
The current checker still shares its parser, contract, runtime and declared edge semantics.

The retained conventional script imports no Engine code. Its exact unchanged bytes independently
recalculate score eligibility, nominal range, same-class suppression, retained detection identities
and every source-row disposition from the selected assistance. It confirms 490 ineligible rows,
158 qualifying rows, 85 retained base detections, 16 additions and 57 suppressed candidate rows.
Its 902-byte output is identical to the earlier calculation. This rechecks declared representation;
the upstream source scan, projection, nominal geometry and physical interpretation remain trusted.

## What changed during the window

The 16 preceding closed checkpoints and all 9,103 file bindings were rechecked. They retain
first failures, corrections and withdrawn hypotheses. The most consequential Engine changes are
custody checks around discovery and viewer outputs, preservation of selected original records,
a prepared opening at the actual declared anchor, and bounded sharing of equivalent references
without rewriting joint alternatives or source membership. Matching competition, loss, weights,
tolerance and explicit unknowns remain in the common interface.

The [latest conformance audit](PERCEPTION_PARTITION_CONFORMANCE_2026-09-13.md) checks all 5,400
cases in its declared tiny domain, including complete original graphs and ordered provenance.
It corrected its own missing operand and shared-node identity checks. Passing this grid does not
justify claims about unexamined physical error operations, human effort, novelty or state of the art.

The latest full repository suite retains 404 passing tests. The 93 measurement tests and the eight
checks in each of the two subsequent accounting/conformance audits remain separately identified.
This documentation/evidence checkpoint does not replay unchanged broad suites. The research
consistency entry point passes on 52 retained identities; it is not a Gate A release replay.

The combined real refresh, controls and custody checks took 1.183 reported command seconds with
70,205,440 maximum child RSS bytes. The conventional row check took 0.150 seconds with 82,624,512
bytes. The commands perform different work; neither includes full human preparation or review.
Supervisor intervals include stream hashing. A missing checks-parent directory stopped the first
supervisor before the child ran; the failure is recorded without inventing a supervisor duration,
and the corrected run uses a fresh capture identity. Prior [command accounting](ENGINE_EFFORT_ACCOUNTING_2026-09-13.md)
selects only the first fourteen checkpoints. Its totals must not be relabeled the cost of this
entire window or combined with recursively copied receipts.

## The next observation

The bounded opening is ready at
`~/.codex/reports/reiyah/engine-anchor-opening-2026-09-13/private/opening/OPENING.md`.
It opens capture-000041 at the first declared anchor, with all 34,720 original point records and
all 725 supplied capture occurrences retained. The return belongs only in
`~/.codex/reports/reiyah/engine-anchor-input-2026-09-13/`. The earlier opening and return folder
remain separate. A reviewer can report visible display, select a point or region, save a new
scene and record actual time, prior exposure, help and failure. The Engine can then check the
selection against the exact original capture and record indices. It requests no object judgment.

Actual interactive observation and participant usability remain absent. Native desktop startup
has a retained Swift-loader incompatibility. Chrome's installed extension requires activation in
its installed profile before a supported browser connection is available. Do not assume missing
screen permission or gcloud login, or repeat an unchanged failed bootstrap. Background imports,
saved scenes, code checks and generated images are not interactive or human observations.

After a valid opening/selection return, the next substantive evidence requires independent
unassisted discoveries, locked before assistance, followed by the staged assisted review and
adjudication. Preserve disagreements, unknowns, joint worlds and all source mappings for both
analysts. A source annotation or a synthetic world cannot substitute for a human reference.
The competent analyst has the same evidence, mathematics, abstention and adaptive questions;
preparation, verification, review, computation, integration and repair effort must all be counted.

Fable retains its independent research/comparator ownership. Remote
`814f26b26970399ecd255c9dca720f6620b3a059` was observed only; newer claims require a newly selected
sealed exchange. No Fable source, ref, status, process or outbox was changed. Gate A is unaccepted,
external scientific review is missing, and the prospective physical study has no selected cohort
or seed and has not run. P005 is operator-reported published; no further outreach is authorized.
The authorized ten-hour window ends at 15:58:25 UTC. Its final private window record identifies
completion; the exact checkpoint remains reviewable without reopening any closed evidence packet.
