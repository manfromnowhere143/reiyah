# Qualify public predictions and test a replacement decision

Version `0.1.0`, 18 September 2026. Status: `exploratory`.

Two frozen local public checkpoints now supply complete, qualified predictions
on 64 previously exposed development images. The four-arm comparison preserves
the earlier parity finding: conventional and checked stopping make the same
queries and decisions when given the same selector and mathematics. The strong
conventional selector reaches the retrospective minimum query count in **every
resolved case**, including both resolved primary contracts. No observation or
full-cost advantage is established.

This is a YOLO11n-to-YOLO26n development proxy on one selected nuScenes camera
cohort. It is not a customer revision history, a second detector family, a
three-revision study, an AP benchmark or physical safety evidence. All **1,433
REC-D outcome-reserved images remain closed**. Engine source remains
`38a50ec014cc83e86ea6f247df803ded2971b386`; its implementation is unchanged.

## From public leads to usable inputs

All three specified EdgeFirst sessions yielded actual Parquet predictions
through public unauthenticated routes. Their 5,000 image IDs and dimensions
exactly match the official COCO val2017 annotation index. YOLOv8n has no explicit
empty placeholder; YOLO11n has one; YOLO26n has two. These are publisher-encoded
empty outputs, distinct from missing members. The historical checkpoint bytes
and complete actual inference configurations are unbound, so **zero cached
packets qualify for the replacement experiment**. See [sources](SOURCES.md) and
the complete [source identities](sources.json).

The authorized fallback freezes two official Ultralytics checkpoint files,
implementation, runtime, configuration and image membership. One-image and
eight-image checks precede each full 64-image export. A separately implemented
preprocessing and decoder check agrees exactly for all 146 staged calls.

| Local packet | Assigned | Processed with detections | Explicit empty | Failed/missing | All-class detections |
| --- | ---: | ---: | ---: | ---: | ---: |
| YOLO11n | 64 | 62 | 2 | 0 | 487 |
| YOLO26n | 64 | 60 | 4 | 0 | 353 |

All images were already exposed in the prior reference study. Membership was
selected by a frozen sensor-token hash from 226 available inputs before new
prediction scores. The 64 samples span 46 scenes; these are dependent,
previously selected development inputs. They are separate from the earlier
REC-D development allocation that retained six blocked members.

The publisher's nuScenes devkit projects its 3D annotations into each camera.
All 64 inputs qualify. The camera samples precede annotation sample times by
33.120–38.308 ms; this uses the publisher keyframe procedure without motion
interpolation. Projected rectangles are geometric, generally non-tight proxies,
including all visibility bins. No new human correction or physical truth is
observed. The archive was streamed to select these records; scanning public
metadata is distinct from accessing the closed REC-D outcomes.

## Frozen comparison and full-answer result

[PROTOCOL.md](PROTOCOL.md) fixes car eligibility, exact rational IoU at least
1/2, maximum one-to-one matching, unit false-positive/false-negative loss and
strict mean improvement above zero. The protocol was frozen before reference
preparation or replacement scores. A later 148-binding implementation/input
freeze precedes scoring. [ANALYSIS_PLAN.md](ANALYSIS_PLAN.md) separately freezes
the retrospective full-answer analysis. Neither protocol was revised to rescue
a result.

There are 73 overlapping cases: 64 singletons, eight fixed blocks and one
primary all-64 case. Each has three reference contracts and four arms, retaining
all **876 assigned rows** in [results.csv](results.csv). A uses largest open
width with conventional matching; B changes only to native checked matching.
C uses a fixed count-difference selector with checked matching; D supplies its
conventional interaction cell. Answers and caches have identical scope.

| Primary contract | A/B queries | C/D queries | Full-answer interval | Decision | Exact query floor |
| --- | ---: | ---: | --- | --- | ---: |
| Exact projected reference | 46 | 49 | [37/64, 37/64] | supported | 46 |
| At most one edit in the case | 47 | 50 | [33/64, 41/64] | supported | 47 |
| At most one edit per image | 60 | 60 | [-89/64, 173/64] | unresolved | undefined |

