# Distribution and reproduction, 0.1.0

Only authored code, derivations, source identities, aggregate results and cost/failure
records are distributed. Third-party bodies and full recorded data/proofs are private.
Publisher push/readback establishes publisher-observed byte integrity only, never
independent transport verification, scientific replication or operator acceptance.

From the repository root, with Python 3.11+ and an output directory that already
exists, authored controls and workflows reproduce offline without dependencies:

~~~sh
python -B research/grid-fidelity/0.1.0/controls.py pre --output /tmp/grid-controls.json
python -B research/grid-fidelity/0.1.0/run.py --arm reiyah --output /tmp/grid-reiyah.json --proofs /tmp/grid-reiyah-proofs.json --timing /tmp/grid-reiyah-time.json
python -B research/grid-fidelity/0.1.0/run.py --arm conventional --output /tmp/grid-conventional.json --proofs /tmp/grid-conventional-proofs.json --timing /tmp/grid-conventional-time.json
python -B research/grid-fidelity/0.1.0/check.py --reiyah /tmp/grid-reiyah.json --reiyah-proofs /tmp/grid-reiyah-proofs.json --conventional /tmp/grid-conventional.json --conventional-proofs /tmp/grid-conventional-proofs.json --output /tmp/grid-check.json
~~~

Outputs are created exclusively; existing files cause refusal. Public commands
execute 13 authored cases per arm. For the five exposed source parts, supply
--sources pointing to a private inputs directory containing the two exact file
identities in inputs.json. Private source availability is not assumed for a
public reproducer. The author used a bounded supervisor and pinned runtime,
with network denied before child runtime startup. Ordinary manual commands
above are development reproductions, not original cost measurements.

Integration uses the reviewed parent commit and normal nonforce push. The private
owner retains commit, scope, push and exact-file readback receipts; a final commit
digest is not inserted into its own committed files. Publisher integrity is not
independent transport or scientific verification. The continuing Reiyah mission
remains active after this study checkpoint.

