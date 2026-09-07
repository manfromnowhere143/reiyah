#!/usr/bin/env python3
"""Exact synthetic control: proportional counts and uniform label noise differ.

This is an elementary Bernoulli error model, not a nuScenes measurement or a
physical noise model validated for Reiyah's present detector-matching process.
"""
from fractions import Fraction as F
import hashlib
import itertools
import json
from pathlib import Path


CELLS = tuple(itertools.product((0, 1), repeat=2))


def ratio(distribution):
    n = sum(distribution.values())
    a = sum(p for (x, _), p in distribution.items() if x)
    b = sum(p for (_, y), p in distribution.items() if y)
    return None if not a or not b else distribution[(1, 1)] * n / (a * b)


def corrupt(distribution, epsilon, shared):
    if not 0 <= epsilon <= 1 or set(distribution) != set(CELLS) or sum(distribution.values()) != 1:
        raise ValueError("invalid probability model")
    observed = {cell: F(0) for cell in CELLS}
    for (x, y), mass in distribution.items():
        if shared:
            masks = [((0, 0), 1 - epsilon), ((1, 1), epsilon)]
        else:
            masks = [((a, b), (epsilon if a else 1 - epsilon) * (epsilon if b else 1 - epsilon))
                     for a, b in CELLS]
        for (a, b), probability in masks:
            observed[(x ^ a, y ^ b)] += mass * probability
    return observed


def record(distribution):
    n = sum(distribution.values())
    return {"cells": {str(a) + str(b): str(mass) for (a, b), mass in distribution.items()},
            "p_A": str(sum(p for (x, _), p in distribution.items() if x) / n),
            "p_B": str(sum(p for (_, y), p in distribution.items() if y) / n),
            "p_AB": str(distribution[(1, 1)] / n), "c": None if ratio(distribution) is None else str(ratio(distribution))}


def experiment():
    truth = {(a, b): (F(1, 10) if a else F(9, 10)) * (F(1, 10) if b else F(9, 10)) for a, b in CELLS}
    epsilon = F(1, 10)
    common = corrupt(truth, epsilon, True)
    independent = corrupt(truth, epsilon, False)
    scaled = {cell: mass * F(7, 3) for cell, mass in truth.items()}
    if ratio(truth) != 1 or ratio(scaled) != 1 or ratio(common) != F(25, 9) or ratio(independent) != 1:
        raise ValueError("exact control calculation differs")
    if corrupt(truth, F(0), True) != truth or corrupt(truth, F(0), False) != truth:
        raise ValueError("zero-noise control failed")
    if record(common)["p_A"] != record(independent)["p_A"] or record(common)["p_B"] != record(independent)["p_B"]:
        raise ValueError("matched-marginal control failed")
    # Each mask distribution is independent of the true cell; all four have the same corruption probability.
    return {"artifact_id": "reiyah.uniform-reference-noise-counterexample.0.1.0", "version": "0.1.0",
            "lifecycle_status": "exploratory", "data_kind": "authored exact synthetic probability model",
            "analyzer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "truth": record(truth), "proportional_rescaling": record(scaled),
            "shared_uniform_reference_flip": record(common), "independent_reference_flips": record(independent),
            "reference_flip_probability_given_each_true_cell": {str(a) + str(b): str(epsilon) for a, b in CELLS},
            "claim_supported": "Common positive rescaling leaves c unchanged",
            "claim_refuted": "Every outcome-independent uniform reference-label corruption leaves c unchanged",
            "controls": ["True channel errors are independent", "Reference flip rate is constant over true error cells",
                         "Proportional-rescaling invariant holds", "Independent-reference ablation preserves c=1 at matched noisy marginals",
                         "Zero reference noise reproduces truth"],
            "limits": ["No observed detector, human or physical safety performance is estimated",
                       "Shared binary label corruption is not claimed to be the nuScenes matching-error mechanism",
                       "This does not refute M4's rescaling theorem; it refutes the broader immunity interpretation",
                       "No novelty is claimed for this elementary label-noise construction"]}


if __name__ == "__main__":
    print(json.dumps(experiment(), indent=2, sort_keys=True))
