"""Independent replacement calculations and adversarial conditional-audit proofs."""
from copy import deepcopy
from fractions import Fraction
import hashlib
from itertools import combinations, product
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from tools.perception_decision import kernel as legacy_kernel
from tools.perception_revision import audit, audit_checker, checker, cli, contract, kernel

ROOT = Path(__file__).resolve().parents[1]


def ratio(n, d=1):
    return contract.wire(Fraction(n, d))


def detection(name):
    return {'id': name, 'record_sha256': hashlib.sha256(name.encode()).hexdigest()}


def example():
    old = json.loads((ROOT / 'research/perception-decision/0.1.0/matching-ambiguity.json').read_text())
    return contract.from_addition(old)


def finite(aa, bb, objects, edges):
    case = example()
    case['model'] = {'variables': [], 'clauses': []}
    anchor = case['anchors'][0]
    anchor['output_a']['value'] = [detection(n) for n in aa]
    anchor['output_b']['value'] = [detection(n) for n in bb]
    anchor['reference'] = {'state': 'finite', 'objects': [{'id': o, 'when': []} for o in objects],
                           'edges': [{'detection': d, 'object': o, 'when': []} for d, o in sorted(edges)]}
    return case


def brute_count(left, objects, edges):
    """Enumerate partial injections, independently of augmenting paths and covers."""
    best = 0
    for assignment in product([None] + list(objects), repeat=len(left)):
        used = [o for o in assignment if o is not None]
        if len(used) == len(set(used)) and all(o is None or (d, o) in edges for d, o in zip(left, assignment)):
            best = max(best, len(used))
    return best


def direct_delta(case, removed=frozenset(), env=None):
    env = env or {}
    fn, fp = (contract.rational(case['loss'][k]) for k in ('false_negative', 'false_positive'))
    total = Fraction(0)
    for a in case['anchors']:
        objects = [o['id'] for o in a['reference']['objects']
                   if all(env[t['variable']] == t['value'] for t in o['when'])
                   and (a['id'], o['id']) not in removed]
        edges = {(e['detection'], e['object']) for e in a['reference']['edges']
                 if e['object'] in objects and all(env[t['variable']] == t['value'] for t in e['when'])}
        losses = []
        for role in contract.ROLES:
            left = [d['id'] for d in a[role]['value']]
            tp = brute_count(left, objects, edges)
            losses.append(fn * (len(objects) - tp) + fp * (len(left) - tp))
        total += contract.rational(a['weight']) * (losses[0] - losses[1])
    return total


def request_for(case, budget=1, outcomes=()):
    return {'artifact_id': 'reiyah.perception-revision.audit-request', 'version': '0.1.0',
            'comparison_id': case['comparison_id'], 'reference_context_sha256': case['reference_context_sha256'],
            'family': 'reference_deletions', 'deletion_budget': budget, 'observation_basis': 'hypothetical',
            'observations': [{'anchor': a, 'object': o, 'outcome': answer,
                              'evidence_sha256': hashlib.sha256((a + o + answer).encode()).hexdigest()}
                             for a, o, answer in outcomes]}


def two_labels():
    return finite([], ['b1', 'b2'], ['o1', 'o2'], {('b1', 'o1'), ('b2', 'o2')})


