# Checked bounds for reference-position uncertainty

Document ID: `reiyah.perception-localization-certificates`. Version: `0.1.0`.
Lifecycle status: `exploratory`.

## Result and scope

The Engine now checks whether a detector comparison survives declared planar
reference-position errors. `localization` produces graph-envelope certificates;
`verify-localization` checks them without invoking a matcher or optimizer. An
optional explicit displacement is checked against every residual radius and the
complete recalculated graph before it can refute robustness.

On the retained forty-frame Mapillary base plus Megvii additions case, the new
method proves strict improvement for every allowed displacement up to **0.25 m**
per reference record. The lower bound is **1/2**, above tolerance **1/10**.
At 0.50 m and 1.00 m this method remains unresolved. No adverse displacement is
inferred from a conservative bound crossing the threshold.

The family fixes detector membership, detector positions, classes, reference
membership and the strict same-class center-distance rule. Each supplied reference
center can move independently within a closed planar ball. This is a conditional
calculation over declared coordinates and radii. It does not measure annotation
error, establish physical completeness, or constitute an official nuScenes score.
General independent A/B output comparisons are supported by this graph argument.
Open references, unavailable outputs and latent joint-world inputs remain explicitly
unavailable for this particular method; other Engine methods retain their scope.

## Research handoff checked

Selected source: research commit `eb0ac64038f125bc4d216fe8b378f78bc589e01f`, outbox
manifest SHA-256 `02bf603d4f4d70ad8fe1c3089b98fb860e81102d78621f7681dd56baa7bd52cd`.
All sixteen payloads and fifteen committed origins match. The request still names
the earlier deletion checkpoint; its 373-label question was already settled by
the [ordered-endpoint proof](PERCEPTION_MONOTONE_AUDIT_2026-09-17.md). The new
localization code and report are the selected subject here. Owner files are preserved.

A consumer-bound snapshot contains 1,125 localization census rows. Independent
aggregation reproduces the reported status counts at all four radii. This is an
aggregate reconciliation, not replay of the MILP campaign or verification of its
universal robustness and position-audit claims. The selected census output does
not contain the claimed per-object displacement coordinates needed for witness
checking. The earlier random-seed and preparation-gate repairs remain outstanding
in the selected census source.

## Two concrete corrections

### Strict matching needs the inner boundary included

The research candidate-edge rule omits a present edge when its distance equals
`threshold - radius`. But displacement is allowed **up to and including** the
radius, while matching requires distance **strictly less than** the threshold.
That edge can disappear at the ball boundary.

The retained synthetic control has no A detections, one B detection at (0,0),
one reference at (1.9,0), radius 0.1 and threshold 2. With unit penalties the
improvement starts at +1. Moving the reference by (0.1,0) is allowed, removes
the strict match and gives -1. The copied research certificate reports robust.
Its own displacement search also finds exactly (0.1,0) when explicitly asked to
realize that flip. This is an executable false-robust control, not a demonstrated
error in any particular census row.

### A measured position retains its residual uncertainty

The research audit freezes all edges of a confirmed object. That is justified
only by a premise fixing those edges. Measuring a position to within a nonzero
radius generally does not do so. A second control places the reference at 1.95,
with radius 0.1: a displacement of 0.05 reaches the strict threshold, although
the research confirmation operation reports robust.

The new request supplies a **residual radius for every record**. A refined
measurement can provide a new center and smaller radius under a newly qualified
context; no confirmation flag silently substitutes radius zero. Exact position,
known adjacency, bounded measurement error and physical truth remain different
premises. No human measurements were performed in this checkpoint.

## Exact geometry and proof

Let R be the strict matching threshold, e the closed displacement radius, and
s the squared distance between the declared centers. For same-class pairs:

```text
guaranteed edge: e < R and s < (R-e)^2
possible edge:             s < (R+e)^2
```

Every realizable graph lies between those edge sets. Equality at the inner
boundary is uncertain; equality at the outer boundary cannot produce a strict
match. Rational arithmetic avoids square-root rounding and tolerance patches.
Coordinates, radii and the threshold are bounded rational operands; missing
coordinates and inconsistent nominal adjacency are rejected.

Write A for output A, B for output B, E- for guaranteed edges and E+ for possible
edges. Two maximum-matching/vertex-cover certificates give:

