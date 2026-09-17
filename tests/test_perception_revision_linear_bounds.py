"""Challenge the LP embedding with independently enumerated finite graphs."""
from copy import deepcopy
from fractions import Fraction
from itertools import product
import unittest
from unittest.mock import patch

from test_perception_revision import ratio
from test_perception_revision_localization import fixture
from test_perception_revision_position_audit import answers
from tools.perception_revision import contract, linear_bounds as linear
from tools.perception_revision import localization, localization_checker, localization_contract
from tools.perception_revision import position_audit, position_checker


def paired_fixture(reverse=False):
    dets = {'a': ('car', (Fraction(0), Fraction(0))), 'b': ('car', (Fraction(10), Fraction(0)))}
    refs = {'x': ('car', (Fraction(19, 10), Fraction(0))), 'y': ('car', (Fraction(10), Fraction(0)))}
    aa, bb = (('a', 'b'), ('a',)) if reverse else (('a',), ('a', 'b'))
    case, request = fixture(aa, bb, dets, refs)
    reason, prepared = localization_contract.prepare(case, request)
    assert reason is None
    direction = 'a_minus_b' if reverse else 'b_minus_a'
    p = linear.program(prepared['rows'][0], direction)
    nonzero = {('cover', 'a', 'x'), ('cover', 'b', 'y'), ('available', 'a', 'x')}
    cert = {'artifact_id': 'reiyah.perception-revision.linear-certificate', 'version': '0.1.0',
            'entries': [{'anchor': case['anchors'][0]['id'], 'direction': direction,
                         'program_sha256': linear.digest(p),
                         'multipliers': [ratio(int(tuple(r['id']) in nonzero)) for r in p['rows']]}]}
    return case, request, cert


def independent_pair(left, edges):
    available = sorted(e for e in edges if e[0] in left)
    matchings = [set(e for e, bit in zip(available, bits) if bit) for bits in product((0, 1), repeat=len(available))]
    matchings = [m for m in matchings if len({d for d, _ in m}) == len({o for _, o in m}) == len(m)]
    matched = max(matchings, key=len)
    vertices = [('d', d) for d in sorted(left)] + [('o', o) for o in ('0', '1')]
    covers = [set(v for v, bit in zip(vertices, bits) if bit) for bits in product((0, 1), repeat=len(vertices))]
    covers = [c for c in covers if all(('d', d) in c or ('o', o) in c for d, o in available)]
    cover = min(covers, key=len)
    assert len(cover) == len(matched)
    return matched, cover


