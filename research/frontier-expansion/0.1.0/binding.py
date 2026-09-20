"""Verify the immutable study projection before offline execution."""
import hashlib,json
from pathlib import Path
def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def verify_freeze(root):
    freeze=json.loads((root/"freeze-correction.json").read_text())
    for entry in freeze["implementation"]:
        path=root/entry["path"]
        assert path.resolve().is_relative_to(root.resolve())
        assert sha(path)==entry["sha256"], "changed frozen artifact: "+entry["path"]
        assert path.stat().st_size==entry["bytes"]
    return sha(root/"freeze-correction.json")