```text
rank(B,E-) <= rank(B,E) and rank(A,E) <= rank(A,E+)
rank(B,E) - rank(A,E) >= rank(B,E-) - rank(A,E+).
```

For the upper bound, retain the edges of A's checked matching that remain
guaranteed. They form a matching in every admitted graph. Extend B's checked
cover to cover every remaining possible edge, adding either all uncovered left
endpoints or all uncovered right endpoints, whichever is smaller. This gives a
valid upper rank bound without another optimization call. Intersect both gain
bounds with the shared-output limits `-|A\B| <= gain <= |B\A|`.

Apply the existing nonnegative loss penalties and common anchor weights. These
are universal enclosures, generally not attained extrema. Equal endpoints prove
a constant value over the declared family. All possible edge combinations need
not correspond to geometric displacements: that makes the universal bound
conservative, and prevents an arbitrary edge-flip pattern from serving as a witness.

For a displacement proof, the checker instead verifies each rational shift is
inside its record's closed ball, applies one shared shift to all incident edges,
rebuilds every same-class adjacency and checks both matching/cover certificates.
Unlisted records remain at their declared centers. A witness returning a value
above tolerance does not establish robustness of the whole family.

Input and packet limits stay at 4 MiB and 16 MiB. The existing node/edge ceilings
remain, including a 2,048-edge limit per possible anchor graph. The 2,000,000-work
ceiling includes all geometric pair comparisons and matching estimates. Explicit
displacements also charge their additional graph reconstruction. No limit was raised.

## Development results

The source join checks every anchor, output membership, reference ID, weight,
loss and nominal edge against the previously sealed forty-frame geometry source.
Coordinates are its exact decimal values. Original sensor/prediction preparation
is not replayed here. The first/second native exchange contains normalized graphs
without the corresponding coordinate premise; those cases are not assigned
invented coordinates or counted as geometric results.

| Per-record radius | Engine improvement enclosure | Engine result |
|---|---|---|
| 0 m | [51/20, 51/20] | Robust; constant |
| 0.10 m | [9/5, 63/10] | Robust |
| 0.25 m | [1/2, 229/20] | Robust |
| 0.50 m | [-57/20, 153/10] | Unresolved |
| 1.00 m | [-129/10, 361/20] | Unresolved |

The research solver reports robustness at 0.50 m for this unit; the new simple
bound does not establish that stronger result. At 1 m the research report itself
retains an unrealized relaxed counterexample. Neither difference is converted
into an Engine geometric counterexample. These methods have different proof
strength and no equal-result speed comparison is claimed.

Both synthetic failure controls produce an unresolved [-1,1] enclosure and a
separately checked admitted displacement with value -1. The previous 372-label
minimum confirmation packet still passes the unchanged deletion checker.

The [verification record](../research/perception-revision/0.1.0/localization-verification.json)
binds nine result cases, eighteen packets, eighteen fresh-process CLI commands,
source joins, controls and validation. All 512 repository tests and 93 measurement
tests pass. Eleven geometry tests include 2,500 independently computed grid-loss
challenges, closed-circle boundary controls, general replacements, unequal weights,
malformed inputs, proof mutations, work limits and producer-disabled checking.
The grid challenges can falsify enclosures; the mathematical argument supplies
continuous coverage. The first measurement-test command used a nonexistent test
directory and failed before discovery; the corrected command and first failure
are both retained. Final resource-accounting checks and assay use fresh identities.

## Next consumer action

Repair the research boundary and residual-measurement semantics, then retain
the actual displacement vectors and complete audit histories in a fresh sealed
return. Use this checker as a conventional stopping baseline where it resolves
the decision, and preserve stronger solver claims as a separate tier until their
proof is checked. Count real acquired measurements, residual uncertainty and
complete costs; reference positions do not become exact because a policy queries them.

Private checkpoint:
`~/.codex/reports/reiyah/engine-localization-certificates-2026-09-17-0ynsueeo/`.
Read PLAN, source snapshots, both probes, final assay, closeout and packet seal.
This work adds no model inference, cloud compute, physical control, human audit,
post or outreach. Gate A remains operator-unaccepted. Scientific novelty, reduced
total validation cost and frontier superiority remain unestablished.
