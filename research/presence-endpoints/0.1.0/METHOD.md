# Existing-path conversion method, 0.1.0

Status: exploratory authored compatibility study. This reuses an implemented
monotone audit solver; it does not introduce a new matching theorem or solver.

For each guarded object there is either an unconditional presence premise or
one positive variable used for that object alone. The model has no clauses and
edges are fixed. Each relevant Boolean assignment therefore corresponds to
exactly one deletion subset of optional objects, and each such subset has an
assignment. Unused variables only duplicate the same graph and are discarded.
Retain mandatory objects through explicitly hypothetical, derived premises.
Bind those premises and the new context to the complete original authored case.

The conversion changes representation, not the admitted reference sets. All
matching graphs, fixed outputs, source IDs, weights, penalties and tolerance
are otherwise preserved. The existing monotone path calculates matching and
cover witnesses at two extremal object sets. Its separate checker establishes
exact finite-family bounds when the full free-deletion set is within budget.
This study sets that budget to the number of optional objects. It does not
change the actual engine, its caps, or any historical source/protocol bytes.

The independently implemented conventional path reads the original case. It
uses existing SciPy assignment code at its all-false and all-true endpoints,
constructs vertex covers, and checks matching/cover equality. The truth checker
for the small grid enumerates full original worlds and partial injections and
calculates both absolute losses before subtraction. It does not use a matching
producer. A separate conversion check reconstructs target fields without calling
the conversion function. The stored-result checker runs with the engine's
endpoint producer and matching-proposal entry points disabled.

The two exact bounds are translated using the original strict tolerance rule.
Audit 'insufficient' says the premises do not establish universal improvement;
it does not say the added detector is worse. Bounds crossing the tolerance may
remain unresolved as a detector preference even when audit insufficiency has
a valid counterexample.

All512small cases and six larger authored cases are fixed before execution.
The large cases change representation beyond the old assignment cap. They do
not evaluate physical correctness or new observations. Source IDs in these
fixtures bind authored records, not a sensor or model run. One author, the same
original parser, rational format, and installed runtime remain shared trust.
Baseline equality is retained. Timings have different explicit workflow scopes
and one fixed order, so they do not establish general speed superiority.

Reject non-synthetic inputs, correlations, clauses, negative/conjunctive object
conditions, conditional edges, open/missing data and invalid contracts. Broader
families may require different mathematics and evidence semantics; never admit
them by silently relaxing the conversion guard.
