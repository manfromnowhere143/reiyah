# Audit every row of the three cached exports

Version `0.1.0`, 18 September 2026. Status: `exploratory`.

All 2,063,562 rows in the three public EdgeFirst prediction files now agree
across Polars and PyArrow decoding. Every file contains all 5,000 expected
COCO val2017 image members and dimensions. **No cached packet is fully admitted:**
historical checkpoint/configuration and redistribution bindings remain absent,
and the complete content audit identifies zero-extent detections under the
declared positive-area contract.

| Public session | Rows | Images with valid nonempty content | Explicit empty images | Images with invalid content | Zero-extent rows |
| --- | ---: | ---: | ---: | ---: | ---: |
| v-e89, publisher-labelled YOLOv8n | 744,885 | 4,962 | 0 | 38 | 45 |
| v-e93, publisher-labelled YOLO11n | 722,891 | 4,947 | 1 | 52 | 172 |
| v-e9c, publisher-labelled YOLO26n | 595,786 | 4,990 | 2 | 8 | 8 |

Missing and extra members are zero in every file. Invalid content is not a
missing image or an empty output. All flagged detections have exactly one
zero extent and a center on the normalized canvas boundary; none has a
negative extent. Their maximum scores are approximately 0.01953, 0.00907 and
0.00353 respectively. This describes retained rows; it neither identifies
their generating code path nor authorizes silently dropping or repairing them.

Every nonempty row has a finite score in [0,1], a four-component finite box,
and consistent image metadata. Exact duplicate detections are absent. The
separate out-of-canvas diagnostics count 1,774, 1,434 and 2,351 rows; those
boxes are retained without clipping. All 80 observed index/name pairs match
the sorted dense COCO category convention, while none matches the sparse
source-ID convention at the same numeric index. No remapping is applied.
Each file reaches 300 detections on some images. Neither that observation nor
the minimum observed score establishes the historical decoder configuration.

The original frozen timing test found no complete match under separate
capture/preprocessing components. A disclosed, separately frozen diagnostic
then tested one alternate formula suggested by two chart entries. All 4,995
four-component chart tuples match exactly in every file under one of 36
declared trials: original first-appearance order, offset five, preprocessing
equal to capture/load plus preprocessing, and float32 stage rounding. All
5,000 capture values separately equal the retained load duration. The five
omitted member IDs and every unsuccessful trial remain private and retained.
This proves an artifact relationship; the publisher's reason for omission
and intended total-latency accounting remain unknown.

The [source follow-up](SOURCES.md) retains profiler v1.14.2 release identity,
listed timing artifacts and the documented task route's Unauthorized response.
It supplies no historical run checkpoint digest or full argument binding.
The earlier separate-family RT-DETR result is unchanged. The two qualified
local 64-image packets and their conventional-baseline parity remain intact;
this audit performs no detector accuracy comparison or new model inference.

The original audit freezes 500 source/implementation/runtime bindings before
full-row diagnostics. Its [plan](PLAN.md), 34 controls and full synthetic
pipeline preserve missing, empty, invalid and duplicate states. A separate
529-binding follow-up freezes the disclosed timing hypothesis and flagged-row
characterization; seven controls include a complete three-file synthetic
pipeline. All original and follow-up checks pass. First failures remain
retained, including the nullable-list reader failure and rejected footer
rewrites. [FORMAT.md](FORMAT.md) explains the final byte-preserving operation.

[summary.json](summary.json) retains every packet's aggregate findings, all
timing trials, exact source/result identities, resource costs and admission
blocks. [COSTS.md](COSTS.md) distinguishes outer processes from nested timers.
Raw predictions, image joins, timing vectors and derived views remain private
under [DISTRIBUTION.md](DISTRIBUTION.md). Decoder agreement is a software check,
not independent scientific replication. All 1,433 reserved images stay closed;
human costs, economic savings and customer demand remain unproved.

## Reproduction

Use Python 3.14 with the retained Polars 1.44.2 and PyArrow 25.0.1 environment.
The public synthetic controls require no third-party dataset:

```sh
python -B -m unittest discover -s research/cached-packet-audit/0.1.0 -p 'test_packet_*.py'
```

With authorized private source custody, `packet_freeze.py --area AREA --output
FREEZE_DIRECTORY` binds the already acquired files and reader runtime.
`packet_run.py --area AREA --freeze FREEZE.json --output RUN` performs the
audit; add `--verify-run RUN` and a fresh output path for the separate decoder
check. `packet_synthetic.py` supplies the complete 5,000-image synthetic path.
Actual work used a network-denied process and a 1,200-second phase limit.
Exact private manifests retain the invocation, environment and first failures.
Reproduction needs the original source bytes; this repository does not
redistribute them or provide the absent historical model/settings bindings.
