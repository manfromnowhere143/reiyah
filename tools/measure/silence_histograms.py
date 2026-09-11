"""Exact integer silence histograms per declared population.

The moment-cone decision is exact when its input is the integer count of
opportunities on which exactly s channels were silent. This tool produces those
counts directly from the retained matched-prediction caches, so a certificate can
be asked of the exact rationals rather than of printed decimals.

It is written independently of the redundancy-scaling lane's own tool and imports
nothing from it. Its correctness gate is that it reproduces that lane's published
row counts and, where the histogram is already recoverable from published
summaries, the histogram itself. If a gate fails the tool refuses to emit,
because an unvalidated population definition would silently certify the wrong set.

The cache directory is a command-line argument and is never recorded in the
output. Only aggregate counts are emitted: no per-object row, annotation token,
prediction, coordinate or source-derived identifier leaves this program.
"""
from fractions import Fraction
from math import comb
import hashlib
import json
import os
import sys
import time

FLOOR = Fraction(1, 10)
CHANNELS = ("mapillary", "fcos3d", "megvii", "pointpillars", "centerpoint")

# Published by the redundancy-scaling lane. These are the gate, not the output.
EXPECTED_ROWS = {
    "all annotated objects": 134565,
    "most observable": 25049,
    "radar returns at least 3": 21890,
    "range 0-20 m": 54624,
    "range 20-30 m": 38243,
    "range 30-40 m": 26386,
    "range 40-50 m": 15312,
}
EXPECTED_HISTOGRAM = {
    "all annotated objects": (70970, 25485, 18533, 7727, 5468, 6382),
    "most observable": (21344, 2475, 864, 232, 79, 55),
}


def digest(path):
    with open(path, "rb") as handle:
        return "sha256:" + hashlib.sha256(handle.read()).hexdigest()


def load_scores(path, rows):
    """Score per row for one channel, with the absent-row meaning stated explicitly.

    The matched file records, per class, the score of the detection matched to each
    annotation row. A row absent from it means the channel emitted no same-class
    detection within the matching radius for that annotation. Under this evaluation
    that is an **evaluated miss**, not unavailable input: the channel was run over
    every sample and its output was scored. Absence would mean unavailable input only
    if a channel had not been evaluated on part of the population, which the coverage
    figures returned here let a reader check.

    Duplicate row keys, non-integer rows, rows outside range and non-finite or
    out-of-range scores are refused rather than coerced.
    """
    with open(path, "r", encoding="utf-8") as handle:
        body = json.load(handle)
    if "matched_at_2m" not in body:
        raise ValueError(f"{os.path.basename(path)} has no matched_at_2m table")
    matched = body["matched_at_2m"]
    scores = [None] * rows
    assigned = 0
    for class_name, per_row in matched.items():
        if not isinstance(per_row, dict):
            raise ValueError(f"class {class_name} does not carry a row table")
        for row, score in per_row.items():
            index = int(row)
            if not 0 <= index < rows:
                raise ValueError(f"row {index} is outside the annotation range")
            if scores[index] is not None:
                raise ValueError(f"row {index} is matched more than once")
            if not isinstance(score, (int, float)) or isinstance(score, bool):
                raise ValueError(f"row {index} carries a non-numeric score")
            if not 0.0 <= float(score) <= 1.0:
                raise ValueError(f"row {index} carries a score outside [0,1]")
            scores[index] = float(score)
            assigned += 1
    return [0.0 if value is None else value for value in scores], assigned


def populations(ground_truth):
    nl = [g["nl"] for g in ground_truth]
    dist = [g["dist"] for g in ground_truth]
    vis = [g["vis"] for g in ground_truth]
    nr = [g["nr"] for g in ground_truth]
    n = len(ground_truth)
    return [
        ("all annotated objects", [True] * n),
        ("most observable", [nl[i] >= 20 and vis[i] == "v80-100" and dist[i] < 20
                             for i in range(n)]),
        ("radar returns at least 3", [nr[i] >= 3 for i in range(n)]),
        ("range 0-20 m", [dist[i] < 20 for i in range(n)]),
        ("range 20-30 m", [20 <= dist[i] < 30 for i in range(n)]),
        ("range 30-40 m", [30 <= dist[i] < 40 for i in range(n)]),
        ("range 40-50 m", [40 <= dist[i] < 50 for i in range(n)]),
    ]