Four identical-output images have zero-width bounds and need no query. A direct
eligible-image audit therefore uses 60 queries, rather than 64. The table's
intervals use complete supplied answers; the original earlier stopping bounds
are retained separately in the row table. Floors use retrospective answers and
the frozen mathematics, not an executable blinded selector or a universal
lower bound across every possible future proof method.

| Contract, all 73 dependent cases, per arm | Supported | Excluded | Unresolved | Input-blocked | A/B queries | C/D queries |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Exact projection | 37 | 36 | 0 | 0 | 159 | 164 |
| One edit per image | 5 | 6 | 62 | 0 | 180 | 180 |
| One edit globally | 9 | 6 | 58 | 0 | 163 | 167 |

A/B and C/D have identical ordered histories and decisions on all 219 paired
rows. The candidate selector uses more observations on four cases and fewer
on none. Both-zero-query pairs are ties. For the 73, 11 and 15 resolved cases
respectively, the baseline attains every independently checked query floor.
There is no remaining selector headroom under these bounds on resolved cases.

All **120 unresolved full-answer rows** have admitted worlds on opposite sides
of the decision. The finite search attains both universal per-image bounds on
all 64 images. Attainment plus a valid bound proves exact extrema for these
fixed operands; it does not imply an exhaustive search of arbitrary rectangle
geometry. The exact minimum affected-image count needed to exclude primary
improvement is **15**, allowing at most one arbitrary eligible edit per affected
image: 14 images can change the nominal total by at most 36, while it starts
at 37; an attained 15-image world gives total -1. This does not cover multiple
edits within one image or estimate an empirical annotation-error frequency.

See [the derivation](DERIVATION.md), [all 219 full-answer rows](analysis.csv)
and [machine-readable summaries](summary.json). These results strengthen the
negative conclusion about selector/stopping superiority for this family. They
do not measure demand, reviewer productivity or investment value.

## Evidence, costs and limits

All 83 targeted synthetic controls and the default research consistency check
pass. [verification.json](verification.json) binds the retained check receipts.
Replay checks 2,026 queries, 2,902 stopping points and 4,599 native proofs. The
full-answer verifier checks another 128 native proofs, 292 composed worlds and
120 opposite pairs, with independent query-floor cardinality bounds. These
are internal implementation checks, not independent scientific replication.
Prior-revision proof reuse is not studied here; a false-reuse result cannot be
inferred from successful current-proof checking.

The worker OS policy denies network access and private answer-directory reads;
canary probes exercise both. The trusted service parent supplies only requested
answers. It cannot run inside a second macOS sandbox because nested sandbox
application fails. The initial failed attempt is retained, followed by the
declared worker boundary. This is process isolation, not independent blinding.

New downloads total **227,930,532 bytes** against the 2 GiB cap. All staged
prediction calls total **11.847570214 charged seconds**, including their decode
checks, against the 60-minute inference cap. Preparation, failed attempts,
comparison, proof/checking and verification costs are retained in
[COSTS.md](COSTS.md) and [costs.json](costs.json). No nested duration is added
again to outer elapsed time. Human review, complete economics and actual
customer decisions remain unknown. The existing 3x observation / 2x full-cost
investment targets are not met.

All raw source responses, weights, images, prediction tensors, reference
answers, query histories and proof payloads stay in the owned private packet
`~/.codex/reports/reiyah/value-10h-2026-09-18-c1y8k9yc/`. Read its SESSION,
PROGRESS, source receipts and comparison freezes. Public code, synthetic controls
and derived result tables are reviewable here. [REPRODUCE.md](REPRODUCE.md)
states the exact data/runtime requirements and commands. [DISTRIBUTION.md](DISTRIBUTION.md)
records the nuScenes attribution and applicable terms for derived reports.

The next bounded question is how much *localized* reference displacement can
change this fixed proxy decision. It needs a separate declared stress set and
must preserve the broader one-edit counterexamples. No extra images, model
training, reserved outcomes or selector tuning are needed. Gate A remains
operator-unaccepted; this authorized research fallback does not change it.
