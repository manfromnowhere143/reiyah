# Gate A Offline Validation

## Purpose

The Gate A validator checks static repository contracts. It does not train a model, run
inference, contact a network, process private data, evaluate real-world safety, or create an
acceptance decision.

## Reproducible entry point

From the verified Reiyah Git root:

```sh
python3 tools/validate_gate_a.py
```

When indexed architecture bytes intentionally change, rebuild the acyclic candidate index
before validation. The builder itself writes only to stdout; these explicit shell redirects are
the authorized mechanical update:

```sh
python3 tools/build_gate_a_index.py > gate/GATE_A_EVIDENCE_INDEX.json
python3 tools/build_gate_a_index.py --sidecar > gate/GATE_A_EVIDENCE_INDEX.sha256
python3 tools/validate_gate_a.py
```

The index excludes itself, its sidecar, the exact canonical report path, append-only operator
decision records, Git internals, and declared transient caches. Those exclusions and reasons are
stored in the index and checked against the validation plan. The validator inspects excluded
locations independently and accepts only the exact authorized filename, media, and record shape;
an exclusion is never a general hiding place. No other repository artifact may be silently
omitted. `evidence/sources/` must equal the source-ledger path set exactly.

Git implementation metadata is an explicit external trust boundary, not Gate A evidence or data.
Only `git rev-parse --show-toplevel` is consumed for repository identity; opaque `.git/` content is
not indexed, interpreted, or granted scientific, safety, acceptance, or publication authority.
Every other exclusion is content-constrained, and transient cache files are rejected if present.

The validation plan freezes the exact SHA-256 bytes of the only two authorized Python files: the
stdout-only index builder and the read-only validator. Both tools refuse a source mismatch before
accepting an index build or scope result. Static AST restrictions independently reject repository
writes, dynamic callable indirection, nondeterministic inputs, and every process/network call
except the exact Git-root query and the validator's exact builder invocation.

The command must:

1. refuse to run outside the canonical Reiyah root;
2. make no network requests and write no repository files;
3. validate normative JSON instances against pinned Draft 2020-12 schemas;
4. verify identifier references, release immutability metadata, retained-source digests,
   evidence-index digests, and required document inventory;
5. dispatch semantic checks over every scientific instance by schema identity, including global
   identifier/reference integrity, temporal ordering, evidence disposition, and belief-vector
   normalization;
6. run every fixture declared in `fixtures/fixture-catalog.json`;
7. require known-good fixtures to pass and known-bad fixtures to fail with the declared
   diagnostic code;
8. scan normative JSON for forbidden ambiguous null/zero coercions and unknown fields through
   schemas and semantic checks; and
9. emit stable, sorted diagnostics and a nonzero exit status on any failure.

Gate A `1.1.0` freezes the totals reported by its canonical evidence index and retained
validation report. The validator recomputes those totals from repository bytes rather than
trusting narrative counts. Every declared known-good fixture must pass, every declared
known-bad fixture must reject for its exact primary rule, and the control summary must show
GA-01 through GA-16 required, covered, and passed with no failed controls. GA-17 remains
external operator authority and is always `not_evaluated` by the offline validator.

The historical Gate A `1.0.0` report covered 25 schemas, 122 normative instances, 91 fixture
cases, eight retained sources, and 164 indexed artifacts. Those numbers describe only the
historical packet and are not expectations for `1.1.0`.

The 140 known-bad cases are reason-specific counterexamples and must reject for their exact
declared primary rules. Production-overlay families invoke the same diagnostic functions as a
real repository check. They exercise mission and manifest authority,
claims, threat coverage, scientific lineage and references, preregistration freezes, evidence
witnesses, belief and epistemic policies, denominators and uncertainty, worst-group selection,
source and standards identity, tool writes/network attempts, excluded-path opacity, complete
index metadata, validation coverage, and decision history without writing those prohibited states
to disk. Fixture-only surrogates cannot substitute for these production-path checks.

Use `--format json` for a machine-readable report and `--fixture-only` to replay just the
fixture catalog. These modes must be observational and produce no stored result unless the
operator explicitly redirects stdout outside the validator.

A closeout may retain the machine-readable integrity report without placing it inside the
index's input cycle:

```sh
mkdir -p gate/validation-reports
python3 tools/validate_gate_a.py --format json > \
  gate/validation-reports/gate-a-validation-1.1.0.json
```

The retained report binds the evidence-index digest and remains an integrity signal only. Its
canonical sorted JSON bytes, exact coverage totals, zero diagnostics, and GA-01 through GA-16
control summary are recomputed before any operator decision may bind it. It is not a scientific
result or operator decision.

## Determinism contract

Inputs are repository bytes, the interpreter, and the locally installed schema-validation
library. The validator must not depend on wall-clock time, locale ordering, randomized seeds,
the Git commit, a network, or mutable external services. Paths are repository-relative;
diagnostics are sorted by code and path. SHA-256 is calculated over exact stored bytes.

The validated toolchain and library versions are recorded in the session handoff after each
architecture closeout. A toolchain difference is visible provenance, not permission to change
expected fixture outcomes.

## Result interpretation

- Full-mode exit `0`: the checked architecture is internally complete for its exact
  evidence-index digest. This is not operator acceptance or scientific support. Fixture-only
  exit `0` reports the architecture status as `not_evaluated`.
- Exit `1`: one or more deterministic contract failures occurred.
- Exit `2`: validation could not execute safely (wrong root, missing dependency, malformed
  fixture catalog, or internal validator error).

Known-bad fixtures are synthetic counterexamples, never empirical data. A validator that lets
one pass is itself invalid for Gate A.
