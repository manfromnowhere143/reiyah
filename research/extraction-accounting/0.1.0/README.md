# Declared camera/gaze extraction accounting: 0.1.0

Status: exploratory offline engineering correction. This is a replacement
preprocessing boundary for possible future H5 reuse. The historical H5/H5b/H6
scripts and their results remain unchanged. No historical cohort was decoded,
no inference ran, and this helper is not yet integrated into a model consumer.
Gate A remains operator-unaccepted; this is not product runtime or release
validation. Broad product expansion remains stopped.

## Problem and implemented boundary

Historical `extract` functions in
[H5](../../../human-channel/tools/h5_cross_agent_joint.py) and
[H5b](../../../human-channel/tools/h5b_cross_agent_interval.py) ignore the return
value of `subprocess.run(..., check=False)`. Their main loops skip absent gaze
videos or absent matching gaze frames. These paths can remove observations
without a complete expected/processed/failed ledger. Whether this happened in a
historical run is **not established**. The unit control executes only the old
function's AST under an authored failed-process response; it imports no model.

[extract.py](extract.py) implements a small, standard-library-only boundary:

1. Require an explicit cohort, source byte digests, rational sampling rate and
   expected output count per clip before starting. Reject malformed plans,
   duplicate IDs/JSON fields, empty cohorts and unknown plan properties.
2. Require a fresh output directory. Do not discover a cohort from successful
   files or overwrite a prior run.
3. Record a disposition for each declared camera and gaze source, including
   missing files, mismatched bytes, process failure, timeout and incomplete or
   extra output membership. Continue accounting for later clips after a failure.
4. Retain commands, decoder return codes, stdout/stderr, source identities before
   and after execution, and every observed frame identity. Partial files remain
   available for diagnosis; they cannot qualify as a complete cohort.
5. Return pairs only after `require_complete` has checked **all** declared clips,
   both streams, expected frame membership, source/log/frame bytes and the
   caller-supplied ledger digest. It returns no partial iterator.

FFmpeg runs with local-file input protocol, no stdin, one decoder/filter/encoder
thread, a per-stream timeout, `-xerror` and `-abort_on empty_output`. It requests
at most `expected_frames + 1` outputs: the additional output detects an
under-declared count instead of silently truncating to the declared count.
Every nonzero return blocks consumption, even if all expected files exist.

## Plan and execution contract

The exact JSON fields are:

```json
{
  "artifact_id": "reiyah.extraction-plan",
  "version": "0.1.0",
  "fps": "2/5",
  "clips": [{
    "id": "example",
    "expected_frames": 2,
    "camera": {"path": "/absolute/camera.mkv", "sha256": "64 lowercase hex characters"},
    "gaze": {"path": "/absolute/gaze.mkv", "sha256": "64 lowercase hex characters"}
  }]
}
```

Replace the example paths, digests and count with independently specified
values. The example is not an eligible dataset declaration. Limits are 128
clips, 1–1000 frames per stream and a canonical positive rational rate up to
60 fps. Missing or unknown counts are rejected, not encoded as zero. Counts
must reflect the agreed extraction interval/filter semantics; inferring them
from whatever a decoder happened to emit defeats this control.

```sh
python3 -B research/extraction-accounting/0.1.0/extract.py \
  --plan /absolute/plan.json --plan-sha256 PLAN_FILE_SHA256 \
  --output /absolute/fresh-output --ffmpeg /absolute/ffmpeg
```

CLI exit 0 means accounting complete relative to that plan; exit 3 means a
completed accounting run is blocked; exit 2 means invalid input or an execution
exception. Process interruption or filesystem failure may leave partial files
without a final ledger. A missing ledger never admits consumption. Preserve the
failed directory and use a new destination on retry.

The CLI checks the exact supplied plan-file digest, then stores canonical JSON
and its digest in the ledger. These digests may differ if the original plan used
different whitespace. `require_complete(plan, output, expected_ledger_sha256)`
requires an expected ledger digest from the caller's trusted execution record.
Hashing whatever ledger happens to exist does not establish trustworthy origin.

## Verification and reproduction

```sh
python3 -B -m unittest discover \
  -s research/extraction-accounting/0.1.0 -p test_extract.py -v
python3 -B research/extraction-accounting/0.1.0/smoke.py \
  --artifact-root /absolute/fresh-authored-smoke --ffmpeg /absolute/ffmpeg
```

[test_extract.py](test_extract.py) uses mocked processes and authored bytes to
check membership, explicit failures, mutation rejection, schema rejection,
non-overwrite behavior and the historical failure control. Mocked frame bytes
are deliberately not presented as decoded images.

[smoke.py](smoke.py) uses installed FFmpeg to generate two 32×32, two-second
constant-color FFV1 videos, then exercises the CLI with: a complete plan, two
equally shortened streams relative to the plan, extra frames, corrupt gaze
media and a missing gaze file. It retains inputs, commands, logs, plans,
ledgers and a summary in the specified fresh directory. Requires local lavfi,
color, FFV1, Matroska and JPEG support. No downloads, GPU, weights or private
data are required. These are authored engineering controls, not research cases.

## Boundaries that remain open

- **Accounting is conditional on the declared cohort.** Matching expected
  counts does not establish that the declaration contains the complete intended
  population, unique subjects or independent sessions. A count can itself be
  wrong. It also cannot detect a substituted frame with the same ordinal/count
  if the substitution predates the trusted record.
- **Physical synchronization is not established.** Matching output ordinals is
  not matching source capture times. This helper does not retain per-frame PTS,
  clock calibration, source-frame mapping, dropped-frame timing or gaze validity.
  Both streams could have a common timing error. Any subsequent study must
  independently qualify those facts before treating a pair as a joint event.
- **No measurement is performed.** Every ledger says `not_performed`; no
  scientific, uncertainty, human-state, population or safety claim follows from
  `accounting_status: complete`.
- The tool binary is fingerprinted, not cryptographically attested. Dynamic
  libraries, decoder correctness, JPEG semantics and process authenticity are
  not independently verified. Directory ancestry and concurrent hostile writes
  are outside this local trusted-workspace control. Files can change after
  returned paths are checked; a later consumer needs a stable projection.
- The historical scripts do not call this boundary. Future H5 reuse requires a
  separately versioned consumer that cannot bypass `require_complete`, a
  qualified cohort/count/timing declaration and authorization for the intended
  experiment. Reusing old scripts leaves their original behavior intact.
- The explicit first-video-stream mapping, strict decoder errors and pinned
  command differ from old preprocessing. Byte or sample equivalence with old
  outputs is not asserted. Failures must be investigated, not silently dropped
  or converted into a smaller successful cohort.

Stop expanding this helper after the bounded correction unless an authorized
reuse case needs it. It is ordinary reliability work, not novel perception or
evidence of a commercial advantage.

## Reference status

[FFmpeg command-line documentation](https://ffmpeg.org/ffmpeg.html), inspected
10 October 2026, describes `-xerror`, `-abort_on` and decoding error handling.
This is a pointer-only reference, not retained scientific evidence. Local
FFmpeg 8.0.1 help was also inspected for the used flags; execution records must
identify the actual binary used. The live documentation is not asserted to be
an immutable specification of that installed version.
