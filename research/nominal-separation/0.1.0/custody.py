"""Byte custody and container decoding, shared by both calculations."""

import hashlib
import json
from pathlib import Path
import sys


def require(value, reason):
    if not value:
        raise ValueError(reason)


def unique(pairs):
    out = {}
    for key, value in pairs:
        require(key not in out, "duplicate_json_key")
        out[key] = value
    return out


def read_json(path):
    def bad(_):
        raise ValueError("nonfinite_json")

    return json.loads(
        Path(path).read_text(), object_pairs_hook=unique, parse_constant=bad
    )


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def identity(path):
    return dict(bytes=path.stat().st_size, sha256=digest(path))


def canonical_digest(value):
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def verify_files(root, files):
    for name, expected in files.items():
        require(Path(name).name == name, "unsafe_path")
        path = root / name
        require(path.is_file() and not path.is_symlink(), "missing_or_symlink")
        require(identity(path) == expected, "byte_identity")


def bind(packet, numeric, clock, sources, expected):
    require(digest(packet / "freeze.json") == expected, "freeze_identity")
    f = read_json(packet / "freeze.json")
    verify_files(packet, f["files"])
    verify_files(numeric, f["numeric_files"])
    verify_files(clock / "sources", f["context_files"])
    verify_files(clock, f["clock_files"])
    verify_files(sources, f["new_source_files"])
    require(
        digest(Path(sys.executable).resolve()) == f["runtime"]["sha256"],
        "runtime_identity",
    )
    import numpy
    import scipy

    require(numpy.__version__ == f["numpy_version"], "numpy_version")
    require(scipy.__version__ == f["scipy_version"], "scipy_version")
    return f


def mat_rows(path):
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
    return rows


def write_new(path, value):
    with Path(path).open("x") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")
