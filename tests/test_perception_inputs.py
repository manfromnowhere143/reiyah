"""Adversarial source framing, clock independence and private catalog roundtrips."""
from copy import deepcopy
from collections import Counter
from decimal import Decimal
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

from tools.perception_decision.contract import Invalid, encoded
from tools.perception_inputs import catalog, clock, sensors, source_io
from tools.perception_inputs import __main__ as ingest_cli

ROOT = Path(__file__).resolve().parents[1]


def tables():
    scenes, samples = [], []
    for s in range(2):
        scenes.append({'token': f's{s}', 'name': f'scene-{s}', 'nbr_samples': 5,
                       'first_sample_token': f'f{s}-0', 'last_sample_token': f'f{s}-4'})
        for i in range(5):
            samples.append({'token': f'f{s}-{i}', 'scene_token': f's{s}', 'timestamp': (s*10+i+1)*1_000_000,
                            'prev': f'f{s}-{i-1}' if i else '', 'next': f'f{s}-{i+1}' if i < 4 else ''})
    return {'scene.json': scenes, 'sample.json': samples}


def meta_bytes(values, extra=()):
    result = io.BytesIO()
    with tarfile.open(fileobj=result, mode='w:gz') as archive:
        for name, rows in values.items():
            data = encoded(rows)
            info = tarfile.TarInfo('v1.0-trainval/' + name)
            info.size = len(data)
            archive.addfile(info, io.BytesIO(data))
        for info, data in extra:
            archive.addfile(info, io.BytesIO(data))
    return result.getvalue()


def sensor_tables():
    result = {'sensor.json': [{'token': 'sensor-l', 'channel': 'LIDAR_TOP', 'modality': 'lidar'},
                              {'token': 'sensor-c', 'channel': 'CAM_FRONT', 'modality': 'camera'}],
              'calibrated_sensor.json': [{'token': 'cal-l', 'sensor_token': 'sensor-l'},
                                         {'token': 'cal-c', 'sensor_token': 'sensor-c'}],
              'sample_data.json': [], 'ego_pose.json': []}
    for row in tables()['sample.json']:
        sample, time = row['token'], row['timestamp']
        result['ego_pose.json'].append({'token': 'pose-'+sample, 'translation': [1, 2, 0], 'timestamp': time})
        for channel in ['l', 'c']:
            result['sample_data.json'].append({'token': 'data-'+channel+sample, 'is_key_frame': True,
                                               'sample_token': sample, 'calibrated_sensor_token': 'cal-'+channel,
                                               'ego_pose_token': 'pose-'+sample, 'timestamp': time,
                                               'filename': 'samples/'+channel+'/'+sample+'.bin'})
    return result


def prediction(sample, score=0.7):
    return {'sample_token': sample, 'detection_name': 'car', 'detection_score': score,
            'translation': [0.125, 0, 0], 'velocity': [float('nan'), float('nan')],
            'attribute_name': 'synthetic \u03bb'}


def prediction_bytes(results):
    # Historical JSON may carry nonfinite unused velocity. Required operands reject it.
    return json.dumps({'meta': {k: False for k in sorted(catalog.META_FIELDS)}, 'results': results},
                      ensure_ascii=False, allow_nan=True).encode('utf-8')


