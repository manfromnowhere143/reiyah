# Training inputs: availability established, lineage constraints identified

Document ID: `reiyah.training-input-findings.2026-09-07`

Version: `0.1.0`

Lifecycle status: `exploratory`

All 536,780 requested nuScenes sensor paths exist as nonempty regular files on
the inspected read-only dataset copy. A separate directory enumeration agrees
on every filename and size. The total is 261,258,587,213 bytes. This removes
the file-availability uncertainty for all three proposed training partitions.
It does not measure a training effect or validate sensor contents.

## Complete file population

The request derives from the retained official metadata and SDK split source,
without consulting detector predictions or annotation outcomes. It includes
all six camera keyframes, LIDAR_TOP keyframes, and lidar sweeps associated by
metadata with official training/validation samples. Every selected frame must
have seven distinct keyframe-channel records; incomplete metadata fails the
request build. Radar and non-keyframe camera images are outside this scope.

| Split | Scenes / logs | Frames | Keyframe files | Lidar sweep files | Missing or unresolved requested files |
| --- | --- | ---: | ---: | ---: | ---: |
| Train | 700 / 50 | 28,130 | 196,910 | 245,255 | 0 |
| Validation | 150 / 18 | 6,019 | 42,133 | 52,482 | 0 |

The [availability aggregate](../evidence/training-overlap/sensor-availability-0.1.0.json),
[directory recount](../evidence/training-overlap/directory-recount-0.1.0.json),
and [verification](../evidence/training-overlap/verification-0.1.0.json) retain
the denominators, observations and exact identities. The original private
request and per-file observations remain available for replay. Seven cloud
metadata tables, including sample data and annotations, are byte-identical to
the corresponding retained archive members by the
[metadata check](../evidence/training-overlap/metadata-binding-0.1.0.json).

All six partitions across seeds 20260910, 20260911 and 20260912 have complete
requested file coverage. Their original split bytes remain unchanged. Unequal
sample budgets remain unequal; file availability does not resolve the choice
of common optimization work or independent calibration logs.

File size establishes neither successful decoding nor sensor validity. Image
dimensions, calibration use, lidar numeric contents and each loader's actual
temporal support still need checking. The separate enumeration shares the
same disk and reference metadata, so it supplies computational cross-checking,
not independent physical adjudication.

## Existing checkpoints cannot establish disjoint training

Fresh official downloads match the two cloud checkpoint files by full SHA-256:

| Checkpoint | Bytes | SHA-256 |
| --- | ---: | --- |
| FCOS3D r101 DCN finetune | 220,360,111 | `35aaaad0467f0758e77e192c4c320707c1881a0efbe653150d759b65eaec71c3` |
| CenterPoint 0.075-voxel circle NMS | 35,917,497 | `358fbe3b39a235b9c505bed31f2ee9f2b77ae7c58503ab4a09ab643a59f230f7` |

The [source ledger](../evidence/training-overlap/model-source-ledger-0.1.0.json)
retains identities for MMDetection3D v0.17.1 at commit
`f1107977dfd26155fc1f83779ee6535d2468f449`, dated 2021-10-08, twelve configuration
files reached through literal base references, the source license, and both
privately retained model downloads. No upstream configuration or weight was
executed or deserialized in this inventory.

The [FCOS3D finetune recipe](https://github.com/open-mmlab/mmdetection3d/blob/f1107977dfd26155fc1f83779ee6535d2468f449/configs/fcos3d/fcos3d_r101_caffe_fpn_gn-head_dcn_2x8_1x_nus-mono3d_finetune.py)
loads an already trained nuScenes detector. Its base recipe also names a
Detectron2/Caffe ResNet-101 initialization. A new experiment must distinguish
common backbone initialization from prior nuScenes detector training. Splitting
the data used for another finetuning stage cannot erase earlier shared exposure.
Original sample-level training and pretraining lineage remain unverified.

The [CenterPoint recipe](https://github.com/open-mmlab/mmdetection3d/blob/f1107977dfd26155fc1f83779ee6535d2468f449/configs/centerpoint/centerpoint_0075voxel_second_secfpn_4x8_cyclic_20e_nus.py)
uses `ObjectSample` with `nuscenes_dbinfos_train.pkl`. This creates a concrete
route for cross-partition object exposure if only the main annotation list is
filtered. Partition-specific object databases, annotation caches and sweep
references are required. This is a prospective design constraint, not evidence
that an unexecuted Reiyah training run leaked data.

The inspected historical invocation names `uniad:latest`; it does not by itself
bind an immutable execution image. The existing FCOS3D run also has the already
reported size/yaw evaluation discrepancy. Fresh container/dependency identities
and a geometry smoke test belong before new training. This inventory does not
reclassify that historical run as a full benchmark reproduction.

## Next experiment

Retain the four-fit pairing contrast in the
[training design](TRAINING_OVERLAP_NEXT_EXPERIMENT_2026-09-07.md). First construct
partition-contained training inputs from the verified metadata, including the
object sampler and temporal sources. Then fix calibration logs, initialization
policy, equal steps within architecture, training repetitions, the minimum
useful effect and the interval procedure before fitting or examining new test
outcomes. Preserve the complete validation opportunity population.

The existing L4 VM could not start because its zone reported exhausted capacity.
No detector was trained in this task. Independent judgments for the separate
frozen 240-case study remain absent, and Gate A remains operator-unaccepted.
