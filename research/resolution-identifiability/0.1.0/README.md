# Can the available observations justify a decision

Document ID: `reiyah.resolution-identifiability`. Version: `0.1.0`.

Lifecycle status: `exploratory`. Date: 11 October 2026.

**Check whether a decision can be resolved before optimizing which observation
to request.** This standalone offline control checks that question for a finite,
explicit model of possible worlds, acceptable decisions and joint observation
outcomes. It returns a decision for each complete observation or a concrete set
of compatible worlds that rules out any common acceptable decision.

This is a conditional mathematical capability, not a physically qualified review
process. No actual observation channel, engineering comparison packet, human
work saving or product advantage is established. The mathematical basis is
established decision-region reasoning; no algorithmic novelty is claimed.

## Why this question matters now

The [earlier comparison](../../value-disproof/0.1.0/README.md) uses hypothetical
answers and shows parity with an equally equipped conventional process. The
[threshold screen](../../threshold-reference-screen/0.1.0/README.md) discloses
image reference policies hypothetically; an image review has not been shown to
reveal such a policy. Neither exercise qualifies a real resolution action.

The [earlier planner-consumption review](../../perception-plan-consumption/0.1.0/README.md)
already recognizes finite geometry ambiguity and preserves failures of an
external checker. This study does not replace or repair that dependency. Its
specific extension of the research question is joint, possibly ambiguous
response support and overlapping acceptable decisions. No sibling code or
new product integration is introduced.

Three existing public contact threads were read once for this continuation.
There was no new response after Daniel's requests: zero evaluator comments,
three RF-DETR comments ending with his request, and zero automotive comments.
Exact read metadata and digests are in [sources.json](sources.json). The
[upstream report](../../../docs/maintainer-reports/evaluator-populations-2026-10-11.md)
is already sent; no additional contact was made.

## Finite observation contract

Let W be a nonempty finite set of admitted worlds, D a nonempty finite decision
set, and Q a finite list of available read-only queries. Each world w has:

- A nonempty set A(w) of acceptable decisions.
- A nonempty finite set S(w) of complete joint response vectors, one response
  for every query in Q.

The vectors are complete declared supports. They can preserve correlation,
repeat-review dependence and explicit `unresolved` responses. No independence
assumption, probabilities or imputed point answers are supplied. Repeated
measurements must be represented explicitly within the joint model.

All listed queries must be obtainable and must reveal coordinates of the same
static realization, regardless of order. This excludes interventions that
change the world, unavailable tests, unmodeled history-dependent responses and
an unlimited stream of new measurements. A stochastic confidence guarantee
under a separately justified error distribution is a different question.

For any complete response vector x that occurs in at least one support, define:

```text
C(x) = {w in W : x belongs to S(w)}
J(x) = intersection of A(w) over w in C(x)
```

A guaranteed decision policy exists **if and only if J(x) is nonempty for every
admitted x** under this contract.

**Sufficiency.** Obtain all finitely many query responses and choose a decision
in J(x). Every world compatible with the actual response permits that decision.
This establishes existence, not the cheapest policy.

**Necessity.** Suppose an admitted x has empty J(x). Every world in C(x) permits
that entire response vector. Any adaptive policy receives the same answer to
each query along that realization, so its terminal decision cannot be acceptable
in every compatible world. Early stopping cannot add information. Randomization
cannot give a probability-one acceptable decision when the common set is empty.
The argument concerns a fixed finite query list and complete declared supports.

`not_guaranteed_resolvable` means at least one admitted response leaves a
conflict. Other responses may still permit a justified decision. It does not
mean that every actual review must fail. A resource limit raises an error; it
is never reclassified as such an impossibility certificate.

## Two controls that prevent misleading shortcuts

**Preserve correlation.** In one control, world A allows joint responses 00 or
11, and world B allows 01 or 10. Each question separately can answer 0 or 1 in
either world. Together they resolve A versus B in two observations. Replacing
the supports with products of their marginals invents additional responses and
loses that conclusion. Such an enlarged model is conservative for a positive
certificate; its obstruction does not prove impossibility in the smaller model.

**Pairwise agreement is insufficient.** Three worlds have acceptable decisions
{A,B}, {B,C} and {A,C}, and all yield the same observation. Each pair shares an
acceptable decision, but no decision works in all three worlds. The checked
obstruction therefore needs all three worlds. The emitted obstruction is
irredundant: removing any member restores a common decision. It is not advertised
as a minimum-cardinality obstruction in arbitrary cases.

| Authored case | Verified conclusion | Minimum worst-case observations in the declared model |
| --- | --- | ---: |
| Hidden policy, same image-review response | No guaranteed resolution | Undefined |
| Same case with a distinguishing policy record | Resolvable | 1 |
| Correlated two-question responses | Resolvable | 2 |
| Repeated review can remain jointly unresolved | No guaranteed resolution | Undefined |
| Different worlds permit the same decision | Decision already justified | 0 |
| Three overlapping decision sets | No guaranteed resolution; three-world obstruction | Undefined |
| Some responses resolve, one remains ambiguous | No guaranteed resolution | Undefined |
| Conflicting worlds, no available questions | No guaranteed resolution | Undefined |

These counts come from a separate exhaustive decision-tree oracle. They are
hypothetical finite-query counts, not observed reviewer effort or an optimized
Reiyah-versus-conventional comparison.

## Implementation and challenge