def moments(histogram, channels):
    total = sum(histogram)
    return [Fraction(sum(histogram[s] * comb(s, k) for s in range(channels + 1)),
                     total * comb(channels, k)) for k in range(1, channels + 1)]


def main(argv):
    if len(argv) not in (2, 3):
        sys.stderr.write("usage: silence_histograms.py CACHE_DIR [EXPECTED_INPUTS.json]\n")
        return 2
    cache = argv[1]
    expected_path = argv[2] if len(argv) > 2 else None
    inputs = ["gt_val_cache.json"] + [f"matched_{c}.json" for c in CHANNELS]
    paths = {name: os.path.join(cache, name) for name in inputs}

    # Source identity is taken before anything is parsed, and again afterwards, so a
    # file changing under the run is detected rather than assumed impossible.
    before = {name: digest(path) for name, path in paths.items()}
    if expected_path is not None:
        with open(expected_path, "r", encoding="utf-8") as handle:
            expected = json.load(handle)["inputs"]
        mismatched = [name for name in inputs if expected.get(name) != before[name]]
        if mismatched:
            sys.stderr.write("REFUSED: input identities do not match the pre-bound expectation\n")
            for name in mismatched:
                sys.stderr.write(f"  {name}\n")
            return 1

    started = time.time()
    with open(paths["gt_val_cache.json"], "r", encoding="utf-8") as handle:
        ground_truth = json.load(handle)
    rows = len(ground_truth)
    silent, coverage = [], {}
    for channel in CHANNELS:
        scores, assigned = load_scores(paths[f"matched_{channel}.json"], rows)
        coverage[channel] = {"rows_with_a_matched_detection": assigned,
                             "rows_without": rows - assigned}
        silent.append([Fraction(str(score)) < FLOOR for score in scores])

    failures = []
    out = {"artifact_id": "reiyah.moment-cone.silence-histograms", "version": "0.1.0",
           "channels": list(CHANNELS), "score_floor": "0.10",
           "total_annotation_rows": rows, "populations": {}}
    for label, mask in populations(ground_truth):
        selected = [i for i in range(rows) if mask[i]]
        histogram = [0] * (len(CHANNELS) + 1)
        for index in selected:
            histogram[sum(1 for channel in silent if channel[index])] += 1
        expected_rows = EXPECTED_ROWS.get(label)
        if expected_rows is not None and len(selected) != expected_rows:
            failures.append(f"{label}: {len(selected)} rows against the published {expected_rows}")
        expected_hist = EXPECTED_HISTOGRAM.get(label)
        if expected_hist is not None and tuple(histogram) != expected_hist:
            failures.append(f"{label}: histogram {tuple(histogram)} against the published {expected_hist}")
        out["populations"][label] = {
            "opportunities": len(selected),
            "silence_histogram": histogram,
            "moments": [str(value) for value in moments(histogram, len(CHANNELS))],
        }

    after = {name: digest(path) for name, path in paths.items()}
    changed = [name for name in inputs if before[name] != after[name]]
    if changed:
        sys.stderr.write("REFUSED: an input changed during the run\n")
        return 1
    out["gates"] = {"row_counts_checked": len(EXPECTED_ROWS),
                    "histograms_checked": len(EXPECTED_HISTOGRAM),
                    "failures": failures}
    out["inputs"] = {name: before[name] for name in inputs}
    out["input_identity_prebound"] = expected_path is not None
    out["inputs_unchanged_across_the_run"] = True
    out["channel_coverage"] = coverage
    out["absent_row_meaning"] = ("an annotation row absent from a channel's matched table is an "
                                 "evaluated miss for that channel, not unavailable input; the "
                                 "coverage counts above let a reader check that claim")
    out["elapsed_seconds"] = round(time.time() - started, 3)
    out["disclosure"] = ("aggregate counts only: no annotation token, prediction, coordinate, row "
                         "index or file path is emitted. These are counts over a public benchmark "
                         "split at the granularity the redundancy-scaling lane already publishes. "
                         "They are not automatically anonymous and were assessed as such, not "
                         "assumed to be so because they are small")
    if failures:
        sys.stderr.write("REFUSED: the population definition does not reproduce published values\n")
        for line in failures:
            sys.stderr.write(f"  {line}\n")
        return 1
    json.dump(out, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
