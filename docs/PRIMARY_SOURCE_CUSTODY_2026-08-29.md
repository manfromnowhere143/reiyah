# Primary-source custody for the dependence program

Document ID: `reiyah.gate-b.primary-source-custody-2026-08-29`

Version: `0.1.0`

Lifecycle status: `proposed`

## 1. Why this document exists

`docs/SOURCE_POLICY.md` holds that a URL is not retained evidence. Before this document, the
Gate B dependence results cited three mathematical-lineage sources and one safety-model
corollary that were never retrieved, never digested, and never bound to an exact proposition.
`tools/measure/result_k_evidence_cost_interval.py` carried the attribution
`RSS Corollary 3 gives P <= 6 c p^2` and the constant `RSS_BASELINE_N = 77460` with no ledger
entry anywhere in the repository.

This document records what was retrieved on 2026-08-29, what each source does and does not
support, and which prior claims must be withdrawn or narrowed as a result.

Retrieval was performed offline of the validation path, by direct document fetch. No retrieved
third-party payload is committed to this repository. Payload bytes are held outside the worktree
and are recorded here as pointer records with digests, consistent with RGA-019.

## 2. Custody states

| State | Meaning |
|---|---|
| `primary_retained` | Exact primary bytes retrieved, digested, and the cited proposition read in the primary text |
| `primary_pointer_only` | Exact bibliographic identity established from an authoritative catalogue, primary body text not retrieved |
| `third_party_unretained` | Only third-party description available; may not be used to characterise the source |
| `unavailable` | Retrieval attempted and failed; recorded with the exact failure |

## 3. Ledger

### S-01 Shalev-Shwartz, Shammah, Shashua 1708.06374

| Field | Value |
|---|---|
| Title | On a Formal Model of Safe and Scalable Self-driving Cars |
| Authors | Shai Shalev-Shwartz, Shaked Shammah, Amnon Shashua |
| Identifier | arXiv:1708.06374 |
| Versions | v1 2017-08-21; v2 2017-10-08; v3 2017-12-12; v4 2017-12-18; v5 2018-03-15; v6 2018-10-27 |
| Retrieved | 2026-08-29T19:33Z, PDF fetch of `https://arxiv.org/pdf/1708.06374` |
| Retained bytes | 1,325,278 bytes, `sha256:403a0545b3b9abe195193de990debcb5b4043765f58d7c02c869b9e826dce3bb` |
| Custody | `primary_retained` |
| Redistribution | Not redistributed here. Pointer plus digest only. |

Propositions the primary text supports, read in the primary body:

1. Definition 32, verbatim: "Two Bernoulli random variables `r1`, `r2` are called one side
   c-approximate independent if `P[r1 and r2] <= c P[r1] P[r2]`."
2. Corollary 3, verbatim: "Assume that for any pair `i != j`, the random variables `e_i^m`,
   `e_j^m` are one sided c-approximate independent, and the same holds for `e_i^g`, `e_j^g`.
   Assume also that for every `i`, `P[e_i^m] <= p` and `P[e_i^g] <= p`. Then,
   `P[e^m or e^g] <= 6 c p^2`."
3. The fusion scheme analysed is three sub-systems `s1, s2, s3` under a majority rule:
   "Situations which are non-dangerous according to the majority of the sub-systems (2 in our
   case) are considered safe."
4. The constant 6 arises as three sub-systems by a union bound over two mistake types. The
   intermediate step is `P[e^m] <= 3 c p^2`, and "The exact same derivation holds for the
   safety-critic ghost mistakes. By applying a union bound we therefore conclude" Corollary 3.
5. The validation-burden consequence, verbatim: "This corollary allows us to use significantly
   smaller data sets in order to validate the sensing system. For example, if we would like to
   achieve a safety-critic mistake probability of `10^-9`, instead of taking order of `10^9`
   examples, it suffices to take order of `10^5` examples and test each system separately."
6. The stated rationale for the independence assumption, verbatim: "Seemingly, camera and lidar
   have common sources of mistakes, both are affected by foggy weather, heavy rain or snow.
   However, the type of mistake for camera and lidar would be different, camera might miss
   objects due to bad weather while lidar might detect a ghost due to reflections from particles
   in the air. Since we have distinguished between the two types of mistakes, the approximate
   independency is still likely to hold."
7. The errors are `safety-critic` misses and ghosts, not detection misses in general: "a
   safety-critic miss is caused by a false negative while a safety-critic ghost is caused by a
   false positive", and "our comfort objective ensures we are far away from the boundaries of
   non-safe distances, and therefore reasonable measurement errors are unlikely to lead to
   safety-critic mistakes."

