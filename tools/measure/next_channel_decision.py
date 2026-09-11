"""Does the moment-cone diagnostic help a named next-channel decision?

The user is a perception-validation lead with an installed configuration, deciding
whether an added observer earns further integration work. This module builds the
smallest comparison that answers whether a model-representability diagnostic
improves that decision beyond a conventional analysis with the same evidence.

Three methods are put to the same question on the same population:

  cone        is the subset-averaged moment vector representable by a scalar iid
              mixture? A yes or no about a model, not about a channel.
  independent predict the added benefit assuming the candidate is independent of
              the installed set, at its own measured marginal rate. The serious
              conventional baseline, and not an equal-rate straw man.
  labelled    read the benefit directly off the labelled joint cells.

The restricted query is miss-only and is stated exactly:

  benefit(C, j) = P(every channel in C silent AND j observes)
                = P(every channel in C silent) - P(every channel in C+{j} silent)

under one shared reference and one shared opportunity population. This is not the
Engine's detector loss. It carries no false-positive term, no unmatched
predictions and no matching competition, so it must not be used to infer
false-detection cost, planner effect or crash risk.

Aggregate counts only. Standard library plus the retained caches, read only.
"""
from fractions import Fraction
from itertools import combinations
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from silence_histograms import CHANNELS, FLOOR, digest, load_scores  # noqa: E402


def cell_counts(silent, rows):
    """Count of opportunities for each of the 2^K silence patterns."""
    counts = {}
    for index in range(rows):
        key = tuple(channel[index] for channel in silent)
        counts[key] = counts.get(key, 0) + 1
    return counts


def all_silent(counts, subset, total):
    hits = sum(n for pattern, n in counts.items() if all(pattern[j] for j in subset))
    return Fraction(hits, total)


def main(argv):
    if len(argv) != 2:
        sys.stderr.write("usage: next_channel_decision.py CACHE_DIR\n")
        return 2
    cache = argv[1]
    paths = {n: os.path.join(cache, n) for n in
             ["gt_val_cache.json"] + [f"matched_{c}.json" for c in CHANNELS]}
    before = {n: digest(p) for n, p in paths.items()}
    with open(paths["gt_val_cache.json"], "r", encoding="utf-8") as handle:
        rows = len(json.load(handle))
    silent = []
    for channel in CHANNELS:
        scores, _assigned = load_scores(paths[f"matched_{channel}.json"], rows)
        silent.append([Fraction(str(score)) < FLOOR for score in scores])
    counts = cell_counts(silent, rows)
    if sum(counts.values()) != rows:
        raise ValueError("cell counts do not partition the population")

    marginals = [all_silent(counts, (j,), rows) for j in range(len(CHANNELS))]
    out = {"artifact_id": "reiyah.moment-cone.next-channel-decision", "version": "0.1.0",
           "opportunities": rows, "score_floor": "0.10",
           "query": "benefit(C, j) = P(all of C silent) - P(all of C and j silent)",
           "scope": ("miss only, one shared reference and opportunity population; carries no "
                     "false-positive term, no unmatched predictions and no matching competition"),
           "marginal_silent_rates": {CHANNELS[j]: str(marginals[j]) for j in range(len(CHANNELS))},
           "inputs": before, "decisions": []}

    for candidate in range(len(CHANNELS)):
        installed = tuple(j for j in range(len(CHANNELS)) if j != candidate)
        base = all_silent(counts, installed, rows)
        joint = all_silent(counts, installed + (candidate,), rows)
        observed = base - joint
        predicted = base * (1 - marginals[candidate])
        out["decisions"].append({
            "installed": [CHANNELS[j] for j in installed],
            "candidate": CHANNELS[candidate],
            "installed_all_silent": str(base),
            "installed_and_candidate_all_silent": str(joint),
            "observed_benefit": str(observed),
            "independent_prediction": str(predicted),
            "prediction_over_observed": (str(predicted / observed) if observed != 0 else "undefined"),
        })
    json.dump(out, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
