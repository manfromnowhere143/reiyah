# Recorded reviewer identities and majority decisions

Document ID: `reiyah.reviewer-identity-sensitivity`

Version: `0.1.0`

Lifecycle status: `exploratory`

Date: 11 October 2026.

In a released Cityscapes annotation sample, the raw strict-majority outcome
survives every permitted one-response-per-reviewer-ID interpretation for
**996 of 1,000 objects with a proposed class and 988 of 1,000 without one**.
No ordinary class majority can switch directly to another ordinary class.
This quantifies the effect of one recorded-identity policy on a reference
decision. It does not establish independent voters, physical truth or detector
performance.

Reiyah's earlier qualification found repeated reviewer identifiers in this
sample. A repeat count alone does not show whether a decision changes. This
study supplies the missing conditional calculation, using the complete selected
file and preserving both annotation procedures. The conventional solution is
elementary counting and capacitated matching; no proprietary algorithm,
novelty or work-saving advantage is claimed.

## Question and scope

For each object and procedure, compare two explicitly different policies:

1. Count every stored response entry once. A class has a strict majority only
   when its count exceeds half the number of entries.
2. Group entries by their exact recorded reviewer ID. Retain exactly one of
   that ID's observed class responses, and consider every such choice.

The second policy is a sensitivity family, not a correction declared to be
right. An ID is not an authenticated person; repeated entries may reflect
legitimate repeated tasks. The records do not establish which response is
authoritative or its chronological position. Responses outside the observed
support, ID aliases and other identity errors are outside this family.

`cantsolve` remains an abstention response. A `cantsolve` majority and
`no_strict_majority` are separate unresolved outcomes. Neither becomes a
physical object class, a missing object or a successful negative observation.
The raw-entry comparator is our specified calculation, not the authors'
final bias-corrected or postprocessed reference.

The [protocol](protocol.json) was frozen before this calculation. Source
structure and prior repeat counts were already exposed. This is exploratory
qualification, not a blinded test or a preregistered performance study.

## Complete results

| Object-level quantity | Proposed class | No proposal |
| --- | ---: | ---: |
| Objects evaluated | 1,000 | 1,000 |
| Objects containing a repeated reviewer ID | 123 | 240 |
| Objects with conflicting responses under an ID | 38 | 35 |
| Raw outcome invariant under every allowed choice | 996 | 988 |
| Raw outcome not invariant | 4 (0.4%) | 12 (1.2%) |
| One normalized outcome, different from raw | 2 | 9 |
| Multiple attainable normalized outcomes | 2 | 3 |
| Ordinary majority can switch to another ordinary class | 0 | 0 |

All 15,994 proposed-class and 11,000 no-proposal response entries are included.
The percentages describe these finite object records. They are not population
estimates, error rates or independent sample proportions.

The changes have different meanings:

- With a proposed class, two car majorities can lose their strict majority;
  one no-majority outcome becomes a car majority; one `cantsolve` majority can
  become no strict majority.
- Without a proposal, one person majority and one train majority can lose
  their strict majority; ten `cantsolve` majorities can become no strict
  majority.

Thus eleven of the sixteen affected procedure-object records change between
two unresolved outcomes. The other five affect whether an ordinary class has
a strict majority. These are sixteen records across two procedures, not a
claim about sixteen distinct objects or observed label corrections. Some
changes are possible in only part of the family. The
[result](result.json) gives every raw-to-attainable outcome pair and distinguishes
possibility from a uniquely determined change.

The 1,000 objects occupy 388 image groups and form an object sample, not
complete image annotations. The sample cannot supply a full-image false-positive
or false-negative denominator. IDs recur across objects and procedures, so
neither iid-vote inference nor a causal comparison of the two procedures follows.

## Exact calculation and joint feasibility

Let `S_r` be the nonempty set of classes recorded for reviewer ID `r` within
one object and procedure, and let `n` be the number of such IDs. An allowed
world chooses one class `x_r` from each `S_r`.

For any class `c`, its sharp count bounds are:

```text
lower(c) = number of IDs whose support is exactly {c}
upper(c) = number of IDs whose support contains c
```

Both endpoints are attained: choose an alternative to `c` wherever possible
for the lower endpoint, and choose `c` wherever possible for the upper endpoint.
A strict majority for `c` is possible exactly when `2 * upper(c) > n`, and
universal exactly when `2 * lower(c) > n`.

Marginal bounds alone do not establish whether no strict majority is possible.
For example, three IDs each supporting `{A, B}` have no universally winning
class, but every allowed world has a strict majority. Averaging A and B would
create a tie that no allowed one-response-per-ID world realizes.

A no-majority world assigns each ID to an allowed class with capacity
`floor(n/2)` per class. The producer solves this ordinary bipartite matching
problem by expanding class capacities into slots. A separate counting check
tests every subset `T` of the class vocabulary:

```text
number of IDs with S_r contained in T <= floor(n/2) * number of classes in T
```