Propositions the primary text does NOT support:

1. It does not state a two-channel form of Corollary 3. The corollary is stated for a set of
   sub-systems with a pairwise assumption and a three-system majority fusion.
2. It does not state the constant `77460`. That number does not appear in the text. The text
   says "order of `10^5` examples."
3. It does not license applying `c` measured over all annotated objects to `c` in Definition 32,
   whose Bernoulli variables are safety-critic mistakes.
4. It does not attach a confidence level to "order of `10^5` examples", so it does not support
   quoting a sampling confidence interval on a derived example count.
5. It does not claim the independence assumption has been empirically validated.

Relation to Reiyah's estimand: Reiyah's `c_s = P_s(M_A and M_B) / [P_s(M_A) P_s(M_B)]` is the
smallest `c` satisfying Definition 32 for that stratum and that channel pair. The estimand is
therefore definitionally identical to the parameter of Definition 32 whenever the Bernoulli
variables are matched. Reiyah's Bernoulli variables are currently detection misses, not
safety-critic misses, so the populations differ and the values are not interchangeable.

### S-02 Weast 2020, arXiv:2009.03301

| Field | Value |
|---|---|
| Title | Sensors, Safety Models and A System-Level Approach to Safe and Scalable Automated Vehicles |
| Author | Jack Weast, Intel |
| Identifier | arXiv:2009.03301v1, 2020-09-04, dated 2020-09-09 in the document |
| Retrieved | 2026-08-29T19:22Z |
| Retained bytes | 1,235,612 bytes, `sha256:ae76b5b07f5e80c841b97b3cd093d3ec765f45bea3d638b0307485a0fc0b62a3` |
| Custody | `primary_retained` |
| Redistribution | Not redistributed here. Pointer plus digest only. |

Propositions supported, verbatim from the primary body:

1. "Let us say that the probability of failure for either sensing channel is p. As they are
   independent, the probability of them both failing at the same time is p2."
2. "the probability of two independent sensing systems failing at exactly the same time is the
   product of their independent failure rates, thus in this case the MTBF would be 108"
3. The two channels named are a camera-only subsystem and a radar-and-lidar subsystem, each
   assigned a `10^4` hour MTBF goal, combining to a claimed `10^8`.
4. The validation-burden claim: a per-channel `10^4` MTBF "can be achieved in a few months" with
   "a fleet of 100 vehicles operating concurrently", against a single non-independent channel
   needing `10^8`, "equivalent to driving 2 hours a day for 10,000 years".
5. The architectural contrast is explicit: a fused camera-radar-lidar single channel has
   "redundancy in terms of overlapping fields of view between sensing types" but "there is no
   independence between the sensing subsystems".

Propositions NOT supported: no empirical estimate of the dependence between the two subsystems
is given, and no sensitivity of the `10^8` figure to dependence is computed.

Relation to Reiyah's estimand: this is a company-authored primary statement that the product of
marginals is the operative arithmetic for a camera channel against a range-sensor channel. Under
Definition 32 the correct expression is `c` times the product, so the claimed combined MTBF is
overstated by a factor `c` whenever `c > 1` on the relevant population.

### S-03 Knight and Leveson 1986

| Field | Value |
|---|---|
| Title | An Experimental Evaluation of the Assumption of Independence in Multiversion Programming |
| Authors | John C. Knight, Nancy G. Leveson |
| Venue | IEEE Transactions on Software Engineering, volume 12, issue 1, pages 96 to 109, 1986 |
| DOI | 10.1109/TSE.1986.6312924 |
| Custody | `primary_pointer_only` |

Body text was not retrieved. A document fetched from a university course page was found on
inspection to be a **student seminar review of** the paper, not the paper. Its bibliographic
header and its transcription of the abstract are consistent with the catalogue record, but its
body carries a third-party critique and cannot be cited as primary. Experimental details that
appear only in that review, including institution split, test-case counts beyond the abstract,
and any test statistic, are `third_party_unretained` and MUST NOT be quoted.

The abstract, as transcribed by that third-party document and therefore not itself primary,
states that 27 versions were prepared from the same specification at two universities, subjected
to one million tests, and that "the number of tests in which more than one program failed was
substantially more than expected". Until the primary text is retrieved, Reiyah may cite only the
existence and title of this result, not its numbers.

