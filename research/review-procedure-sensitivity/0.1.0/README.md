# Does the review procedure change the decision?

Document ID: `reiyah.review-procedure-sensitivity`. Version: `0.1.0`.
Lifecycle status: `exploratory`. Date: 11 October 2026.

**For 133 of 1,000 recorded Cityscapes objects, proposed-class and no-proposal
review have incompatible strict-majority outcomes under every allowed choice
of one observed response per recorded reviewer ID.** Seventeen objects have
different ordinary class majorities. This is a result about two recorded
annotation procedures and a declared decision rule, not which label is true.

Reiyah needs to know what a review can resolve before optimizing which reviews
to request. The [earlier identity study](../../reviewer-identity-sensitivity/0.1.0/README.md)
checked whether repeated IDs affect the conclusion **within** each procedure.
Here the question is whether the procedures support the same conclusion for
the same object. The source and earlier results were already exposed. The
[protocol](protocol.json) fixes this new question and endpoints before the
paired calculation; it is exploratory, not blinded or preregistered.

## Complete paired results

All 1,000 objects, all 388 image groups, all 15,994 proposed-class responses
and all 11,000 no-proposal responses in the selected file are included.

| Relationship between normalized outcome sets | Objects |
| --- | ---: |
| Guaranteed same outcome within the declared family | 865 |
| Forced different outcomes within the declared family | 133 |
| Agreement depends on the allowed response choices | 2 |
| Total | 1,000 |

The 133 forced differences partition as follows. Direction means proposed-class
versus no-proposal procedure, not a temporal transition or causal intervention.

| Proposed-class outcome versus no-proposal outcome | Objects |
| --- | ---: |
| Different ordinary class majorities | 17 |
| Ordinary class versus unresolved | 83 |
| Unresolved versus ordinary class | 27 |
| Different unresolved outcomes | 6 |

The unresolved outcomes `cantsolve` and `no_strict_majority` stay distinct.
Neither is a negative detection or a physical class. In the private rows,
a winning-vote count is JSON `null` when no majority exists.

The forced differences occur in 113 image groups. Across all objects, 658 have
at least one recorded ID in both procedures; 124 of the 133 forced differences
have that overlap. These records do not justify independent-voter or independent
object assumptions, and an ID is not an authenticated person.

Counting every raw entry once gives 868 equal and 132 different outcomes,
including 18 different ordinary class majorities. Two of those 18 have at least
80% raw support for each of the conflicting labels; both remain ordinary-class
switches under every allowed ID choice. The 80% threshold was fixed in the
protocol. Vote share is not a probability that the physical label is correct.
The [result](result.json) includes the complete raw outcome transition table.

Every proposed-class stratum is retained, including the small ones:

| Proposed class | Objects | Forced differences | Forced ordinary class switches |
| --- | ---: | ---: | ---: |
| person | 331 | 40 | 7 |
| rider | 58 | 15 | 8 |
| car | 425 | 43 | 0 |
| truck | 4 | 1 | 0 |
| bus | 12 | 3 | 0 |
| train | 3 | 2 | 1 |
| motorcycle | 12 | 3 | 0 |
| bicycle | 155 | 26 | 1 |

These are finite-file counts. The strata do not establish population rates,
worst-group guarantees or differences attributable to the proposed class.

## Exact meaning of incompatibility

For object `i`, let `A_i` and `B_i` be the nonempty sets of attainable majority
outcomes in the two procedures. Within each procedure, group responses by their
recorded ID and choose exactly one observed response from each group. A category
wins only with strictly more than half of those votes. Otherwise the outcome is
`no_strict_majority`.

The previous counting and capacitated-matching calculation constructs each set.
The paired rule is elementary:

```text
Guaranteed same: A_i = B_i = {one outcome}
Forced different: intersection(A_i, B_i) is empty
Ambiguous agreement: all remaining cases
```

The comparison uses the Cartesian product as a sensitivity envelope, not a
probabilistic independence assumption. If the sets are disjoint, every pair in
any nonempty subset of that product still differs. Thus additional dependence
constraints cannot restore agreement while staying inside these supports.
If the sets overlap, agreement is possible in the envelope; the records do not
show whether a real behavioral coupling permits that pair.

The supports contain **observed** responses only. A new review can produce an
unobserved response. Cross-object behavioral constraints, reviewer aliases and
which repeat should count are not identified. Per-object possibilities must
not be promoted into an empirically established whole-sample world model.