These inequalities are necessary because those IDs have nowhere outside `T`
to go. They are sufficient by the bipartite matching criterion: for any set
of IDs, take the union of their allowed classes as `T`. The displayed bound
supplies enough slots for that set. A failed inequality gives an explicit
obstruction; a successful assignment gives a no-majority witness. There are
only nine classes here, so the separate check examines at most 512 subsets
per object and procedure.

These are sharp statements within each declared response family. They are
not confidence intervals. Per-object witnesses are not asserted to form an
empirically supported model of a shared person's behavior across the sample.

## Verification

The [producer](reproduce.py) and a separately written
[direct-enumeration verifier](verify.py) agree on all 2,000 procedure-object
rows, all 18,000 class-bound pairs and all reported aggregate counts.
Enumeration visits 2,091 row-specific worlds, with at most four in any row,
and checks 2,005 outcome witnesses. This count is a sum of small per-row
families, not the size of a joint full-sample world space.

Six [unit tests](test_reproduce.py) include exhaustive comparison on 1,715
authored support problems with three classes and up to six IDs. The
[rejection checks](check_rejections.py) reject eleven alterations to source
identity, row membership, outcomes, bounds, assignments, matching obstructions,
repeat flags, numeric types and aggregate claims. Two final CPU reproductions produce
identical result and private witness bytes.

An initial replay comparison falsely rejected identical output because
integer histogram keys became strings after JSON serialization. The producer
now creates those keys as strings. The failed run is retained; the protocol,
numeric findings and witness bytes did not change. The
[verification record](verification.json) binds the final source and outcomes.
A prepublication check also exposed Python's equality between `false` and zero
in the verifier. Exact JSON type comparisons now reject boolean and floating
values in integer count fields. The original failed control is retained;
the study's numeric findings are unchanged.
These checks were conducted by one investigator and do not constitute
independent scientific review.

## Reproduce on CPU

Python 3.10 or newer and the standard library suffice. Obtain the exact
[author-released sample](https://raw.githubusercontent.com/JonathanKlees/Uncertainty-aware-Object-Detection/f793379ad7a9760f71c18ba57b7ed71fa76a5e6c/our_datasets/unbiased_samples/Cityscapes_sample_with_unbiased_annotations.json)
under its terms, or reuse an existing matching copy. The input is 8,568,020
bytes; its SHA-256 is
`1eb5506f328316f46fa5a036486b05689f4d504602895b80c87ee8bda0e0dd1d`.
The command rejects different bytes before analysis.

From the repository root, choose the actual input path and a fresh output
directory outside public Git:

```sh
reiyah_votes=/absolute/path/Cityscapes_sample_with_unbiased_annotations.json
reiyah_run=$(mktemp -d)/run
reiyah_study=research/reviewer-identity-sensitivity/0.1.0
python3 -B "$reiyah_study/test_reproduce.py"
python3 -B "$reiyah_study/reproduce.py" \
  --data "$reiyah_votes" --output "$reiyah_run" \
  --expected "$reiyah_study/result.json"
python3 -B "$reiyah_study/verify.py" \
  --data "$reiyah_votes" --rows "$reiyah_run/private_rows.json" \
  --result "$reiyah_run/result.json"
python3 -B "$reiyah_study/check_rejections.py" \
  --data "$reiyah_votes" --rows "$reiyah_run/private_rows.json" \
  --result "$reiyah_run/result.json"
```

Keep `private_rows.json` outside public Git: it contains source identifiers
and the per-object witnesses. The public result contains aggregate counts.
The existing input was reused; no images, weights, models or new annotations
were acquired. Runtime measurements exclude research, acquisition, preparation
and human review. They do not measure complete work or savings.

## Consequence for Reiyah

The repeated-ID warning is now quantified. It supports carrying a bounded
reference-policy ambiguity where that policy matters, rather than silently
counting entries as independent humans or discarding the whole file. The
observed stability does not qualify voter independence or physical labels.

This is a separate observation-qualification result. It neither admits a
detector-value experiment nor rescues earlier comparisons that showed parity.
A complete paired-output packet, justified reference-resolution process,
compatible decision and measured complete costs are still needed. The full
HARBOR mission remains the research objective; broad product expansion remains
stopped pending demonstrated value.

The source is the pinned release associated with Penquitt, Klees, van Betteray,
Jashnieh, Stehr, Rottmann and Schmarje,
[*Object Detection Benchmarks are Incomplete: The Role of Label Errors and Annotation Uncertainty*](https://arxiv.org/html/2609.21822v1),
arXiv v1, 18 September 2026. Its
[license statement](https://github.com/JonathanKlees/Uncertainty-aware-Object-Detection/blob/f793379ad7a9760f71c18ba57b7ed71fa76a5e6c/README.md#license)
applies CC BY-SA 4.0 to created annotations; underlying datasets retain their
own terms. No annotation, paper or upstream-code payload is redistributed here.
[Provenance](provenance.json) records exposure, input custody and scope.
