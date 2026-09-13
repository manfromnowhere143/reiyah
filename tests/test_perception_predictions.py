"""Source fidelity and invalid-input controls for prediction-only preparation."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import perception_predictions as p
from tools.perception_decision.contract import Invalid, encoded


class PredictionInputs(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.inputs = self.root/'inputs'; self.inputs.mkdir()
        self.request_dir = self.root/'requests'; self.request_dir.mkdir()
        self.tokens = ['a'*32, 'b'*32, 'c'*32]
        # Lexical distinctions, UTF-8, duplicates, low scores and nonfinite/unknown
        # fields must survive even though they need later semantic validation.
        row = ('{ "sample_token":"'+self.tokens[0]+'", "detection_score":0.00, '
               '"translation":[10000,-0.0,1e-4], "velocity":[NaN,Infinity], '
               '"detection_name":"unmapped", "extra":"é" }').encode()
        self.row = row
        self.array = b'[ \n'+row+b', '+row+b' ]'
        self.meta = encoded({key: False for key in p.META_FIELDS}).strip()
        self.raw = (b'{"results":{"'+self.tokens[0].encode()+b'":'+self.array+b',"'+
                    self.tokens[1].encode()+b'":[]},"meta":'+self.meta+b'}')
        self.source = self.inputs/'submission.json'; self.source.write_bytes(self.raw)
        self.request = {'artifact_id': 'reiyah.perception-predictions.request', 'version': '0.1.0',
                        'exposure': p.EXPOSURE, 'sources': [self.source_spec()],
                        'frames': [{'id': f'frame-{i}', 'sample_token': token} for i, token in enumerate(self.tokens)]}

    def source_spec(self):
        data = self.source.read_bytes()
        return {'id': 'configuration-1', 'state': 'observed', 'path': str(self.source),
                'byte_size': len(data), 'sha256': hashlib.sha256(data).hexdigest()}

    def bind_request(self, request=None):
        path = self.request_dir/'request.json'
        data = encoded(self.request if request is None else request)
        path.write_bytes(data)
        return path, hashlib.sha256(data).hexdigest()

    def reject(self, fn, code):
        with self.assertRaises(Invalid) as caught:
            fn()
        self.assertEqual(caught.exception.code, code)

    def files(self, request=None):
        return p.materialize(self.request if request is None else request, '0'*64)[0]

    def test_exact_original_arrays_rows_and_states(self):
        files = self.files(); packet = json.loads(files['PREDICTIONS.json'])
        frames = packet['frames']; observed = frames[0]['predictions']['configuration-1']
        self.assertEqual(files[observed['file']], self.array)
        self.assertEqual(observed['byte_offset'], self.raw.index(self.array))
        for index, row in enumerate(observed['rows']):
            self.assertEqual(row['source_index'], index)
            data = self.raw[row['byte_offset']:row['byte_offset']+row['byte_size']]
            self.assertEqual(data, self.row)
            self.assertEqual(hashlib.sha256(data).hexdigest(), row['sha256'])
        self.assertNotEqual(observed['rows'][0]['byte_offset'], observed['rows'][1]['byte_offset'])
        self.assertEqual(frames[1]['predictions']['configuration-1']['row_count'], 0)
        self.assertEqual(frames[2]['predictions']['configuration-1']['state'], 'missing')
        self.assertNotIn('row_count', frames[2]['predictions']['configuration-1'])
        self.assertEqual(packet['sources'][0]['full_document_rows'], 2)
        self.assertFalse(packet['association_performed'])

    def test_all_unavailable_states_remain_distinct(self):
        request = copy.deepcopy(self.request)
        request['sources'] = [{'id': state, 'state': state, 'reason': 'deliberately unavailable'}
                              for state in sorted(p.UNAVAILABLE)]
        packet = json.loads(self.files(request)['PREDICTIONS.json'])
        self.assertEqual(set(packet['summary']), set(p.UNAVAILABLE))
        for frame in packet['frames']:
            for state in p.UNAVAILABLE:
                self.assertEqual(frame['predictions'][state], {'state': state, 'reason': 'deliberately unavailable'})

    def test_duplicate_frame_or_configuration_and_unknown_fields_reject(self):
        for mutate in (lambda r:r['frames'].append(r['frames'][0]),
                       lambda r:r['sources'].append(r['sources'][0]),
                       lambda r:r.update(annotations=[]),
                       lambda r:r.pop('artifact_id'),
                       lambda r:r.update(version='0.2.0'),
                       lambda r:r.update(exposure='prospectively_blind'),
                       lambda r:r['sources'][0].update(byte_size=True),
                       lambda r:r['frames'][0].update(id='../escape')):
            request = copy.deepcopy(self.request); mutate(request)
            self.reject(lambda:p.validate_request(request), 'PREDICTIONS_REQUEST')

    def test_container_limits(self):
        for key in ('sources', 'frames'):
            request = copy.deepcopy(self.request); request[key] = []
            self.reject(lambda:p.validate_request(request), 'PREDICTIONS_LIMIT')
        with patch.object(p, 'MAX_SELECTED_BYTES', 1):
            self.reject(self.files, 'PREDICTIONS_LIMIT')
        with patch.object(p, 'MAX_SELECTED_ROWS', 1):
            self.reject(self.files, 'PREDICTIONS_LIMIT')
        with patch.object(p, 'MAX_PACKET_BYTES', 1):
            self.reject(self.files, 'PREDICTIONS_LIMIT')

    def test_label_concatenation_cannot_collide(self):
        request = copy.deepcopy(self.request)
        request['frames'][0]['id'] = 'a--b'; request['frames'][1]['id'] = 'a'
        request['sources'][0]['id'] = 'c'
        request['sources'].append({**request['sources'][0], 'id': 'b--c'})
        files = self.files(request)
        names = [v['file'] for f in json.loads(files['PREDICTIONS.json'])['frames']
                 for v in f['predictions'].values() if v['state'] == 'observed']
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(len(files), len(names)+1)

    def test_missing_source_is_invalid_not_evaluated_empty(self):
        self.source.unlink()
        with self.assertRaises(FileNotFoundError):
            self.files()

    def test_exact_parent_size_and_digest_required(self):
        self.source.write_bytes(self.raw+b' ')
        self.reject(self.files, 'SOURCE_SIZE')
        self.source.write_bytes(self.raw.replace(b'0.00', b'0.01'))
        self.reject(self.files, 'SOURCE_DIGEST')

    def test_wrong_row_sample_rejects_even_on_unselected_frame(self):
        self.request['frames'] = [self.request['frames'][-1]]
        self.source.write_bytes(self.raw.replace(b'"sample_token":"'+self.tokens[0].encode(),
                                                b'"sample_token":"'+self.tokens[2].encode()))
        self.request['sources'][0] = self.source_spec()
        self.reject(self.files, 'PREDICTIONS_FORMAT')

    def test_repeated_results_key_and_trailing_data_reject(self):
        for bad in (self.raw[:-1]+b',"results":{}}', self.raw+b'{}'):
            self.source.write_bytes(bad); self.request['sources'][0] = self.source_spec()
            self.reject(self.files, 'SOURCE_JSON')

    def test_honest_prepare_and_source_replay(self):
        request, digest = self.bind_request(); out = self.root/'out'
        result = p.prepare(request, digest, out)
        replay = p.check(request, digest, out, result['packet_sha256'])
        self.assertEqual(replay['status'], 'source_replay_matches')
        self.assertFalse(replay['independent_checker'])
        self.reject(lambda:p.prepare(request, digest, out), 'OUTPUT_EXISTS')

    def test_omit_row_rehash_or_forge_index_does_not_pass_replay(self):
        request, digest = self.bind_request(); out = self.root/'out'
        p.prepare(request, digest, out)
        original = (out/'PREDICTIONS.json').read_bytes()
        for mutate in (lambda v:v['rows'].pop(), lambda v:v['rows'][0].update(source_index=1),
                       lambda v:v.update(state='missing'), lambda v:v.update(row_count=0)):
            packet = json.loads(original); mutate(packet['frames'][0]['predictions']['configuration-1'])
            data = encoded(packet); (out/'PREDICTIONS.json').write_bytes(data)
            self.reject(lambda:p.check(request, digest, out, hashlib.sha256(data).hexdigest()), 'PREDICTIONS_PACKET')

    def test_changed_bytes_extra_file_and_symlink_fail(self):
        request, digest = self.bind_request(); out = self.root/'out'
        result = p.prepare(request, digest, out)
        check = lambda:p.check(request, digest, out, result['packet_sha256'])
        target = next((out/'frames').iterdir()); raw = target.read_bytes()
        target.write_bytes(raw+b' '); self.reject(check, 'PREDICTIONS_PACKET'); target.write_bytes(raw)
        extra = out/'frames/extra.json'; extra.write_text('[]')
        self.reject(check, 'PREDICTIONS_PACKET'); extra.unlink()
        copy_path = self.root/'copy.json'; copy_path.write_bytes(raw)
        target.unlink(); target.symlink_to(copy_path)
        self.reject(check, 'PREDICTIONS_PACKET')

    def test_output_cannot_enter_inputs_requests_or_their_symlink_aliases(self):
        request, digest = self.bind_request()
        alias = self.root/'alias'; alias.symlink_to(self.inputs, target_is_directory=True)
        for out in (self.inputs/'out', self.request_dir/'out', alias/'out', p.ROOT/'out'):
            self.reject(lambda:p.prepare(request, digest, out), 'PREDICTIONS_OUTPUT')
            self.assertFalse(out.exists())

    def test_snapshot_prevents_later_original_path_replacement(self):
        original = p.scan
        def replace_after_scan(stream, selected):
            result = original(stream, selected)
            self.source.write_bytes(b'changed after snapshot')
            return result
        with patch.object(p, 'scan', replace_after_scan):
            packet_files = self.files()
        packet = json.loads(packet_files['PREDICTIONS.json'])
        self.assertEqual(packet_files[packet['frames'][0]['predictions']['configuration-1']['file']], self.array)


if __name__ == '__main__':
    unittest.main()
