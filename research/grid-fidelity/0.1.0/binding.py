"""Offline immutable packet verification, independent of mathematical outcomes."""

import hashlib
from pathlib import Path

from common import keys, load, require

ROOT = Path(__file__).resolve().parent


def verify():
    path = ROOT / "freeze.json"
    freeze = load(path)
    keys(freeze, "document_id version frozen_utc scope files runtime supervisor_sha256")
    require(
        freeze["document_id"] == "reiyah.grid-fidelity.freeze"
        and freeze["version"] == "0.1.0",
        "freeze_identity",
    )
    for name, identity in freeze["files"].items():
        require(Path(name).name == name, "freeze_path")
        data = (ROOT / name).read_bytes()
        require(
            len(data) == identity["bytes"]
            and hashlib.sha256(data).hexdigest() == identity["sha256"],
            "frozen_bytes:" + name,
        )
    return hashlib.sha256(path.read_bytes()).hexdigest()
