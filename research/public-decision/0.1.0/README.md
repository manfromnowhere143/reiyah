# Missing simulation records: what the ranking still establishes

Document ID: `reiyah.public-decision.result`.
Version: `0.1.0`.
Lifecycle status: `exploratory`.
Date: 21 September 2026.

**The proposed complete-group comparison is blocked. A separate, conditional
aggregate comparison is supported, with exact conventional/Reiyah parity.**
This is an audit of published simulation records, not a new driving experiment
or evidence of competitive advantage.

The [original question](QUESTION.md) asked whether the artifact labelled
UniAD-Base improves the mean recorded score over UniAD-Tiny without regressing
in any reported scenario group's success rate. Both files had to contain the
same complete 220-record population. The official files contain **218 and 215
unique records**, respectively. Their union has 218 records; shared metadata
agrees on the 215 common identifiers. The required complete-group comparison
therefore did not run. All 44 reported group memberships are retained privately;
no favorable subset was selected.

The [separately frozen diagnostic](DIAGNOSTIC.md) asks what those missing scores
alone could change. Conditional on a common intended 220-route population and
every unrecorded score lying between 0 and 100, Base's mean exceeds Tiny's by
**2.811919809 to 5.993737991 score points for every completion**. Two constructed
extreme completions attain the endpoints. Neither completion is an observation.

## Why the distinction matters

The publisher's merger divides the observed score sum by 220. Its documentation
explicitly says missing contributions receive zero under that scoring convention.
The two resulting means here are approximately 45.8131641 and 40.7285170.
A declared zero contribution is not a recorded zero outcome.

Allowing arbitrary missing outcomes makes the comparison less certain, but the
lower difference is still positive. Missing scores alone therefore cannot reverse
this conditional aggregate ordering. They still prevent the original complete-
group audit under its frozen admission rule. This calculation does not repair
unknown cohort, model, runtime or simulator provenance.

The screening rule was authored for this research. It is not an actual customer's
release criterion or the publisher's adoption rule. No release or deployment
decision occurred, and no practical savings or willingness to pay were measured.

## Reused method and conventional comparison

The existing [finite-population methods](../../sequential-audit/0.1.0/methods.py)
provide the native validation and exact interval calculation. The conversion uses
four weighted blocks: each arm's observed average and its explicitly missing
average. Missing blocks retain their full interval and missing status. The
existing six-unit cap remains intact. No statistical sampling, new solver,
perception runtime change or production promotion occurs.

A separately written conventional arm parses decimal JSON, sums scaled integers
and calculates the two extreme means. Both arms receive the same files, record
identity checks, observed failures, score bounds and conditional assumptions.
They agree exactly:

| Quantity | Conventional | Reiyah |
| --- | ---: | ---: |
| Lower Base-minus-Tiny mean difference | 309311179/110000000 | 309311179/110000000 |
| Upper difference | 659311179/110000000 | 659311179/110000000 |
| Conditional aggregate result | Supported | Supported |
| Original complete-group question | Blocked | Blocked |

This is ordinary bounded-missing-data arithmetic, not a novel Reiyah theorem.
The implementation and checker share an author and runtime. Separately coded
checks are not independent scientific replication.

## Verification and costs

The original question froze at 11:52:23 UTC, before acquiring the result files.
The structural check exposed the missing records before the diagnostic question
froze at 11:55:24 UTC. Publisher aggregate figures were already exposed throughout.
The implementation/source freeze preceded deliberate route-score computation:

`fb41416ebfa9f14b225013b63a5272e149b20ca6ee3fe5879e1e79f94c00c7a6`.

Twenty-one authored controls pass, including strict-zero decisions, recorded
failures, genuinely missing outcomes, duplicate identities and unavailable
states. A separate checker reconstructs all 433 delivered records, checks both
extreme completions and rejects 23 actual saved-result mutations. It imports
neither arm. The original blocked result is bound into each saved result.

The conventional and native whole processes took 0.103643917 and 0.110721250
seconds; internal work through computation took 0.011486125 and 0.015944084
seconds. The separate check took 0.111119625 seconds and authored controls
0.106571167 seconds. Internal and child-CPU timers overlap outer process time.
One fixed-order run per arm is not a general speed benchmark. Shared acquisition,
failed attempts and later packaging/integration costs remain separately charged.

