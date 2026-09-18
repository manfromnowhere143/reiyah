"""Reject misleading retained histories and forged results on synthetic inputs."""
from copy import deepcopy
import unittest

from admission import Rejected, digest
from compare_math import ARMS, decision, interval, measure, subject, wire_interval
from replay import replay_record
from test_compare_math import picture, rectangle


def fixture(arm='B', family='exact_projection'):
    image = picture([], [rectangle('prediction')]); references = [rectangle('reference')]
    case = {'id': image['id'], 'group': 'singleton', 'images': [image['id']]}
    request = {'case_id': case['id'], 'arm': arm, 'family': family, 'sequence': 1,
        'image_id': image['id'], 'subject_sha256': subject(image), 'precision': 'whole_image_projection', 'method_version': '0.1.0'}
    answer = {'subject_sha256': subject(image), 'answer': references, 'source_sha256': 'c' * 64}
    event = {'request': request, 'answer': references, 'source_sha256': answer['source_sha256'],
        'basis': 'published_annotation_projection', 'residual': family,
        'requested_utc': '2026-09-18T00:00:00+00:00', 'returned_utc': '2026-09-18T00:00:00+00:00',
        'cost': {'observation_units': 1, 'human_seconds': None, 'human_cost': None, 'service_seconds': 0.0}}
    event['evidence_sha256'] = digest(event)
    measured = measure(image, references, family, ARMS[arm][1])
    bounds = interval([image], {image['id']: measured}, family); outcome = decision(bounds)
    row = {'begin': {'arm': arm, 'family': family, 'case_id': case['id'], 'group': 'singleton',
                     'ranking': [image['id']], 'query_budget': 1},
        'history': [
            {'type': 'checkpoint', 'sequence': 0, 'bounds': wire_interval(interval([image], {}, family)), 'decision': 'unresolved'},
            {'type': 'observation', 'event': event}, {'type': 'measurement', 'image_id': image['id'], 'value': measured},
            {'type': 'checkpoint', 'sequence': 1, 'bounds': wire_interval(bounds), 'decision': outcome}],
        'result': {'case_id': case['id'], 'group': 'singleton', 'arm': arm, 'family': family, 'query_order': [image['id']],
            'queries': 1, 'query_budget': 1, 'bounds': wire_interval(bounds), 'decision': outcome,
            'stop_reason': 'decision' if outcome in ('supported', 'excluded') else 'instrument_exhausted',
            'human_seconds': None, 'total_cost': None,
            'timing': {**measured['timing'], 'selection_seconds': 0.001, 'stopping_seconds': 0.001},
            'elapsed_seconds': measured['timing']['measurement_seconds'] + 1}}
    return row, [image], case, lambda iid: answer


class ReplayControls(unittest.TestCase):
    def test_valid_conventional_and_checked_histories_replay(self):
        for arm in ('A', 'B'):
            check = replay_record(*fixture(arm))
            self.assertEqual(check['queries'], 1)
            self.assertEqual(check['proofs'], 0 if arm == 'A' else 1)

    def test_false_acceptance_under_residual_uncertainty_is_rejected(self):
        args = list(fixture(family='one_edit_per_image')); args[0]['result']['decision'] = 'supported'
        with self.assertRaises(Rejected):
            replay_record(*args)

    def test_unserved_changed_or_omitted_answer_is_rejected(self):
        for kind in ('omitted', 'changed'):
            args = list(fixture())
            if kind == 'omitted':
                del args[0]['history'][1]
            else:
                event = args[0]['history'][1]['event']; event['answer'] = []
                event['evidence_sha256'] = digest({key: value for key, value in event.items() if key != 'evidence_sha256'})
            with self.assertRaises(Rejected):
                replay_record(*args)

    def test_missing_native_proof_is_rejected(self):
        args = list(fixture()); args[0]['history'][2]['value']['proofs'] = []
        with self.assertRaises(Rejected):
            replay_record(*args)

    def test_forged_native_matching_proof_is_rejected(self):
        args = list(fixture())
        args[0]['history'][2]['value']['proofs'][0]['payload']['proof']['worlds'][0]['anchors'][0]['output_b']['matching'] = []
        with self.assertRaises(ValueError):
            replay_record(*args)

    def test_premature_stopping_is_rejected(self):
        args = list(fixture()); args[0]['history'] = args[0]['history'][:1]
        with self.assertRaises(Rejected):
            replay_record(*args)

    def test_hidden_cost_and_fabricated_human_measurement_are_rejected(self):
        args = list(fixture()); args[0]['result']['timing']['measurement_seconds'] = 0
        with self.assertRaises(Rejected):
            replay_record(*args)
        args = list(fixture()); args[0]['result']['human_seconds'] = 1.0
        with self.assertRaises(Rejected):
            replay_record(*args)


if __name__ == '__main__':
    unittest.main()
