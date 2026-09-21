"""Research-only conversion into the already implemented monotone audit path."""

from copy import deepcopy
from hashlib import sha256

from tools.perception_decision import contract as legacy
from tools.perception_revision import contract as revision

RULE = "reiyah.authored-independent-presence-to-deletions:0.1.0"


class Refusal(ValueError):
    pass


def digest(value):
    return sha256(legacy.encoded(value)).hexdigest()


def convert(original):
    # Scope is deliberately checked first: this study cannot promote any
    # non-synthetic material, even if its spelling is otherwise invalid.
    if original.get("evidence_kind") != "synthetic":
        raise Refusal("research_scope")
    try:
        legacy.validate(original)
    except legacy.Invalid as exc:
        raise Refusal("invalid_input") from exc
    if original["model"]["clauses"]:
        raise Refusal("model_clauses")
    seen = set()
    mapping = []
    for anchor in original["anchors"]:
        if any(anchor[role]["state"] != "observed" for role in ("base", "additions")):
            raise Refusal("outputs_unavailable")
        if anchor["reference"]["state"] != "finite":
            raise Refusal("open_reference")
        if any(edge["when"] for edge in anchor["reference"]["edges"]):
            raise Refusal("conditional_edge")
        for obj in anchor["reference"]["objects"]:
            when = obj["when"]
            if when and (len(when) != 1 or when[0]["value"] is not True):
                raise Refusal("object_condition")
            variable = when[0]["variable"] if when else None
            if variable is not None:
                if variable in seen:
                    raise Refusal("shared_presence_variable")
                seen.add(variable)
            mapping.append(
                {"anchor": anchor["id"], "object": obj["id"], "variable": variable}
            )
    source = digest(original)
    context = digest({"rule": RULE, "source_sha256": source})
    target = revision.from_addition(original, reference_context_sha256=context)
    target["model"] = {"variables": [], "clauses": []}
    for anchor in target["anchors"]:
        for obj in anchor["reference"]["objects"]:
            obj["when"] = []
    observations = []
    for row in mapping:
        if row["variable"] is None:
            evidence = digest(
                {
                    "rule": RULE,
                    "source_sha256": source,
                    "anchor": row["anchor"],
                    "object": row["object"],
                    "premise": "mandatory_in_original_model",
                }
            )
            observations.append(
                {
                    "anchor": row["anchor"],
                    "object": row["object"],
                    "outcome": "present",
                    "evidence_sha256": evidence,
                }
            )
    request = {
        "artifact_id": "reiyah.perception-revision.audit-request",
        "version": "0.1.0",
        "comparison_id": target["comparison_id"],
        "reference_context_sha256": context,
        "family": "reference_deletions",
        "deletion_budget": len(seen),
        "observation_basis": "hypothetical",
        "observations": observations,
    }
    revision.validate(target)
    revision.validate_request(target, request)
    return {
        "rule": RULE,
        "source_sha256": source,
        "mapping": mapping,
        "dropped_unused_variables": [
            v for v in original["model"]["variables"] if v not in seen
        ],
        "case": deepcopy(target),
        "request": request,
        "scope": "authored_model_premises_only_no_new_observations",
    }