class RevisionTests(unittest.TestCase):
    def evaluate(self, case, **kwargs):
        contract.validate(case)
        payload = kernel.produce(case, **kwargs)
        self.assertEqual(checker.check(case, payload), payload['result'])
        return payload

    def reject(self, fn, code=None):
        with self.assertRaises(contract.Invalid) as caught:
            fn()
        if code:
            self.assertEqual(caught.exception.code, code)

    def test_replacement_graphs_against_direct_loss_and_count_bound(self):
        checked = 0
        for common, na, nb, no in product(range(2), range(2), range(2), range(4)):
            shared = ['s'] if common else []
            aa = shared + (['a'] if na else [])
            bb = shared + (['b'] if nb else [])
            objects = ['o' + str(i) for i in range(no)]
            candidates = list(product(sorted(set(aa + bb)), objects))
            for mask in range(1 << len(candidates)):
                edges = {e for i, e in enumerate(candidates) if mask & (1 << i)}
                case = finite(aa, bb, objects, edges)
                for fn, fp in [(1, 1), (3, 0), (Fraction(1, 3), 2)]:
                    case['loss'].update(false_negative=ratio(fn), false_positive=ratio(fp))
                    packet = kernel.produce(case)
                    checker.check(case, packet)
                    expected = direct_delta(case)
                    self.assertEqual(packet['result']['bounds'], {'lower': ratio(expected), 'upper': ratio(expected)})
                    lo, hi = contract.anchor_bounds(case['anchors'][0], fn, fp)
                    self.assertLessEqual(lo, expected)
                    self.assertGreaterEqual(hi, expected)
                    checked += 1
        self.assertGreater(checked, 2000)

    def test_legacy_adapter_preserves_math_and_swap_is_antisymmetric(self):
        old = json.loads((ROOT / 'research/perception-decision/0.1.0/matching-ambiguity.json').read_text())
        previous = deepcopy(old)
        case = contract.from_addition(old)
        result = self.evaluate(case)['result']
        self.assertEqual(old, previous)
        self.assertEqual(result['bounds'], legacy_kernel.produce(old)['result']['bounds'])
        case = finite(['a', 's'], ['s', 'b', 'c'], ['o'], {('a', 'o'), ('s', 'o')})
        forward = self.evaluate(case)['result']['bounds']
        a = case['anchors'][0]
        a['output_a'], a['output_b'] = a['output_b'], a['output_a']
        backward = self.evaluate(case)['result']['bounds']
        self.assertEqual(contract.rational(forward['lower']), -contract.rational(backward['upper']))

    def test_identical_outputs_zero_under_open_and_resource_limited_references(self):
        case = finite(['s'], ['s'], ['o'], {('s', 'o')})
        for limit in (False, True):
            case['anchors'][0]['reference'] = {'state': 'open', 'reason': 'Unlisted objects possible'}
            if limit:
                case['model']['variables'] = ['v' + str(i) for i in range(13)]
            result = self.evaluate(case)['result']
            self.assertEqual(result['bounds'], {'lower': ratio(0), 'upper': ratio(0)})
            self.assertEqual(result['decision']['preference'], 'equivalent_within_tolerance')

    def test_joint_worlds_missing_outputs_and_inconsistency(self):
        case = example()
        first = case['anchors'][0]
        second = deepcopy(first)
        second['id'] = 'anchor-2'
        first['weight'] = second['weight'] = ratio(1, 2)
        second['reference']['objects'][1]['when'][0]['value'] = False
        case['anchors'].append(second)
        payload = self.evaluate(case)
        self.assertEqual(payload['result']['bounds'], {'lower': ratio(0), 'upper': ratio(0)})
        forged = deepcopy(payload)
        forged['proof']['worlds'].pop()
        self.reject(lambda: checker.check(case, forged), 'CERTIFICATE_INVALID')
        for state in ('missing', 'unmeasured', 'sensor_invalid', 'abstained', 'outside_support', 'unknown'):
            altered = deepcopy(case)
            altered['anchors'][0]['output_b'] = {'state': state, 'reason': 'Not observed empty'}
            result = self.evaluate(altered)['result']
            self.assertEqual(result['execution_status'], 'input_blocked')
            self.assertIsNone(result['bounds'])
        case['model']['clauses'] = [[]]
        result = self.evaluate(case)['result']
        self.assertEqual(result['model_status'], 'inconsistent')
        self.assertEqual(result['decision']['improvement_criterion'], 'not_evaluated')

    def test_contract_rejects_false_common_identity_and_invalid_context(self):
        original = example()
        changed = deepcopy(original)
        changed['anchors'][0]['output_b']['value'][0]['record_sha256'] = '0' * 64
        self.reject(lambda: contract.validate(changed), 'COMMON_OUTPUT_IDENTITY')
        for mutate in [lambda c: c.update(invented=True),
                       lambda c: c['anchors'][0].update(weight=0.5),
                       lambda c: c.update(reference_context_sha256='unbound')]:
            changed = deepcopy(original)
            mutate(changed)
            self.reject(lambda: contract.validate(changed), 'INPUT_SCHEMA')

    def test_checker_rejects_forgery_without_using_matching_solver(self):
        case = example()
        payload = self.evaluate(case)
        with patch('tools.perception_revision.kernel._matching_certificate', side_effect=AssertionError('solver')):
            checker.check(case, payload)
        forged = deepcopy(payload)
        forged['result']['decision']['improvement_criterion'] = 'supported'
        self.reject(lambda: checker.check(case, forged), 'CERTIFICATE_INVALID')
        forged = deepcopy(payload)
        forged['proof']['worlds'][0]['anchors'][0]['output_a']['cover']['objects'] = []
        forged['proof']['worlds'][0]['anchors'][0]['output_a']['cover']['detections'] = []
        self.reject(lambda: checker.check(case, forged), 'CERTIFICATE_INVALID')

    def test_work_screen_counts_both_outputs_and_all_guarded_edges(self):
        case = example()
        count, work = contract.capacity(case)
        self.assertEqual(count, 2)
        # A has one vertex and two potential edges; B has two and three.
        self.assertEqual(work, 1 + 1 + 1 + 2 * 2 * (2 + 2 + 1) + 2 * 3 * (2 + 3 + 1))
        case['model']['variables'].extend('v' + str(i) for i in range(13))
        payload = self.evaluate(case)
        self.assertEqual(payload['result']['execution_status'], 'resource_limited')
        forged = deepcopy(payload)
        forged['proof'] = {'kind': 'enumerated', 'worlds': []}
        self.reject(lambda: checker.check(case, forged), 'CERTIFICATE_INVALID')

    def test_revalidation_projects_certificates_and_recomputes_affected_graphs(self):
        before = finite(['a'], ['a', 'b'], ['o1', 'o2', 'unused'], {('a', 'o1'), ('b', 'o2')})
        old = self.evaluate(before)
        after = deepcopy(before)
        after['anchors'][0]['reference']['objects'].pop()
        counts = {'reused_certificates': 0, 'computed_certificates': 0}
        reused = self.evaluate(after, prior=(before, old), counters=counts)
        self.assertEqual(reused['result'], self.evaluate(after)['result'])
        self.assertEqual(counts, {'reused_certificates': 2, 'computed_certificates': 0})
        after['anchors'][0]['reference']['edges'] = []
        counts = {'reused_certificates': 0, 'computed_certificates': 0}
        self.assertEqual(self.evaluate(after, prior=(before, old), counters=counts)['result'], self.evaluate(after)['result'])
        self.assertEqual(counts['computed_certificates'], 2)

    def test_revalidation_new_edges_worlds_and_loss_are_checked_current(self):
        old_case = example()
        old_case['model']['clauses'] = [[{'variable': 'disputed_present', 'value': False}]]
        old = self.evaluate(old_case)
        new = example()
        new['loss']['tolerance'] = ratio(2)
        counts = {'reused_certificates': 0, 'computed_certificates': 0}
        fresh = self.evaluate(new, prior=(old_case, old), counters=counts)
        self.assertEqual(fresh['result'], self.evaluate(new)['result'])
        self.assertEqual(len(fresh['proof']['worlds']), 2)
        self.assertEqual(counts['reused_certificates'], 2)
        self.assertEqual(counts['computed_certificates'], 2)
        missing = deepcopy(new)
        missing['anchors'][0]['id'] = 'different-population'
        self.reject(lambda: kernel.produce(missing, prior=(old_case, old)), 'REVALIDATION_COHORT')
        disconnected = finite([], ['b'], ['o'], set())
        connected = deepcopy(disconnected)
        connected['anchors'][0]['reference']['edges'] = [{'detection': 'b', 'object': 'o', 'when': []}]
        counts = {'reused_certificates': 0, 'computed_certificates': 0}
        self.evaluate(connected, prior=(disconnected, self.evaluate(disconnected)), counters=counts)
        self.assertEqual(counts, {'reused_certificates': 1, 'computed_certificates': 1})


