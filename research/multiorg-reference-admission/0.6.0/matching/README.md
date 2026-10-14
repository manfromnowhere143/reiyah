# The original selected cohort

This separately versioned adapter requires the exact four preselected image
pairs and all twelve recorded-reference cases. The first pair retains its
immutable 0.5.0 worker, checker and input bindings. The other three use their
literal 0.6.0 profiles. The old contracts and owners remain unchanged.

The analysis endpoint, model variants, source coordinates, score threshold,
reference procedures and loss are unchanged. Each pair must have a qualified
complete result and successful supervisor and checker receipts. Every observed
file is digest-bound. Missing, failed or incomplete observations cannot become
empty detections. A missing or substituted image prevents the cohort endpoint.

`contract.json` pins image identities, source hashes, original/rescaled shapes,
complete lattice sizes, per-image versions and exact worker, checker, protocol
and manifest digests. New pairs also bind their literal image-contract digest.
`DEPENDENCIES.json` binds the existing native `references`, `fixed_case` and
`compose` implementation and its schemas, kernels and checkers.

Each fixed case preserves 128 reference objects, 1,024 detections per output,
2,048 combined edges, 2,000,000 work units, 4 MiB input and 16 MiB proof limits.
These are per-case limits; the composed result is not a single native certificate
for every reference family. Coordinates remain un-clipped, exact IoU at least
one half defines an edge, and the matcher preserves distinct source identities
even when geometry is duplicated. Every native bound remains active; no
truncation, replacement or relaxed limit is permitted.

For each image `i` and procedure `p`, define
`d[i,p] = FP_A + FN_A - FP_B - FN_B`. A is the corrected Faster observation
variant; B is unchanged YOLO. Equal image weights preserve the original question:

```text
G = [min_p sum_i d[i,p] / 4, max_p sum_i d[i,p] / 4]
P = [sum_i min_p d[i,p] / 4, sum_i max_p d[i,p] / 4]
```

G chooses one recorded procedure for the entire cohort. P permits each image to
choose a procedure. Neither construction asserts a distribution over procedures
or treats them as physical truth. Negative upper bounds prefer A, positive lower
bounds prefer B, and zero remains unresolved. A resolved G with unresolved P is
the declared coupling contrast. An unresolved G is retained as inconclusive; a
resolved contrast that persists under P is `no_observed_fragility`. The cohort
must not be enlarged to change a null result.

`check_matching.py` independently parses reference coordinates and uses unchanged
generic exact-IoU/Edmonds–Karp functions. The new file's terminal newline was
normalized before freeze; the old file remains untouched. The checker recomputes
all twelve cardinalities and both reference-family compositions. It shares only
the explicit custody/endpoint gate with the producer. Native proof files are
digest-bound; the existing native checker is executed by the producer and is
not separately reexecuted by this arithmetic checker. This remains one
investigation, not independent scientific replication.

The private input manifest has exactly `artifact_id`, `version`,
`contract_sha256`, `pairs`, `reference_manifest` and `reference_root`.
Its artifact ID is `reiyah.multiorg.selected-cohort-matching-input`, version
`0.6.0`. `pairs` contains exactly four entries in frozen image order, each with
`image_id`, `pair`, `supervisor`, `pair_checker` and `checker_execution`.
Every file descriptor contains exactly `path` and `sha256`. The source manifest
retains its original 55-image digest; the twelve required reference files appear
under `reference_root` at their original manifest-relative locations.

```text
python3 -B match_analysis.py --input INPUT.json --input-sha256 INPUT_SHA \
  --repository REIYAH_CANDIDATE --output NEW_RESULT_DIRECTORY
python3 -B check_matching.py --input INPUT.json --input-sha256 INPUT_SHA \
  --repository REIYAH_CANDIDATE --result NEW_RESULT_DIRECTORY/result.json \
  --result-sha256 RESULT_SHA --output NEW_CHECK.json
```

Each actual command requires separate external supervision: 120 seconds,
3 GiB sampled RSS and network denied. Internal deadline checks do not replace
that boundary. Preserve any partial packet files on refusal without promoting
them to a completed cohort result. Parent admission and a prospective execution
freeze remain prerequisites.

Authored controls cover mixed-version admission, identity, complete coverage,
missing versus empty, reference and detection caps, exact geometry, augmenting
paths, duplicate geometry, receipt tampering and twelve-case composition. Small
authored matrices compare the independent composition with all 81 imagewise
procedure choices. These controls do not read new empirical predictions or
annotation payloads and do not perform model inference.
