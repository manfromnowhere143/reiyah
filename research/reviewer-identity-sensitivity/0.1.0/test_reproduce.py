"""Finite exhaustive oracle and invalid-witness controls; no external data."""
import itertools
import unittest

from reproduce import (NO_MAJORITY, characterize, check_assignment, load_json,
                       validate_supports)


def enumerated(supports, classes):
    """Direct product, independent of bounds, matching and Hall implementations."""
    counts_by_world = []
    winners = set()
    for world in itertools.product(*(sorted(support) for support in supports)):
        counts = tuple(sum(vote == label for vote in world) for label in classes)
        counts_by_world.append(counts)
        winner = NO_MAJORITY
        for label, count in zip(classes, counts):
            if count * 2 > len(world):
                winner = label
        winners.add(winner)
    extrema = [(min(row[i] for row in counts_by_world),
                max(row[i] for row in counts_by_world)) for i in range(len(classes))]
    return winners, extrema


class SensitivityTests(unittest.TestCase):
    def test_all_three_class_support_multisets_through_six_groups(self):
        classes = ("a", "b", "c")
        vocabulary = [frozenset(c for i, c in enumerate(classes) if mask & (1 << i))
                      for mask in range(1, 8)]
        problems = 0
        for n in range(1, 7):
            for supports in itertools.combinations_with_replacement(vocabulary, n):
                expected_outcomes, extrema = enumerated(supports, classes)
                actual = characterize(supports, classes)
                self.assertEqual(set(actual["possible_outcomes"]), expected_outcomes)
                for label, (low, high) in zip(classes, extrema):
                    self.assertEqual(actual["class_count_bounds"][label],
                                     {"lower": low, "upper": high, "denominator": n})
                for label, assignment in actual["outcome_witnesses"].items():
                    self.assertIn(label, expected_outcomes)
                    self.assertEqual(len(assignment), n)
                    self.assertTrue(all(a in s for a, s in zip(assignment, supports)))
                problems += 1
        self.assertEqual(problems, 1715)

    def test_joint_feasibility_not_inferred_from_marginal_bounds(self):
        # Three uncertain votes, two labels: no universally winning class,
        # yet a strict majority exists in EVERY integral assignment.
        r = characterize([frozenset({"a", "b"})] * 3, ("a", "b"))
        self.assertEqual(r["possible_outcomes"], ["a", "b"])
        self.assertIsNotNone(r["no_majority_obstruction"])

    def test_permutations_preserve_outcomes_and_bounds(self):
        supports = [frozenset({"a"}), frozenset({"b", "c"}), frozenset({"a", "b"})]
        expected = characterize(supports, ("a", "b", "c"))
        for reordered in itertools.permutations(supports):
            actual = characterize(reordered, ("c", "a", "b"))
            self.assertEqual(actual["possible_outcomes"], expected["possible_outcomes"])
            self.assertEqual(actual["class_count_bounds"], expected["class_count_bounds"])

    def test_missing_and_undeclared_states_rejected(self):
        for supports, classes in (([], ("a",)), ([frozenset()], ("a",)),
                                  ([frozenset({"unknown"})], ("a",)),
                                  ([frozenset({"a"})], ("a", "a")),
                                  ([frozenset({NO_MAJORITY})], (NO_MAJORITY,))):
            with self.assertRaises(ValueError):
                validate_supports(supports, classes)

    def test_tampered_witness_refused(self):
        supports = [frozenset({"a"}), frozenset({"b"})]
        for assignment in (["a"], ["a", "a"], ["a", "b", "b"], [None, "b"]):
            with self.assertRaises(ValueError):
                check_assignment(supports, assignment)

    def test_duplicate_and_nonfinite_json_refused(self):
        for raw in ('{"a":1,"a":2}', '{"a":NaN}', '{"a":Infinity}'):
            with self.assertRaises(ValueError):
                load_json(raw)


if __name__ == "__main__":
    unittest.main()
