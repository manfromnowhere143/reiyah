# Coordinate-export admission experiment

Document ID: `reiyah.compact-motion.decision-plan`. Version: `0.1.0`.
Status: exploratory recorded-data experiment. Date: 20 September 2026.

## Decision and prior exposure

Should this selected target CSV be admitted as a numerically lossless substitute
for the corresponding MATLAB coordinate records? The dataset README says the
two formats contain the same data. For a downstream pipeline requiring exact
coordinate preservation, a counterexample changes the input-admission decision:
use the original numeric representation or explicitly budget serialization error.
It does not decide whether either representation is physically accurate.

Lossless means both finite latitude and longitude values compare equal after
binary64 decoding for every identity-matched row. Exact equality is required by
this engineering question; no convenient clearance or safety threshold is added.
NaN, missing or infinity cannot establish a match or a mismatch. A mismatch in
one otherwise eligible coordinate record refutes universal losslessness.

This supplement was chosen after the operator's review emphasized a useful
decision experiment. Before its freeze, two first CSV records, the MAT header,
dimensions and types, source documentation and twenty synthetic diagnostic
controls were known. No MAT coordinate value or full-file numeric outcome had
been inspected. The coarse first CSV coordinates make lossiness plausible; this
is a development case, not a blind source selection or a representative benchmark.
The earlier analysis freeze is preserved unchanged and bound by this supplement.

## One complete population, two equal-information methods

Allocate the entire selected Honda file. Require the CSV/MAT row count, column
identities and exact timestamp sequence to agree before either method runs.
Both receive the same CSV and identity metadata and can reveal MAT coordinate
pairs in original row order. The source adapter has already decoded the full
MAT file. These are logical reveals of retained data, not independently acquired
sensor observations or a claim of reduced download/decoding work.

The Reiyah method maintains bounds `[L,U]` on the number of mismatching records.
Initially `[0,N]`. A finite match lowers U by one; a mismatch raises L by one;
unavailable information leaves both unchanged. The universal decision is
contradicted if L is positive, supported if U is zero, otherwise unresolved.
These bounds cover every completion of the unrevealed records under this exact
coordinate-preservation contract. They do not merely distinguish two examples.
Stop on a resolved decision or after all N records have been queried.

The competent conventional method scans the same ordered records. It rejects
at the first finite mismatch, accepts only if every record is a finite match,
and otherwise reports unresolved after exhaustion. It has no dependency on the
Reiyah verdict or trace. Execute both; retain parity and any discrepancy.
Both methods are authored in this session, so this is not an independently
authored baseline study or external replication.

## Reference, costs and stop

A separate checker traverses all source coordinate pairs, computes the complete
reference, reconstructs the query prefix, and verifies every emitted bound and
decision. Report useful resolution, false acceptance/refusal relative only to
this full-file reference, unresolved cases and logical reveal counts. These are
single-case counts, not estimated error rates or driving outcomes.

Record shared capture/decoding separately from each method's wall and process CPU
time. One execution per method is a correctness experiment; tiny timing differences
do not establish speed. Charge shared preparation once, retain total workflow
costs, and leave engineering effort, human acquisition/review, money and energy
unknown. Do not interpret logical query counts as actual acquisition savings.

Before actual outcomes, exercise support, contradiction, unavailable information,
late counterexample and equal-information parity on small authored controls.
After execution, test forged bounds, decisions and costs/trace identities as
applicable. No source selection, policy tuning, additional case or threshold
search follows automatically. Physical clearance remains unresolved; retain the
missing uncertainty/calibration contract and all 1,433 closed reserved images.
