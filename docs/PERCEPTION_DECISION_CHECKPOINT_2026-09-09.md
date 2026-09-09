# Perception-decision implementation checkpoint

Document ID: `reiyah.perception-decision.checkpoint-2026-09-09`

Version: `0.1.0`

Lifecycle status: `exploratory`

The first offline Engine implementation now computes and checks paired detection-loss enclosures
for a fixed base configuration and retained additions. This implements the computational core
of the [selected architecture](PERCEPTION_DECISION_ARCHITECTURE_2026-09-09.md). The
[guide](../research/perception-decision/0.1.0/README.md) contains the input semantics and runnable
commands. The [machine continuation](../research/perception-decision/0.1.0/implementation-status.json)
binds the tested source files, verification records, current limits and next authorized actions.

## What works

The closed input contract keeps unavailable outputs distinct from observed empty outputs. It
requires one common weighted cohort and constructs the augmented detections as the base plus
the supplied additions. Reference alternatives are Boolean-constrained graphs with shared
variables across anchors, or explicitly open references.

For each admitted finite interpretation, the producer computes maximum matching counts for
both configurations. The separate checker validates matching and vertex-cover witnesses,
their equal cardinality, the complete permitted interpretation set and the reported extrema.
It never calls the producer's matcher. A third, brute-force partial-assignment calculation in
the tests compares both implementations against every small graph in the declared test grid.

The paired additive loss uses the identity

```text
Delta = (FN_penalty + FP_penalty) * (TP_augmented - TP_base)
        - FP_penalty * retained_additions
```

Open reference uncertainty retains the unconditional interval
`[-FP_penalty * additions, FN_penalty * additions]`. Computational scope limits return a
checked coarse bound and an explicit model-consistency state. They do not silently truncate
interpretations. Missing required outputs block the comparison. An inconsistent model cannot
produce vacuous support. Excluding the chosen improvement threshold remains distinct from
establishing that the base configuration is better.

The CLI verifies expected input hashes before parsing, checks the certificate before writing,
creates outputs atomically without replacement, and provides a separate packet-verification
command. A successful computation can still have an unresolved scientific conclusion.

The per-frame nuScenes adapter applies the selected score, range and class-specific suppression
policy with exact source-decimal arithmetic. It preserves base duplicates, stable camera order,
all exclusion/suppression decisions and unavailable frames. Each normalized detection has its
source-bound record retained in the normalization receipt. Returned references remain open.
Whole-source verification and human reference constraints are separate work.

## Verification

All 199 offline unit tests passed on Python 3.14.2: 106 in `tests` and 93 in `tools/measure`.
Twenty-six tests exercise this new core and adapter, including the independent graph calculation,
forged certificates, omitted interpretations, exact boundary behavior, unknown values and actual
CLI processes. No test result is an independent scientific judgment.

```sh
python3 -B -m unittest discover -s tests -v
python3 -B -m unittest discover -s tools/measure -p 'test_*.py' -v
python3 -B tools/measure/gate_b_check.py --json /absolute/private/path/gate-b.json
```

The synthetic matching-ambiguity example was executed through `run` and a separate `verify`
process. It yields `[-1, 1]` with an unresolved preference. Removing the disputed object gives
`-1`; requiring its presence gives `+1` in the tests. These are constructed counterexamples,
not observations of detector performance. The example and resulting packet identities are in
the machine continuation.

The existing 52 empirical transcripts and 57 claim-register rows are preserved. The Gate B
development check does not rerun those experiments or establish a Gate A release result.
Gate A remains operator-unaccepted. Integration is authorized for this offline research slice;
there is no product-runtime or physical-control acceptance.

## Next work and limits

Bind and parse the full metadata and two prediction sources, then construct clock-derived input
records and explicit raw-window availability without selecting scenes from detector outcomes.
Build the physical-reference adapter with preserved class, geometry, alias, time and cross-anchor
constraints. A finite graph enclosure is exact only for its formal model; physical coverage must
be justified separately. Retain an open reference wherever matchable alternatives are not bounded.

The 60-scene physical study remains unselected and unrun. Two independent discovery reviewers,
a competent independent conventional comparator, an adjudication arrangement and checked raw
observation windows remain prerequisites to its frozen execution. No fresh cohort seed has been
generated. Historical model outputs do not establish frontier detector quality. No new model
fits, inference, independent physical judgments or commercial differentiation are reported.

The shared parser, rational representation and resource policy remain part of the trusted
computational surface. The per-frame adapter is tested on synthetic data and assumes upstream
source checking. The CLI provides bounded offline computation, not OS-enforced isolation.

Work was prepared in a fresh export from main `f9715f6`, preserving the separate Gate A and
Gate B owner checkouts and the Console. The architecture checkpoint is `62c10cb`. Resolve later
main integration and publisher readback from Git and the private task delivery record. Original
research reports, released manifests, negative results, README diagrams and attribution history
remain preserved. New commits use the operator's author and committer identity without AI trailers.
