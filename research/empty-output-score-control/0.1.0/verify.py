"""Independent exact recall-grid oracle for this authored control family."""
import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path


def require(condition, message):
    if not condition:
        raise ValueError(message)


def integral(similarities, true_positives, reference_count):
    require(reference_count > 0, "positive reference population required")
    prefix = []
    similarity_sum, hits = Fraction(0), 0
    for i, (similarity, hit) in enumerate(zip(similarities, true_positives), 1):
        similarity_sum += similarity
        hits += hit
        prefix.append((Fraction(hits, reference_count), similarity_sum / i))
    heights = [max((value for recall, value in prefix if recall >= Fraction(k, 100)),
                   default=Fraction(0)) for k in range(101)]
    return sum(heights, Fraction(0)) / 101


def verify(path):
    raw = Path(path).read_bytes()
    result = json.loads(raw)
    checked = 0

    def score(observed, expected, denominator):
        nonlocal checked
        require(observed["status"] == "defined", "expected defined AUSRC")
        value = observed["AUSRC"]
        require(type(value) is float, "AUSRC type")
        require(abs(value - float(expected)) <= 2e-7, "AUSRC differs from exact oracle")
        require(type(observed["total_gt"]) is int and observed["total_gt"] == denominator,
                "reference denominator")
        checked += 1

    require(result["source_sha256"] == "d19fab4078ffc61c594e72ad1719bd2179108187de26099c6614eb39ddeeba20", "source binding")
    expected_primary = {"A": (Fraction(1), integral([Fraction(1)], [1], 2)),
                        "B": (Fraction(4, 5), integral([Fraction(4, 5)] * 2, [1, 1], 2))}
    require(set(result["primary"]) == {"A", "B"}, "primary membership")
    expected_variants = {(reverse, chunk, workers) for reverse in (False, True)
                         for chunk, workers in ((1, 1), (1, 2), (64, 1), (64, 2))}
    for arm, variants in result["primary"].items():
        require(len(variants) == 8, "primary variant count")
        require({(r["reverse"], r["chunk_size"], r["workers"]) for r in variants} == expected_variants,
                "primary variants")
        for row in variants:
            require(type(row["reverse"]) is bool and type(row["chunk_size"]) is int
                    and type(row["workers"]) is int, "variant metadata types")
            score(row["native"], expected_primary[arm][0], 1 if arm == "A" else 2)
            score(row["corrected"], expected_primary[arm][1], 2)
    require(expected_primary["A"][0] > expected_primary["B"][0], "native ordering")
    require(expected_primary["A"][1] < expected_primary["B"][1], "corrected ordering")

    rows = result["presence_subsets"]
    expected_sets = {tuple(i + 1 for i in range(3) if mask & (1 << i)) for mask in range(8)}
    require(len(rows) == 8, "subset count")
    require({tuple(r["detected_image_ids"]) for r in rows} == expected_sets, "subset membership")
    for row in rows:
        require(all(type(i) is int for i in row["detected_image_ids"]), "subset ID types")
        count = len(row["detected_image_ids"])
        if count:
            score(row["native"], Fraction(1), count)
        else:
            require(row["native"]["status"] == "error", "native empty failure absent")
            require(row["native"]["exception"] == "ValueError", "native failure type")
            require(row["native"]["message"] == "torch.cat(): expected a non-empty list of Tensors",
                    "native failure message")
        score(row["corrected"], integral([Fraction(1)] * count, [1] * count, 3), 3)
    for control in ("single_image", "outside_area"):
        for arm in ("native", "corrected"):
            score(result[control][arm], Fraction(1), 1)
    require(type(result["nonempty_tensor_equalities"]) is int and result["nonempty_tensor_equalities"] == 16,
            "nonempty tensor parity count")
    require(set(result["rejections"]) == {"missing", "failed", "duplicate", "extra", "boolean_id", "undefined_denominator"},
            "rejection membership")
    require(all(type(v) is str and v for v in result["rejections"].values()), "rejection evidence")
    return dict(artifact_id="reiyah.empty-output-score-control.verification", version="0.1.0",
                status="pass", result_sha256=hashlib.sha256(raw).hexdigest(),
                numeric_scores_checked=checked, subset_cases=8, primary_variants_per_arm=8,
                exact_primary={arm: {"native": str(values[0]), "corrected": str(values[1])}
                               for arm, values in expected_primary.items()},
                scope="Separate rational arithmetic implementation; no producer import, no native tensor code; authored cases only, not independent scientific review.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    receipt = verify(args.result)
    with open(args.output, "x") as output:
        json.dump(receipt, output, indent=2, allow_nan=False)
        output.write("\n")
