#!/usr/bin/env python3
"""Exact observational-equivalence controls for a binary reference model.

All opportunities in the binary example are known and observed. A separate
omitted-opportunity construction concerns a different selection problem.
Neither construction estimates a nuScenes noise process or physical risk.
"""
from fractions import Fraction as F
import hashlib
import itertools
import json
from pathlib import Path


BITS = (0, 1)
CELL_ORDER = ((1, 1), (1, 0), (0, 1), (0, 0))


def coefficient(cells):
    a, b, c, d = cells
    return None if (a + b) * (a + c) == 0 else a * sum(cells) / ((a + b) * (a + c))


def observed(world):
    answer = {key: F(0) for key in itertools.product(BITS, repeat=3)}
    for (y, a, b, r), mass in world.items():
        answer[a, b, r] += mass
    return answer


def error_cells(world, target="truth", condition_truth=None):
    cells = {key: F(0) for key in CELL_ORDER}
    for (y, a, b, r), mass in world.items():
        if condition_truth is not None and y != condition_truth:
            continue
        label = y if target == "truth" else r
        cells[a ^ label, b ^ label] += mass
    total = sum(cells.values())
    if not total:
        raise ValueError("empty conditional population")
    return tuple(cells[k] / total for k in CELL_ORDER)


def independent_world():
    world = {}
    for y, ea, eb, er in itertools.product(BITS, repeat=4):
        mass = F(1, 2)
        for error in (ea, eb, er):
            mass *= F(1, 10) if error else F(9, 10)
        world[y, y ^ ea, y ^ eb, y ^ er] = mass
    return world


def world_with_reference_flips(observation, flip_masses):
    """Lift aggregate reference-flip masses to a complete joint (Y,A,B,R) law."""
    if any(not isinstance(v, F) for v in flip_masses) or len(flip_masses) != 4:
        raise ValueError("four exact flip masses are required")
    groups = {key: sum(p for (a, b, r), p in observation.items() if (a ^ r, b ^ r) == key) for key in CELL_ORDER}
    rates = {}
    for key, mass in zip(CELL_ORDER, flip_masses):
        if not 0 <= mass <= groups[key]:
            raise ValueError("reference-flip mass exceeds the observed cell")
        rates[key] = mass / groups[key] if groups[key] else F(0)
    world = {key: F(0) for key in itertools.product(BITS, repeat=4)}
    for (a, b, r), mass in observation.items():
        flip = rates[a ^ r, b ^ r]
        world[r, a, b, r] += mass * (1 - flip)
        world[1 - r, a, b, r] += mass * flip
    return world


def symmetric_fixture_bounds(epsilon):
    """Sharp bounds for this one observed table, for 0 <= epsilon <= 9/100.

    epsilon bounds total P(Y != R). No conditional-independence assumption is
    imposed. This function is deliberately not a general-purpose noise solver.
    """
    if not isinstance(epsilon, F) or not F(0) <= epsilon <= F(9, 100):
        raise ValueError("this fixture requires an exact error budget from 0 to 9/100")
    a = F(9, 100)
    return (a - epsilon) / (2 * a - epsilon)**2, a / ((2 * a)**2 - epsilon**2)


def encode(distribution):
    return {"".join(map(str, key)): str(mass) for key, mass in sorted(distribution.items())}


def describe(world):
    if sum(world.values()) != 1 or any(mass < 0 for mass in world.values()):
        raise ValueError("invalid probability world")
    truth = error_cells(world)
    reference = error_cells(world, target="reference")
    conditional = {str(y): str(coefficient(error_cells(world, condition_truth=y))) for y in BITS}
    return {"joint_probability_order": ["Y", "A", "B", "R"], "joint_probabilities": encode(world),
            "true_error_cells": [str(v) for v in truth], "true_coefficient": str(coefficient(truth)),
            "true_coefficient_given_truth": conditional,
            "reference_error_probability": str(sum(p for (y, _, _, r), p in world.items() if y != r)),
            "reference_relative_error_cells": [str(v) for v in reference],
            "reference_relative_coefficient": str(coefficient(reference))}


def experiment():
    independent = independent_world()
    observation = observed(independent)
    perfect_reference = world_with_reference_flips(observation, (F(0),) * 4)
    first, second = describe(independent), describe(perfect_reference)
    if observed(perfect_reference) != observation or first["true_coefficient"] != "1" or second["true_coefficient"] != "25/9":
        raise ValueError("observational-equivalence construction failed")
    expected = {key: F(73, 200) if key in ((0, 0, 0), (1, 1, 1)) else F(9, 200)
                for key in itertools.product(BITS, repeat=3)}
    if observation != expected:
        raise ValueError("complete observable distribution differs")
    sensitivities = []
    for epsilon in (F(0), F(1, 100), F(1, 20), F(2, 25), F(9, 100)):
        lower, upper = symmetric_fixture_bounds(epsilon)
        low_world = world_with_reference_flips(observation, (epsilon, F(0), F(0), F(0)))
        high_world = world_with_reference_flips(observation, (F(0), F(0), epsilon, F(0)))
        if (coefficient(error_cells(low_world)) != lower or coefficient(error_cells(high_world)) != upper
                or observed(low_world) != observation or observed(high_world) != observation):
            raise ValueError("sharpness witness failed")
        sensitivities.append({"total_reference_error_budget": str(epsilon), "sharp_interval": [str(lower), str(upper)],
                              "lower_world": describe(low_world), "upper_world": describe(high_world)})
    recorded = (F(100), F(900), F(900), F(8100))
    omitted = 50
    augmented = (recorded[0] + omitted, *recorded[1:])
    if coefficient(recorded) != 1 or coefficient(augmented) != F(67, 49):
        raise ValueError("omitted-opportunity witness failed")
    return {"artifact_id": "reiyah.reference-identification-counterexamples.0.1.0", "version": "0.1.0",
            "lifecycle_status": "exploratory", "data_kind": "authored exact synthetic probability models",
            "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "binary_error_cell_order": ["both", "a_only", "b_only", "neither"],
            "complete_observable_probability_order": ["A", "B", "R"],
            "complete_observable_probabilities": encode(observation),
            "observationally_equivalent_worlds": {"independent_detectors_noisy_reference": first,
                                                  "dependent_detectors_perfect_reference": second},
            "same_complete_observable_distribution": True, "true_coefficient_point_identified": False,
            "reference_error_budget_sensitivity": sensitivities,
            "minimum_total_reference_error_budget_allowing_c_at_most_one_in_this_fixture": "2/25",
            "omitted_opportunity_pair": {"same_recorded_cells_in_both_worlds": [str(v) for v in recorded],
                "world_one": {"unrecorded_true_both_errors": 0, "true_coefficient": "1"},
                "world_two": {"unrecorded_true_both_errors": omitted, "true_cells": [str(v) for v in augmented], "true_coefficient": "67/49"},
                "observation_scope": "Recorded object opportunities; this does not assert identical raw sensor images"},
            "limits": ["Complete binary opportunities are assumed only in the first construction",
                       "The second construction concerns an unobserved opportunity population and a different selection problem",
                       "The 8 percent threshold applies only to the authored table and total binary reference-flip budget",
                       "No calibrated error budget, independent human judgment, physical estimate or safety conclusion is supplied",
                       "The examples are elementary identifiability controls; no novelty claim"]}


if __name__ == "__main__":
    print(json.dumps(experiment(), indent=2, sort_keys=True))
