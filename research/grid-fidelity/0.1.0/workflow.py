"""Declared adaptive protocol with a counted, availability-checked oracle."""

import copy

from common import exact, integer_value, parse, require


class Oracle:
    def __init__(self, case):
        self.model = parse(case["model"])
        self.values = tuple(map(exact, case["oracle_values_mps"]))
        self.mapping = tuple(case["source_indices"])
        self.available = tuple(case["model"]["availability"])
        self.seen = {row["index"] for row in case["model"]["observations"]}
        self.calls = []
        require(
            len(self.values) == len(self.mapping) == len(self.available), "oracle_size"
        )
        require(
            all(type(i) is int and i >= 0 for i in self.mapping)
            and len(set(self.mapping)) == len(self.mapping),
            "oracle_source_mapping",
        )
        require(
            all(self.values[i] == value for i, value in self.model.known.items()),
            "initial_source_binding",
        )
        for value in self.values:
            integer_value(self.model, value)

    def acquire(self, index):
        require(
            type(index) is int and 0 <= index < len(self.values), "oracle_membership"
        )
        require(index not in self.seen, "oracle_repeat")
        require(self.available[index] == "available", "oracle_unobtainable")
        self.seen.add(index)
        row = dict(
            query_index=index,
            source_index=self.mapping[index],
            value_mps=str(self.values[index]),
        )
        self.calls.append(row)
        return dict(row)


def response_class(prediction, value):
    tick = value / exact(prediction["quantum_mps"])
    if tick.denominator != 1:
        return "unrepresentable_value"
    for cell in prediction["response_partition"]:
        if cell["lower_integer"] <= tick <= cell["upper_integer"]:
            return cell["status"]
    return "outside_current_family"


def run(case, engine, arm):
    model = parse(case["model"])
    oracle = Oracle(case)
    known = dict(model.known)
    stages, records = [], []
    for step in range(len(model.times) + 1):
        state, witness = engine.evaluate(model, known)
        stages.append(
            dict(
                step=step,
                known_indices=sorted(known),
                decision=copy.deepcopy(state),
                witness=witness,
            )
        )
        if records:
            records[-1]["after"] = copy.deepcopy(state)
        if state["status"] != "unresolved":
            workflow = state["status"]
            break
        candidates = [
            i
            for i in range(len(model.times))
            if i not in known and model.available[i] == "available"
        ]
        if not candidates:
            workflow = (
                "acquisition_blocked" if len(known) < len(model.times) else "exhausted"
            )
            break
        scores = engine.priorities(model, known)
        query = max(candidates, key=lambda i: (scores[i], -i))
        prediction = engine.responses(model, known, query)
        reply = oracle.acquire(query)
        value = exact(reply["value_mps"])
        # The stored case is validated before the run. A caller supplying an
        # unencodable reply receives a source error, never a safety decision.
        integer_value(model, value)
        records.append(
            dict(
                step=step,
                before=copy.deepcopy(state),
                predicted=prediction,
                **reply,
                predicted_response_class=response_class(prediction, value),
            )
        )
        known[query] = value
    else:
        raise AssertionError("finite_query_budget")
    summary = dict(
        id=model.identifier,
        arm=arm,
        evidence_kind=case["evidence_kind"],
        initial=stages[0]["decision"],
        final=state,
        workflow_status=workflow,
        oracle_calls=len(oracle.calls),
        query_indices=[x["query_index"] for x in oracle.calls],
        unqueried_indices=[i for i in range(len(model.times)) if i not in known],
        records=records,
    )
    return summary, dict(id=model.identifier, stages=stages)
