"""Execute one frozen arm; sources and full results remain private."""

import hashlib
import importlib
import json
from pathlib import Path
import sys
import time

SOURCES = {
    "UniAD-Base.json": (
        "ab07b2b9ab3bfe614bf7bc15c70ad9e4543ab664448dba98641b33fe6aa4dfac",
        571747,
    ),
    "UniAD-Tiny.json": (
        "b0f60431dc667ae692787c9ee11dc7911d1f6bc39f30fabe518007a37888c900",
        551056,
    ),
}


def bound_payloads(directory):
    result = []
    for name, (digest, size) in SOURCES.items():
        payload = (directory / name).read_bytes()
        if len(payload) != size or hashlib.sha256(payload).hexdigest() != digest:
            raise ValueError("source_binding")
        result.append(payload)
    return result


def main():
    arm, source, output = sys.argv[1:]
    if arm not in ("conventional", "native"):
        raise ValueError("arm")
    target = Path(output)
    if target.exists() or not target.parent.is_dir():
        raise ValueError("new_existing_parent_required")
    started = time.perf_counter()
    module = importlib.import_module(arm)
    payloads = bound_payloads(Path(source))
    result = module.calculate(*(module.read(x) for x in payloads))
    result.update(
        document_id="reiyah.public-decision.arm-result",
        version="0.1.0",
        arm=arm,
        source_sha256={name: spec[0] for name, spec in SOURCES.items()},
        internal_seconds_through_computation=time.perf_counter() - started,
        scope="Post-structure conditional diagnostic; original complete-group question blocked",
    )
    target.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"arm": arm, **result["summary"]}, indent=2))


if __name__ == "__main__":
    main()
