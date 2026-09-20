"""Shared byte custody and MAT container decoding; no diagnostic arithmetic."""

import hashlib
import json
from pathlib import Path
import sys


def require(value, reason):
    if not value:
        raise ValueError(reason)


def unique(items):
    out = {}
    for k, v in items:
        require(k not in out, "duplicate_json_key")
        out[k] = v
    return out


def read_json(path):
    def invalid(_):
        raise ValueError("nonfinite_json")

    return json.loads(
        Path(path).read_text(), object_pairs_hook=unique, parse_constant=invalid
    )


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_files(root, records):
    for name, identity in records.items():
        require(Path(name).name == name, "unsafe_path")
        p = root / name
        require(p.is_file() and not p.is_symlink(), "missing_or_symlink_source")
        require(
            p.stat().st_size == identity["bytes"] and digest(p) == identity["sha256"],
            "byte_identity",
        )


def bind(packet, sources, expected):
    require(digest(packet / "freeze.json") == expected, "freeze_identity")
    freeze = read_json(packet / "freeze.json")
    verify_files(packet, freeze["files"])
    verify_files(sources, freeze["source_files"])
    require(
        digest(Path(sys.executable).resolve()) == freeze["runtime"]["sha256"],
        "runtime_identity",
    )
    import numpy
    import scipy

    require(numpy.__version__ == freeze["numpy_version"], "numpy_version")
    require(scipy.__version__ == freeze["scipy_version"], "scipy_version")
    return freeze


def mat_rows(path):
    # loadmat is a container decoder, never Python pickle or source execution.
    import scipy.io

    data = scipy.io.loadmat(path, verify_compressed_data_integrity=True)
    require(
        {k for k in data if not k.startswith("__")} == {"BME_HondaCorr"},
        "mat_variables",
    )
    array = data["BME_HondaCorr"]
    require(array.ndim == 2 and array.shape[1] == 6 and array.shape[0] > 1, "mat_shape")
    rows = []
    for row in array:
        require(all(cell.size == 1 for cell in row), "mat_scalar_cell")
        rows.append([cell.item() for cell in row])
    require(all(isinstance(x, str) for x in rows[0]), "mat_header")
    require(all(isinstance(row[0], str) for row in rows[1:]), "mat_time_type")
    require(
        all(type(x) is float for row in rows[1:] for x in row[1:]), "mat_numeric_type"
    )
    return rows


def write_new(path, result):
    with Path(path).open("x") as out:
        json.dump(result, out, indent=2, allow_nan=False)
        out.write("\n")