class AuditTests(unittest.TestCase):
    reject = RevisionTests.reject
    def audited(self, case, request, candidate=None):
        contract.validate(case)
        contract.validate_request(case, request)
        packet = audit.produce(case, request, candidate)
        self.assertEqual(audit_checker.check(case, request, packet), packet['result'])
        return packet

    def test_one_minimum_witness_is_not_a_sufficient_confirmed_set(self):
        case = two_labels()
        aid = case['anchors'][0]['id']
        first = request_for(case, outcomes=[(aid, 'o1', 'present')])
        packet = self.audited(case, first)
        self.assertEqual(packet['result']['sufficiency'], 'insufficient')
        self.assertEqual(packet['proof']['deletions'], [{'anchor': aid, 'object': 'o2'}])
        both = request_for(case, outcomes=[(aid, o, 'present') for o in ('o1', 'o2')])
        certified = self.audited(case, both)
        self.assertEqual(certified['result']['sufficiency'], 'sufficient')
        with patch('tools.perception_revision.audit._matching_certificate', side_effect=AssertionError('solver')):
            audit_checker.check(case, both, certified)
        forged = deepcopy(packet)
        forged['result']['sufficiency'] = 'sufficient'
        self.reject(lambda: audit_checker.check(case, first, forged), 'CERTIFICATE_INVALID')

    def test_absent_answers_update_worlds_and_error_budget(self):
        case = two_labels()
        aid = case['anchors'][0]['id']
        absent = request_for(case, outcomes=[(aid, 'o1', 'absent')])
        packet = self.audited(case, absent)
        self.assertEqual(packet['result']['sufficiency'], 'insufficient')
        self.assertEqual(packet['result']['counterexample_value'], ratio(0))
        impossible = request_for(case, budget=0, outcomes=[(aid, 'o1', 'absent')])
        result = self.audited(case, impossible)['result']
        self.assertEqual(result['model_status'], 'inconsistent')
        self.assertEqual(result['sufficiency'], 'not_evaluated')
        conditional = example()
        aid = conditional['anchors'][0]['id']
        observed_absent = request_for(conditional, budget=0, outcomes=[(aid, 'disputed', 'absent')])
        packet = self.audited(conditional, observed_absent)
        self.assertEqual(packet['proof']['assignment'], [False])
        self.assertEqual(packet['proof']['deletions'], [])

    def test_exact_audit_requires_every_permitted_deletion_and_joint_world(self):
        case = two_labels()
        case['loss']['false_positive'] = ratio(0)
        request = request_for(case)
        payload = self.audited(case, request)
        self.assertEqual(payload['proof']['kind'], 'enumerated_deletions')
        self.assertEqual(payload['result']['sufficiency'], 'sufficient')
        forged = deepcopy(payload)
        forged['proof']['worlds'][0]['variants'].pop()
        self.reject(lambda: audit_checker.check(case, request, forged), 'CERTIFICATE_INVALID')
        case['model']['variables'] = ['irrelevant']
        payload = self.audited(case, request)
        forged = deepcopy(payload)
        forged['proof']['worlds'].pop()
        self.reject(lambda: audit_checker.check(case, request, forged), 'CERTIFICATE_INVALID')

    def test_bounded_deletion_enclosures_contain_independent_exhaustive_losses(self):
        # Check conservative certificates even when exhaustive certificates would fit.
        checked = 0
        names = ['o1', 'o2', 'o3']
        possible = list(product(['a', 's', 'b'], names))
        for mask in range(1 << len(possible)):
            case = finite(['a', 's'], ['s', 'b'], names,
                          {e for i, e in enumerate(possible) if mask & (1 << i)})
            aid = case['anchors'][0]['id']
            for budget in (0, 1, 2):
                for answer in ('present', 'absent'):
                    request = request_for(case, budget, [(aid, 'o1', answer)])
                    domain = audit_checker.domain(case, request, {})
                    if domain is None:
                        continue
                    required, free, remaining = domain
                    rows, _ = audit.world_proposal(case, {}, required)
                    lo, hi = audit_checker.bounded_interval(case, {}, rows, required, free, remaining)
                    for size in range(min(len(free), remaining) + 1):
                        for selected in combinations(free, size):
                            value = direct_delta(case, required | frozenset(selected))
                            self.assertLessEqual(lo, value)
                            self.assertGreaterEqual(hi, value)
                            checked += 1
        self.assertGreater(checked, 1000)

    def test_large_family_defers_and_protected_matching_can_certify_sufficiency(self):
        case = finite([], ['b'], ['o' + str(i) for i in range(30)], {('b', 'o0')})
        request = request_for(case, 15)
        packet = self.audited(case, request)
        self.assertEqual(packet['result']['sufficiency'], 'unresolved')
        self.assertEqual(packet['proof']['kind'], 'bounded_deletions')
        request['observations'] = request_for(case, outcomes=[('anchor-1', 'o0', 'present')])['observations']
        packet = self.audited(case, request)
        self.assertEqual(packet['result']['sufficiency'], 'sufficient')
        self.assertEqual(packet['result']['enclosure_kind'], 'conservative_deletion_bound')

    def test_audit_keeps_coupled_worlds_and_does_not_treat_answers_as_independent(self):
        case = finite([], ['b'], ['o'], {('b', 'o')})
        case['loss']['false_positive'] = ratio(0)
        case['model']['variables'] = ['shared']
        first = case['anchors'][0]
        first['weight'] = ratio(1, 2)
        first['reference']['objects'][0]['when'] = [{'variable': 'shared', 'value': True}]
        second = deepcopy(first)
        second['id'] = 'second'
        second['reference']['objects'][0]['when'][0]['value'] = False
        case['anchors'].append(second)
        result = self.audited(case, request_for(case, 0))['result']
        self.assertEqual(result['bounds'], {'lower': ratio(1, 2), 'upper': ratio(1, 2)})
        self.assertEqual(result['sufficiency'], 'sufficient')
        impossible = request_for(case, 0, [('anchor-1', 'o', 'present'), ('second', 'o', 'present')])
        result = self.audited(case, impossible)['result']
        self.assertEqual(result['model_status'], 'inconsistent')
        self.assertEqual(result['sufficiency'], 'not_evaluated')

    def test_global_deletion_bound_with_unequal_weights_and_shared_uncertainty(self):
        case = example()
        first = case['anchors'][0]
        first['weight'] = ratio(1, 4)
        second = deepcopy(first)
        second['id'], second['weight'] = 'second', ratio(3, 4)
        second['reference']['objects'][1]['when'][0]['value'] = False
        case['anchors'].append(second)
        for _, env in contract.worlds(case['model']):
            for budget in range(4):
                req = request_for(case, budget)
                required, free, remaining = audit_checker.domain(case, req, env)
                rows, _ = audit.world_proposal(case, env, required)
                lo, hi = audit_checker.bounded_interval(case, env, rows, required, free, remaining)
                for n in range(min(len(free), remaining) + 1):
                    for selected in combinations(free, n):
                        value = direct_delta(case, frozenset(selected), env)
                        self.assertLessEqual(lo, value)
                        self.assertGreaterEqual(hi, value)

    def test_audit_scope_and_observation_reuse_reject_invalid_premises(self):
        case = two_labels()
        request = request_for(case, outcomes=[('anchor-1', 'o1', 'present')])
        duplicate = deepcopy(request)
        duplicate['observations'].append(deepcopy(duplicate['observations'][0]))
        self.reject(lambda: contract.validate_request(case, duplicate), 'DUPLICATE_ID')
        candidate = {'assignment': [], 'deletions': [{'anchor': 'anchor-1', 'object': 'o1'}]}
        self.reject(lambda: self.audited(case, request, candidate), 'AUDIT_CANDIDATE')
        new = deepcopy(case)
        new['comparison_id'] = 'next-comparison'
        new['anchors'][0]['output_b']['value'].pop()
        new['anchors'][0]['reference']['edges'].pop()
        rebound = contract.rebind_observations(case, request, new)
        self.assertEqual(rebound['observations'], request['observations'])
        self.assertEqual(rebound['comparison_id'], 'next-comparison')
        new['reference_context_sha256'] = '0' * 64
        self.reject(lambda: contract.rebind_observations(case, request, new), 'AUDIT_REFERENCE_CONTEXT')
        case['anchors'][0]['reference'] = {'state': 'open', 'reason': 'Missing objects possible'}
        empty = request_for(case)
        self.assertEqual(self.audited(case, empty)['result']['execution_status'], 'scope_unavailable')


