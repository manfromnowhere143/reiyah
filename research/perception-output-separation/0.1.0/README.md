# Private outputs stay outside source packages

Document ID: `reiyah.output-separation.checkpoint`

Version: `0.1.0`

Lifecycle status: `exploratory`

On 2026-09-13, complete synthetic workflows reproduced nine ways to bypass Engine output
separation on this case-insensitive filesystem. The commands returned success after placing
private review, assistance or custody material inside a protected input or disclosure directory.
Fresh verification rejected the contaminated packages. Original files were not overwritten;
additional files were sufficient to break the package's declared contents and stage separation.

| Writer and destination | Before correction through case alias | Corrected rejection |
| --- | --- | --- |
| Binding report into observations | Success; package then `OBS_FILE_SET` | `BINDING_PRIVATE_OUTPUT` |
| Admission report into observations | Success; package then `OBS_FILE_SET` | `ADMISSION_PRIVATE_OUTPUT` |
| Rehearsal kit into observations | Success; package then `OBS_FILE_SET` | `REHEARSAL_OUTPUT` |
| Assistance into observations | Success; package then `OBS_FILE_SET` | `ASSISTANCE_OUTPUT` |
| Open operands into observations or assistance | Success; source package then invalid | `OPERANDS_OUTPUT` |
| Reviewed operands into observations or assistance | Success; source package then invalid | `REVIEWED_OUTPUT` |
| New observation package with private custody inside itself | Success; completed package then `OBS_FILE_SET` | `OBS_CUSTODY`, no payload/custody/completion seal written |

All 18 direct-path and symlink controls already rejected before the correction. All 27 cases
now meet their rejection and source-preservation expectations. The existing input verifiers
were not weakened: direct inventories and fresh verification against the original expected
package seals supply the conventional oracle. Full before/after effects and source bindings
are retained under the private `engine-output-separation-2026-09-13` packet; compact public
identities, measurements and results are in [verification.json](verification.json).

## Changed engineering decision

Resolved path spelling is insufficient for this boundary. Python's
[lexical containment operation](https://docs.python.org/3.14/library/pathlib.html#pathlib.PurePath.is_relative_to)
does not compare filesystem objects. On this host, different capitalization names the same
directory even though that lexical check returns false. The exact official documentation
read earlier on 2026-09-13 and the local alias experiment remain privately retained.

The shared `private_output_path` helper compares the existing output parent's ancestor
directory identities with each protected directory. It returns the resolved private path,
so the writers do not follow a retargeted original parent symlink later. The prior discovery
guard delegates to this same helper. Existing diagnostics, output-parent requirements,
non-overwrite behavior, record formats and staged evidence rules remain in force.

The new observation directory does not exist at the preliminary check. Its builder therefore
also checks directory identity after creating the root and `assets`, before disclosing any
payload or writing custody. A rejected preparation can retain empty partial directories.
It has no completion seal and must not be reused. This preserves the existing interrupted-
preparation convention rather than claiming an atomic transaction across two locations.

The [regressions](../../../tests/test_perception_output_separation.py) exercise observation
and assistance aliases, protected code-directory aliases before materialization, all six
writers' parent-symlink retargeting, and private custody aliases at a new package's root and
`assets`. The existing 29 discovery tests also pass after consolidation. The full development
run passes 364 repository tests and 93 measurement tests. These counts describe engineering
checks; they do not measure reviewer usability or scientific validity.

## Reproduce

Use a complete selected checkout and the pinned
[discovery dependencies](../../perception-discovery/0.1.0/requirements.txt). The broader suite's
additional versions are retained in the selected runtime inventory. Output parents must exist,
and every output directory must be new. From the selected checkout:

```sh
python -B research/perception-output-separation/0.1.0/reproduce.py \
  --source-root . \
  --source-sha256 1b37991c52387686b7b49a4a1544ee0d30cefae8554ca05a11cb12e902bd6733 \
  --expect protected --output /private/new-output-separation-control

python -B -m unittest -v tests.test_perception_output_separation tests.test_perception_discovery
```

For the before behavior, use this script with a separate read-only checkout of
`7fd06ea8adfb9370e486e78a6ea50f8ea33aec72`, `--expect vulnerable`, and source SHA-256
`f27146d67cae65f3f11bb6e53f7770f5d2c6dc004e8e46d8f025e6dfba4ed719`.
The selected source digest covers the listed Engine code, fixture code and existing guide
files. The script builds fresh synthetic source/review packages in temporary directories,
records inventories and exact effects, then removes only those temporary controls. It never
accepts a real package as a mutation target. Case-alias cases explicitly skip when unsupported
by the execution filesystem; that run does not establish case-insensitive behavior.

Fixture sealing uses the actual local clock, and temporary source paths vary. Retained
`returned.json` files and assistance inventories need not repeat exactly. The compact result
table is deterministic for the same selected source and filesystem behavior. Process time
includes fixture preparation and is not an estimate of human review effort.

## Scope and next falsifiable check

The guard assumes a stable local directory hierarchy. Concurrent directory replacement,
mount changes and privileged filesystem mutation remain outside its scope. It introduces no
new dependency, record format, IPC service or mathematical assumption. Code consolidation
reduces the number of independent path policies to maintain; it supplies no performance or
state-of-the-art claim. No Fable source, ref, planner, checker or outbox was modified or consumed.

The viewer is a separate next boundary: it receives a package seal and a selected asset path,
but no package location against which to check output separation. Reproduce an actual source-
directory mutation before changing that interface. Actual participant return takes priority
if supplied; no tool or generated record replaces that observation.

All review claims in these controls are explicitly synthetic. No human reference judgment,
phase release, real admission or actual interactive observation was performed. Joint reference
alternatives, matching competition, weights, loss, tolerance and unknown states are unchanged.
Real bounds remain [-8,8]; Gate A is unaccepted and the physical study is unrun. P005 is
operator-reported published; no further publication or outreach is authorized.
