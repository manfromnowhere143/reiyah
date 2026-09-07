#!/usr/bin/env python3
"""Retrospective arithmetic audit of selected, privately retained sibling artifacts.

Never imports or executes sibling code. This does not rerun planners, providers,
simulators, human adjudication, or the siblings' validation/release systems.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import gzip
import hashlib
import json
from pathlib import Path
import random
import re
import statistics


def retained(root: Path, project: str, path: str) -> bytes:
    ledger = json.loads((root / "sibling-source-ledger.json").read_text())
    rows = [r for r in ledger["entries"] if r["project"] == project and r["path"] == path]
    if len(rows) != 1:
        raise ValueError("source must resolve exactly once")
    raw = (root / "sibling-sources" / project / path).read_bytes()
    if len(raw) != rows[0]["byte_size"] or hashlib.sha256(raw).hexdigest() != rows[0]["sha256"]:
        raise ValueError("retained source bytes changed")
    return raw


def sentinel(root: Path) -> dict:
    base = "experiments/iter134_neuroncap_placebo_semantics_execution/"
    raw = retained(root, "sentinel", base + "proof/sentinel-i134.log.gz")
    records = defaultdict(list)
    active = None
    for line in gzip.decompress(raw).decode("utf-8").splitlines():
        header = re.fullmatch(r"##### I134PAIR (off|union|placebo) (stationary|frontal|side) (\d+) #####", line)
        if header:
            active = tuple(header.groups())
            if active in records:
                raise ValueError("duplicate arm/pair header")
            records[active] = []
        match = re.match(r"^ncap_score: ([0-9.]+),  impact_speed: ([0-9.]+),", line)
        if match:
            if active is None:
                raise ValueError("unbound score")
            score, impact = map(float, match.groups())
            if not 0 <= score <= 5 or impact < 0:
                raise ValueError("score outside retained protocol scale")
            records[active].append((score, impact))
    arms = ("off", "union", "placebo")
    classes = ("stationary", "frontal", "side")
    pairs = sorted({key[1:] for key in records})
    if len(pairs) != 20 or len(records) != 60 or any(len(v) != 20 for v in records.values()):
        raise ValueError("incomplete fixed 3-arm/20-pair/20-run record")
    means = {key: statistics.mean(v[0] for v in values) for key, values in records.items()}
    scores = {a: statistics.mean(statistics.mean(means[a, c, s] for c0, s in pairs if c0 == c)
                                 for c in classes) for a in arms}
    rng = random.Random(134)
    deltas = []
    incomplete_draws = 0
    for _ in range(10000):
        draw = [pairs[rng.randrange(len(pairs))] for _ in pairs]
        components = []
        for c in classes:
            diffs = [means["union", c, s] - means["placebo", c, s] for c0, s in draw if c0 == c]
            components.append(statistics.mean(diffs) if diffs else 0.0)
        incomplete_draws += any(not any(c0 == c for c0, _ in draw) for c in classes)
        # Deliberately reconstruct the historical zero-component convention,
        # disclose its frequency, and do not recommend it for a new design.
        deltas.append(statistics.mean(components))
    deltas.sort()
    interval = [round(deltas[250], 4), round(deltas[9749], 4)]
    decisions = [json.loads(line) for line in gzip.decompress(retained(
        root, "sentinel", base + "proof/sentinel_i134_placebo.jsonl.gz")).decode().splitlines()]
    expected = json.loads(retained(root, "sentinel", base + "proof/placebo134_report.json"))
    recomputed = {
        "arm_episode_counts": {a: sum(len(v) for k, v in records.items() if k[0] == a) for a in arms},
        "arm_ncap_class_weighted": {a: round(scores[a], 4) for a in arms},
        "arm_collision_fraction": {a: sum(x[1] > 0 for k, v in records.items() if k[0] == a for x in v) / 400 for a in arms},
        "primary_union_minus_placebo": round(scores["union"] - scores["placebo"], 4),
        "historical_primary_ci": interval,
        "primary_interval_reproduces": interval == expected["primary_union_minus_placebo"]["ci_ncap"],
        "placebo_brake_rows": sum(row.get("brake") is True for row in decisions),
        "placebo_frame_rows": sum(row.get("frame") is True for row in decisions),
        "frame_rows_missing_pair_key": sum(row.get("frame") is True and "pair" not in row for row in decisions),
        "historical_report_frame_count": expected["placebo_realized_frames"],
        "bootstrap_draws_missing_a_class": incomplete_draws,
        "bootstrap_draw_count": 10000,
        "scenario_class_pairs": len(pairs),
        "distinct_scene_identifiers": len({s for _, s in pairs}),
    }
    recomputed["all_arm_ncap_reproduce"] = all(recomputed["arm_ncap_class_weighted"][a] == expected[a + "_ncap"] for a in arms)
    recomputed["scope"] = "Independent aggregation of retained execution logs; no new simulation or safe-progress replay"
    return recomputed


def telos(root: Path) -> dict:
    raw = retained(root, "telos", "experiments/iter231_gold_free_execution_oracle/proof/oracle_result.json")
    source = json.loads(raw)
    rows = source["rows"]
    if len({(r["run"], r["instance_id"]) for r in rows}) != len(rows):
        raise ValueError("duplicate Telos opportunity")
    output = {}
    for label in ("certified_yet_wrong", "certified_correct"):
        group = [r for r in rows if r["label"] == label]
        observed = [r for r in group if r["outcome"] == "observed"]
        flagged = [r for r in observed if r["flagged"] is True]
        failed = [r for r in flagged if r["instrument_failure"] is not None]
        n, k, u = len(group), len(flagged), len(group) - len(observed)
        output[label] = {"opportunities": n, "observed": len(observed), "flags": k,
                         "missing": u, "observed_lower": [k, n], "missing_upper": [k + u, n],
                         "complete_case": [k, n - u], "flagged_instrument_failures": len(failed),
                         "adjusted_flags": k - len(failed)}
    output["scope"] = "Reaggregation of retained adjudicator rows; labels and instrument-failure diagnoses not independently verified"
    output["external_semantic_ground_truth"] = "unestablished"
    return output


def inbar(root: Path) -> dict:
    raw = retained(root, "inbar", "experiments/iter001_physical_causal_evidence_acquisition/proof/susceptibility_confirmatory_v1/reconstruction.json")
    source = json.loads(raw)
    def key(row):
        return row["baseline_command"], row["mechanism_key"], row["severity"]
    predictions = {key(r): r for r in source["predictions"]}
    if len(predictions) != len(source["predictions"]):
        raise ValueError("duplicate prediction cell")
    cells = source["measurements"]
    if len({(*key(r), r["seed"]) for r in cells}) != len(cells):
        raise ValueError("duplicate measurement cell")
    def masked(row):
        return row["separability_pre_permille"] >= 1000 and row["separability_post_permille"] < 1000
    joined = [(r, masked(predictions[key(r)]), masked(r)) for r in cells]
    # Retain the historical informative-baseline definition instead of selecting
    # a new subgroup or relabeling the excluded baseline as a fresh control.
    informative = [r for r in joined if r[0]["baseline_command"] in (30, 45)]
    counts = Counter((pred, actual) for _, pred, actual in informative)
    tp, fp, fn, tn = (counts[k] for k in [(True, True), (True, False), (False, True), (False, False)])
    return {
        "scope": "Reaggregation of retrospective reconstructed cells; not historical run recovery or a new simulator experiment",
        "historical_execution_artifact_retained": source["historical_execution_artifact_retained"],
        "prediction_cells": len(predictions), "measurement_cells": len(cells),
        "informative_cells": len(informative), "agreement": [tp + tn, len(informative)],
        "confusion": {"true_positive": tp, "false_positive": fp, "false_negative": fn, "true_negative": tn},
        "always_negative_accuracy": [tn + fp, len(informative)],
        "always_negative_clears_frozen_90_percent_rule": 10 * (tn + fp) >= 9 * len(informative),
        "exact_commands": sum(r["commanded_correction"] == predictions[key(r)]["predicted_command"] for r, _, _ in informative),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--private-root", type=Path, required=True)
    args = parser.parse_args()
    result = {
        "artifact_id": "reiyah.sibling-evidence-audit.0.1.0", "version": "0.1.0",
        "lifecycle_status": "exploratory", "scientific_authority_imported": False,
        "source_ledger_sha256": hashlib.sha256((args.private_root / "sibling-source-ledger.json").read_bytes()).hexdigest(),
        "analyzer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "sentinel": sentinel(args.private_root), "telos": telos(args.private_root), "inbar": inbar(args.private_root),
    }
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
