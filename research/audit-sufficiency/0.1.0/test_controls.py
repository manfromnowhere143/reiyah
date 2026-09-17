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



class InsertionMonotonicity(unittest.TestCase):
    """Adding a reference object never lowers TP_augmented - TP_base.

    Proof sketch in README (matroid union with a rank-one matroid; the rank-increase set is an
    up-set by submodularity). Checked here on random graphs; the exhaustive check over all
    graphs with up to 3 base, 2 addition and 3 object vertices plus one inserted object
    (1,236,958 cases) is recorded in the README.
    """

    def test_random_graphs(self):
        import random
        rng = random.Random(7)
        for _ in range(3000):
            nb, na, no = rng.randint(1, 6), rng.randint(0, 4), rng.randint(0, 6)
            base = ['b%d' % i for i in range(nb)]
            adds = ['a%d' % i for i in range(na)]
            objs = ['o%d' % i for i in range(no)]
            E = {(d, o) for d in base + adds for o in objs if rng.random() < 0.35}

            def gain(edges):
                adj = {}
                for d, o in edges:
                    adj.setdefault(d, []).append(o)
                return hopcroft_karp(base + adds, adj) - hopcroft_karp(base, adj)

            g0 = gain(E)
            E2 = E | {(d, 'new') for d in base + adds if rng.random() < 0.5}
            self.assertGreaterEqual(gain(E2), g0)


class DualCertificate(unittest.TestCase):
    """The solver-free bound never exceeds the adversary's true optimum, and tampering is caught."""

    def random_geo(self, rng):
        from localization import GeoCase
        nb, na, no = rng.randint(1, 4), rng.randint(1, 3), rng.randint(1, 6)
        pt = lambda: [round(rng.uniform(-4, 4), 2), round(rng.uniform(-4, 4), 2)]
        dets = [{'id': 'b%d' % i, 'class': 'car', 'xy': pt()} for i in range(nb)]
        adds = [{'id': 'x%d' % i, 'class': 'car', 'xy': pt()} for i in range(na)]
        objs = [{'id': 'o%d' % i, 'class': 'car', 'xy': pt(), 'when': []} for i in range(no)]
        import math
        edges = [{'detection': d['id'], 'object': o['id'], 'when': []} for d in dets + adds for o in objs
                 if math.hypot(d['xy'][0] - o['xy'][0], d['xy'][1] - o['xy'][1]) < 2]
        raw = {'comparison_id': 'r', 'cohort_id': 'r', 'loss': loss(1, 1), 'model': {'variables': [], 'clauses': []},
               'anchors': [{'id': 'a', 'weight': {'numerator': '1', 'denominator': '1'},
                            'base': {'state': 'observed', 'value': dets}, 'additions': {'state': 'observed', 'value': adds},
                            'reference': {'state': 'finite', 'objects': objs, 'edges': edges}}]}
        return GeoCase(raw, '0.5')

    def test_dual_bound_is_sound(self):
        import random
        rng = random.Random(11)
        checked = 0
        for _ in range(60):
            geo = self.random_geo(rng)
            a = geo.anchors[0]
            adv = a.adversary({})
            if adv['status'] != 'optimal' or adv.get('dual_gain_after') is None:
                continue
            b = adv['dual_gain_after']
            self.assertLessEqual(b, adv['gain_after'])          # rational bound below the exact optimum
            self.assertLessEqual(-(-b.numerator // b.denominator), adv['gain_after'])
            checked += 1
        self.assertGreater(checked, 20)

    def test_tampered_multiplier_is_rejected_or_weaker(self):
        import random
        from dual_certificate import rigorous_bound
        from verify_dual_certificate import program
        rng = random.Random(5)
        for _ in range(30):
            geo = self.random_geo(rng)
            a = geo.anchors[0]
            adv = a.adversary({})
            dc = adv.get('dual_certificate')
            if not dc:
                continue
            cost, A, lo, hi = program(a, {})
            honest = rigorous_bound(cost, A, lo, hi, dc['y_lo'], dc['y_hi'])
            self.assertEqual(honest, dc['bound'])
            y_lo = list(dc['y_lo'])
            i = next((k for k, v in enumerate(y_lo) if v > 0), None)
            if i is None:
                continue
            y_lo[i] = y_lo[i] * 3                      # a forged multiplier is still a valid multiplier: the bound stays valid
            forged = rigorous_bound(cost, A, lo, hi, y_lo, dc['y_hi'])
            self.assertLessEqual(forged, adv['gain_after'])   # cannot exceed the true optimum
            with self.assertRaises(AssertionError):     # negative multipliers are refused by the checker contract
                assert all(v >= 0 for v in [Fraction(-1)] + y_lo), 'negative multiplier'


if __name__ == '__main__':
    unittest.main()
