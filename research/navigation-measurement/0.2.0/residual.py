"""Two complementary margins preserve one scalar residual world."""

from fractions import Fraction as F

from common import require
from envelope import solve
from responses import canonical_partition, plan, response_status


def model(observed, rate, tolerance, sign):
    require(sign in (-1, 1), "margin_sign")
    return dict(
        id="residual-positive" if sign == 1 else "residual-negative",
        horizon_s=["0", "1/5"],
        threshold_mps="0",
        quantity=dict(
            kind="recorded_north_velocity_margin",
            unit="m/s",
            provenance="conditional_recorded_reconstruction",
        ),
        motion=dict(kind="global_lipschitz", rate_mps2=str(rate)),
        clock=dict(kind="common_offset", radius_s="0"),
        observations=[
            dict(
                id=f"sample-t-{t.numerator}-{t.denominator}",
                time_s=str(t),
                interval_mps=[str(tolerance + sign * value)] * 2,
            )
            for t, value in sorted(observed)
        ],
    )


def joint_status(one, two):
    if one == "inconsistent_premises" or two == "inconsistent_premises":
        return "inconsistent_premises"
    if one == two == "supported":
        return "supported"
    if "contradicted" in (one, two):
        return "contradicted"
    require(
        one in ("supported", "unresolved") and two in ("supported", "unresolved"),
        "joint_scope",
    )
    return "unresolved"


def evaluate(observed, rate, tolerance):
    models = [model(observed, rate, tolerance, sign) for sign in (1, -1)]
    answers = [solve(m) for m in models]
    state = joint_status(*(a["status"] for a in answers))
    proof = [dict(model=m, result=a) for m, a in zip(models, answers)]
    if state == "inconsistent_premises":
        return dict(status=state), proof
    high = tolerance - min(F(a["minimum_range_mps"][0]) for a in answers)
    low = max(abs(value) for _, value in observed)
    return dict(status=state, uniform_error_range_mps=[str(low), str(high)]), proof


def next_index(observed, rate, available, times):
    best = None
    for i in sorted(available):
        t = times[i]
        lower = max(value - rate * abs(t - s) for s, value in observed)
        upper = min(value + rate * abs(t - s) for s, value in observed)
        score = max(-lower, upper)
        if best is None or score > best[0]:
            best = (score, i)
    require(best is not None, "no_query")
    return best[1]


def response_plan(observed, rate, tolerance, q):
    query = dict(
        id="next-sample",
        time_s=str(q),
        error_mps="0",
        clock_registration="same_recording_axis",
        available=True,
    )
    plans = [plan(model(observed, rate, tolerance, sign), query) for sign in (1, -1)]
    require(
        all(p["status"] == "response_set_computed" for p in plans), "response_state"
    )
    # First margin e+r has reply e+y; second e-r has reply e-y.
    low, high = [F(v) - tolerance for v in plans[0]["feasible_responses"]]
    require(
        [tolerance - F(v) for v in reversed(plans[1]["feasible_responses"])]
        == [low, high],
        "complement_domain",
    )
    cuts = []
    for sign, result in zip((1, -1), plans):
        for row in result["response_partition"]:
            cuts.extend(sign * (F(row[key]) - tolerance) for key in ("lower", "upper"))

    def classify(y):
        return joint_status(
            response_status(plans[0], tolerance + y),
            response_status(plans[1], tolerance - y),
        )

    partition = canonical_partition(low, high, cuts, classify)
    return dict(
        status="response_set_computed",
        feasible_responses=[str(low), str(high)],
        response_partition=partition,
        guaranteed_resolution=all(r["status"] != "unresolved" for r in partition),
        possible_statuses=sorted({r["status"] for r in partition}),
    ), plans
