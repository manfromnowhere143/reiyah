"""A fair comparison of three ways to decide the same question.

The question: does a probability measure on [0,1] reproduce a population's
subset-averaged k-wise silence moments? Three methods are compared on the two
retained nuScenes populations, on identical inputs, with their costs measured.

  screen   the finite-difference complete-monotonicity check. Cheapest, and the
           method the predecessor lane adopted mid-stream. It is automatic at
           order K and so cannot refute anything at that order.
  grid     minimise the uniform moment error over a rational atom grid. Sound
           for feasibility: a grid measure is a measure. Not sound for
           infeasibility: a grid restricts the support.
  exact    the certificate procedure in this lane.

This module deliberately reimplements the screen and the grid search rather than
importing the predecessor's tools, so the comparison does not depend on them.
"""
from fractions import Fraction
import json
import sys
import time

import moment_cone_certificate as exact
from moment_cone_certificate import simplex_feasible

POPULATIONS = {
    "all annotated objects": ["0.207356", "0.102807", "0.069423", "0.055554", "0.047427"],
    "most observable": ["0.043834", "0.010316", "0.004383", "0.002826", "0.002196"],
}
RETAINED_VERDICT = {"all annotated objects": "refuted", "most observable": "not refuted"}


def complete_monotonicity_screen(moments):
    """Non-negativity of (-1)^j Delta^j m_i for i + j <= n."""
    order = len(moments) - 1
    table = [moments[:]]
    for _ in range(order):
        previous = table[-1]
        table.append([previous[i] - previous[i + 1] for i in range(len(previous) - 1)])
    for degree, row in enumerate(table):
        for index, value in enumerate(row):
            if index + degree <= order and value < 0:
                return False, f"negative difference at i={index}, j={degree}"
    return True, "every admissible finite difference is nonnegative"


def grid_admits_error(moments, denominator, bound):
    """Is there a measure on the uniform grid whose moments are within `bound`?

    Exact rational feasibility, phrased directly rather than by bisection so the
    cost stays proportional to the number of probes actually reported.
    """
    atoms = [Fraction(j, denominator) for j in range(denominator + 1)]
    order = len(moments) - 1
    columns = len(atoms)
    slack = 2 * order
    surplus = 2 * order
    width = columns + slack + surplus
    rows, targets = [], []
    for power in range(order + 1):
        row = [Fraction(0)] * width
        for index, atom in enumerate(atoms):
            row[index] = atom ** power
        if power > 0:
            row[columns + 2 * (power - 1)] = Fraction(-1)
            row[columns + 2 * (power - 1) + 1] = Fraction(1)
        rows.append(row)
        targets.append(moments[power])
    for index in range(slack):
        row = [Fraction(0)] * width
        row[columns + index] = Fraction(1)
        row[columns + slack + index] = Fraction(1)
        rows.append(row)
        targets.append(bound)
    return simplex_feasible(rows, targets, width) is not None


def grid_profile(moments, denominator, probes):
    """Which uniform error levels the grid can reach, smallest first."""
    outcome = {}
    for bound in probes:
        outcome[str(bound)] = grid_admits_error(moments, denominator, bound)
    return outcome


def main(argv):
    report = {"artifact_id": "reiyah.moment-cone.method-comparison", "version": "0.1.0",
              "populations": {}}
    for name, values in POPULATIONS.items():
        moments = [Fraction(1)] + [Fraction(text) for text in values]
        entry = {"retained_verdict": RETAINED_VERDICT[name]}

        start = time.perf_counter()
        passes, note = complete_monotonicity_screen(moments)
        entry["screen"] = {"refutes": not passes, "note": note,
                           "seconds": round(time.perf_counter() - start, 6)}

        start = time.perf_counter()
        probes = [Fraction(1, 10 ** power) for power in (3, 4, 5, 6, 7)]
        profile = {}
        for denominator in (200, 800):
            profile[denominator] = grid_profile(moments, denominator, probes)
        entry["grid"] = {"error_level_reachable": profile,
                         "sound_for_feasibility": True,
                         "sound_for_infeasibility": False,
                         "seconds": round(time.perf_counter() - start, 3)}

        start = time.perf_counter()
        # No grid is pinned here, so this measures the shipped default ladder
        # rather than a denominator chosen to flatter the comparison.
        task = {"schema_id": "reiyah.moment-cone.task", "channel_count": len(values),
                "moments": values, "rounding_half_width": "0.0000005"}
        outcome = exact.decide(task)
        entry["exact"] = {"verdict": outcome["verdict"],
                          "certificate": outcome["certificate"],
                          "seconds": round(time.perf_counter() - start, 3)}
        report["populations"][name] = entry
    json.dump(report, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
