"""Controls for the sufficiency certificate. Run: python -B -m unittest test_controls -v"""
import unittest
from fractions import Fraction

from sufficiency import Case, hopcroft_karp


def loss(fn, fp, tol='1/10'):
    n, d = tol.split('/')
    return {'false_negative': {'numerator': str(fn), 'denominator': '1'},
            'false_positive': {'numerator': str(fp), 'denominator': '1'},
            'tolerance': {'numerator': n, 'denominator': d}}


def one_anchor(base, additions, objects, edges, fn=1, fp=1):
    return Case({'loss': loss(fn, fp), 'model': {'variables': [], 'clauses': []},
                 'anchors': [{'id': 'a', 'weight': {'numerator': '1', 'denominator': '1'},
                              'base': {'state': 'observed', 'value': [{'id': b} for b in base]},
                              'additions': {'state': 'observed', 'value': [{'id': x} for x in additions]},
                              'reference': {'state': 'finite', 'objects': [{'id': o, 'when': []} for o in objects],
                                            'edges': [{'detection': d, 'object': o, 'when': []} for d, o in edges]}}]})


class Matcher(unittest.TestCase):
    def test_all_three_by_three_graphs_against_brute_force(self):
        import itertools
        L, R = ['a', 'b', 'c'], ['x', 'y', 'z']
        U = list(itertools.product(L, R))
        for mask in range(1 << 9):
            E = {e for i, e in enumerate(U) if (mask >> i) & 1}
            adj = {}
            for u, v in E:
                adj.setdefault(u, []).append(v)
            brute = 0
            for ch in itertools.product([None] + R, repeat=3):
                used = [v for v in ch if v is not None]
                if len(used) != len(set(used)):
                    continue
                if all(v is None or (u, v) in E for u, v in zip(L, ch)):
                    brute = max(brute, len(used))
            self.assertEqual(hopcroft_karp(L, adj), brute)


class Certificates(unittest.TestCase):
    def test_joint_deletion_trap_floor_one_minimum_two(self):
        objs = ['o1', 'o2', 'o3']
        case = one_anchor(['b'], ['x'], objs, [(d, o) for d in ('b', 'x') for o in objs])
        self.assertEqual(case.delta(), Fraction(1))
        self.assertEqual(case.certificate(budget=1)['solver'], 'sufficient')
        c2 = case.certificate(budget=2)
        self.assertEqual(c2['solver'], 'insufficient')
        self.assertEqual(c2['achieved'], 'crosses')
        self.assertEqual(c2['counterexample_size'], 2)

    def test_two_carrier_control_needs_both_confirmed(self):
        case = one_anchor(['b'], ['x1', 'x2'], ['o1', 'o2'],
                          [('b', 'o1'), ('b', 'o2'), ('x1', 'o1'), ('x2', 'o2')], fn=1, fp=0)
        self.assertEqual(case.delta(), Fraction(1))
        for o in ('o1', 'o2'):
            self.assertEqual(case.delta() - case.delta(frozenset([('a', o)])), Fraction(1))
        self.assertEqual(case.delta() - case.delta(frozenset([('a', 'o1'), ('a', 'o2')])), Fraction(1))
        self.assertEqual(case.certificate()['solver'], 'insufficient')
        self.assertEqual(case.certificate(frozenset([('a', 'o1')]))['solver'], 'insufficient')
        both = case.certificate(frozenset([('a', 'o1'), ('a', 'o2')]))
        self.assertEqual(both['solver'], 'sufficient')
        self.assertEqual(both['sound'], 'sufficient')

    def test_excluded_criterion_is_not_certified(self):
        case = one_anchor(['b'], ['x'], ['o1'], [('b', 'o1'), ('x', 'o1')])
        self.assertEqual(case.delta(), Fraction(-1))
        self.assertEqual(case.certificate()['criterion'], 'excluded')

    def test_solver_and_achieved_agree_on_trap(self):
        objs = ['o1', 'o2', 'o3']
        case = one_anchor(['b'], ['x'], objs, [(d, o) for d in ('b', 'x') for o in objs])
        cert = case.certificate()
        self.assertEqual(cert['solver_max_drop'], cert['achieved_drop'])
        self.assertEqual(cert['solver_unverified_anchors'], 0)


if __name__ == '__main__':
    unittest.main()
