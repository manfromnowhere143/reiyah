#!/usr/bin/env python3
"""Frozen, offline finite-record comparison. Raw input and trace stay private."""
import argparse
from collections import Counter, defaultdict
import csv
from decimal import Decimal, InvalidOperation
from fractions import Fraction
import hashlib
import io
from itertools import combinations
import json
from pathlib import Path
import struct
import sys
import time
import zlib

PROTOCOL_SHA = "98522dd1dc96c94621acc852ab7a90f6c753efa51fccdd7ea4a479710cd0d78b"
MODES = ("agree", "disagree", "unresolved")
INVALID = ("missing", "nonnumeric", "nonfinite", "nonpositive")


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True, allow_nan=False).encode("utf-8")


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def fraction(value):
    return f"{value.numerator}/{value.denominator}"


def timing(value):
    if not value.strip():
        return None, "missing"
    if len(value) > 128:
        return None, "nonnumeric"
    try:
        number = Decimal(value)
    except InvalidOperation:
        return None, "nonnumeric"
    if not number.is_finite():
        return None, "nonfinite"
    if number <= 0:
        return None, "nonpositive"
    return number, None


class Inflate(io.RawIOBase):
    """Bounded raw-deflate reader; validates the complete stream before acceptance."""
    def __init__(self, compressed, expected, deadline):
        self.source = memoryview(compressed)
        self.expected = expected
        self.deadline = deadline
        self.position = self.total = self.crc = 0
        self.decoder = zlib.decompressobj(-15)
        self.pending = b""
        self.sha = hashlib.sha256()
        self.complete = False

    def readable(self):
        return True

    def readinto(self, buffer):
        require(time.monotonic() < self.deadline, "analysis wall cap exceeded")
        if self.complete:
            return 0
        while True:
            chunk = self.pending
            if not chunk and self.position < len(self.source):
                end = min(self.position + 65536, len(self.source))
                chunk = self.source[self.position:end]
                self.position = end
            out = self.decoder.decompress(chunk, min(len(buffer), 65536))
            self.pending = self.decoder.unconsumed_tail
            self.total += len(out)
            require(self.total <= self.expected["member"]["uncompressed"], "inflated length exceeds bound")
            self.crc = zlib.crc32(out, self.crc)
            self.sha.update(out)
            if self.decoder.eof:
                require(not self.pending and not self.decoder.unused_data and self.position == len(self.source), "trailing deflate bytes")
                require(self.total == self.expected["member"]["uncompressed"], "CSV length differs")
                require(self.crc == self.expected["member"]["crc32"], "CSV CRC differs")
                require(self.sha.hexdigest() == self.expected["csv_sha256"], "CSV digest differs")
                self.complete = True
            if out:
                buffer[:len(out)] = out
                return len(out)
            if self.complete:
                return 0
            require(self.pending or self.position < len(self.source), "truncated deflate stream")


def source_reader(path, expected, deadline):
    with path.open("rb") as stream:
        raw = stream.read(expected["member_bytes"] + 1)
    require(len(raw) == expected["member_bytes"] and hashlib.sha256(raw).hexdigest() == expected["sha256"], "compressed source identity differs")
    require(len(raw) >= 30, "ZIP header truncated")
    sig, _, flags, method, _, _, crc, compressed, size, nlen, xlen = struct.unpack("<4s5H3I2H", raw[:30])
    member = expected["member"]
    require(sig == b"PK\x03\x04" and flags == member["flags"] == 0 and method == member["compression"] == 8, "ZIP method or flags differ")
    require((crc, compressed, size) == (member["crc32"], member["compressed"], member["uncompressed"]), "ZIP metadata differs")
    offset = 30 + nlen + xlen
    require(raw[30:30+nlen] == member["name"].encode() and offset == expected["local_header_bytes"] and len(raw) - offset == compressed, "ZIP member boundary differs")
    inflater = Inflate(raw[offset:], expected, deadline)
    text = io.TextIOWrapper(io.BufferedReader(inflater, 65536), encoding="utf-8", errors="strict", newline="")
    csv.field_size_limit(1 << 20)
    reader = csv.reader(text, strict=True)
    require(next(reader) == expected["header"], "CSV header differs")
    return reader, inflater, text


def squared_distance(a, na, b, nb):
    return Fraction(sum((a[c] * nb - b[c] * na) ** 2 for c in a.keys() | b.keys()), (na * nb) ** 2)


def mode(counts):
    largest = max(counts.values())
    winners = [category for category, count in counts.items() if count == largest]
    return winners[0] if len(winners) == 1 else None


def modal_status(selected, reference):
    a, b = mode(selected), mode(reference)
    return "unresolved" if a is None or b is None else "agree" if a == b else "disagree"


