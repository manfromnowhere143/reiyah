"""Authored development cases fixed before execution; no source outcomes."""

from fractions import Fraction


def case(
    identifier,
    times,
    values,
    coarse,
    rate,
    tolerance,
    unavailable=(),
    quantum="1/100",
    limits=(-1000, 1000),
):
    times, values = (
        [str(Fraction(x)) for x in times],
        [str(Fraction(x)) for x in values],
    )
    return dict(
        model=dict(
            id=identifier,
            native_times_s=times,
            coarse_indices=coarse,
            observations=[dict(index=i, value_mps=values[i]) for i in coarse],
            availability=[
                "unavailable" if i in unavailable else "available"
                for i in range(len(times))
            ],
            rate_bound_mps2=str(Fraction(rate)),
            tolerance_mps=str(Fraction(tolerance)),
            value_domain=dict(
                kind="uniform_integer_encoding",
                quantum_mps=quantum,
                minimum_integer=limits[0],
                maximum_integer=limits[1],
            ),
        ),
        oracle_values_mps=values,
        source_indices=list(range(len(times))),
        evidence_kind="authored_development",
    )


def authored():
    return [
        case("rate-saturated-line", [0, 1, 2], [0, 1, 2], [0, 2], 1, 0),
        case("known-grid-no-hidden-bends", [0, 1], [0, 0], [0, 1], 1, 0),
        case("one-native-query-resolves", [0, "1/2", 1], [0, 0, 0], [0, 2], 1, "1/4"),
        case(
            "three-native-queries",
            [0, "1/4", "1/2", "3/4", 1],
            [0] * 5,
            [0, 4],
            1,
            "1/5",
        ),
        case(
            "acquired-fidelity-violation",
            [0, "1/2", 1],
            [0, "2/5", 0],
            [0, 2],
            1,
            "1/4",
        ),
        case("inconsistent-initial-rate", [0, "1/2", 1], [0, 1, 2], [0, 2], 1, "1/4"),
        case(
            "inconsistent-acquired-value",
            [0, "1/2", 1],
            [0, "3/4", 0],
            [0, 2],
            1,
            "1/4",
        ),
        case(
            "unavailable-native-query",
            [0, "1/2", 1],
            [0, 0, 0],
            [0, 2],
            1,
            "1/4",
            unavailable=(1,),
        ),
        case("singleton-support-reply", [0, 1, "3/2", 2, 3], [0] * 5, [0, 4], 1, "1/2"),
        case(
            "encoded-baseline-rounding",
            [0, 1, 2],
            [0, 0, 1],
            [0, 2],
            1,
            "1/4",
            quantum="1",
            limits=(-2, 2),
        ),
        case(
            "integer-edge-capacity",
            [0, "3/5", "6/5"],
            [0, 0, 1],
            [0, 2],
            1,
            1,
            quantum="1",
            limits=(-2, 2),
        ),
        case(
            "finite-encoding-range",
            [0, 1, 2],
            [0, 1, 0],
            [0, 2],
            2,
            1,
            quantum="1",
            limits=(0, 1),
        ),
        case(
            "encoded-single-query",
            [0, "1/2", 1],
            [0, 1, 0],
            [0, 2],
            2,
            "1/4",
            quantum="1",
            limits=(-2, 2),
        ),
    ]
