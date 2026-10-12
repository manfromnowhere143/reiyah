#!/usr/bin/env python3
"""Check six authored interpretation cases against a byte-pinned native scorer.

No Waymo data, model or server is used. Obtain the source separately under its
terms; this script does not download or redistribute it. Requires NumPy.
"""

import argparse
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path

import numpy as np


PROTOCOL_SHA256 = "72c86e1c8faa4a3fff3ede3433eb965923598cdb898448102c0dd0d15fa74f84"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    protocol_bytes = Path(__file__).with_name("protocol.json").read_bytes()
    if digest(protocol_bytes) != PROTOCOL_SHA256:
        raise ValueError("protocol digest mismatch")
    protocol = json.loads(protocol_bytes)
    source = args.native.read_bytes()
    if digest(source) != protocol["source_sha256"]:
        raise ValueError("native source digest mismatch")
    # Execute the already verified bytes, avoiding a second source-file read.
    spec = importlib.util.spec_from_loader("pinned_native_rater_score", loader=None)
    native = importlib.util.module_from_spec(spec)
    exec(compile(source, "pinned_native_rater_score", "exec"), native.__dict__)

    time = np.arange(1, 21, dtype=np.float64) / 4
    x = 10 * time
    zero = np.zeros_like(time)
    side = 6 * np.minimum(time / 2.5, 1)
    references = [np.stack([x, y], axis=-1) for y in (zero, side, -side)]
    switch = 3 * np.maximum(time - 3, 0)
    excursion = 6 * np.maximum(1 - np.abs(time - 4), 0)
    far = 100 * np.minimum(time / 2.5, 1)
    ys = [zero, switch, switch, excursion, far, switch]
    trajectories = np.stack([np.stack([x, y], axis=-1) for y in ys])
    cases = protocol["cases"]
    expected_scores = np.array([c["expected_score"] for c in cases])
    expected_trust = np.array([c["expected_trust"] for c in cases])
    calls = []

    def evaluate(indices, permutation=(0, 1, 2), name="canonical"):
        outputs = native.get_rater_feedback_score(
            trajectories[indices, None, :, :].copy(),
            np.ones((len(indices), 1), dtype=np.float64),
            [[references[j].copy() for j in permutation] for _ in indices],
            [np.array([cases[i]["labels"][j] for j in permutation], dtype=np.float64)
             for i in indices],
            np.full(len(indices), 10.0),
        )
        scores = outputs["rater_feedback_score"]
        trust = outputs["is_fully_within_trust_region"][:, 0]
        if scores.shape != (len(indices),) or trust.shape != (len(indices),):
            raise AssertionError("unexpected native output shape")
        np.testing.assert_allclose(scores, expected_scores[indices], rtol=0, atol=1e-12)
        np.testing.assert_array_equal(trust, expected_trust[indices])
        calls.append({"name": name, "case_indices": indices,
                      "reference_permutation": list(permutation),
                      "scores": scores.tolist(), "trust": trust.tolist()})
        return scores, trust

    scores, trust = evaluate(list(range(6)))
    for i in range(6):
        evaluate([i], name=f"singleton_{i}")
    evaluate(list(reversed(range(6))), name="reverse_batch")
    for order in itertools.permutations(range(3)):
        evaluate(list(range(6)), order, name="reference_permutation")

    rows = []
    for i, case in enumerate(cases):
        rows.append({
            "id": case["id"], "score": float(scores[i]),
            "same_reference_trust": bool(trust[i]),
            "prediction_y_at_3_and_5_seconds": ys[i][[11, 19]].tolist(),
            "max_absolute_y_from_reference_0": float(np.max(np.abs(ys[i]))),
        })
    result = {
        "artifact_id": "reiyah.rater-score-contract.result", "version": "0.1.0",
        "status": "exploratory", "all_declared_checks_pass": True,
        "protocol_sha256": digest(protocol_bytes),
        "native_source_sha256": digest(source),
        "reproduction_script_sha256": digest(Path(__file__).read_bytes()),
        "authored_cases": 6, "native_calls": len(calls),
        "case_evaluations": sum(len(c["case_indices"]) for c in calls),
        "cases": rows, "calls": calls,
        "scope": "Authored source-semantics witnesses; not dataset outcomes, server replication, physical validity or workflow advantage",
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
