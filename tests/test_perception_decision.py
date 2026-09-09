"""Adversarial and independent small-population checks for the decision core."""
from copy import deepcopy
from fractions import Fraction
import hashlib
from itertools import product
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from tools.perception_decision import checker, cli, contract, kernel

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / 'research/perception-decision/0.1.0/matching-ambiguity.json'


def example():
    return json.loads(EXAMPLE.read_text())


def ratio(n, d=1):
    q = Fraction(n, d)
    return {'numerator': str(q.numerator), 'denominator': str(q.denominator)}


def detection(name):
    return {'id': name, 'record_sha256': hashlib.sha256(name.encode()).hexdigest()}


def brute_count(left, objects, edges):
    """Different algorithm: enumerate every partial injective assignment."""
    best = 0
    for assignment in product([None] + objects, repeat=len(left)):
        used = [o for o in assignment if o is not None]
        if len(used) != len(set(used)):
            continue
        if all(o is None or (d, o) in edges for d, o in zip(left, assignment)):
            best = max(best, len(used))
    return best


class DecisionCoreTests(unittest.TestCase):
    def evaluate(self, case):
        contract.validate(case)
        payload = kernel.produce(case)
        self.assertEqual(checker.check(case, payload), payload['result'])
        return payload

    def rejected(self, call, code):
        with self.assertRaises(contract.Invalid) as raised:
            call()
        self.assertEqual(raised.exception.code, code)

    def test_matching_competition_changes_preference(self):
        case = example()
        unresolved = self.evaluate(case)
        self.assertEqual(unresolved['result']['bounds'], {'lower': ratio(-1), 'upper': ratio(1)})
        self.assertEqual(unresolved['result']['decision']['preference'], 'unresolved')
        for exists, preference, value in [(False, 'prefer_base', -1), (True, 'prefer_augmented', 1)]:
            case['model']['clauses'] = [[{'variable': 'disputed_present', 'value': exists}]]
            result = self.evaluate(case)['result']
            self.assertEqual(result['bounds'], {'lower': ratio(value), 'upper': ratio(value)})
            self.assertEqual(result['decision']['preference'], preference)

    def test_exhaustive_graphs_against_independent_assignment_search(self):
        checked = 0
        for n_base, n_added, n_objects in product(range(3), range(3), range(4)):
            n_detections = n_base + n_added
            if n_detections > 3:
                continue
            base = ['b' + str(i) for i in range(n_base)]
            added = ['c' + str(i) for i in range(n_added)]
            objects = ['o' + str(i) for i in range(n_objects)]
            possibilities = list(product(base + added, objects))
            for mask in range(1 << len(possibilities)):
                edges = {edge for i, edge in enumerate(possibilities) if mask & (1 << i)}
                case = example()
                case['model'] = {'variables': [], 'clauses': []}
                anchor = case['anchors'][0]
                anchor['base']['value'] = [detection(n) for n in base]
                anchor['additions']['value'] = [detection(n) for n in added]
                anchor['reference'] = {'state': 'finite', 'objects': [{'id': n, 'when': []} for n in objects],
                                       'edges': [{'detection': d, 'object': o, 'when': []} for d, o in sorted(edges)]}
                payload = kernel.produce(case)
                checker.check(case, payload)
                tp_a = brute_count(base, objects, edges)
                tp_c = brute_count(base + added, objects, edges)
                direct_loss_a = n_objects - tp_a + n_base - tp_a
                direct_loss_c = n_objects - tp_c + n_detections - tp_c
                exact = ratio(direct_loss_a - direct_loss_c)
                self.assertEqual(payload['result']['bounds'], {'lower': exact, 'upper': exact})
                checked += 1
        self.assertGreater(checked, 1000)

    def test_shared_variables_preserve_cross_anchor_constraints(self):
        case = example()
        first = case['anchors'][0]
        second = deepcopy(first)
        second['id'] = 'anchor-2'
        first['weight'] = second['weight'] = ratio(1, 2)
        second['reference']['objects'][1]['when'][0]['value'] = False
        case['anchors'].append(second)
        # Every joint world has one +1 and one -1 contribution. Independent extrema would be loose.
        result = self.evaluate(case)['result']
        self.assertEqual(result['bounds'], {'lower': ratio(0), 'upper': ratio(0)})
        self.assertEqual(result['decision']['preference'], 'equivalent_within_tolerance')

    def test_open_reference_and_unavailable_outputs_are_different(self):
        case = example()
        case['anchors'][0]['reference'] = {'state': 'open', 'reason': 'unlisted matchable objects possible'}
        case['loss']['false_positive'] = ratio(4)
        open_result = self.evaluate(case)['result']
        self.assertEqual(open_result['bounds'], {'lower': ratio(-4), 'upper': ratio(1)})
        self.assertEqual(open_result['enclosure_kind'], 'conservative_open_reference')
        for state in ('missing', 'unmeasured', 'sensor_invalid', 'abstained', 'outside_support', 'unknown'):
            with self.subTest(state=state):
                missing = deepcopy(case)
                missing['anchors'][0]['additions'] = {'state': state, 'reason': 'not an observed empty output'}
                result = self.evaluate(missing)['result']
                self.assertEqual(result['execution_status'], 'input_blocked')
                self.assertIsNone(result['bounds'])
                self.assertEqual(result['decision']['preference'], 'not_evaluated')
        case['anchors'][0]['additions']['value'] = []
        self.assertEqual(self.evaluate(case)['result']['bounds'], {'lower': ratio(0), 'upper': ratio(0)})

    def test_inconsistent_model_does_not_yield_vacuous_support(self):
        case = example()
        case['model']['clauses'] = [[]]
        result = self.evaluate(case)['result']
        self.assertEqual(result['model_status'], 'inconsistent')
        self.assertIsNone(result['bounds'])
        self.assertEqual(result['decision']['improvement_criterion'], 'not_evaluated')

    def test_large_model_has_checked_coarse_fallback_and_explicit_consistency(self):
        case = example()
        case['model']['variables'].extend('v' + str(i) for i in range(13))
        result = self.evaluate(case)['result']
        self.assertEqual(result['execution_status'], 'resource_limited')
        self.assertEqual(result['bounds'], {'lower': ratio(-1), 'upper': ratio(1)})
        self.assertEqual(result['model_status'], 'consistent')
        case['model']['clauses'] = [[{'variable': 'disputed_present', 'value': True}]]
        result = self.evaluate(case)['result']
        self.assertEqual(result['model_status'], 'not_checked')
        self.assertEqual(result['decision']['preference'], 'not_evaluated')
        case['model']['feasible_assignment'] = [True] + [False] * 13
        self.assertEqual(self.evaluate(case)['result']['model_status'], 'consistent')

    def test_excluding_improvement_does_not_claim_base_superiority(self):
        case = example()
        case['model'] = {'variables': [], 'clauses': []}
        case['anchors'][0]['reference'] = {'state': 'open', 'reason': 'unresolved'}
        case['loss']['false_negative'] = ratio(1, 20)
        case['loss']['false_positive'] = ratio(2, 5)
        self.assertEqual(self.evaluate(case)['result']['decision'],
                         {'improvement_criterion': 'excluded', 'preference': 'unresolved'})

    def test_strict_tolerance_boundary(self):
        for value, criterion, preference in [(Fraction(1, 10), 'excluded', 'equivalent_within_tolerance'),
                                              (Fraction(11, 100), 'supported', 'prefer_augmented')]:
            case = example()
            case['model']['clauses'] = [[{'variable': 'disputed_present', 'value': True}]]
            case['loss']['false_negative'] = ratio(value)
            result = self.evaluate(case)['result']
            self.assertEqual(result['decision'], {'improvement_criterion': criterion, 'preference': preference})

    def test_omitted_world_and_forged_interval_are_rejected(self):
        case = contract.validate(example())
        original = kernel.produce(case)
        mutants = []
        omitted = deepcopy(original)
        omitted['proof']['worlds'].pop(0)
        mutants.append(omitted)
        repeated = deepcopy(original)
        repeated['proof']['worlds'][1] = deepcopy(repeated['proof']['worlds'][0])
        mutants.append(repeated)
        forged = deepcopy(original)
        forged['result']['bounds']['lower'] = ratio(1)
        mutants.append(forged)
        leaked_type = deepcopy(original)
        leaked_type['proof']['worlds'][0]['assignment'] = [0]
        mutants.append(leaked_type)
        unknown_field = deepcopy(original)
        unknown_field['result']['physical_truth_verified'] = True
        mutants.append(unknown_field)
        false_limit = deepcopy(original)
        false_limit['proof'] = {'kind': 'count_bound', 'reason': 'resource_limit', 'feasible_assignment': [False]}
        mutants.append(false_limit)
        for mutant in mutants:
            self.rejected(lambda: checker.check(case, mutant), 'CERTIFICATE_INVALID')

    def test_false_matching_and_cover_rejected(self):
        case = contract.validate(example())
        original = kernel.produce(case)
        for mutation in ('remove_cover', 'duplicate_match', 'invent_edge', 'remove_anchor'):
            forged = deepcopy(original)
            cert = forged['proof']['worlds'][0]['anchors'][0]['augmented']
            if mutation == 'remove_cover':
                cert['cover'] = {'detections': [], 'objects': []}
            elif mutation == 'duplicate_match':
                cert['matching'].append(cert['matching'][0])
            elif mutation == 'invent_edge':
                cert['matching'][0] = ['added-1', 'disputed']
            else:
                forged['proof']['worlds'][0]['anchors'] = []
            self.rejected(lambda: checker.check(case, forged), 'CERTIFICATE_INVALID')

    def test_contract_rejection_paths(self):
        changes = [
            ('DUPLICATE_ID', lambda c: c['anchors'].append(deepcopy(c['anchors'][0]))),
            ('DUPLICATE_ID', lambda c: c['anchors'][0]['additions']['value'].append(detection('base-1'))),
            ('UNKNOWN_ENDPOINT', lambda c: c['anchors'][0]['reference']['edges'][0].update(object='missing')),
            ('UNKNOWN_VARIABLE', lambda c: c['anchors'][0]['reference']['objects'][1]['when'][0].update(variable='other')),
            ('INVALID_RATIONAL', lambda c: c['anchors'][0].update(weight={'numerator':'2','denominator':'2'})),
            ('NEGATIVE_LOSS', lambda c: c['loss'].update(false_positive=ratio(-1))),
            ('POPULATION_WEIGHTS', lambda c: c['anchors'][0].update(weight=ratio(1,2))),
            ('ASSIGNMENT_SIZE', lambda c: c['model'].update(feasible_assignment=[])),
            ('INPUT_SCHEMA', lambda c: c.update(unknown=True)),
            ('INPUT_SCHEMA', lambda c: c.update(comparison_id='identity\n')),
            ('INPUT_SCHEMA', lambda c: c['anchors'][0]['base']['value'][0].update(record_sha256='a'*64+'\n')),
            ('INPUT_SCHEMA', lambda c: c['loss'].update(tolerance={'numerator':'1\n','denominator':'10'})),
            ('INPUT_SCHEMA', lambda c: c['loss'].update(tolerance={'numerator':True,'denominator':'1'})),
            ('INPUT_SCHEMA', lambda c: c['anchors'][0].update(base={'state':'missing','reason':'x','value':[]})),
        ]
        for code, change in changes:
            with self.subTest(code=code):
                case = example()
                change(case)
                self.rejected(lambda: contract.validate(case), code)
        case = example()
        case['model'].update(clauses=[[]], feasible_assignment=[False])
        self.rejected(lambda: contract.validate(case), 'INVALID_MODEL_WITNESS')

    def test_digest_is_checked_before_parsing(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / 'input'
            p.write_bytes(b'{not json')
            self.rejected(lambda: contract.load(p, '0' * 64), 'INPUT_DIGEST_MISMATCH')
            digest = hashlib.sha256(p.read_bytes()).hexdigest()
            self.rejected(lambda: contract.load(p, digest), 'INVALID_JSON')
            self.rejected(lambda: contract.load(p, digest, limit=2), 'INPUT_SIZE')
            self.rejected(lambda: contract.load(p, 'xyz'), 'EXPECTED_DIGEST')
        self.rejected(lambda: contract.parse(b'{"x":1,"x":2}'), 'DUPLICATE_KEY')
        self.rejected(lambda: contract.parse(b'{"x":NaN}'), 'INVALID_NUMBER')
        self.rejected(lambda: contract.parse(b'{"x":1e999}'), 'INVALID_NUMBER')
        self.rejected(lambda: contract.parse(b'{"x":0.1}'), 'INVALID_NUMBER')
        self.rejected(lambda: contract.parse(b'{"x":' + b'9' * 5000 + b'}'), 'INVALID_NUMBER')

    def test_packet_roundtrip_and_no_overwrite_or_partial_output(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'packet.json'
            digest = hashlib.sha256(EXAMPLE.read_bytes()).hexdigest()
            receipt = cli.run(EXAMPLE, digest, output)
            result = cli.verify(EXAMPLE, digest, output, receipt['sha256'])
            self.assertTrue(result['certificate_checked'])
            self.assertTrue(result['producer_matches_current_source'])
            before = output.read_bytes()
            with self.assertRaises(FileExistsError):
                cli.run(EXAMPLE, digest, output)
            self.assertEqual(output.read_bytes(), before)
            interrupted = Path(directory) / 'interrupted.json'
            with patch('tools.perception_decision.cli.os.link', side_effect=OSError('injected failure')):
                with self.assertRaises(OSError):
                    cli.run(EXAMPLE, digest, interrupted)
            self.assertFalse(interrupted.exists())
            self.assertEqual(list(Path(directory).glob('.perception-decision-*')), [])
            packet = json.loads(before)
            packet['payload']['proof']['worlds'].pop()
            output.write_bytes(contract.encoded(packet))
            changed = hashlib.sha256(output.read_bytes()).hexdigest()
            self.rejected(lambda: cli.verify(EXAMPLE, digest, output, receipt['sha256']), 'INPUT_DIGEST_MISMATCH')
            self.rejected(lambda: cli.verify(EXAMPLE, digest, output, changed), 'CERTIFICATE_INVALID')

    def test_cli_exit_distinguishes_valid_unresolved_and_blocked(self):
        with tempfile.TemporaryDirectory() as directory:
            for state, expected_exit in [('finite', 0), ('missing', 3), ('inconsistent', 3)]:
                case = example()
                if state == 'missing':
                    case['anchors'][0]['additions'] = {'state': 'missing', 'reason': 'required output absent'}
                elif state == 'inconsistent':
                    case['model']['clauses'] = [[]]
                source = Path(directory) / (state + '.input.json')
                source.write_bytes(contract.encoded(case))
                target = Path(directory) / (state + '.packet.json')
                digest = hashlib.sha256(source.read_bytes()).hexdigest()
                process = subprocess.run([sys.executable, '-m', 'tools.perception_decision', 'run',
                                          '--input', str(source), '--input-sha256', digest,
                                          '--output', str(target)], cwd=ROOT, capture_output=True)
                self.assertEqual(process.returncode, expected_exit, process.stderr)
                self.assertEqual(process.stderr, b'')
                self.assertTrue(json.loads(process.stdout)['certificate_checked'])
                self.assertTrue(target.is_file())


if __name__ == '__main__':
    unittest.main()