def source(path, data):
    path.write_bytes(data)
    return {'state': 'observed', 'path': str(path), 'byte_size': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def exposure():
    return [{'case_id': 'prior-case', 'candidate_sample_timestamp_us': 3_000_000,
             'evidence': [{'evidence_id': 'image', 'state': 'available', 'sensor_timestamp_us': 3_001_000,
                           'asset_sha256': 'a'*64},
                          {'evidence_id': 'boundary', 'state': 'scene_boundary', 'asset_sha256': None}]}]


def request(folder):
    return {'artifact_id': 'reiyah.perception-inputs.request', 'version': '0.1.0', 'sources': {
        'metadata': source(folder/'meta.tgz', meta_bytes({**tables(), **sensor_tables()})),
        'splits': source(folder/'splits.py', b"val = ['scene-0', 'scene-1']\n"),
        'base': source(folder/'base.json', prediction_bytes({'f0-0': [], 'f0-2': [prediction('f0-2')]})),
        'camera': source(folder/'camera.json', prediction_bytes({})),
        'exposures': source(folder/'exposures.json', encoded(exposure()))}}


class PerceptionInputTests(unittest.TestCase):
    def rejected(self, function, code):
        with self.assertRaises(Invalid) as raised:
            function()
        self.assertEqual(raised.exception.code, code)

    def test_verified_snapshot_is_not_a_second_read_of_mutable_input(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder)/'source'
            spec = source(p, b'correct original')
            with source_io.snapshot(spec) as stream:
                p.write_bytes(b'mutated afterward')
                self.assertEqual(stream.read(), b'correct original')
            self.assertTrue(stream.closed)

    def test_identity_is_checked_before_source_can_be_consumed(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder)/'source'
            spec = source(p, b'{invalid JSON')
            def consume(s):
                with source_io.snapshot(s):
                    self.fail('A mismatched source was exposed to the parser')
            changed = dict(spec, sha256='0'*64)
            self.rejected(lambda: consume(changed), 'SOURCE_DIGEST')
            self.rejected(lambda: consume(dict(spec, byte_size=1)), 'SOURCE_SIZE')
            self.rejected(lambda: consume(dict(spec, byte_size=100)), 'SOURCE_SIZE')
            self.rejected(lambda: consume(dict(spec, byte_size=True)), 'SOURCE_IDENTITY')
            self.rejected(lambda: consume(dict(spec, byte_size=source_io.MAX_SOURCE_BYTES+1)), 'SOURCE_IDENTITY')

    def test_streamed_spans_preserve_utf8_and_chunk_boundary_numbers(self):
        data = prediction_bytes({'f0-0': [prediction('f0-0', 0.3123456789)], 'f0-1': []})
        digest = hashlib.sha256(data).hexdigest()
        for chunk in (1, 2, 7, 64, 65536):
            with self.subTest(chunk=chunk):
                entries, header = catalog.prediction_index(io.BytesIO(data), digest, {'f0-0', 'f0-1'}, chunk)
                span = entries['f0-0']
                raw = data[span['byte_offset']:span['byte_offset']+span['byte_size']]
                values = source_io.document(raw)
                self.assertEqual(values[0]['detection_score'], Decimal('0.3123456789'))
                self.assertEqual(values[0]['attribute_name'], 'synthetic \u03bb')
                self.assertEqual(hashlib.sha256(raw).hexdigest(), span['sha256'])
                self.assertEqual(entries['f0-1']['row_count'], 0)
                self.assertTrue(values[0]['velocity'][0].is_nan())

    def test_streamed_object_rejects_duplicate_trailing_and_truncated_content(self):
        data = prediction_bytes({'f0-0': []})
        mutations = [data[:-1], data+b' trailing', data+b'{}', data.replace(b'"f0-0": []', b'"f0-0": [], "f0-0": []'),
                     data.replace(b'"results": {', b'"meta": {}, "results": {'),
                     data.replace(b'"f0-0": []}', b'"f0-0": [],}'), data.replace(b'"f0-0": []', b'"f0-0": [}'),
                     data.replace(b'"f0-0": []', b'"f0-0": [] "bad": []'), data+b'\xa0']
        for altered in mutations:
            self.rejected(lambda: catalog.prediction_index(io.BytesIO(altered), 'a'*64, {'f0-0'}, 3), 'SOURCE_JSON')

    def test_nested_duplicate_and_oversized_values_are_rejected(self):
        reader = source_io.JSONStream(io.BytesIO(b'{"a":1,"a":2}'), chunk_bytes=2)
        self.rejected(lambda: reader.value(dict), 'SOURCE_JSON')
        reader = source_io.JSONStream(io.BytesIO(b'['+b' '*100+b']'), chunk_bytes=8, value_limit=32)
        self.rejected(lambda: reader.value(list), 'SOURCE_VALUE_SIZE')
        self.rejected(lambda: source_io.document(b'{"x":1e999999}'), 'SOURCE_NUMBER')
        self.rejected(lambda: source_io.document(b'{"x":'+b'9'*100+b'}'), 'SOURCE_NUMBER')

    def test_required_prediction_numbers_classes_and_samples_are_checked(self):
        for mutation, code in [
            (lambda p: p.update(sample_token='other'), 'PREDICTION_SAMPLE'),
            (lambda p: p.update(detection_name='vehicle.car'), 'PREDICTION_CLASS'),
            (lambda p: p.update(detection_score=float('nan')), 'ADAPTER_NUMBER'),
            (lambda p: p.update(detection_score=1.01), 'PREDICTION_SCORE'),
            (lambda p: p.update(translation=[float('inf'), 0, 0]), 'ADAPTER_NUMBER'),
            (lambda p: p.update(translation=[0, 0]), 'PREDICTION_COORDINATES')]:
            row = prediction('f0-0');mutation(row);data = prediction_bytes({'f0-0': [row]})
            self.rejected(lambda: catalog.prediction_index(io.BytesIO(data), 'a'*64, {'f0-0'}), code)
        too_many = prediction_bytes({'f0-0': [prediction('f0-0')]*513})
        self.rejected(lambda: catalog.prediction_index(io.BytesIO(too_many), 'a'*64, {'f0-0'}), 'PREDICTION_FRAME')
        self.rejected(lambda: catalog.prediction_index(io.BytesIO(prediction_bytes({'unknown': []})), 'a'*64, {'f0-0'}), 'PREDICTION_POPULATION')

    def test_complete_catalog_preserves_missing_empty_and_parent_clock(self):
        with tempfile.TemporaryDirectory() as folder:
            req = request(Path(folder));result = catalog.build(req)
            rows = {r['sample_token']: r for r in result['anchors']}
            self.assertEqual(result['summary']['clock_anchor_count'], 10)
            self.assertEqual(result['summary']['context_anchor_count'], 2)
            self.assertEqual(result['summary']['eligible_anchor_count'], 1)
            self.assertEqual(rows['f0-0']['base']['row_count'], 0)
            self.assertEqual(rows['f0-1']['base']['state'], 'missing')
            self.assertNotIn('row_count', rows['f0-1']['base'])
            self.assertEqual(rows['f0-2']['eligibility'], 'excluded_prior_exposure')
            self.assertEqual(rows['f1-2']['eligibility'], 'eligible_under_declared_rule')
            self.assertEqual(result['summary']['exposure_history']['scene_boundary_placeholders'], 1)
            self.assertIsNone(result['summary']['selected_cohort'])
            self.assertEqual(result['summary']['prediction_comparison'], 'not_performed')
            self.assertEqual(rows['f0-2']['nominal_ego_xy']['state'], 'observed')
            self.assertEqual(rows['f0-2']['keyframe_metadata']['CAM_BACK']['metadata_state'], 'missing')
            self.assertEqual(rows['f0-2']['keyframe_metadata']['CAM_FRONT']['payload_validity'], 'not_checked')

    def test_prediction_changes_cannot_change_population_or_eligibility(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder);req = request(directory);first = catalog.build(req)
            every = {row['sample_token']: [prediction(row['sample_token'], score=0.01)] for row in first['anchors']}
            req['sources']['base'] = source(directory/'all.json', prediction_bytes(every))
            req['sources']['camera'] = {'state': 'abstained', 'reason': 'No prediction source'}
            second = catalog.build(req)
            self.assertEqual(first['clock_and_exclusion_sha256'], second['clock_and_exclusion_sha256'])
            self.assertEqual(first['summary']['eligible_anchor_count'], second['summary']['eligible_anchor_count'])
            self.assertEqual(second['summary']['prediction_availability']['camera'], {'abstained': 10})
            self.assertEqual([r['sample_token'] for r in first['anchors']], [r['sample_token'] for r in second['anchors']])

    def test_unknown_exposure_history_does_not_mean_unexposed(self):
        with tempfile.TemporaryDirectory() as folder:
            req = request(Path(folder));req['sources']['exposures'] = {'state': 'unknown', 'reason': 'Unlocated historical records'}
            result = catalog.build(req)
            self.assertIsNone(result['summary']['eligible_anchor_count'])
            self.assertIsNone(result['summary']['eligible_scene_count'])
            self.assertEqual(Counter(r['eligibility'] for r in result['anchors']),
                             {'outside_scene_context': 8, 'exposure_history_unavailable': 2})

    def test_exposure_overlap_is_closed_and_scene_local(self):
        anchors = [{'scene_token': 's0', 'has_declared_scene_context': True, 'context_window_us': [3, 7]},
                   {'scene_token': 's1', 'has_declared_scene_context': True, 'context_window_us': [3, 7]}]
        clock.apply_exclusions(anchors, {'s0': [(7, 9)]})
        self.assertEqual([r['eligibility'] for r in anchors], ['excluded_prior_exposure', 'eligible_under_declared_rule'])
        clock.apply_exclusions(anchors, {'s0': [(8, 9)]})
        self.assertEqual(anchors[0]['eligibility'], 'eligible_under_declared_rule')

    def test_missing_exposed_time_cannot_be_disguised_as_boundary(self):
        anchors = clock.population(tables(), ['scene-0', 'scene-1'])
        records = exposure();records[0]['evidence'][0].pop('sensor_timestamp_us')
        self.rejected(lambda: clock.exposure_windows(io.BytesIO(encoded(records)), anchors), 'EXPOSURE_INCOMPLETE')
        records = exposure();records[0]['evidence'][1]['relative_asset_path'] = 'exposed.png'
        self.rejected(lambda: clock.exposure_windows(io.BytesIO(encoded(records)), anchors), 'EXPOSURE_INCOMPLETE')
        records = exposure();records[0]['evidence'][0]['sensor_timestamp_us'] = None
        self.rejected(lambda: clock.exposure_windows(io.BytesIO(encoded(records)), anchors), 'CLOCK_TIME')

    def test_exposure_identity_join_and_hull(self):
        anchors = clock.population(tables(), ['scene-0', 'scene-1'])
        records = exposure();records[0]['evidence'][0]['sensor_timestamp_us'] = 8_000_000
        windows, _ = clock.exposure_windows(io.BytesIO(encoded(records)), anchors)
        self.assertEqual(windows['s0'], [(1_000_000, 8_000_000)])
        self.rejected(lambda: clock.exposure_windows(io.BytesIO(encoded(records*2)), anchors), 'EXPOSURE_RECORD')
        ambiguous = anchors+[dict(anchors[2], sample_token='alias')]
        self.rejected(lambda: clock.exposure_windows(io.BytesIO(encoded(records)), ambiguous), 'EXPOSURE_JOIN')

    def test_signed_historical_evidence_ids_are_not_dataset_tokens(self):
        anchors = clock.population(tables(), ['scene-0', 'scene-1'])
        records = exposure()
        records[0]['evidence'][0]['evidence_id'] = '-1:CAM_FRONT'
        records[0]['evidence'][1]['evidence_id'] = '+0:CAM_FRONT'
        _, counts = clock.exposure_windows(io.BytesIO(encoded(records)), anchors)
        self.assertEqual(counts['exposed_assets'], 1)
        records[0]['evidence'][0]['evidence_id'] += '\n'
        self.rejected(lambda: clock.exposure_windows(io.BytesIO(encoded(records)), anchors), 'EXPOSURE_RECORD')

    def test_broken_clock_and_split_fail_without_deleting_samples(self):
        for change, code in [
            (lambda t: t['sample.json'][2].update(next=''), 'CLOCK_CHAIN'),
            (lambda t: t['sample.json'][2].update(timestamp=True), 'CLOCK_TIME'),
            (lambda t: t['sample.json'].append(deepcopy(t['sample.json'][0])), 'CLOCK_IDENTITY'),
            (lambda t: t['scene.json'][0].update(nbr_samples=6), 'CLOCK_CHAIN'),
            (lambda t: t['sample.json'][0].update(scene_token='unknown'), 'CLOCK_IDENTITY')]:
            values = tables();change(values)
            self.rejected(lambda: clock.population(values, ['scene-0', 'scene-1']), code)
        self.rejected(lambda: clock.population(tables(), ['missing-scene']), 'CLOCK_SPLIT')
        for code in (b"val = list(['scene-0'])", b"val=['a'];val=['b']", b"val=['a','a']", b"val=[None]"):
            self.rejected(lambda: clock.validation_names(io.BytesIO(code)), 'SPLIT_ASSIGNMENT')

    def test_metadata_rejects_unsafe_linked_duplicate_and_missing_tables(self):
        for name, kind in [('../escape', tarfile.REGTYPE), ('link', tarfile.SYMTYPE),
                           ('v1.0-trainval/scene.json', tarfile.REGTYPE), ('other/scene.json', tarfile.REGTYPE)]:
            info = tarfile.TarInfo(name);info.type = kind
            data = meta_bytes(tables(), [(info, b'')])
            self.rejected(lambda: clock.metadata_tables(io.BytesIO(data)), 'METADATA_ARCHIVE')
        self.rejected(lambda: clock.metadata_tables(io.BytesIO(meta_bytes({'scene.json': tables()['scene.json']}))), 'METADATA_TABLE')

    def test_frame_extraction_rechecks_parent_and_span(self):
        with tempfile.TemporaryDirectory() as folder:
            req = request(Path(folder));result = catalog.build(req);span = result['anchors'][2]['base']
            values = catalog.extract_frame(req['sources']['base'], 'f0-2', span)
            self.assertEqual(values[0]['translation'][0], Decimal('0.125'))
            self.rejected(lambda: catalog.extract_frame(req['sources']['base'], 'wrong', span), 'PREDICTION_SAMPLE')
            self.rejected(lambda: catalog.extract_frame(req['sources']['base'], 'f0-2', dict(span, byte_offset=span['byte_offset']+1)), 'FRAME_DIGEST')
            self.rejected(lambda: catalog.extract_frame(req['sources']['base'], 'f0-2', dict(span, source_sha256='0'*64)), 'FRAME_BINDING')
            self.rejected(lambda: catalog.extract_frame(req['sources']['base'], 'f0-2', dict(span, row_count=0)), 'FRAME_BINDING')

    def test_extraction_rejects_unavailable_or_malformed_source_with_typed_diagnostic(self):
        for source in [None, {'state': 'missing', 'reason': 'Unavailable source'},
                       {'state': 'observed', 'path': None, 'byte_size': 5, 'sha256': 'a'*64}]:
            self.rejected(lambda: catalog.extract_frame(source, 'f0-0', {}), 'FRAME_BINDING')

    def test_code_change_during_build_prevents_catalog_publication(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder);req = request(directory);p = directory/'request.json';p.write_bytes(encoded(req))
            target = directory/'catalog.json';digest = hashlib.sha256(p.read_bytes()).hexdigest()
            original_read = Path.read_bytes
            after_build = False
            def changed_read(path):
                data = original_read(path)
                return data+b'changed' if after_build and path.parent.name == 'perception_inputs' else data
            def altered_build(_):
                nonlocal after_build
                after_build = True
                return {}
            errors = io.BytesIO()
            with patch.object(Path, 'read_bytes', changed_read), patch.object(ingest_cli, 'build', altered_build), \
                    patch.object(ingest_cli.sys, 'stderr', SimpleNamespace(buffer=errors)):
                code = ingest_cli.main(['--request', str(p), '--request-sha256', digest, '--output', str(target)])
            self.assertEqual(code, 2)
            self.assertEqual(json.loads(errors.getvalue())['code'], 'SOURCE_CODE_CHANGED')
            self.assertFalse(target.exists())

    def test_cli_publishes_only_complete_output_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder);req = request(directory);input_path = directory/'request.json';target = directory/'catalog.json'
            input_path.write_bytes(encoded(req));digest = hashlib.sha256(input_path.read_bytes()).hexdigest()
            argv = [sys.executable, '-B', '-m', 'tools.perception_inputs', '--request', str(input_path),
                    '--request-sha256', digest, '--output', str(target)]
            result = subprocess.run(argv, cwd=ROOT, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            before = target.read_bytes()
            self.assertEqual(hashlib.sha256(before).hexdigest(), json.loads(result.stdout)['sha256'])
            self.assertEqual(json.loads(before)['request_file_sha256'], digest)
            repeated = subprocess.run(argv, cwd=ROOT, capture_output=True)
            self.assertEqual(repeated.returncode, 2)
            self.assertEqual(target.read_bytes(), before)
            broken = directory/'bad.json'
            camera = Path(req['sources']['camera']['path']);camera.write_bytes(camera.read_bytes()[:-1])
            failed = subprocess.run(argv[:-1]+[str(broken)], cwd=ROOT, capture_output=True)
            self.assertEqual(failed.returncode, 2)
            self.assertFalse(broken.exists())
            self.assertEqual(json.loads(failed.stderr)['code'], 'SOURCE_SIZE')

    def test_request_is_closed_and_required_sources_cannot_be_missing(self):
        with tempfile.TemporaryDirectory() as folder:
            original = request(Path(folder))
            for mutation, code in [(lambda r: r.update(extra=True), 'INGEST_REQUEST'),
                                   (lambda r: r['sources']['metadata'].update(sha256='a'*64+'\n'), 'SOURCE_IDENTITY'),
                                   (lambda r: r['sources']['base'].update(byte_size=True), 'SOURCE_IDENTITY'),
                                   (lambda r: r['sources'].update(metadata={'state':'missing','reason':'x'}), 'SOURCE_STATE'),
                                   (lambda r: r['sources'].update(camera={'state':'missing','reason':'x','value':[]}), 'SOURCE_STATE')]:
                req = deepcopy(original);mutation(req)
                self.rejected(lambda: catalog.validate_request(req), code)

    def test_streamed_metadata_array_rejects_incomplete_or_excess_rows(self):
        for data in (b'[{"x":1},]', b'[{"x":1}', b'[true]', b'[{}]{}'):
            def consume():
                reader = source_io.JSONStream(io.BytesIO(data), chunk_bytes=1)
                list(reader.objects(10));reader.finish()
            self.rejected(consume, 'SOURCE_JSON')
        reader = source_io.JSONStream(io.BytesIO(b'[{},{}]'))
        self.rejected(lambda: list(reader.objects(1)), 'SOURCE_VALUE_SIZE')

    def sensor_join(self, data):
        anchors = clock.population(tables(), ['scene-0', 'scene-1'])
        files = {name: io.BytesIO(encoded(rows)) for name, rows in data.items()}
        return anchors, sensors.join(files, anchors)

    def test_missing_keyframe_or_pose_preserves_the_clock(self):
        data = sensor_tables();data['sample_data.json'] = [r for r in data['sample_data.json'] if r['sample_token'] != 'f0-2']
        anchors, summary = self.sensor_join(data)
        self.assertEqual(len(anchors), 10)
        self.assertEqual(anchors[2]['nominal_ego_xy']['state'], 'missing')
        self.assertIsNone(anchors[2]['keyframe_metadata']['LIDAR_TOP']['capture_delta_us'])
        data = sensor_tables();data['ego_pose.json'] = data['ego_pose.json'][1:]
        anchors, summary = self.sensor_join(data)
        self.assertEqual(summary['anchor_ego_states']['missing'], 1)
        self.assertEqual(anchors[0]['nominal_ego_xy']['state'], 'missing')

    def test_pose_time_mismatch_never_silently_interpolates(self):
        data = sensor_tables();data['ego_pose.json'][0]['timestamp'] += 1
        anchors, summary = self.sensor_join(data)
        self.assertEqual(anchors[0]['nominal_ego_xy']['state'], 'unknown')
        self.assertNotIn('value', anchors[0]['nominal_ego_xy'])
        self.assertEqual(summary['anchor_ego_states']['unknown'], 1)

    def test_sensor_join_rejects_ambiguous_and_malformed_relations(self):
        for mutation, code in [
            (lambda d: d['sample_data.json'].append(dict(d['sample_data.json'][0], token='other')), 'SENSOR_METADATA'),
            (lambda d: d['calibrated_sensor.json'][0].update(sensor_token='absent'), 'SENSOR_METADATA'),
            (lambda d: d['sensor.json'][0].update(modality='camera'), 'SENSOR_METADATA'),
            (lambda d: d['sample_data.json'][0].update(filename='../escape.bin'), 'SENSOR_METADATA'),
            (lambda d: d['sample_data.json'][0].update(is_key_frame=1), 'SENSOR_METADATA'),
            (lambda d: d['sample_data.json'][0].update(sample_token=[]), 'CLOCK_IDENTITY'),
            (lambda d: d['ego_pose.json'].append(deepcopy(d['ego_pose.json'][0])), 'SENSOR_METADATA'),
            (lambda d: d['ego_pose.json'][0].update(translation=[True, 2, 0]), 'ADAPTER_NUMBER')]:
            data = sensor_tables();mutation(data)
            self.rejected(lambda: self.sensor_join(data), code)


if __name__ == '__main__':
    unittest.main()