The [producer](analyze.py) groups full response vectors, preserves exact world
membership and computes common acceptable decisions. The [checker](verify.py)
independently validates inputs, enumerates adaptive decision trees, reconstructs
terminal membership and checks every obstruction. It imports no producer code.
Both consume the same authored premises; this is not independent scientific
review or evidence that the premises cover physical reality.

The [frozen protocol](protocol.json) and [eight cases](cases.json) preceded
execution. Their outcomes were anticipated; this is neither a blind experiment
nor a preregistered empirical study. The final [verification](verification.json)
checks 16 terminal cells. The [challenge](challenge.py) covers every model in two
small finite families:

| Family | Models |
| --- | ---: |
| Three worlds, two deterministic binary queries, all nonempty subsets of three decisions | 21,952 |
| Three worlds, one binary query with nonempty set-valued responses, same decision subsets | 9,261 |
| Total | 31,213 |

The terminal-cell criterion and independently searched adaptive trees agree
throughout. Every terminal membership, acceptable set and obstruction is also
checked. These are dependent authored configurations, not 31,213 empirical
trials or a general proof of implementation correctness. The mathematical
argument above provides the general finite-model criterion.

All **28 malformed-input and forged-result controls reject** for their expected
reason. They cover empty worlds/supports, incomplete or null responses, duplicate
identities/properties, unsupported observation models, false decisions, invented
or incomplete witnesses, omitted cells, changed digests and fabricated physical
qualification. The [challenge result](challenge.json) retains every reason.

Manual review found that the initial checker trusted input structure and could
accept a vacuous zero-world result even though the producer refused that input.
The failure and original scripts/results remain in private custody. Independent
checker input validation and nine additional rejection controls repaired it;
the entire finite-family challenge then passed again. The scientific cases and
protocol were unchanged. Three producer outputs are byte-identical.

The interface rejects unknown properties and duplicate JSON properties. It
allows at most 64 cases, 32 worlds per case, 16 decision IDs, 8 queries, 256
vectors per world and 2,048 vectors per case, within a 2-MiB input. The oracle
and terminal enumeration each have a 65,536-state/candidate limit. Exceeding a
limit refuses calculation; it does not supply a scientific conclusion.

## Research basis and source custody

Golovin, Krause and Ray's [NeurIPS 2010 paper](https://proceedings.neurips.cc/paper_files/paper/2010/file/1e6e0a04d20f50967c64dac2d639a577-Paper.pdf)
models hypotheses and joint test outcomes, including correlated noise, for
Bayesian test selection. Its cost guarantees require its own probabilistic
premises; they are not transferred here.

Javdani and colleagues' [AISTATS 2014 publisher record](https://proceedings.mlr.press/v33/javdani14.html)
describes overlapping decision regions and the goal of placing all consistent
hypotheses within one such region. This motivates retaining acceptable-decision
sets instead of forcing every world into a single decision class. We do not
implement or claim the performance guarantees of their HEC algorithm.

The complete first paper and second publisher page are retained privately with
byte identities in [sources.json](sources.json). The latter page records
publication on 2 April 2014 and the conference on 22–25 April. Its full PDF
exceeded the retrieval cap: one bounded response was not preserved; a second
1,572,865-byte prefix is retained as incomplete and evidence ineligible. The
abstract/bibliographic page supplies the limited attribution above. No paper
payload is redistributed, and no incomplete PDF is claimed as fully read.

## Reproduce offline

Python 3.10 or newer, standard library only. The retained run used Python 3.14.2
on macOS arm64 with network access denied before the interpreter started. No
images, model weights, third-party code, installation or inference is required.
Use a new output directory:

```sh
reiyah_study=research/resolution-identifiability/0.1.0
reiyah_run=/absolute/path/to/new-run
mkdir "$reiyah_run"
python3 -B "$reiyah_study/analyze.py" --cases "$reiyah_study/cases.json" \
  --output "$reiyah_run/result.json"
python3 -B "$reiyah_study/verify.py" --cases "$reiyah_study/cases.json" \
  --result "$reiyah_run/result.json" --output "$reiyah_run/verification.json"
python3 -B "$reiyah_study/challenge.py" --cases "$reiyah_study/cases.json" \
  --result "$reiyah_run/result.json" --output "$reiyah_run/challenge.json"
cmp "$reiyah_run/result.json" "$reiyah_study/result.json"
cmp "$reiyah_run/verification.json" "$reiyah_study/verification.json"
cmp "$reiyah_run/challenge.json" "$reiyah_study/challenge.json"
```

See [environment](environment.json) and [provenance](provenance.json) for scope,
source accounting, script/result bindings and the retained initial failure.

## Next evidence needed

Before any real comparison uses this criterion, justify its acceptable decisions,
complete world family, available actions and joint response supports. An empty
intersection is a conditional obstruction, not proof that a real reviewer could
never help. A nonempty one does not authenticate a sensor, annotation or reviewer.
Do not append an always-permitted abstention action and call the original
comparison resolved; abstention remains an explicit unresolved task outcome.

The next step is to qualify an actual resolution channel for a fresh consequential
decision, with complete work records and an equally equipped conventional
comparator. The upstream packet request remains open. This bounded mathematical
control is complete; another synthetic sweep would not supply those missing
premises. Broad product expansion remains stopped pending demonstrated value,
Gate A remains operator-unaccepted, and the closed images and comparison pairs
remain closed.