def evaluate_cell(cellid, duration, origin, records):
    """records=(physical row index, exact response, Decimal time or None, reason)."""
    valid = [record for record in records if record[2] is not None]
    n, n_all = len(valid), len(records)
    selected = sorted(valid, key=lambda r: (r[2], r[0]))[:3]
    invalid = Counter(record[3] for record in records if record[3] is not None)
    out = {"cellid": cellid, "duration": duration, "origin": origin,
           "status": "admitted" if n >= 3 else "excluded", "n": n, "n_all": n_all,
           "invalid_reasons": dict(sorted(invalid.items())),
           "membership_sha256": digest({"all": [r[0] for r in records], "timed": [r[0] for r in valid], "selected": [r[0] for r in selected]}),
           "dselected": None, "duniform": None, "delta": None, "missingdist": None,
           "tie_min": None, "tie_max": None, "boundary_tie": False,
           "modal_selected": None, "modal_uniform": None}
    full = Counter(r[1] for r in records)
    reference = Counter(r[1] for r in valid)
    if n:
        out["missingdist"] = fraction(squared_distance(full, n_all, reference, n))
    if n < 3:
        return out
    subset_distances = []
    modal = Counter({name: 0 for name in MODES})
    for subset in combinations(valid, 3):
        counts = Counter(r[1] for r in subset)
        subset_distances.append(squared_distance(counts, 3, reference, n))
        modal[modal_status(counts, reference)] += 1
    uniform = sum(subset_distances, Fraction()) / len(subset_distances)
    formula = Fraction(n - 3, 3 * (n - 1)) * (1 - sum((Fraction(count, n) ** 2 for count in reference.values()), Fraction()))
    require(uniform == formula, "enumeration and uniform formula disagree")
    selected_counts = Counter(r[1] for r in selected)
    chosen_distance = squared_distance(selected_counts, 3, reference, n)
    boundary = selected[-1][2]
    before = [r for r in valid if r[2] < boundary]
    tied = [r for r in valid if r[2] == boundary]
    slots = 3 - len(before)
    tie_values = [squared_distance(Counter(r[1] for r in before + list(tail)), 3, reference, n) for tail in combinations(tied, slots)]
    out.update(dselected=fraction(chosen_distance), duniform=fraction(uniform), delta=fraction(chosen_distance - uniform),
               tie_min=fraction(min(tie_values)), tie_max=fraction(max(tie_values)), boundary_tie=len(tied) > slots,
               modal_selected=modal_status(selected_counts, reference),
               modal_uniform={name: fraction(Fraction(modal[name], len(subset_distances))) for name in MODES})
    return out


def aggregate(records):
    admitted = [r for r in records if r["status"] == "admitted"]
    count = len(admitted)
    def mean(key):
        return fraction(sum((Fraction(r[key]) for r in admitted), Fraction()) / count) if count else None
    invalid = Counter()
    for r in records:
        invalid.update(r["invalid_reasons"])
    selected = Counter({name: 0 for name in MODES})
    selected.update(r["modal_selected"] for r in admitted)
    return {"cells": len(records), "admitted_cells": count, "excluded_cells": len(records) - count,
            "rows": sum(r["n_all"] for r in records), "valid_time_rows": sum(r["n"] for r in records),
            "invalid_time_rows": sum(r["n_all"] - r["n"] for r in records), "invalid_reasons": dict(sorted(invalid.items())),
            "n_histogram": dict(sorted(Counter(str(r["n"]) for r in records).items())),
            "timing_boundary_tie_cells": sum(r["boundary_tie"] for r in admitted),
            "mean_dselected": mean("dselected"), "mean_duniform": mean("duniform"), "mean_delta": mean("delta"),
            "mean_missingdist": mean("missingdist"),
            "tie_mean_delta_min": fraction(sum((Fraction(r["tie_min"]) - Fraction(r["duniform"]) for r in admitted), Fraction()) / count) if count else None,
            "tie_mean_delta_max": fraction(sum((Fraction(r["tie_max"]) - Fraction(r["duniform"]) for r in admitted), Fraction()) / count) if count else None,
            "modal_selected": dict(selected),
            "modal_uniform": {name: fraction(sum((Fraction(r["modal_uniform"][name]) for r in admitted), Fraction())) for name in MODES}}