class RevisionCLITests(unittest.TestCase):
    def test_generated_input_limit_rejects_before_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'oversize.json'
            with self.assertRaises(contract.Invalid) as raised:
                cli.write_output(path, {'data': 'long'}, limit=2)
            self.assertEqual(raised.exception.code, 'OUTPUT_SIZE')
            self.assertFalse(path.exists())

    def test_selected_bytes_revalidation_and_audit_packets(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            def save(name, value):
                data = contract.encoded(value)
                p = root / name
                p.write_bytes(data)
                return str(p), hashlib.sha256(data).hexdigest()
            def run(args):
                return subprocess.run([sys.executable, '-B', '-m', 'tools.perception_revision', *args],
                                      cwd=ROOT, capture_output=True)
            case = two_labels()
            path, digest = save('case.json', case)
            common = ['--input', path, '--input-sha256', digest]
            output = root / 'packet.json'
            first = run(['run', *common, '--output', str(output)])
            self.assertEqual(first.returncode, 0, first.stderr)
            packet_digest = hashlib.sha256(output.read_bytes()).hexdigest()
            verified = run(['verify', *common, '--packet', str(output), '--packet-sha256', packet_digest])
            self.assertEqual(verified.returncode, 0, verified.stderr)
            self.assertEqual(run(['run', *common, '--output', str(output)]).returncode, 2)
            self.assertEqual(run(['run', *common, '--prior-input', path, '--output', str(root / 'bad.json')]).returncode, 2)
            reused = run(['run', *common, '--prior-input', path, '--prior-input-sha256', digest,
                          '--prior-packet', str(output), '--prior-packet-sha256', packet_digest,
                          '--output', str(root / 'reused.json')])
            self.assertEqual(reused.returncode, 0, reused.stderr)
            self.assertEqual(json.loads(reused.stdout)['producer_path_counts']['reused_certificates'], 2)
            request = request_for(case, outcomes=[('anchor-1', o, 'present') for o in ('o1', 'o2')])
            rpath, rdigest = save('request.json', request)
            args = [*common, '--request', rpath, '--request-sha256', rdigest]
            out = root / 'audit.json'
            created = run(['audit', *args, '--output', str(out)])
            self.assertEqual(created.returncode, 0, created.stderr)
            answer = json.loads(created.stdout)
            verified = run(['verify-audit', *args, '--packet', str(out), '--packet-sha256', answer['sha256']])
            self.assertEqual(verified.returncode, 0, verified.stderr)
            request['deletion_budget'] = 2
            changed, changed_digest = save('changed.json', request)
            rejected = run(['verify-audit', *common, '--request', changed, '--request-sha256', changed_digest,
                            '--packet', str(out), '--packet-sha256', answer['sha256']])
            self.assertEqual(rejected.returncode, 2)
            self.assertEqual(json.loads(rejected.stderr)['code'], 'PACKET_BINDING')


if __name__ == '__main__':
    unittest.main()