A reply document authored by Knight responding to criticisms is hosted at
`http://sunnyday.mit.edu/critics.pdf`. Retrieval failed: `connect ECONNREFUSED` on HTTPS upgrade.
State `unavailable`.

### S-04 Eckhardt and Lee 1985

| Field | Value |
|---|---|
| Title | A Theoretical Basis for the Analysis of Multiversion Software Subject to Coincident Errors |
| Authors | Dave E. Eckhardt, Larry D. Lee |
| Venue | IEEE Transactions on Software Engineering, volume SE-11, number 12, pages 1511 to 1517, 1985 |
| DOI | 10.1109/TSE.1985.231895 |
| Related | NASA Technical Memorandum 86369, January 1985, titled "A theoretical basis for the analysis of redundant software subject to coincident errors" |
| Custody | `primary_pointer_only` |

Body text not retrieved. The volume, number, and page range above come from a bibliographic
search result and are not yet confirmed against an authoritative catalogue record. Until the
primary text is read, Reiyah MUST NOT attribute any specific functional form, and in particular
MUST NOT assert that Reiyah's scalar `c` is or equals this work's intensity function.

### S-05 Littlewood and Miller 1989

| Field | Value |
|---|---|
| Title | Conceptual modeling of coincident failures in multiversion software |
| Authors | Bev Littlewood (City University London), Douglas R. Miller (George Mason University) |
| Venue | IEEE Transactions on Software Engineering, volume 15 |
| Date | 1989-12-01 |
| DOI | `10.1109/32.58771`, confirmed from the NASA Technical Reports Server catalogue record 19900036555 |
| Custody | `primary_pointer_only`; NTRS records "There are no available downloads for this record" |

**DOI discrepancy, recorded rather than silently corrected.** The current work instruction cites
`10.1109/32.58788`. The NTRS catalogue record for this title and these authors gives
`10.1109/32.58771`. The two differ. This document uses neither as settled: the identity is
carried as title plus authors plus venue plus date, and the DOI is marked disputed pending an
authoritative check.

Catalogue-level content only: the record states that independently developed versions fail
dependently, and that diverse methodologies decrease the probability of simultaneous failure,
with better-than-independent behaviour theoretically possible. Because this is catalogue text
rather than primary body text, it may motivate a hypothesis but may not be cited as a theorem.

### S-06 to S-09 Standards

`ISO 26262-1:2018`, `ISO 21448:2022`, `ISO/TR 21959-1:2020`, and `ISO/PAS 8800:2024` are already
present in `evidence/source-ledger.json` as open-data metadata records under
`evidence/sources/iso-open-data-*.jsonl`. Their normative text is not retained and is not
quotable. Any crosswalk statement must be marked `unavailable-text`.

## 4. Bounded-search novelty statement

A bounded search was run on 2026-08-29 across web search for observational measurements of
cross-modality joint detection-failure dependence with clustered uncertainty and worst-group
inference. Queries covered correlated perception faults, coincident failure in multiversion
software applied to perception, joint miss rates on nuScenes, and worst-group dependence in
safety cases. The retrieved literature within that scope was corruption-injection and
sensor-degradation robustness benchmarking rather than observational dependence estimation.

The admissible statement is: **no prior instance was found in this bounded search.** That is not
a novelty claim. It records the search scope and its outcome. Absence of a found instance is not
evidence of absence.

## 5. Consequences for existing claims

| Prior claim | Disposition after custody |
|---|---|
| `RSS Corollary 3 gives P <= 6 c p^2` | **Confirmed verbatim** in S-01. Attribution was correct. |
| `RSS_BASELINE_N = 77460` described as "RSS's own worked example" | **Narrowed.** The number is not in the primary text. It is a Reiyah derivation from Corollary 3 at `P = 10^-9` and `c = 1`, consistent with the text's "order of `10^5` examples". It must be labelled a Reiyah derivation, not an RSS figure. |
| Evidence requirement scales as `sqrt(c)` | **Conditionally supported.** It follows from Corollary 3 given an added bridge `N proportional to 1/p` that the primary text uses only as an order-of-magnitude statement. The bridge must be declared. |
| Evidence-cost percentages with 95% intervals | **Withdrawn as stated.** See `docs/ESTIMAND_RSS_DEFINITION_32.md` section 6. |
| Reiyah's `c` equated to an Eckhardt and Lee intensity function | **Withdrawn.** No primary text retained. |

## 6. Non-claims

This document creates no scientific support, no operator acceptance, no standards or compliance
determination, and no comparative claim about any vendor. It records source custody only. No
third-party payload is committed. No released `1.2` byte is modified.
