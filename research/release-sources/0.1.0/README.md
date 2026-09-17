# Public detector release sources

Document ID: `reiyah.research.release-sources`

Version: `0.1.0`

Lifecycle status: `exploratory`

## Result

Six checkpoint candidates have public publisher pointers, but **zero new prediction
sets are admitted**. The two-family, three-revision acquisition target remains
unmet. This inventory advances source discovery; it is not a new model evaluation,
customer revision history, or observation-cost result. Product value remains
inconclusive after the [correction-observation comparison](../../correction-observation/0.1.0/README.md).

The September 17 snapshot retains 49 metadata responses privately: 48 successful
responses and one 404 for the old `roboflow/sab` endpoint. Five complete repository
tree responses contain 2,279 entries in total. A bounded filename scan, release
asset listings, documentation and selected export code did not yield a complete
prediction packet. This does not establish that such packets do not exist.

## Candidate sequences

| Publisher family | Candidate 1 | Candidate 2 | Candidate 3 | Comparability limit |
|---|---|---|---|---|
| Ultralytics YOLO | YOLOv8n, 2023 | YOLO11n, 2024 | YOLO26n, 2026 | Successive architectures; no demonstrated customer release sequence |
| RT-DETR | R18, 2023 | v2-S R18 rerun, 2024 | v4-S HGNet, 2025 | v4 changes the backbone; conversions and reruns require their own byte identities |

The first sequence follows the publisher's [roadmap](https://www.ultralytics.com/roadmap)
and pinned model documentation. The second follows the retained
[RT-DETR announcements](https://github.com/lyuwenyu/RT-DETR/blob/29320b6fd828f8e0987a71426cf2d961b09dfed7/README.md)
and [v4 release record](https://github.com/RT-DETRs/RT-DETRv4/blob/55fefaaed7efe2a5f72d0a18fd4e05965e35c292/README.md).
Years order publisher generations only. They do not make differently named
detectors genuine within-team revisions or independent experimental cases.

[candidates.json](candidates.json) records six exact checkpoint pointers, pinned
source commits, chronology qualifications and missing fields. Five weight URLs
have retained GitHub asset metadata; v4-S has a publisher-linked Drive pointer.
None of the six weight payloads was fetched. The three Ultralytics SHA-256 values
are **API-declared**, not locally verified checkpoint hashes. The original-release
byte identity remains unverified, including assets currently hosted under newer
release containers.

Do not replace unknown dates with a convenient timestamp. The pinned YOLO11
document gives September 10, 2024, while the launch article displays September 27
and carries a different structured publication timestamp; package v8.3.0 was
published September 30. The RT-DETR storage `v0.2` container predates the selected
v2-S rerun asset. These observations remain separate in the ledger.

## Prediction and export findings

The current RF-DETR package releases and differently sized models do not establish
three chronological trained-checkpoint revisions. Its benchmark link led to the
[Single Artifact Benchmarking repository](https://github.com/roboflow/single_artifact_benchmarking/tree/7f5bf7e306857fcdcad43373661c0a43dc8665a0).
That snapshot supplies evaluation code and graph pointers, not an admitted cached
prediction packet. Its retained license restricts commercial use and redistribution;
no third-party code was executed or copied into this repository.

Inspection of the pinned
[evaluation routine](https://github.com/roboflow/single_artifact_benchmarking/blob/7f5bf7e306857fcdcad43373661c0a43dc8665a0/sab/evaluation.py)
shows an optional detection-row JSON export. The image list comes from the
annotation input, while the exported rows represent detections. Consequently the
rows alone cannot establish whether an absent image had zero detections or was
never processed. This is a limitation of using the export in isolation, not an
allegation that the publisher skipped images. Admission needs an independently
retained complete image index and processing status, including valid empty outputs.

A concrete follow-up is available in the EdgeFirst model cards: the
[YOLOv8](https://huggingface.co/EdgeFirst/yolov8-det/blob/200126082b2c693bd8e1c698a91350be7b91b34c/README.md),
[YOLO11](https://huggingface.co/EdgeFirst/yolo11-det/blob/21662cab7270c5cd59d7a65d604b6b54d8944d78/README.md)
and [YOLO26](https://huggingface.co/EdgeFirst/yolo26-det/blob/ad9a670a493f46f1e4d10b955b3598de6927082a/README.md)
cards link the Nano FP32 reference sessions `v-e89`, `v-e93`, and `v-e9c` and describe
per-image Arrow/Parquet outputs. The session page requires JavaScript, and no browser
connection was available here. Download availability and export rights remain
unverified. The Hugging Face file listings supply model artifacts, not the described
prediction packets. Compiled runtime outputs also need their own source bindings;
do not equate them with native checkpoint outputs or count different hardware runs
as additional detector families.

## Custody, validation and next work

[sources.json](sources.json) contains source IDs, retrieval times, byte counts,
digests, access and scoped terms records. These public records are evidence-ineligible
pointers. The corresponding privately retained bytes support the limited metadata
observations above; they supply no model-performance evidence. The local research
root is `~/.codex/reports/reiyah/release-sources-2026-09-17-otk429k8/`.
All 49 response bytes and the six candidate bindings are checked there. The default
repository consistency check is used without claiming a new replay of historical
experiments. No Engine implementation or accepted artifact changes.

The [source packet checklist](SOURCE_PACKET.md) makes the next acquisition concrete:
first inspect the three public EdgeFirst sessions for accessible prediction exports,
then pursue the RT-DETR checkpoint exports. A bounded native export may be designed
if cached outputs are unavailable; no inference campaign is launched by this inventory.
Once data is qualified, freeze the comparison and observation contract before
reserved outcomes. All 1,433 REC-D outcome-reserved images remain uninspected by this
continuation. Human preparation, review, integration and agreed cost rates remain
unmeasured. Gate A remains operator-unaccepted.
