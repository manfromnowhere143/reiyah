"""Custody controls; byte rejection does not certify physical metadata."""

import argparse
import json
from pathlib import Path
import tempfile

from contract import HERE, bind_sources
from controls import refusal


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("vendor", type=Path)
    args = parser.parse_args()
    bind_sources(args.vendor)
    files = json.loads((HERE / "sources.json").read_text())["files"]
    results = []
    targets = [
        (
            "origin_substitution",
            "trajectories/fast_lio_sam/construction_seq1/enu_origin.json",
            b"[0,0,0]\n",
        ),
        (
            "checkpoint_substitution",
            "ground_truth/construction_seq1.csv",
            b"different checkpoint\n",
        ),
        (
            "missing_trajectory",
            "trajectories/fast_lio_sam/construction_seq1/traj_online.txt",
            None,
        ),
    ]
    for name, target, body in targets:
        with tempfile.TemporaryDirectory(prefix="custody-control-") as folder:
            root = Path(folder)
            for row in files:
                dest = root / row["path"]
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.symlink_to((args.vendor / row["path"]).resolve())
            changed = root / target
            changed.unlink()
            if body is not None:
                changed.write_bytes(body)
            reason = (
                "source_missing:" if body is None else "source_identity:"
            ) + target
            refusal(name, reason, lambda: bind_sources(root), results)
    print(json.dumps({"controls": results}, indent=2))


if __name__ == "__main__":
    main()
