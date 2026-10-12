#!/usr/bin/env python3
"""Authored synthetic controls only; never opens the empirical member."""
from collections import Counter
from decimal import Decimal
from fractions import Fraction
import hashlib
from itertools import product
import json
from pathlib import Path
import struct
import tempfile
import time
import unittest
import zlib

import reproduce as p
import checker


def cell(labels, times=None):
    times = times if times is not None else [str(i + 1) for i in range(len(labels))]
    rows = [(i, label, *p.timing(t)) for i, (label, t) in enumerate(zip(labels, times))]
    return p.evaluate_cell("authored", "17", "authored", rows)


class Controls(unittest.TestCase):
    def test_unanimous(self):
        result = cell("AAAAAAA")
        self.assertEqual(result["delta"], "0/1")
        self.assertEqual(result["duniform"], "0/1")
        self.assertEqual(result["modal_uniform"], {"agree": "1/1", "disagree": "0/1", "unresolved": "0/1"})

    def test_split_selected_and_formula(self):
        result = cell("AAAABBB")
        self.assertEqual(result["dselected"], "18/49")
        self.assertEqual(result["duniform"], "16/147")
        self.assertEqual(result["delta"], "38/147")

    def test_n3_zero_distance(self):
        result = cell("ABC")
        self.assertEqual(result["dselected"], "0/1")
        self.assertEqual(result["duniform"], "0/1")
        self.assertEqual(result["modal_selected"], "unresolved")

    def test_n6_plurality_tie(self):
        result = cell("AAABBB")
        self.assertEqual(result["modal_selected"], "unresolved")
        self.assertEqual(result["modal_uniform"]["unresolved"], "1/1")

    def test_all_time_ties_cover_uniform(self):
        result = cell("AAAABBB", ["1"] * 7)
        self.assertTrue(result["boundary_tie"])
        self.assertLess(Fraction(result["tie_min"]), Fraction(result["duniform"]))
        self.assertGreater(Fraction(result["tie_max"]), Fraction(result["duniform"]))
        self.assertEqual(result["dselected"], "18/49")

    def test_boundary_only_tie_and_decimal_order(self):
        result = cell("ABCABCA", ["0.01", "0.2", "1.00", "1", "2", "3", "4"])
        self.assertTrue(result["boundary_tie"])
        expected = p.digest({"all": list(range(7)), "timed": list(range(7)), "selected": [0, 1, 2]})
        self.assertEqual(result["membership_sha256"], expected)

    def test_invalid_time_separate_reference(self):
        result = cell("AAAAAAB", ["1"] * 6 + ["-2"])
        self.assertEqual(result["n"], 6)
        self.assertEqual(result["n_all"], 7)
        self.assertEqual(result["invalid_reasons"], {"nonpositive": 1})
        self.assertEqual(result["missingdist"], "2/49")
        self.assertEqual(result["delta"], "0/1")

    def test_timing_states_preserved(self):
        for text, state in [("", "missing"), ("bad", "nonnumeric"), ("NaN", "nonfinite"), ("Infinity", "nonfinite"), ("0", "nonpositive"), ("-1", "nonpositive")]:
            self.assertEqual(p.timing(text), (None, state))

    def test_insufficient_pool_excluded(self):
        result = cell("AAABBBB", ["1", "2", "", "", "", "", ""])
        self.assertEqual(result["status"], "excluded")
        self.assertIsNone(result["delta"])
        aggregate = p.aggregate([result])
        self.assertEqual(aggregate["excluded_cells"], 1)
        self.assertIsNone(aggregate["mean_delta"])

    def test_categorical_strings_not_normalized(self):
        self.assertNotEqual(cell(["A", " A", "a", "A", " A", "a", "A"])["duniform"], "0/1")

    def test_exhaustive_authored_binary_formula(self):
        for n in (3, 4, 5, 6, 7):
            for labels in product("AB", repeat=n):
                result = cell(labels)
                self.assertEqual(Fraction(result["dselected"]) - Fraction(result["duniform"]), Fraction(result["delta"]))

    def test_aggregate_weighting_and_expected_modal_counts(self):
        a, b = cell("AAAAAAA"), cell("AAABBB")
        result = p.aggregate([a, b])
        self.assertEqual(Fraction(result["mean_delta"]), Fraction(b["delta"]) / 2)
        self.assertEqual(sum(map(Fraction, result["modal_uniform"].values())), 2)
        self.assertEqual(result["n_histogram"], {"6": 1, "7": 1})

    def test_independent_synthetic_differential(self):
        outputs = []
        cases = [(labels, [str(i + 1) for i in range(n)]) for n in range(3, 8) for labels in product("AB", repeat=n)]
        cases += [("ABCABCA", values) for values in (["1"] * 7, ["1", "2", "3", "3", "3", "4", "5"], ["1", "2", "-1", "NaN", "", "bad", "0"], [""] * 7)]
        for labels, times in cases:
            rows = [(i, label, *p.timing(t)) for i, (label, t) in enumerate(zip(labels, times))]
            actual = p.evaluate_cell(p.digest(["authored image", "17"]), "17", "authored", rows)
            expected = checker.cell_record("authored image", "17", "authored", rows)
            self.assertEqual(actual, expected)
            outputs.append(actual)
        self.assertEqual(p.aggregate(outputs), checker.aggregate(outputs))

    def test_synthetic_stream_crc_length_digest_and_tampering(self):
        payload = b"head\nvalue\n"
        encoder = zlib.compressobj(wbits=-15)
        compressed = encoder.compress(payload) + encoder.flush()
        name = b"synthetic.csv"
        crc = zlib.crc32(payload)
        raw = struct.pack("<4s5H3I2H", b"PK\x03\x04", 20, 0, 8, 0, 0, crc, len(compressed), len(payload), len(name), 0) + name + compressed
        expected = {"member_bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), "local_header_bytes": 30 + len(name), "csv_sha256": hashlib.sha256(payload).hexdigest(), "header": ["head"], "member": {"flags": 0, "compression": 8, "crc32": crc, "compressed": len(compressed), "uncompressed": len(payload), "name": name.decode()}}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "source"
            path.write_bytes(raw)
            reader, inflater, stream = p.source_reader(path, expected, time.monotonic() + 5)
            self.assertEqual(list(reader), [["value"]])
            self.assertTrue(inflater.complete)
            stream.close()
            path.write_bytes(raw[:-1] + bytes([raw[-1] ^ 1]))
            with self.assertRaisesRegex(ValueError, "identity"):
                p.source_reader(path, expected, time.monotonic() + 5)
            path.write_bytes(raw)
            altered = dict(expected, csv_sha256="0" * 64)
            with self.assertRaisesRegex(ValueError, "digest"):
                reader, inflater, stream = p.source_reader(path, altered, time.monotonic() + 5)
                list(reader)


if __name__ == "__main__":
    unittest.main()
