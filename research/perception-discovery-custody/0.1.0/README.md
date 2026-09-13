# Discovery outputs preserve the observation package

Document ID: `reiyah.discovery-custody.checkpoint`

Version: `0.1.0`

Lifecycle status: `exploratory`

On 2026-09-13, both discovery writers were reproduced returning success after adding a
review file inside their own freshly verified observation package. The next verification
against the same expected seal rejected the extra file with `OBS_FILE_SET`. No original
file was overwritten. The writer had nevertheless invalidated the evidence package and
placed private review material in the wrong stage's directory.

The correction rejects that output destination with `DISCOVERY_PRIVATE_OUTPUT` before
verification or writing. An output's existing parent is resolved once, and each ancestor's
filesystem identity is compared with the package directory. This also detects differently
capitalized aliases on a case-insensitive filesystem. A valid output uses the resolved
parent, so retargeting the original parent symlink during verification does not redirect
the write. Existing private siblings remain usable; output identities are never replaced.

## Evidence and conventional baseline

The baseline is direct filesystem inventory followed by the existing package verifier,
using fresh copies of the repository's synthetic observation fixture. It does not depend
on the new guard to detect package mutation. Both operations were checked at the package
root, inside `assets`, through a symlink, and through a case alias: eight cases on this host.
All eight succeeded and invalidated the package before the correction; all eight now reject
without adding or changing files, and the original expected seal still verifies.

The existing admission/binding output guard suggested a small separation check rather than
a new storage interface. Its resolved-path string comparison is insufficient for this
host's case aliases: two differently spelled paths referred to the same directory while
`is_relative_to` returned false. This checkpoint changes discovery custody only. The other
writers require their own bounded review before making a broader separation claim.

The [regressions](../../../tests/test_perception_discovery.py) also exercise successful
private sibling outputs, structured CLI rejection with no mutation, and parent-symlink
retargeting during verification for both writers. Existing record validation, exposure,
unknown-state, package-identity and non-overwrite checks remain active. Exact source
identities, failures, process costs and results are in [verification.json](verification.json).

## Reproduce

Use Python 3.14 and the pinned [discovery dependencies](../../perception-discovery/0.1.0/requirements.txt)
in an isolated environment. The reproduction needs only these dependencies; the complete
repository suite has additional dependencies recorded in the verification environment.
Choose an unused output directory whose parent exists. From the selected repository root:

```sh
python -B research/perception-discovery-custody/0.1.0/reproduce.py \
  --source-root . \
  --custody-sha256 adc8e84b2fc2a7b8c18aa3ce1515996f6210d8493efb32c75164d2cae7050361 \
  --expect protected --output /private/new-custody-reproduction

python -B -m unittest -v tests.test_perception_discovery
```

To reproduce the previous behavior, select a separate read-only checkout of
`f7ae44dcd30510ec695cc5271abd89ecb026192f` as `--source-root`, use the same reproduction
script with a fresh output directory, pass `--expect vulnerable`, and select custody SHA-256
`0108db4755b3e9ea8215d8497f3b6c6a66426817c8ff9070ae6f53873995eb9f`.
Never run a reproduction against a real or retained observation package: this script creates
its own synthetic packages and deletes those temporary package copies after recording results.
It retains the manifest, synthetic submitted record and any unexpected review-file bytes.

On a filesystem that does not resolve the case alias, those two cases are explicitly skipped;
that run does not establish case-insensitive behavior. The original sealer uses an actual
local clock, so unexpected sealed files from the vulnerable run need not repeat byte for byte.
The result table and protected replay are deterministic for the selected source/runtime.

## Cost, assumptions and limits

The production change is one small guard and two call sites, with no added dependency or
record-format change. It makes one path-resolution pass and at most one directory identity
comparison per output-parent ancestor. Captured elapsed time includes interpreter startup,
fixture creation and verification. It is not a human-review budget or a performance ranking.

The guard assumes a stable local directory hierarchy. It is not a filesystem sandbox and
does not protect against concurrent directory replacement, mount changes or other privileged
mutation. Missing or inaccessible parents fail through the existing I/O error path. The
package verifier still establishes exact retained-file identity, not physical source truth.

Python's primary documentation distinguishes [lexical path containment](https://docs.python.org/3.14/library/pathlib.html#pathlib.PurePath.is_relative_to),
[symlink resolution](https://docs.python.org/3.14/library/pathlib.html#pathlib.Path.resolve) and
[filesystem identity](https://docs.python.org/3.14/library/pathlib.html#pathlib.Path.samefile).
The accessed documentation identifies itself as 3.14.7; this host runs Python 3.14.2. Exact
accessed bytes, access date and license-page identity are retained privately, not redistributed.
The local before/after experiment is the evidence for the observed host behavior.

All records in these controls are synthetic. No human reference, reviewer independence,
interactive observation or admission is established. Real comparison bounds remain [-8,8].
Gate A is unaccepted; the physical study is unrun, with no selected cohort or seed. Fable's
source, refs, planner and outboxes are untouched. P005 is operator-reported published; no
further publication or outreach is authorized.