No numerical execution failed. Retained preparation failures include a 16 KB
license request refused on its 19,133-byte header, an incomplete 32,000-byte
benchmark commit-API response, and a subsequent attempt to parse that incomplete
JSON. The license was captured under an explicit pre-outcome allocation amendment.
The incomplete commit response was not retried; normal Git reference metadata
provided the separate identity check. One discarded probe byte is charged.
Nothing was relabelled as empty data or successful complete evidence.

The first packaging process also failed while reading its own unfinished command
receipt. Its partial output, failed helper and cost are retained. Corrected
packaging verifies already-written output identities and reads active-command
metadata from START. No frozen code, source or scientific result changed.

The provisional new-source allocation changed from 1 MiB to 1.5 MiB after file-
size metadata, before result access. The inherited combined 8 MiB ceiling did
not change. Both original allocation and amendment remain retained. Artifact
and free-space limits are 128 MiB and 5 GiB. Active effort, full monetary cost,
network overhead, energy and peak memory remain unknown.

## Sources and scope

The official [Bench2DriveZoo files and documentation](https://github.com/Thinklab-SJTU/Bench2DriveZoo/tree/498c1f799dd90faf840dedb3f0d3234ec2e567db)
are pinned to the 2 December 2024 repository revision. The separate
[Bench2Drive documentation and scoring code](https://github.com/Thinklab-SJTU/Bench2Drive/tree/7ec25d1c9f7522d923ce5f3420986cef1cb2d956)
describe later protocol changes, including a new August 2026 validation set.
These old result files are **not** a reproduction of that new validation set.

Neither the old 693,537-byte route XML nor the new 735,811-byte XML was acquired:
the necessary old manifest did not fit alongside the selected pair and retained
prior sources within the inherited remaining source allowance. Matching record
labels and a count of 220 would not independently establish the complete official
route allocation or authentic execution provenance anyway.

All third-party bodies and route-level derivatives remain private. The source
license is CC-BY-NC-ND 4.0; no commercial-use, source-integration or redistribution
permission is inferred. Credit: Thinklab-SJTU; Xiaosong Jia, Zhenjie Yang, Qifeng Li,
Zhiyuan Zhang and Junchi Yan, *Bench2Drive: Towards Multi-Ability Benchmarking of
Closed-Loop End-To-End Autonomous Driving* (2024). The findings do not imply their
endorsement. Exact captures, access status, terms and digests are in sources.json.

## Next evidence and investment decision

Keep the research investment at MODIFY. This case demonstrates a useful distinction
between a missing observation and a scoring convention, while a competent method
reaches the same conclusion. It does not justify a larger framework or another
selector/scoring sweep on these exposed records.

To resume the original group question, first establish the intended route manifest
and obtain provenance-bearing terminal results for the omitted routes. For example,
Tiny lacks the route labelled RouteScenario_11755_rep0 that appears in Base:
the needed record would identify that route's actual run, terminal state and
recorded score under the same evaluation rules. A source-authenticated terminal
failure may justify a scoring-policy zero; an absent row alone is not that record.
Two intended route identities are absent from both files and remain unresolved.

The manifest is a concrete public lead. Missing terminal-run evidence is not
asserted available from Daniel or a private team. Further acquisition must fit the
remaining inherited budget; this owner authorizes no additional source sweep.
Public arithmetic cannot manufacture execution provenance, human costs or demand.
Preserve these results and all earlier parity, disadvantage and physical unknowns.
All 1,433 reserved images remain closed; Gate A remains operator-unaccepted.

## Reproduction

The source files must match run.py's exact size and SHA256 bindings. Place them in
a private source directory under their applicable terms. From the repository root,
the following are development replay commands, not canonical timing evidence or
Gate A release validation:

~~~sh
python3 -B research/public-decision/0.1.0/controls.py /new/private/controls.json
python3 -B research/public-decision/0.1.0/run.py conventional /private/sources /new/private/conventional.json
python3 -B research/public-decision/0.1.0/run.py native /private/sources /new/private/native.json
python3 -B research/public-decision/0.1.0/check.py /private/sources /new/private/conventional.json /new/private/native.json /new/private/check.json
~~~

Output parents must exist and output paths must be new. The canonical run used
the existing pinned Python runtime and network denial before interpreter startup.
Its private owner is
`~/.codex/reports/reiyah/public-decision-2026-09-21-sftzjbvb/`.
Read CLOSEOUT, FINAL_COSTS, PUBLISH_FINAL and FINAL_CONFIRMATION there after
integration. Publisher readback is integrity evidence, not independent transport
verification or scientific acceptance.
