"""Nonadditive and invalid timer controls."""
from decimal import Decimal
import unittest
from cost_accounting import interval_union, span


def row(a,b):return {'started_utc':'2026-09-19T00:00:'+a+'+00:00','finished_utc':'2026-09-19T00:00:'+b+'+00:00'}


class CostTests(unittest.TestCase):
    def test_overlap_and_nested_intervals_charge_union_once(self):
        self.assertEqual(interval_union([row('00','10'),row('05','15'),row('07','08')]),Decimal(15))
    def test_disjoint_and_touching_intervals(self):
        self.assertEqual(interval_union([row('00','02'),row('02','03'),row('04','06')]),Decimal(5))
    def test_duplicate_duration_not_double_counted(self):
        self.assertEqual(interval_union([row('00.1','00.2')]*2),Decimal('.1'))
    def test_missing_reversed_or_timezone_free_times_fail(self):
        for a,b in [('2026-09-19T00:00:00','2026-09-19T00:00:01'),('2026-09-19T00:00:02Z','2026-09-19T00:00:01Z')]:
            with self.assertRaises(ValueError):span(a,b)
        with self.assertRaises(KeyError):interval_union([{}])


if __name__=='__main__':unittest.main()
