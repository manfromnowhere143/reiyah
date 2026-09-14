# Comparator 0.2.0: eight corrections, and the Engine's actual answer

Date: 2026-09-14. Lane: independent research. Lifecycle status: `proposed`.

Successor to [`ORDINARY_COMPARATOR_2026-09-14.md`](ORDINARY_COMPARATOR_2026-09-14.md), which is
retained unchanged apart from a pointer to this page. Its artifact
`research/comparator/0.1.0/end-to-end.json` is retained unchanged as well.

Artifacts: [`research/comparator/0.2.0/end-to-end.json`](../research/comparator/0.2.0/end-to-end.json),
[`research/comparator/0.2.0/CORRECTIONS.json`](../research/comparator/0.2.0/CORRECTIONS.json),
[`research/preparation-robustness/0.4.0/PREMISE_CORRECTIONS.json`](../research/preparation-robustness/0.4.0/PREMISE_CORRECTIONS.json)

Seven of the defects below were found by the Engine consumer review of 14 September 2026 and
reproduced here on the exact selected source before anything was changed. The eighth was found
here, by a fixture retained to repair the second. The first failures are retained.

## The Engine's actual answer, on the real comparison

The Engine exported its fixed comparison in this lane's own case shape. It is another owner's
private export and its detection identifiers are source derived row references, so no byte of it
is copied into this repository. What is recorded is the digest that binds the bytes, the
structure in counts, and the result both checkers accept.

| anchor | reference | base detections | additions | weight |
|---|---|---:|---:|---|
| `window-0001` | open | 48 | 9 | 1/2 |
| `window-0002` | open | 37 | 7 | 1/2 |

Case SHA-256 `8e79f3636ef337d7ea2f12ec213e67106d7d4afce55bdafb6c63ba10d667f299`. Loss 1 and 1,
tolerance 1/10. Admitted joint readings: **zero**. The enclosure is `[-8, 8]`, the criterion is
`unresolved`, and the observation state is `waits_on_a_reference` naming both anchors.

This is the real result and it replaces the old `open-two-anchor` fixture as the thing this lane
points at. The fixture had generic identifiers and no base detections; it reproduced the count
bound, not the comparison. No reading is admitted, no object is invented, and no human reference
is created. An empty `joint_worlds` list is not an assertion that the scene is empty.

## The eight corrections

### C1. The packet's source binding failed

Seventeen of eighteen payloads in the comparator 0.1.0 outbox came from the distributed commit.
`LANE_STATUS.json` was generated at seal time, 5,064 bytes, and declared under a repository path
that holds 2,896 different bytes at that commit. One blanket sentence covered all eighteen, so
the whole packet's source binding was false.

Two things were wrong: a stale `LANE_STATUS.json` was left committed at the repository root, and
the manifest asserted an origin instead of establishing one. The repair is mechanical.
[`tools/measure/seal_outbox.py`](../tools/measure/seal_outbox.py) classifies every payload as
`committed` or `generated`, compares each committed payload byte for byte against its blob at the
declared commit, and **refuses to write a manifest at all** when one does not match. No sentence
in the new manifest speaks for every payload at once. The old outbox is not rewritten.

### C2. An open reference is not always an outstanding question

A cohort with a finite anchor of weight 9/10 contributing `+9/10` and an open anchor of weight
1/10 contributing `[-1/10, 1/10]` has enclosure `[4/5, 1]`. At tolerance 1/10 the criterion is
already `supported` across the whole open interval. Version 0.1.0 reported
`waits_on_a_reference` and said the decision waits. Both checkers accepted it.

Nothing is waiting there. Sending a validation lead to look for evidence that cannot change the
answer is the opposite of the point of this lane. The criterion is now read first. The new
`already_decided` state preserves the open anchors and their contribution, names what it settles,
and says plainly that a settled criterion is neither physical certainty nor the preference
output, which can remain unresolved while the criterion is not. The case is retained at
`research/cohort-packet/0.1.0/settled-with-open-reference-case.json`.

### C3. The checker returned before checking

On an unchanged, valid open packet, version 0.1.0 accepted invented open anchor names, a false
`supported` criterion, an invented certified observation list, and any unknown field. It did so
because the open state returned as soon as it saw an open contribution, and everything after that
point was never reached. An early return that skips validation is the same defect as no
validation, and this lane has been caught by that shape before.

Every state now runs the same checks first: a whitelist of fields this checker knows, then the
criterion, the preference, the packet state and the open anchor names recomputed against the
packet, then the state specific semantics. Thirteen forgeries are retained as tests, including the
three the consumer supplied.

**What this checker requires the packet checker to establish.** It reads the packet's reported
certificates and recomputes world values from them. It does not verify that a reported matching
uses real edges, that a cover covers them, or that the enclosure is the range the worlds support.
Those are `check_cohort_packet`'s obligations. Verifying a packet does not verify a separate
report about it, and verifying a report does not verify the packet.

### C4. A searched optimum is not a certificate

