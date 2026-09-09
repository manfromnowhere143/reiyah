# Perception-input implementation checkpoint

Document ID: `reiyah.perception-inputs.checkpoint-2026-09-09`

Version: `0.1.0`

Lifecycle status: `exploratory`

The Engine now has a complete-source input adapter feeding the existing paired-loss core.
It constructs the population from metadata, preserves unavailable frames, records historical
exposure exclusions, and joins nominal sensor timing and position. The
[guide](../research/perception-inputs/0.1.0/README.md) explains its interface and limits; the
[machine checkpoint](../research/perception-inputs/0.1.0/checkpoint.json) binds code and results.

## Retained-data inventory

| Observation | Count |
| --- | ---: |
| Official validation scenes | 150 |
| Clock anchors retained | 6,019 |
| Anchors with declared +/-2-second scene context | 4,682 |
| Anchors eligible under the supplied historical-exposure rule | 2,935 |
| Scenes containing those eligible anchors | 138 |
| Observed frames in each prediction file | 6,019 |
| Joined camera/lidar keyframe metadata records | 42,133 |
| Resolved nominal lidar ego positions at the anchor time | 6,019 |

All source files were checked in full against expected sizes and hashes before use. The
catalog agrees with a separate calculation against the retained clock on every sample
identity, scene/time/context field, keyframe capture record and eligible identity. This is
an internal cross-check using project records, not independent physical adjudication.

The exclusion calculation accounts for 240 historical cases, 4,956 exposed assets and 84
explicit scene-boundary placeholders. The first real run rejected the signed historical
evidence-ID syntax. The correction separates those opaque record IDs from dataset IDs;
the failed run and a regression test are retained. No failed output was promoted to a catalog.

The final catalog contains 25,998,480 bytes, SHA-256
`038089ed22b6f4ca5e05d250310f6457e3f4a533bcc32bdc6b422dd7b90b2d65`.
Its raw records and source paths remain private. No prospective seed or cohort was generated,
and ingestion computed no detector comparison outcomes.

## Integration and verification

Two previously exposed development anchors were chosen by historical case-ID order, without
using prediction values or reference labels. Their exact source arrays passed through verified
extraction, the existing normalizer, paired-loss computation and separate certificate checker.
Both references stayed open. The resulting conservative interval was `[-8, 8]` error units per
anchor, with unresolved preference. This verifies plumbing and unknown-state propagation; it
is not a new performance result or evidence that the camera improves the lidar system.

That integration and the separate clock check used the preceding catalog revision. The final
catalog's complete data projection is identical; only its implementation identity fields
changed after the source-change and unavailable-extraction guards were added. The retained
equivalence record binds this relationship explicitly. It does not relabel the earlier run
as a later one.

All 223 offline unit tests passed: 130 repository tests and 93 measurement-tool tests. The
24 new input tests exercise malformed source framing, duplicate identities, exact decimal
and byte-span behavior, source mutation, independent clock population, missing/empty frames,
exposure boundaries, sensor/time joins, and actual CLI failures without partial output.

```sh
python3 -B -m unittest discover -s tests -v
python3 -B -m unittest discover -s tools/measure -p 'test_*.py' -v
python3 -B tools/measure/gate_b_check.py --json /absolute/private/path/gate-b.json
```

The Gate B closeout checks retained evidence integrity and document consistency. It does not
rerun the 52 empirical transcripts or establish Gate A release validation. The 57 claim-register
rows, original evidence, selected study plan and paired-loss core remain unchanged.

## Next authorized work

Implement the reviewed-reference adapter and check raw observation windows. Preserve shared
class, presence, alias, geometry and time alternatives, including objects that can alter
matching through neighbors of base detections. Admit a finite model only with an explicit
coverage basis; otherwise retain the unconditional open-reference enclosure. Metadata presence
and exact arithmetic cannot supply that physical coverage basis.

The selected 60-scene study remains unselected and unrun. Its two independent reviewers,
conventional comparator, adjudication arrangement and valid raw windows remain prerequisites.
No new training, model inference, independent human judgments or commercial differentiation
are reported. Gate A remains operator-unaccepted; this is authorized offline research work.

Work was prepared from main `e19049b8a02c621bb92f504d0f47d1cfe6d2a13d` in a private export.
Owner worktrees and UI work remain separate. Resolve committed integration and publisher
readback from Git and the task delivery record. Publisher readback is not independent
transport verification.
