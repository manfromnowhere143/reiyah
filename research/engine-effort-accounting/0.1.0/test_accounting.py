"""Adversarial accounting checks; no participant or performance evidence."""
import copy
from fractions import Fraction
import itertools
from pathlib import Path
import tempfile
import unittest

import analyze as audit


def observation():
    def command(name, start, end):
        return {"id": "engine-test/checks/" + name + "/receipt.json", "task": "engine-test",
                "receipt_sha256": ("a" if name == "one" else "b") * 64, "started_utc": f"2026-09-13T00:00:{start:02d}Z",
                "ended_utc": f"2026-09-13T00:00:{end:02d}Z", "elapsed_seconds": str(end - start),
                "child_max_rss_bytes_macos": 10, "exit_code": 0}
    return {"artifact_id": "reiyah.engine.effort-accounting.observations", "version": "0.1.0",
            "selected_window_sha256": "c" * 64,
            "scope": {"started_utc": "2026-09-13T00:00:00Z", "ended_utc": "2026-09-13T00:00:10Z"},
            "checkpoints": [{"task": "engine-test", "closeout_sha256": "b" * 64}],
            "commands": [command("one", 0, 4), command("two", 2, 6)],
            "receipt_copies": [], "nested_receipts": []}


def sweep(intervals):
    """Independent endpoint multiplicities, without merge or union code."""
    events = {}
    for start, end in intervals:
        events[start] = events.get(start, 0) + 1
        events[end] = events.get(end, 0) - 1
    active = 0
    total = 0
    previous = None
    for endpoint, change in sorted(events.items()):
        if previous is not None and active > 0:
            total += endpoint - previous
        active += change
        previous = endpoint
    assert active == 0
    return total


class AccountingTests(unittest.TestCase):
    def test_exhaustive_union_against_integer_cell_coverage_and_sweep(self):
        intervals = list(itertools.combinations(range(5), 2))
        for mask in range(1 << len(intervals)):
            chosen = [pair for i, pair in enumerate(intervals) if mask & (1 << i)]
            expected = len({cell for start, end in chosen for cell in range(start, end)})
            self.assertEqual(audit.union(chosen), expected)
            self.assertEqual(sweep(chosen), expected)
        self.assertEqual(audit.union([(0, 0), (0, 2), (0, 2), (2, 4)]), 4)
        with self.assertRaises(ValueError):
            audit.union([(2, 1)])

    def test_repeated_execution_and_copies_and_nested_details(self):
        data = observation()
        # Distinct declared executions remain distinct; copied records add no run.
        data["receipt_copies"] = [{"id": "engine-test/OUTBOX/v/checks/receipt.json",
                                  "canonical_id": data["commands"][0]["id"], "receipt_sha256": "a" * 64}]
        data["nested_receipts"] = [{"id": "engine-test/private/one/child/receipt.json",
                                   "parent_id": data["commands"][0]["id"], "receipt_sha256": "d" * 64}]
        data["commands"][1]["exit_code"] = 1
        result = audit.analyze(data)
        self.assertEqual(result["total"]["command_count"], 2)
        self.assertEqual(result["total"]["reported_monotonic_seconds_sum"], "8")
        self.assertEqual(result["total"]["reported_utc_union_seconds"], "6")
        self.assertEqual(result["total"]["reported_utc_overlap_excess_seconds"], "2")
        self.assertEqual(result["total"]["maximum_reported_child_rss_bytes_macos"], 10)
        self.assertEqual(result["total"]["exit_code_counts"], {"0": 1, "1": 1})
        self.assertEqual((result["excluded_copies"], result["nested_details_not_added"]), (1, 1))
        self.assertEqual(result["outside_captured_utc_intervals_seconds"], "4")
        self.assertEqual(result["total_human_effort"], "unmeasured")

    def test_duplicate_commands_and_forged_copy_parent_or_digest_fail(self):
        original = observation()
        data = copy.deepcopy(original)
        data["commands"].append(copy.deepcopy(data["commands"][0]))
        with self.assertRaisesRegex(ValueError, "Duplicate execution"):
            audit.analyze(data)
        valid = {"id": "engine-test/OUTBOX/v/checks/receipt.json",
                 "canonical_id": original["commands"][0]["id"], "receipt_sha256": "a" * 64}
        for key, value in (("canonical_id", "absent"), ("receipt_sha256", "e" * 64),
                           ("id", "engine-test/OUTBOX/../receipt.json")):
            data = copy.deepcopy(original)
            data["receipt_copies"] = [{**valid, key: value}]
            with self.assertRaises(ValueError):
                audit.analyze(data)

    def test_missing_is_not_zero(self):
        data = observation()
        data["commands"] = []
        result = audit.analyze(data)
        self.assertIsNone(result["total"]["reported_monotonic_seconds_sum"])
        self.assertIsNone(result["total"]["maximum_reported_child_rss_bytes_macos"])
        self.assertIsNone(result["outside_captured_utc_intervals_seconds"])
        self.assertEqual(result["participant_review_effort"], "unmeasured")
        del data["commands"]
        with self.assertRaises(ValueError):
            audit.analyze(data)

    def test_invalid_clock_and_measurement_values_fail(self):
        for key, value in (("elapsed_seconds", None), ("elapsed_seconds", False),
                           ("elapsed_seconds", "NaN"), ("elapsed_seconds", "-1"),
                           ("child_max_rss_bytes_macos", True), ("child_max_rss_bytes_macos", -1),
                           ("exit_code", False), ("ended_utc", "2026-09-13T00:00:00"),
                           ("ended_utc", "2026-09-13T00:00:01Z"),
                           ("ended_utc", "2026-09-13T00:00:11Z")):
            data = observation()
            data["commands"][1][key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                audit.analyze(data)

    def test_exact_decimal_and_separate_clock_bases(self):
        data = observation()
        data["commands"][0]["elapsed_seconds"] = "0.1"
        data["commands"][1]["elapsed_seconds"] = "0.2"
        result = audit.analyze(data)
        self.assertEqual(result["total"]["reported_monotonic_seconds_sum"], "0.3")
        self.assertEqual(result["total"]["reported_utc_overlap_excess_seconds"], "2")
        for value in ("0", "1", "0.000000000000000000000000000001", "86400", "-0.01"):
            self.assertEqual(audit.decimal(Fraction(value)), value)

    def test_duplicate_json_keys_unknown_fields_and_identity_fail(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "record.json"
            path.write_text('{"a":1,"a":2}')
            with self.assertRaises(ValueError):
                audit.load(path)
        for key, value in (("artifact_id", "forged"), ("version", "0.2.0"), ("unrecognized", True)):
            data = observation()
            data[key] = value
            with self.assertRaises(ValueError):
                audit.analyze(data)

    def test_retained_timeline_with_independent_sweep(self):
        data = audit.load(Path(__file__).with_name("observations.json"))
        result = audit.analyze(data)
        groups = [data["commands"]] + [[r for r in data["commands"] if r["task"] == t["task"]] for t in data["checkpoints"]]
        for rows in groups:
            intervals = [(audit.micros(r["started_utc"]), audit.micros(r["ended_utc"])) for r in rows]
            self.assertEqual(audit.union(intervals), sweep(intervals))
        self.assertEqual(result["total_human_effort"], "unmeasured")


if __name__ == "__main__":
    unittest.main()
