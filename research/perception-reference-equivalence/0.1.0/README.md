# Reproduce the proposal member-order control

Artifact ID: `reiyah.engine.reference-equivalence.reproduction`

Version: `0.1.0`

Status: `exploratory`

From a checked current Engine candidate, with the retained offline Python environment:

```sh
reiyah_replay_dir=$(mktemp -d)
git show 2048e3e0dd10eaaed2849aace9e0039ddd654e09:tools/perception_reference.py > "$reiyah_replay_dir/baseline.py"
python -B research/perception-reference-equivalence/0.1.0/reproduce.py \
  --baseline-compiler "$reiyah_replay_dir/baseline.py" --budget-control
```

The program checks the previous compiler's digest, constructs the same explicitly synthetic
operands for both versions and prints deterministic JSON. It creates no files and uses no
network dependency. The source body for every small reference object is generated and hashed;
direct original-coordinate matching checks every small world. The optional dense control checks
the prior and current output bytes and core certificates, not an independent exhaustive search
over its heavy matching problem. All other production dependencies are shared.

The unpermuted control retains exact previous output bytes. The permuted control changes from
open [-1,1] to finite [1,1], preserving every original ordered source mapping. The budget control
retains [0,1]. Unreduced rational strings remain invalid in both compilers. The counterfactual
that removes the prior fallback and the full synthetic admission example are separately retained
in the private checkpoint and sealed exchange.

Read [the decision and proof](../../../docs/PERCEPTION_REFERENCE_EQUIVALENCE_2026-09-13.md) and
[the source/output verification](verification.json). The real comparison remains [-8,8], with
no admitted human references or participant usability evidence. This reproduction is engineering
evidence, not a physical reference study or a measured analyst-effort comparison.
