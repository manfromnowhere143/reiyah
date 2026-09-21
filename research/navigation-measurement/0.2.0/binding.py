"""Byte-bound execution without changing the source or the prespecified question."""

import hashlib
from pathlib import Path
import sys

from common import load, require

SOURCE_SLICE = {
    "start_byte": 8133840,
    "end_byte_inclusive": 8205839,
    "full_file_bytes": 8205840,
    "first_original_packet_index": 112970,
    "original_packet_count": 113970,
    "index_scope": "slice_relative",
}


def identity(path):
    path = Path(path)
    data = path.read_bytes()
    return dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())


def bind(packet, sources, vendor, freeze_sha256):
    packet, sources, vendor = Path(packet), Path(sources), Path(vendor)
    require(
        identity(packet / "freeze.json")["sha256"] == freeze_sha256, "freeze_identity"
    )
    freeze = load(packet / "freeze.json")
    require(freeze["source_slice"] == SOURCE_SLICE, "source_slice_identity")
    for name, expected in freeze["files"].items():
        require(identity(packet / name) == expected, "frozen_file_identity:" + name)
    for name, expected in freeze["sources"].items():
        require(identity(sources / name) == expected, "source_identity:" + name)
    require(identity(vendor) == freeze["vendor_binary"], "vendor_identity")
    require(
        identity(Path(sys.executable).resolve()) == freeze["runtime"],
        "runtime_identity",
    )
    question = load(packet / "question-freeze.json")
    require(
        identity(packet / "QUESTION.md")["sha256"] == question["sha256"],
        "question_identity",
    )
    require(
        freeze["allocation"]
        == dict(
            source_slice_bytes=72000,
            original_packets=1000,
            selected_samples=101,
            dependent_segments=5,
            native_intervals=100,
            maximum_queries_each_arm=90,
            physical_cases=0,
        ),
        "allocation",
    )
    return (sources / "ncom-sample-tail.bin").read_bytes()
