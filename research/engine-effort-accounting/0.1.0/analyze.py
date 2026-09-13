#!/usr/bin/env python3
"""Offline arithmetic on a declared projection of Engine command receipts.

This checks the projection, not the original executions, private source closure,
physical clock accuracy, participant effort or comparator performance.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction
import json
from pathlib import Path
import re


def require(condition, message):
    if not condition:
        raise ValueError(message)


def fields(value, names):
    require(type(value) is dict and set(value) == set(names.split()),
            "Missing or unknown fields")


def digest(value):
    require(type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value),
            "Invalid SHA-256")


def micros(value):
    require(type(value) is str and re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{6})?(?:Z|\+00:00)", value),
        "Require explicit UTC with at most the selected microsecond precision")
    dt = datetime.fromisoformat(value) - datetime(1970, 1, 1, tzinfo=timezone.utc)
    return (dt.days * 86400 + dt.seconds) * 1_000_000 + dt.microseconds


def seconds(value):
    require(type(value) is str and re.fullmatch(r"(?:0|[1-9]\d{0,4})(?:\.\d{1,30})?", value),
            "Require a nonnegative bounded decimal duration string")
    result = Fraction(value)
    require(result <= 86400, "Duration exceeds this one-day audit domain")
    return result


def decimal(value):
    """Exact finite decimal; the input domain has only powers of 2 and 5 below."""
    value = Fraction(value)
    denominator = value.denominator
    powers = []
    for factor in (2, 5):
        count = 0
        while denominator % factor == 0:
            count += 1
            denominator //= factor
        powers.append(count)
    require(denominator == 1, "Nonterminating decimal outside receipt domain")
    scale = max(powers)
    number = value.numerator * (10 ** scale // value.denominator)
    if scale == 0:
        return str(number)
    sign = "-" if number < 0 else ""
    digits = str(abs(number)).rjust(scale + 1, "0")
    return (sign + digits[:-scale] + "." + digits[-scale:]).rstrip("0").rstrip(".")


def union(intervals):
    """Half-open UTC intervals; touching endpoints add no overlap."""
    merged = []
    for start, end in sorted(intervals):
        require(start <= end, "Reversed interval")
        if start == end:
            continue
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return sum(end - start for start, end in merged)


def summarize(commands):
    if not commands:
        return {"command_count": 0, "measurement_state": "no_canonical_receipts",
                "reported_monotonic_seconds_sum": None, "reported_utc_union_seconds": None,
                "reported_utc_interval_seconds_sum": None, "reported_utc_overlap_excess_seconds": None,
                "maximum_reported_child_rss_bytes_macos": None, "exit_code_counts": {}}
    intervals = [(micros(r["started_utc"]), micros(r["ended_utc"])) for r in commands]
    union_us = union(intervals)
    sum_us = sum(end - start for start, end in intervals)
    return {"command_count": len(commands), "measurement_state": "captured_commands_only",
            "reported_monotonic_seconds_sum": decimal(sum(seconds(r["elapsed_seconds"]) for r in commands)),
            "reported_utc_union_seconds": decimal(Fraction(union_us, 1_000_000)),
            "reported_utc_interval_seconds_sum": decimal(Fraction(sum_us, 1_000_000)),
            "reported_utc_overlap_excess_seconds": decimal(Fraction(sum_us - union_us, 1_000_000)),
            "maximum_reported_child_rss_bytes_macos": max(r["child_max_rss_bytes_macos"] for r in commands),
            "exit_code_counts": dict(sorted(Counter(str(r["exit_code"]) for r in commands).items()))}


def analyze(data):
    fields(data, "artifact_id version selected_window_sha256 scope checkpoints commands receipt_copies nested_receipts")
    require(data["artifact_id"] == "reiyah.engine.effort-accounting.observations" and data["version"] == "0.1.0",
            "Unselected observation interface")
    digest(data["selected_window_sha256"])
    fields(data["scope"], "started_utc ended_utc")
    lower, upper = (micros(data["scope"][key]) for key in ("started_utc", "ended_utc"))
    require(0 < upper - lower <= 86400 * 1_000_000, "Invalid one-day scope")
    for name in ("checkpoints", "commands", "receipt_copies", "nested_receipts"):
        require(type(data[name]) is list and len(data[name]) <= 1000, "Invalid bounded list")
    tasks = {}
    for row in data["checkpoints"]:
        fields(row, "task closeout_sha256")
        task = row["task"]
        require(type(task) is str and re.fullmatch(r"engine-[a-z0-9-]+", task), "Invalid task identity")
        require(task not in tasks, "Duplicate checkpoint identity")
        digest(row["closeout_sha256"])
        tasks[task] = []
    require(tasks, "Missing selected checkpoints")
    commands = {}
    for row in data["commands"]:
        fields(row, "id task receipt_sha256 started_utc ended_utc elapsed_seconds child_max_rss_bytes_macos exit_code")
        identity, task = row["id"], row["task"]
        require(type(task) is str and task in tasks, "Unknown command task")
        require(type(identity) is str and re.fullmatch(re.escape(task) + r"/checks/[a-z0-9_-]+/receipt\.json", identity),
                "Require canonical task/checks/job/receipt identity")
        require(identity not in commands, "Duplicate execution identity; copies are not new commands")
        digest(row["receipt_sha256"])
        start, end = micros(row["started_utc"]), micros(row["ended_utc"])
        require(lower <= start <= end <= upper, "Command outside declared UTC scope or reversed")
        seconds(row["elapsed_seconds"])
        require(type(row["child_max_rss_bytes_macos"]) is int and 0 <= row["child_max_rss_bytes_macos"] < 2 ** 63,
                "Invalid reported memory value")
        require(type(row["exit_code"]) is int and -255 <= row["exit_code"] <= 255, "Invalid exit code")
        commands[identity] = row
        tasks[task].append(row)
    excluded = set()
    for kind, parent_key in (("receipt_copies", "canonical_id"), ("nested_receipts", "parent_id")):
        for row in data[kind]:
            fields(row, f"id {parent_key} receipt_sha256")
            identity, parent = row["id"], row[parent_key]
            require(type(parent) is str and parent in commands, "Unknown excluded-record parent")
            require(type(identity) is str and identity.startswith(commands[parent]["task"] + "/"),
                    "Excluded record outside parent task")
            require(identity not in commands and identity not in excluded, "Duplicate record identity")
            parts = identity.split("/")
            require(all(re.fullmatch(r"[A-Za-z0-9_.-]+", p) and p not in (".", "..") for p in parts), "Invalid record path")
            require(parts[1] == ("OUTBOX" if kind == "receipt_copies" else "private") and parts[-1] == "receipt.json",
                    "Invalid exclusion path")
            digest(row["receipt_sha256"])
            if kind == "receipt_copies":
                require(row["receipt_sha256"] == commands[parent]["receipt_sha256"], "Copy digest differs from canonical receipt")
            excluded.add(identity)
    total = summarize(list(commands.values()))
    covered = total["reported_utc_union_seconds"]
    return {"artifact_id": "reiyah.engine.effort-accounting.result", "version": "0.1.0",
            "scope": data["scope"], "scope_utc_seconds": decimal(Fraction(upper - lower, 1_000_000)),
            "outside_captured_utc_intervals_seconds": None if covered is None else decimal(Fraction(upper - lower, 1_000_000) - Fraction(covered)),
            "total": total, "by_checkpoint": {task: summarize(rows) for task, rows in sorted(tasks.items())},
            "excluded_copies": len(data["receipt_copies"]), "nested_details_not_added": len(data["nested_receipts"]),
            "total_human_effort": "unmeasured", "participant_review_effort": "unmeasured",
            "cpu_time": "not_recorded_by_selected_receipts", "system_peak_memory": "not_measured",
            "coverage": "selected_outer_commands_only; uncovered intervals are not idle time",
            "verification_scope": "projection structure and exact arithmetic; original receipt extraction is a separate private check"}


def load(path):
    def unique(pairs):
        obj = {}
        for key, value in pairs:
            require(key not in obj, "Duplicate JSON key")
            obj[key] = value
        return obj
    return json.loads(Path(path).read_bytes(), object_pairs_hook=unique,
                      parse_constant=lambda _: require(False, "Nonfinite JSON number"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("observations", nargs="?", default=Path(__file__).with_name("observations.json"))
    args = parser.parse_args()
    try:
        print(json.dumps(analyze(load(args.observations)), sort_keys=True, indent=2, allow_nan=False))
    except (ValueError, TypeError, KeyError, OSError) as exc:
        parser.exit(2, json.dumps({"state": "invalid", "detail": str(exc)}) + "\n")