The null proposition that both recorded procedures agree under every allowed
normalization is refuted for this file. This is neither a significance test
nor a finding that 133 physical labels are wrong.

## What this changes for Reiyah

A reference-resolution contract needs to name the review procedure, information
shown to the reviewer, response population, identity policy, aggregation rule
and unresolved states. Replacing one procedure with another can change the
reference decision while the object stays fixed. A count of completed reviews
alone cannot establish that a disputed decision has been resolved.

This study supplies an executable check of that premise on real response
records. It does **not** qualify a future review channel or demonstrate a better
selector. There are unequal response counts, overlapping IDs and no established
random assignment or task chronology. Sampling variation, reviewer composition,
presentation and other procedural differences are not separated causally.
The object sample is not complete image ground truth and cannot support a full
image detector denominator. No model scores, review costs or saved work are
calculated. The existing product-value decision remains unchanged.

Proposal-related annotation bias is already studied by the source authors;
their [postprocessing module](https://github.com/JonathanKlees/Uncertainty-aware-Object-Detection/blob/f793379ad7a9760f71c18ba57b7ed71fa76a5e6c/postprocess/README.md)
addresses biased distributions. Our calculation uses raw recorded votes and
our specified majority rule, **not their final postprocessed labels**.
No novelty, upstream defect or performance advantage is claimed.

## Verification and reproduction

The producer reuses the exact hash-bound identity calculation. A separately
written parser and exhaustive enumerator reconstruct every paired row and
aggregate from the original bytes. It visits 2,091 procedure-object response
worlds and agrees on all 1,000 paired objects. This is a sum of small per-row
families, not a joint sample-space size. The checker imports neither the
producer nor the earlier identity engine.

Focused software controls cover all 225 pairs of nonempty subsets of two
ordinary and two unresolved outcomes. Twenty-two negative controls reject
changed source bytes, broken joins, omitted or duplicated rows, false supports,
changed counts, undeclared fields, numeric type coercions and malformed JSON.
They are verification cases, not extra empirical observations.

Review after the first calculation replaced a zero placeholder with `null` for
the nonexistent winning count in no-majority rows. Public aggregate results did
not change. The original private run is retained. Final producer replays match
exactly. See [verification](verification.json), [controls](controls.json) and
[provenance](provenance.json). All checks are by one investigator; separate
implementations do not constitute independent scientific review.

Python 3.10 or newer and the standard library suffice. Reuse the exact
[author-released sample](https://raw.githubusercontent.com/JonathanKlees/Uncertainty-aware-Object-Detection/f793379ad7a9760f71c18ba57b7ed71fa76a5e6c/our_datasets/unbiased_samples/Cityscapes_sample_with_unbiased_annotations.json)
under its terms. The input is 8,568,020 bytes with SHA-256
`1eb5506f328316f46fa5a036486b05689f4d504602895b80c87ee8bda0e0dd1d`.
From the repository root, with a fresh output directory outside public Git:

```sh
reiyah_votes=/absolute/path/Cityscapes_sample_with_unbiased_annotations.json
reiyah_run=$(mktemp -d)/run
reiyah_study=research/review-procedure-sensitivity/0.1.0
python3 -B "$reiyah_study/reproduce.py" \
  --data "$reiyah_votes" --output "$reiyah_run" \
  --expected "$reiyah_study/result.json"
python3 -B "$reiyah_study/verify.py" \
  --data "$reiyah_votes" --rows "$reiyah_run/private_rows.json" \
  --result "$reiyah_run/result.json"
python3 -B "$reiyah_study/check_controls.py" \
  --data "$reiyah_votes" --rows "$reiyah_run/private_rows.json" \
  --result "$reiyah_run/result.json"
```

Keep the source and identifier-bearing output private. The source is the
pinned release associated with Penquitt, Klees, van Betteray, Jashnieh, Stehr,
Rottmann and Schmarje. The authors' [license statement](https://github.com/JonathanKlees/Uncertainty-aware-Object-Detection/blob/f793379ad7a9760f71c18ba57b7ed71fa76a5e6c/README.md#license)
applies CC BY-SA 4.0 to created annotations; underlying data retain their own
terms. No annotation, image, paper or upstream-code payload is redistributed.
No new scientific source was downloaded for this calculation.

This bounded study is complete. The next value experiment still needs a
consequential paired decision and a qualified observation process with complete
work records. Do not expand this exposed sample into selector development,
causal claims or another automatic analysis sweep.