class LinearBoundsTests(unittest.TestCase):
    def test_shared_edge_bound_resolves_ordinary_unresolved_and_reverse(self):
        for reverse in (False, True):
            case, request, cert = paired_fixture(reverse)
            ordinary = localization.produce(case, request)
            self.assertEqual(ordinary['result']['robustness'], 'unresolved')
            payload = localization.produce(case, request, linear_certificate=cert)
            self.assertEqual(localization_checker.check(case, request, payload), payload['result'])
            value = -1 if reverse else 1
            self.assertEqual(payload['result']['bounds'], {'lower': ratio(value), 'upper': ratio(value)})
            self.assertEqual(payload['result']['robustness'], 'excluded_for_family' if reverse else 'robust')

    def test_all_tiny_shared_graphs_embed_actual_matching_difference(self):
        # The same IDs deliberately occur on left and right. No producer or solver.
        all_edges = [('0', '0'), ('0', '1'), ('1', '0'), ('1', '1')]
        checked = 0
        for memberships in product((1, 2, 3), repeat=2):
            aa = {str(i) for i, m in enumerate(memberships) if m & 1}
            bb = {str(i) for i, m in enumerate(memberships) if m & 2}
            for states in product((0, 1, 2), repeat=4):
                guaranteed = {e for e, s in zip(all_edges, states) if s == 1}
                possible = {e for e, s in zip(all_edges, states) if s != 0}
                free = sorted(possible - guaranteed)
                row = {'a': aa, 'b': bb, 'guaranteed': guaranteed, 'possible': possible}
                for direction in ('b_minus_a', 'a_minus_b'):
                    p = linear.program(row, direction)
                    self.assertEqual(len(p['variables']), len({tuple(v) for v in p['variables']}))
                    duals = [ratio((i * 7 + len(free)) % 4, 3) for i in range(len(p['rows']))]
                    bound = linear.lower_bound(p, duals)
                    match_side, cover_side = (aa, bb) if direction == 'b_minus_a' else (bb, aa)
                    for bits in product((0, 1), repeat=len(free)):
                        edges = guaranteed | {e for e, bit in zip(free, bits) if bit}
                        matching, _ = independent_pair(match_side, edges)
                        _, cover = independent_pair(cover_side, edges)
                        values = []
                        for v in p['variables']:
                            values.append(int(tuple(v[1:]) in edges) if v[0] == 'presence' else
                                          int(('d', v[1]) in cover) if v[0] == 'cover_detection' else
                                          int(('o', v[1]) in cover) if v[0] == 'cover_reference' else
                                          int(tuple(v[1:]) in matching))
                        for constraint in p['rows']:
                            self.assertGreaterEqual(sum(values[j] * c for j, c in constraint['terms']), constraint['lower'])
                        gain = len(cover) - len(matching)
                        self.assertEqual(sum(c * v for c, v in zip(p['costs'], values)), gain)
                        self.assertLessEqual(-(-bound.numerator // bound.denominator), gain)
                        checked += 1
        self.assertEqual(checked, 4608)

    def test_no_optimizer_or_matching_producer_is_used_by_checker(self):
        case, request, cert = paired_fixture()
        payload = localization.produce(case, request, linear_certificate=cert)
        with patch.object(localization, '_matching_certificate', side_effect=AssertionError('producer entered')):
            self.assertEqual(localization_checker.check(case, request, payload)['robustness'], 'robust')
        bad = deepcopy(payload); bad['result']['bounds']['lower'] = ratio(2)
        with self.assertRaises(contract.Invalid): localization_checker.check(case, request, bad)

    def test_documented_closed_schema_agrees_with_a_valid_proposal(self):
        _, _, cert = paired_fixture()
        contract.schema_check(cert, linear.SCHEMA)
        cert['entries'][0]['invented'] = True
        with self.assertRaises(contract.Invalid): contract.schema_check(cert, linear.SCHEMA)

    def test_malformed_unbound_or_negative_certificates_reject(self):
        case, request, original = paired_fixture()
        variants = []
        c = deepcopy(original); c['surprise'] = True; variants.append(c)
        c = deepcopy(original); c['entries'][0]['direction'] = 'unknown'; variants.append(c)
        c = deepcopy(original); c['entries'][0]['anchor'] = 'invented'; variants.append(c)
        c = deepcopy(original); c['entries'].append(deepcopy(c['entries'][0])); variants.append(c)
        c = deepcopy(original); c['entries'][0]['program_sha256'] = '0' * 64; variants.append(c)
        c = deepcopy(original); c['entries'][0]['multipliers'].pop(); variants.append(c)
        for v in [ratio(-1), {'numerator': '1', 'denominator': '0'},
                  {'numerator': '2', 'denominator': '2'}, {'numerator': True, 'denominator': '1'},
                  {'numerator': '1' * 90, 'denominator': '1'}, {'numerator': 'NaN', 'denominator': '1'}]:
            c = deepcopy(original); c['entries'][0]['multipliers'][0] = v; variants.append(c)
        for c in variants:
            with self.subTest(c=c):
                with self.assertRaises(contract.Invalid): localization.produce(case, request, linear_certificate=c)

    def test_partial_empty_and_zero_certificates_keep_sound_fallback(self):
        case, request, cert = paired_fixture()
        ordinary = localization.produce(case, request)['result']['bounds']
        for proposal in [dict(cert, entries=[]), deepcopy(cert)]:
            for entry in proposal['entries']:
                entry['multipliers'] = [ratio(0) for _ in entry['multipliers']]
            result = localization.produce(case, request, linear_certificate=proposal)['result']
            self.assertEqual(result['bounds'], ordinary)
            self.assertEqual(result['robustness'], 'unresolved')

    def test_work_and_arithmetic_limits_reject_explicit_candidate(self):
        case, request, cert = paired_fixture()
        with patch.object(linear, 'MAX_WORK', 1):
            with self.assertRaises(contract.Invalid): localization.produce(case, request, linear_certificate=cert)
        with patch.object(linear, 'MAX_ACCUMULATOR_BITS', 0):
            with self.assertRaises(contract.Invalid): localization.produce(case, request, linear_certificate=cert)
        with self.assertRaises(contract.Invalid): localization.produce(case, request, {}, linear_certificate=cert)

    def test_position_observations_require_current_program_and_keep_residuals(self):
        case, request, cert = paired_fixture()
        observations = answers(case, request, {})
        payload = position_audit.produce(case, request, observations, linear_certificate=cert)
        self.assertEqual(position_checker.check(case, request, observations, payload)['robustness'], 'robust')
        aid = case['anchors'][0]['id']
        measured = answers(case, request, {(aid, 'x'): ((Fraction(19,10), Fraction(0)), Fraction(0))})
        with self.assertRaises(contract.Invalid):
            position_audit.produce(case, request, measured, linear_certificate=cert)
        adversarial = deepcopy(payload); adversarial['proof']['geometry']['kind'] = 'localization_displacement'
        with self.assertRaises(contract.Invalid): position_checker.check(case, request, observations, adversarial)

    def test_resource_unavailability_does_not_admit_a_linear_proof(self):
        case, request, cert = paired_fixture()
        with patch.object(localization_contract, 'MAX_WORK', 1):
            result = localization.produce(case, request, linear_certificate=cert)
            self.assertEqual(result['result']['robustness'], 'unresolved')
            self.assertEqual(result['proof']['kind'], 'localization_unavailable')
