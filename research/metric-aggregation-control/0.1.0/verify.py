"""Separate scalar oracle; no producer, upstream source or tensor imports."""
import argparse
from fractions import Fraction
import hashlib
from itertools import permutations
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
METRICS = {"MAE", "MSE", "KL", "JSD", "TVD", "cosine_dist"}
EPS = 1e-8


def require(condition, message):
    if not condition:
        raise ValueError(message)


def per_detection(probability, matched):
    p = Fraction(probability)
    require(0 <= p <= 1, "probability range")
    q = p if matched else 1 - p
    # Only foreground and background have nonzero mass; vector dimension is 81.
    a, b = float(q), float(1 - q)
    middle_a, middle_b = (1 + a) / 2, b / 2
    js = (a * math.log((a + EPS) / (middle_a + EPS))
          + b * math.log((b + EPS) / (middle_b + EPS))
          + math.log((1 + EPS) / (middle_a + EPS))) / 2
    return {"MAE": 2 * (1 - q) / 81,
            "MSE": 2 * (1 - q) ** 2 / 81,
            "TVD": 1 - q,
            "KL": math.log((1 + EPS) / (a + EPS)),
            "JSD": math.sqrt(max(0.0, js)),
            "cosine_dist": 1 - a / math.sqrt(a * a + b * b)}


def image_metrics(image, area):
    all_rows, matched_rows = [], []
    refs = image["reference_boxes"]
    for detection in image["detections"]:
        box, ref = detection["bbox"], detection["expected_reference"]
        require(len(box) == 4 and box[2] > 0 and box[3] > 0, "fixture box")
        if ref is not None:
            require(type(ref) is int and 0 <= ref < len(refs), "reference index")
            require(box == refs[ref], "authored exact match")
        # Every other reference is geometrically disjoint, so no matching ambiguity.
        for j, other in enumerate(refs):
            if j == ref:
                continue
            overlap_x = min(box[0] + box[2], other[0] + other[2]) - max(box[0], other[0])
            overlap_y = min(box[1] + box[3], other[1] + other[3]) - max(box[1], other[1])
            require(overlap_x <= 0 or overlap_y <= 0, "unexpected overlapping geometry")
        selected_area = refs[ref][2] * refs[ref][3] if ref is not None else box[2] * box[3]
        if not area[0] <= selected_area <= area[1]:
            continue
        row = per_detection(detection["probability"], ref is not None)
        all_rows.append(row)
        if ref is not None:
            matched_rows.append(row)
    return all_rows, matched_rows


def verify(result_path, fixtures_path):
    result_raw, fixture_raw = Path(result_path).read_bytes(), Path(fixtures_path).read_bytes()
    result, fixtures = json.loads(result_raw), json.loads(fixture_raw)
    protocol = json.loads((HERE / "protocol.json").read_text())
    digest = hashlib.sha256(fixture_raw).hexdigest()
    require(digest == result["fixtures_sha256"] == protocol["fixtures_sha256"], "fixture binding")
    require(result["source_sha256"] == protocol["upstream_source_sha256"], "source binding")
    cases = {case["id"]: case for case in fixtures["cases"]}
    wanted = {(case["id"], order, chunk, workers) for case in cases.values()
              for order in permutations(image["id"] for image in case["images"])
              for chunk in (1, 2, 64) for workers in (1, 2)}
    rows = result["configurations"]
    actual = {(r["case"], tuple(r["order"]), r["chunk_size"], r["workers"]) for r in rows}
    require(len(rows) == len(actual) == len(wanted) == 90 and actual == wanted, "configuration membership")
    checked = undefined = mismatch = rescued = 0
    examples = {}
    for row in rows:
        require(type(row["chunk_size"]) is int and type(row["workers"]) is int
                and all(type(i) is int for i in row["order"]), "configuration types")
        case = cases[row["case"]]
        images = {image["id"]: image for image in case["images"]}
        area = case.get("area", [0, 10000000000])
        # The inherited empty-image adapter appends GT-only IDs after prediction IDs.
        prepared = [i for i in row["order"] if images[i]["detections"]]
        prepared += [i for i in row["order"] if not images[i]["detections"] and images[i]["reference_boxes"]]
        chunk = row["chunk_size"]
        last_images = [prepared[offset:offset + chunk][-1] for offset in range(0, len(prepared), chunk)]
        expected_gt = sum(area[0] <= b[2] * b[3] <= area[1]
                          for image in images.values() for b in image["reference_boxes"])
        for arm, chosen in (("native", last_images), ("corrected", prepared)):
            observed = row[arm]
            require(type(observed["total_gt"]) is int and observed["total_gt"] == expected_gt, "reference count")
            require(type(observed["AUSRC"]) is float and math.isfinite(observed["AUSRC"]), "AUSRC type")
            expected = [image_metrics(images[i], area) for i in chosen]
            for index, population in enumerate(("all", "matched")):
                values = [v for image in expected for v in image[index]]
                record = observed[population]
                require(type(record["count"]) is int and record["count"] == len(values), "metric population count")
                require(set(record["means"]) == METRICS, "metric membership")
                require(record["state"] == ("defined" if values else "undefined_no_samples"), "metric state")
                for metric in METRICS:
                    value = record["means"][metric]
                    if values:
                        want = sum(v[metric] for v in values) / len(values)
                        require(type(value) is float and math.isfinite(value), "numeric mean type")
                        require(abs(value - float(want)) <= 5e-6, "mean differs from scalar oracle")
                        checked += 1
                    else:
                        require(value is None, "undefined mean must remain null")
                        undefined += 1
        require(row["native"]["AUSRC"] == row["corrected"]["AUSRC"], "AUSRC changed")
        differs = any(row["native"][p]["count"] != row["corrected"][p]["count"]
                      for p in ("all", "matched"))
        mismatch += int(differs)
        rescued += int(row["native"]["all"]["count"] == 0 and row["corrected"]["all"]["count"] > 0)
        if row["case"] in ("primary_A", "primary_B") and row["order"] == [1, 2] and row["workers"] == 1:
            examples.setdefault(row["case"], {})[str(chunk)] = {
                arm: row[arm]["all"]["means"]["TVD"] for arm in ("native", "corrected")}
    return dict(artifact_id="reiyah.metric-aggregation-control.verification", version="0.1.0",
                status="pass", result_sha256=hashlib.sha256(result_raw).hexdigest(),
                fixtures_sha256=digest, configurations=90, native_and_corrected_evaluations=180,
                numeric_means_checked=checked, undefined_mean_fields_checked=undefined,
                configurations_with_population_difference=mismatch,
                configurations_restored_from_empty_to_nonempty_all_population=rescued,
                AUSRC_equal_pairs=90, primary_TVD=examples,
                scope="Authored geometry and distributions; separate exact linear/scalar nonlinear oracle, not independent scientific review or published-data impact.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result", required=True)
    parser.add_argument("--fixtures", default=str(HERE / "fixtures.json"))
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    receipt = verify(args.result, args.fixtures)
    with open(args.output, "x") as output:
        json.dump(receipt, output, indent=2, allow_nan=False)
        output.write("\n")
