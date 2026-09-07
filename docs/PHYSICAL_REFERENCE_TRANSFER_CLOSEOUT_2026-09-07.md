# Physical-reference and transfer-feasibility checkpoint

Document ID: `reiyah.physical-reference-transfer-closeout.2026-09-07`

Version: `0.1.0`

Lifecycle status: `exploratory`

This local continuation extends `ed10cff36d48b30dfddab9484de1da8b289444ae` on
`research/2026-09-07-physical-reference-transfer`. The private delivery/readback records
resolve its final commit and tree. Daniel Wahnich is the sole author and committer.
The canonical Gate A and separate engine/UI worktrees retain their owners. This is
an offline research checkpoint, with no merge, push, deployment or outreach.

## Completed scientific work

The [RSS and sampling audit](RSS_TRANSFER_AND_RARE_EVENT_LIMITS_2026-09-07.md) separates
three coefficients, corrects an overattribution in the older proposed estimand text,
and derives an exact limitation for a declared passive experiment. The older source
file remains unchanged and discoverable beside this correction.

The [producer](../tools/measure/rare_event_dependence_limits.py) constructs two complete
four-cell laws with known equal marginals and coefficients one and two. An exact
total-variation argument bounds any test's discrimination under the stated iid
model. Rational logarithm enclosures also certify three integers for a separate
zero-event confidence rule. Neither result estimates a vehicle failure rate or
provides a usable operational safety budget.

Eleven [tests](../tests/test_rare_event_dependence_limits.py) pass. They include direct
enumeration of small product laws, exact small-binomial boundaries, undefined-state
preservation and forged-conclusion rejection. A
[separate arithmetic checker](../tools/measure/check_rare_event_limits.py), without
importing the producer, agrees using Decimal logarithms at two precisions. This is
a numerical cross-check, not independent human review or a formal proof verifier.
The machine-readable [derivation](../evidence/physical-reference-transfer/limits-0.1.0.json)
and [cross-check](../evidence/physical-reference-transfer/numeric-check-0.1.0.json)
retain their exact scope.

The [physical-reference assessment](PHYSICAL_REFERENCE_OPTIONS_2026-09-07.md) reviews
current NPL/Met Office work and proposes a test of a joint response law with explicit
sensor history and independent target-time references. The
[access preflight](../evidence/physical-reference-transfer/physical-reference-preflight-0.1.0.json)
retains what was inspected: public HTML and client code, no protected data access.
It does not establish a common-target population, data rights or a valid reference.

The [source ledger](../evidence/physical-reference-transfer/source-ledger-0.1.0.json)
records eight new original payload retrievals, one reused RSS payload, two failed
original retrievals, and a separately labeled publisher-index extraction for the
2026 paper. Failed HTTP retrieval is not promoted into original source custody.
The university copy of the 2002 paper explicitly identifies its version as
unspecified; the initial retrieval description was corrected accordingly. Primary
payloads remain private. No original NPL sensor measurements were acquired.

## Verification and scope preservation

The [process custody](../evidence/physical-reference-transfer/custody-0.1.0.json)
retains commands, stream digests and source identities for the new checks. The
[Gate B development check](../evidence/physical-reference-transfer/gate-b-check-0.1.0.json)
checks inherited transcript integrity and document consistency. Its historical
transcript states remain distinct; it does not replay the 52 historical experiments.
Its legacy result-number checks do not automatically validate new scientific prose.
The arithmetic controls above supply the new numerical checks.

The [candidate closure](../evidence/physical-reference-transfer/closure-0.1.0.json)
binds the new files, primary-source custody and preservation of predecessor bytes.
Only the README and three navigation documents change among inherited files.
Earlier results, the frozen studies, the claim register, release operands, schemas
and fixture catalogs remain unchanged. No new Gate A release replay was performed.
Operator acceptance remains **unaccepted**; tests do not create acceptance.

## Reproduction and restart

Private task custody is:

```text
/Users/danielwahnich/.codex/reports/reiyah/physical-reference-transfer-2026-09-07/
```

`baseline/` is the parent export. `implementation/` is the candidate. `checks/`
retains process captures; `external-sources/` retains original payloads, failed
retrieval metadata and the explicitly separate tool extraction; `private/` contains
text extractions. No process must survive for this checkpoint to be resumed.

From `implementation/`, the new calculations run offline:

```sh
python3 -B -m unittest discover -s tests -p test_rare_event_dependence_limits.py -v
python3 -B tools/measure/rare_event_dependence_limits.py
python3 -B tools/measure/check_rare_event_limits.py evidence/physical-reference-transfer/limits-0.1.0.json
```

Start future work at the canonical Reiyah root, repeat its identity check and read
the current owner handoff before considering integration. Do not switch the other
sessions' branches or assume that a remembered snapshot is still their live state.
The [continuation ledger](RESEARCH_CONTINUATION_2026-09-07.md) names the full chain,
the unchanged blinded study and the prepared private console repair.

## Chosen next observation

Obtain the independent judgments for the existing 240-case reference study. There
are still zero human judgments, and the new calculations cannot replace them. This
closes a concrete validity question in an already measured result. A new physical
response/transport study follows only after its own reference and access preflight;
it must not become an unbounded detour into more software or a generic weather
benchmark. The canceled laptop shutdown deadline does not change this priority.
