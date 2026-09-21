"""Authored offline acquisition protocol; no physical sensor or control runtime."""

from bisect import bisect_right
import copy
from fractions import Fraction as F

from common import identifier, keys, parse_case, rational, require


def validate_experiment(item):
    keys(item, ("id", "model", "queries", "oracle_id", "purpose"))
    identifier(item["id"])
    identifier(item["oracle_id"])
    require(type(item["purpose"]) is str and 0 < len(item["purpose"]) < 1000, "purpose")
    parse_case(item["model"])
    require(item["model"]["id"] == item["id"], "model_experiment_id")
    require(type(item["queries"]) is list and len(item["queries"]) <= 8, "query_cap")
    names = []
    for q in item["queries"]:
        keys(q, ("id", "time_s", "error_m", "clock_registration", "available"))
        identifier(q["id"])
        rational(q["time_s"])
        require(rational(q["error_m"]) >= 0, "negative_query_error")
        require(type(q["available"]) is bool, "availability_type")
        require(
            q["clock_registration"] in (None, "same_recording_axis"),
            "clock_registration",
        )
        names.append(q["id"])
    require(len(names) == len(set(names)), "query_id_reuse")


def validate_oracle(record):
    keys(record, ("id", "knots", "reporting_offsets", "fault_injected"))
    identifier(record["id"])
    require(
        type(record["knots"]) is list and 2 <= len(record["knots"]) <= 16,
        "oracle_knots",
    )
    pairs = []
    for row in record["knots"]:
        require(type(row) is list and len(row) == 2, "oracle_knot_shape")
        pairs.append(tuple(map(rational, row)))
    require(all(a[0] < b[0] for a, b in zip(pairs, pairs[1:])), "oracle_time_order")
    require(
        type(record["reporting_offsets"]) is dict
        and type(record["fault_injected"]) is bool,
        "oracle_metadata",
    )
    for name, value in record["reporting_offsets"].items():
        identifier(name)
        rational(value)
    return pairs


class Oracle:
    def __init__(self, record):
        self.points = validate_oracle(record)
        self.offsets = record["reporting_offsets"]
        self.calls = []

    def reveal(self, query):
        require(
            query["available"] and query["clock_registration"] == "same_recording_axis",
            "oracle_access_not_admitted",
        )
        require(query["id"] not in self.calls, "oracle_query_reuse")
        q = rational(query["time_s"])
        require(self.points[0][0] <= q <= self.points[-1][0], "oracle_extrapolation")
        times = [t for t, _ in self.points]
        i = min(bisect_right(times, q) - 1, len(times) - 2)
        a, b = self.points[i], self.points[i + 1]
        value = a[1] + (q - a[0]) * (b[1] - a[1]) / (b[0] - a[0])
        self.calls.append(query["id"])
        return value + rational(self.offsets.get(query["id"], "0"))


def append_measurement(case, query, value):
    new = copy.deepcopy(case)
    q, e = rational(query["time_s"]), rational(query["error_m"])
    lo, hi = value - e, value + e
    old = next((row for row in new["observations"] if F(row["time_s"]) == q), None)
    merge = dict(
        query_id=query["id"],
        time_s=str(q),
        reported_interval_m=[str(lo), str(hi)],
        existing_observation_id=None,
        previous_interval_m=None,
        merged_interval_m=None,
    )
    if old is not None:
        require(old["interval_m"] is not None, "cannot_merge_missing_interval")
        merge.update(
            existing_observation_id=old["id"], previous_interval_m=old["interval_m"][:]
        )
        lo, hi = max(lo, F(old["interval_m"][0])), min(hi, F(old["interval_m"][1]))
        if lo > hi:
            return None, merge
        old["interval_m"] = [str(lo), str(hi)]
    else:
        new_id = "measurement-" + query["id"]
        require(
            all(row["id"] != new_id for row in new["observations"]),
            "measurement_id_collision",
        )
        new["observations"].append(
            dict(id=new_id, time_s=str(q), interval_m=[str(lo), str(hi)])
        )
        new["observations"].sort(key=lambda row: F(row["time_s"]))
    merge["merged_interval_m"] = [str(lo), str(hi)]
    parse_case(new)
    return new, merge


def evidence(result):
    out = {"status": result["status"]}
    if "minimum_range_m" in result:
        out["minimum_range_m"] = result["minimum_range_m"]
    if "missing" in result:
        out["missing"] = result["missing"]
    return out


def run_experiment(item, oracle_record, planner, solver):
    validate_experiment(item)
    require(item["oracle_id"] == oracle_record["id"], "oracle_binding")
    oracle = Oracle(oracle_record)
    case = copy.deepcopy(item["model"])
    current = solver(case)
    initial = evidence(current)
    steps, proofs = [], [dict(model=copy.deepcopy(case), result=current)]
    workflow_status = "exhausted"
    for query in item["queries"]:
        if current["status"] != "unresolved":
            workflow_status = (
                "resolved"
                if current["status"] in ("supported", "contradicted")
                else current["status"]
            )
            break
        partition = planner(case, query)
        step = dict(
            query_id=query["id"],
            before=evidence(current),
            predicted=partition,
            reported_value_m=None,
            merge=None,
            after=None,
        )
        if partition["status"] != "response_set_computed":
            workflow_status = partition["status"]
            steps.append(step)
            break
        value = oracle.reveal(query)
        updated, merge = append_measurement(case, query, value)
        if updated is None:
            current = dict(status="inconsistent_premises")
        else:
            case = updated
            current = solver(case)
            proofs.append(dict(model=copy.deepcopy(case), result=current))
        step.update(reported_value_m=str(value), merge=merge, after=evidence(current))
        steps.append(step)
        if current["status"] != "unresolved":
            workflow_status = (
                "resolved"
                if current["status"] in ("supported", "contradicted")
                else current["status"]
            )
            break
    else:
        if current["status"] != "unresolved":
            workflow_status = (
                "resolved"
                if current["status"] in ("supported", "contradicted")
                else current["status"]
            )
    return dict(
        id=item["id"],
        initial=initial,
        final=evidence(current),
        workflow_status=workflow_status,
        oracle_calls=len(oracle.calls),
        revealed_query_ids=oracle.calls,
        unexecuted_query_ids=[
            q["id"] for q in item["queries"] if q["id"] not in oracle.calls
        ],
        steps=steps,
        evidence_kind="authored_conditional_mechanism",
        physical_status="unresolved",
    ), proofs