Replaying the same 1,400 generated cases gives 683 already decided, 386 with a shortest list and
331 bracketed. Of the 386, **378** have a packing that meets the cover and **8** do not. The first
exception is size 4, seed 9, where the search finds 2 and the packing forces only 1. Version
0.1.0 counted the state name as the certificate and reported 386.

| state | count |
|---|---:|
| already decided | 683 |
| certified shortest | 378 |
| searched shortest | 8 |
| bracketed | 331 |

The certified share is **378 of 717** cases that needed a list, not 386 of 717. `covered` is
replaced by two states so an aggregation cannot read a name as a certificate again.

### C5. The implemented checker is not linear

Checking a supplied cover against supplied separating sets is linear in their total size. The
implemented checker does not trust the supplied sets. It recomputes them from the packet, which
compares every pair of admitted readings, discordant or not.

| discordant pairs | admitted readings | pair verdict comparisons | supplied certificate atoms |
|---:|---:|---:|---:|
| 8 | 9 | 36 | 1 |
| 16 | 17 | 136 | 1 |
| 32 | 33 | 528 | 1 |

These are traced operation counts, not timings. The cost is kept deliberately: a checker that
trusted the reported separating sets would accept a report omitting a discordant pair, which is a
forgery this lane already retains. The unqualified linear time wording is withdrawn; the
implementation is not optimised, because no measured consumer cost justifies that work.

### C6. Equal totals are not equal members

Version 0.3.0 grouped preparations by population and five kept counts. Two different row sets can
share those totals, so that established 33 aggregate signatures and not 33 verified preparations.

Membership is now computed over exact source rows. The declared predicates are reconstructed and
accepted only because they reproduce **all 48 recorded populations exactly**; each label's
selected index sequence is digested and compared. The result is the same 33, now earned:

- 48 labels, 33 distinct memberships, 15 duplicate groups, 30 rows inside one.
- No aggregate group is unconfirmed by membership, and membership finds no duplicate the
  aggregate grouping missed.
- The mechanism is confirmed rather than assumed: the cache reaches 49.998 metres and no further,
  so `within_50m` selects every row; and **0** static furniture rows lie beyond 30 metres, so
  excluding them changes nothing there.
- A control is retained with equal counts and disjoint members. The aggregate grouping merges it;
  the membership grouping keeps it apart.

48 labelled runs and 33 unique memberships are different denominators. Neither supplies
independent trials, and the preregistered family of 48 labels is unchanged.

### C7. The Pillow claim was wrong

Comparator 0.1.0 reported that 125 repository tests errored on a Pillow dependency "absent from
every interpreter on this machine". Four interpreters on `PATH` lack it. The runtime supplied with
the Engine packet has Pillow 12.3.0, and on it **all 309 repository tests pass**. The claim was
overbroad and is withdrawn.

### C8. Found here: a decisive verdict does not pin the value to a point

The fixture retained for C2 was picked up by the admission sensitivity sweep and broke two of its
assertions. That document's central sentence, already retracted once, said that every decisive
verdict this lane had produced was carried entirely by the admission decision, pinning the
enclosure to a point with an asserted share of `1`.

That was true of the four decisive cases retained at the time. It is not a property of a decisive
verdict. Two cases now show otherwise:

| case | anchors | enclosure | coarse bound | asserted share | criterion |
|---|---|---|---|---|---|
| `decisive-interval-case` | all finite | `[1, 3]` | `[-3, 3]` | 2/3 | supported |
| `settled-with-open-reference-case` | one open | `[4/5, 1]` | `[-1, 1]` | 9/10 | supported |

The first has no open anchor, so the open reference is not the explanation. Both readings support
the addition at different values, and the enclosure is an interval the verdict holds across.

What survives is the monotonicity the finding actually rests on: removing admitted readings can
only narrow the enclosure and admitting more can only widen it, so a decisive verdict still rests
on the claim that the admitted set is complete, and no evidence inside the cohort supports that
claim. The document is retracted to version `0.3.0` and both counterexamples are retained.

## What survives

The finite reading equivalence, on the binary improvement criterion over a nonempty complete set
of admitted readings. The selected 56 to 7 atom count across the eight cases. The cover and
packing certificate where the two meet, including the 32 disputed atoms of
`sixteen-candidates-plan-case` reduced to one certified atom with no search. The measured
verification crossover between 30 and 90 detections. The strict cutoff tie rule and the 22 object
granularity obstruction, scoped to the declared uniform cutoff and the retained matched score
cache.

## What is still not earned

No person has run either method. A shorter list of abstract atoms is not measured human value.
The cover argument concerns a fixed list of perfectly answerable binary atoms with equal cost over
a fixed set of readings; it is not an adaptive depth theorem, not a proof that an atom is
observable, and not a minimum of human work. The adaptive versus fixed counterexample stands
against any claim otherwise. A competent analyst can compute the same cover from the same
readings, recognise a settled criterion, and use ordinary source tracing tools.

Both references remain open. The decision remains `[-8, 8]`. The next evidence is actual
inspection, which this lane does not own.
