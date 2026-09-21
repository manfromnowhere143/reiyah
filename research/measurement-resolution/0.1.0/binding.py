"""Frozen packet/source/runtime identity and strict authored experiment allocation."""

import hashlib
from pathlib import Path
import re
import sys

from common import keys, load, require
from workflow import validate_experiment, validate_oracle


def identity(path):
    body = Path(path).read_bytes()
    return dict(bytes=len(body), sha256=hashlib.sha256(body).hexdigest())


def verify_files(root, files):
    for name, expected in files.items():
        require(
            re.fullmatch(r"[A-Za-z0-9_.-]+", name) is not None
            and name not in (".", ".."),
            "binding_path",
        )
        p = root / name
        require(
            p.is_file() and not p.is_symlink() and identity(p) == expected,
            "binding_bytes:" + name,
        )


def bind(packet, sources, expected):
    require(identity(packet / "freeze.json")["sha256"] == expected, "freeze_identity")
    freeze = load(packet / "freeze.json")
    require(
        freeze["document_id"] == "reiyah.measurement-resolution.freeze"
        and freeze["version"] == "0.1.0",
        "freeze_scope",
    )
    verify_files(packet, freeze["files"])
    verify_files(sources, freeze["sources"])
    require(
        identity(Path(sys.executable).resolve())["sha256"]
        == freeze["runtime"]["sha256"],
        "runtime_identity",
    )
    cases, oracle_data = load(packet / "cases.json"), load(packet / "oracles.json")
    keys(cases, ("document_id", "version", "experiments"))
    keys(oracle_data, ("document_id", "version", "oracles"))
    require(
        cases["document_id"] == "reiyah.measurement-resolution.experiments"
        and cases["version"] == "0.1.0",
        "experiment_identity",
    )
    require(
        oracle_data["document_id"] == "reiyah.measurement-resolution.oracles"
        and oracle_data["version"] == "0.1.0",
        "oracle_identity",
    )
    require(
        type(cases["experiments"]) is list
        and len(cases["experiments"]) == freeze["allocation"]["experiments"],
        "experiment_allocation",
    )
    require(
        type(oracle_data["oracles"]) is list
        and len(oracle_data["oracles"]) == freeze["allocation"]["oracles"],
        "oracle_allocation",
    )
    for experiment in cases["experiments"]:
        validate_experiment(experiment)
    for oracle in oracle_data["oracles"]:
        validate_oracle(oracle)
    ids = [x["id"] for x in cases["experiments"]]
    oracle_ids = [x["id"] for x in oracle_data["oracles"]]
    require(
        len(set(ids)) == len(ids) and len(set(oracle_ids)) == len(oracle_ids),
        "duplicate_case_or_oracle",
    )
    require(
        {x["oracle_id"] for x in cases["experiments"]} == set(oracle_ids),
        "oracle_membership",
    )
    return cases["experiments"], {x["id"]: x for x in oracle_data["oracles"]}
