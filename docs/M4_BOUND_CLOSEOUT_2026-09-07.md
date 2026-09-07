# M4 mathematical bound checkpoint

Document ID: `reiyah.m4-bound-closeout.2026-09-07`

Version: `0.1.0`

Lifecycle status: `exploratory`

This local revision extends `ca548d4fd66180e9c2e2aa4a789a366c23903401` on
`research/2026-09-07-m4-bounds`. The private `delivery.json` records the resulting commit,
tree, patch digest, author and exact changed-blob readback. Daniel Wahnich is the sole author
and committer. Neither active worktree is switched or edited, and no merge or push occurs.

## Completed scope and correction

The [findings](M4_RECTANGULAR_BOUND_FINDINGS_2026-09-07.md) correct the retained M4 fixture
F-03's incorrect infinity label. The declared rectangle has finite supremum 49.75, approached
without attainment; some positive-universe coefficients remain undefined. A second authored
counterexample shows a grid missing the actual maximum. All seven direct historical rectangular
report calls were exercised; the other six agree with the analytic values to floating-point
precision. The historical full experiment, random probes and differential solver were not replayed.

The new [specification](M4_RECTANGULAR_BOUND_SPECIFICATION_2026-09-07.md), rational solver,
separate algebra checker, versioned controls and executable CLI example are complete for their
declared nonnegative rectangular domain. The checker verifies complete-interval quadratic
inequalities and extremum witnesses without importing the solver. It is an algorithmic check
from the same session, not independent human mathematical review or a proof-assistant kernel.
The synthetic plot was rendered and visually inspected. A path-suffix error in the initial
plotting invocation was corrected before the successful render; it affected no numerical result.

## Evidence and checks

The [audit capture](../evidence/m4-bounds/audit-capture-0.1.0.json) and
[regression capture](../evidence/m4-bounds/regression-capture-0.1.0.json) retain successful
process exits and source/stream bindings. All 21 tests pass, including 1,296 lattice rectangles,
domain degeneracies, actual CLI execution, and rejection of fabricated bounds and precision.
The [development verification](../evidence/m4-bounds/verification-0.1.0.json) checks the
completed process closure, rechecks mathematical witnesses and binds the comparison table,
including an altered-number rejection. The
[Gate B check](../evidence/m4-bounds/gate-b-check-0.1.0.json) checks retained historical
transcript digests and the inherited review record; its skipped historical replays are explicit.

Every predecessor file except the README and three navigation documents is byte-preserved.
This includes the historical M4 source/transcript, frozen reference-study protocol and selection,
scientific claim register, replay manifest and Gate A release operands. Passing development
checks neither creates Gate A release evidence nor changes its unaccepted operator state.
The new mathematical correction is carried by its own versioned findings and output, without
silently relabeling the old experiment.

## Replay and restart

Begin a resumed session at `/Users/danielwahnich/workspace/reiyah` and read its current
instructions and handoff. Inspect the local research ref while preserving the active owners'
worktrees. Use the [research continuation ledger](RESEARCH_CONTINUATION_2026-09-07.md).
The current private task root is:

```text
/Users/danielwahnich/.codex/reports/reiyah/m4-bounds-2026-09-07/
```

Its `baseline/` exports the parent commit, `implementation/` holds the candidate, and
`checks/` retains actual process streams. The final tree, exact patch and readback are
outside the public candidate in this task root. To repeat the local mathematical checks
from `implementation/`:

```sh
python3 -B -m unittest discover -s tools/measure -p test_rectangular_bounds.py -v
python3 -B tools/measure/audit_m4_bounds.py
python3 -B tools/measure/verify_m4_bounds.py --checks-root ../checks --baseline-root ../baseline
```

The solver/checker example in the findings works without the private process custody. The
closeout verifier intentionally needs that custody to check historical execution assertions.
Use a fresh output identity to retain a replay. Do not overwrite a completed capture or infer
completion from an input specification. No cloud resource or service was created for this
checkpoint, and these local calculations have finished.

## Next scientific dependency

The user canceled the earlier shutdown deadline; this is a durable checkpoint during ongoing
work. A mathematically valid interval is useful only after its empirical constraint model is
justified. The next independent investigation should ask what observations distinguish true
joint failures from shared reference errors and omitted opportunities. The prepared 240-case
study remains frozen and awaits independent human judgments. It does not itself enumerate
objects missed by both detectors and the reference or establish a safety-critical coefficient.
No human observations, physical-performance estimate, service deployment or commercial
acceptance have been manufactured by completing the mathematical component.
