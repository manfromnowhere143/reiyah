#!/usr/bin/env python3
"""Reproduce the private, metadata-only model-input smoke population."""
import argparse
import json
from collections import defaultdict
from pathlib import Path

from audit_mmdet3d_inputs import sha, write_json

SUBSETS = {
    "1": "a438ef8558bfe79de79221f825593289ee294a9a3c612c4b49a1f0f034cc0fe0",
    "2": "5e08b07eb283e4ce4727f0aa8fb60c603851eeef3da94c023ab7adcd98a919b2",
    "val": "e73ec9590f5357e2d1e1f63a8bcc41327b23fa606976655330d8ec0c985646a0",
}


def select(root):
    rows = []
    for group, expected in SUBSETS.items():
        subset = root / group
        if sha(subset / "result.json") != expected:
            raise ValueError("subset identity differs")
        bound = json.loads((subset / "result.json").read_text())
        for name in ("scene", "sample"):
            if sha(subset / "v1.0-trainval" / (name + ".json")) != bound["tables"][name]["sha256"]:
                raise ValueError("selection table identity differs")
        scenes = json.loads((subset / "v1.0-trainval/scene.json").read_text())
        samples = json.loads((subset / "v1.0-trainval/sample.json").read_text())
        first_by_log = {}
        for scene in sorted(scenes, key=lambda r: r["name"]):
            first_by_log.setdefault(scene["log_token"], scene)
        by_scene = defaultdict(list)
        for sample in samples:
            by_scene[sample["scene_token"]].append(sample)
        for log, scene in sorted(first_by_log.items()):
            ordered = sorted(by_scene[scene["token"]], key=lambda r: r["timestamp"])
            if len(ordered) != scene["nbr_samples"] or len(ordered) < 3:
                raise ValueError("invalid scene population")
            for position, index in (("scene_start", 0), ("second_keyframe", 1), ("scene_middle", len(ordered)//2)):
                sample = ordered[index]
                rows.append({"group": group, "log_token": log, "scene_token": scene["token"],
                             "scene_name": scene["name"], "sample_token": sample["token"],
                             "position": position, "index": index, "timestamp": sample["timestamp"]})
    if len(rows) != 204 or len({r["sample_token"] for r in rows}) != 204:
        raise ValueError("smoke population differs")
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--subsets", type=Path, required=True, help="Contains bound 1, 2 and val subset directories")
    parser.add_argument("--output", type=Path, required=True, help="New private JSON path; never put dataset identities in public Git")
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("output identity already exists")
    write_json(args.output, select(args.subsets))
    if sha(args.output) != "43e73e0c55d307084439e73e067c38af8337cdb5530b81844004a0aefc984390":
        raise ValueError("selection differs from the pre-execution frozen population")
    print(json.dumps({"version": "0.1.0", "selected": 204, "sha256": sha(args.output),
                      "role": "Replay of the already frozen selection; no detector outcomes are inputs"}))


if __name__ == "__main__":
    main()
