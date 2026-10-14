# Methods and resource recovery

This continuation preserves the four selected MultiOrg images, three recorded
reference procedures per image, exact model variants, input tensors, thresholds,
coordinate conversion, global NMS and matching loss. The first complete pair
remains the [published 0.5.0 result](../0.5.0/README.md). The three remaining
pairs use fresh output paths. No partial output from the interrupted
[0.6.0 attempt](../0.6.0/README.md) is stitched into this attempt.

## Resource admission and checking

The [0.6.1 supervisor](../0.6.1/monitor/README.md) is unchanged. Before each
pair, the launcher observes twenty available-space samples covering the full
remaining cohort allowance, above the 4 GiB floor and 3 GiB margin. For three
remaining pairs on this filesystem, the required available space is
8,465,320,656 bytes. This includes 256 MiB per pair, a per-file allocation
rounding allowance and 20 MiB for additional metadata. The supervisor performs
its own preflight and samples disk, output size and RSS during execution.
Each worker retains its 600-second and 3 GiB limits. First failure stops later
images; each image has one attempt in this owner.

The new [consumer](consumer/CONTRACT.md) checks the actual supervisor receipt,
outer execution, resource journal, worker log, output inventory and audited
runtime before calling the unchanged numerical checker. It reports its own
identity separately. It does not manufacture a legacy receipt. Missing or
inconsistent evidence refuses admission. Source digests and the prospective
freeze are checked before and after admission.

The [matching adapter](matching/README.md) explicitly admits these resource
consumer reports. Its matching and composition arithmetic is unchanged. All
four complete pairs and twelve recorded-reference cases remain mandatory;
source, geometry, coverage or native-cap failure prevents a cohort endpoint.
The matching producer and separate checker each retain a 120-second and
3 GiB sampled bound. Reference payloads and model data remain privately retained.

## Scientific question

For each image and reference procedure, the loss difference is
`delta = (FP + FN)_Faster − (FP + FN)_YOLO`, using exact IoU ≥ 1/2 and
maximum-cardinality matching. Images have equal weight. A positive interval
lower bound conditionally favors YOLO; a negative upper bound favors Faster.
A zero boundary remains unresolved.

The global interval G varies one reference procedure for the entire cohort.
The imagewise interval P allows each image to use any of the same three
procedures. Thus G is contained in P. The frozen question is whether a
resolved global decision becomes unresolved under imagewise composition.
The ordinary twelve-case matching census is the competent baseline. A null
contrast is retained; it does not justify selecting more favorable images.

## Safe capacity recovery

The operator explicitly authorized cleaning safe disposable files. Native
cache tools and exact allowlists were used for inactive build/download caches,
redundant signed installers and generated packaging staging. Staging removal
required complete comparison with retained release archives. Installed
runtimes, source files, personal documents and research evidence were preserved.
The shared uv cache refused an in-use lock and was not forced. Docker had no
build cache to reclaim; images, containers and volumes were preserved.

The [aggregate cleanup record](cleanup-summary.json) separates pre-removal
allocation from observed free space. Shared APFS storage, other writers and
swap prevent attributing every free-byte change to deletion. Cleanup supplies
capacity; it does not supply scientific evidence or a storage reservation.

## Limits

These are same-investigation source, arithmetic and execution checks, not
independent scientific replication. Sampled resource monitoring does not prove
continuous bounds, exclusive storage or containment of every descendant.
If child discovery fails, an independently grouped child may survive outer
termination; the launcher records that uncertainty. The authored timeout
controls do not remove this limitation.

The corrected Faster observation model and unchanged released YOLO model are
specific variants. Whole-image original-versus-corrected graph preservation,
untapped-model parity, general detector superiority, automotive transfer and
complete analyst-work savings are not established by this experiment.
Gate A remains operator-unaccepted.