def run(source, output):
    started = time.monotonic()
    deadline = started + 120
    protocol_bytes = Path(__file__).with_name("protocol.json").read_bytes()
    require(hashlib.sha256(protocol_bytes).hexdigest() == PROTOCOL_SHA, "frozen protocol identity differs")
    protocol = json.loads(protocol_bytes)
    expected, population = protocol["source"], protocol["population"]
    require(not output.exists(), "output already exists")
    reader, inflater, stream = source_reader(source, expected, deadline)
    cells = defaultdict(list)
    cell_workers = defaultdict(set)
    image_durations = defaultdict(set)
    image_origins = {}
    worker_ids = set()
    row_count = 0
    durations = {str(d) for d in population["assigned_exposure_values"]}
    for index, row in enumerate(reader):
        row_count += 1
        require(row_count <= population["rows"] and len(row) == len(expected["header"]), "CSV row count or shape differs")
        image, raw_duration, response, raw_time, worker, origin = row[1], row[2], row[4], row[5], row[6], row[7]
        require(all((image, response, worker, origin)) and max(map(len, (image, response, worker, origin, raw_duration, raw_time))) <= 4096, "required field missing or oversized")
        try:
            d = Decimal(raw_duration)
        except InvalidOperation:
            raise ValueError("assigned exposure invalid") from None
        require(d.is_finite() and d in population["assigned_exposure_values"], "assigned exposure outside frozen roster")
        duration = str(int(d))
        image_id, worker_id = digest(image), digest(worker)
        cellid = digest([image, duration])
        require(worker_id not in cell_workers[cellid], "repeated worker within cell")
        cell_workers[cellid].add(worker_id)
        worker_ids.add(worker_id)
        image_durations[image_id].add(duration)
        require(image_origins.get(image_id, origin) == origin, "origin varies within image")
        image_origins[image_id] = origin
        value, reason = timing(raw_time)
        cells[(cellid, duration, origin)].append((index, response, value, reason))
        if index % 10000 == 0:
            require(time.monotonic() < deadline, "analysis wall cap exceeded")
    require(inflater.complete, "input not completely verified")
    stream.close()
    require(row_count == population["rows"] and len(cells) == population["cells"] and len(image_durations) == population["images"] and len(worker_ids) == population["recorded_worker_ids"], "frozen population counts differ")
    require(all(value == durations for value in image_durations.values()), "image duration roster differs")
    require(all(len(value) == population["responses_per_cell"] for value in cells.values()), "cell count differs")
    origins = sorted(set(image_origins.values()))
    require(len(origins) == 2, "source origin roster is not two categories")
    trace = []
    for key, records in sorted(cells.items()):
        require(time.monotonic() < deadline, "analysis wall cap exceeded")
        trace.append(evaluate_cell(*key, records))
    aggregates = {"all": aggregate(trace), "by_duration": [], "by_origin": [], "by_duration_origin": []}
    for duration in sorted(durations, key=int):
        aggregates["by_duration"].append({"duration": duration, **aggregate([r for r in trace if r["duration"] == duration])})
    for origin in origins:
        aggregates["by_origin"].append({"origin": origin, **aggregate([r for r in trace if r["origin"] == origin])})
    for duration in sorted(durations, key=int):
        for origin in origins:
            aggregates["by_duration_origin"].append({"duration": duration, "origin": origin, **aggregate([r for r in trace if r["duration"] == duration and r["origin"] == origin])})
    require(time.monotonic() < deadline, "analysis wall cap exceeded")
    output.mkdir(parents=False, exist_ok=False)
    trace_sha = hashlib.sha256()
    with (output / "trace.jsonl").open("xb") as target:
        for record in trace:
            line = canonical(record) + b"\n"
            trace_sha.update(line)
            target.write(line)
    result = {"artifact_id": "reiyah.response-order-sensitivity.result", "version": "0.1.0", "lifecycle_status": "exploratory",
              "protocol_sha256": PROTOCOL_SHA, "producer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "source": {"sha256": expected["sha256"], "csv_sha256": expected["csv_sha256"], "crc32": inflater.crc, "bytes": expected["member_bytes"], "csv_bytes": inflater.total},
              "population": {"rows": row_count, "images": len(image_durations), "cells": len(cells), "recorded_worker_ids": len(worker_ids), "origins": origins},
              "trace_sha256": trace_sha.hexdigest(), "aggregates": aggregates,
              "limits": {"exploratory_not_preregistered": True, "independent_scientific_replication": False, "reference_is_observed_cohort_not_truth": True,
                         "timing_units_or_clock_validity_verified": False, "physical_speed_or_full_work_measured": False, "worker_identity_or_independence_verified": False,
                         "population_inference": False, "causal_deadline_benefit_established": False, "product_advantage_established": False, "full_csv_written": False}}
    with (output / "result.json").open("x", encoding="utf-8") as target:
        json.dump(result, target, indent=2, ensure_ascii=False, sort_keys=True, allow_nan=False)
        target.write("\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = run(args.source, args.output)
        print(json.dumps({"status": "completed_exploratory", "cells": result["population"]["cells"], "trace_sha256": result["trace_sha256"]}, sort_keys=True))
    except Exception as exc:
        reason = str(exc) if type(exc) is ValueError else type(exc).__name__
        print(json.dumps({"status": "invalid", "reason": reason}, sort_keys=True), file=sys.stderr)
        raise SystemExit(2)
