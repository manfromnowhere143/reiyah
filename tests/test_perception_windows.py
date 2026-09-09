"""Raw custody, complete decode, clock linkage, context boundaries and no substitution."""
from copy import deepcopy
import hashlib
import io
import json
import os
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from tools.perception_decision.contract import Invalid, encoded
from tools.perception_inputs import clock, sensors
from tools.perception_windows import payloads, timeline
from tools.perception_windows import __main__ as windows
from tests.test_perception_inputs import meta_bytes, source, tables


def scene_fixture():
    result = tables()
    result.update({'sensor.json': [], 'calibrated_sensor.json': [], 'sample_data.json': []})
    for channel in sensors.CHANNELS:
        camera = channel != 'LIDAR_TOP'
        result['sensor.json'].append({'token': 'sensor-'+channel, 'channel': channel, 'modality': 'camera' if camera else 'lidar'})
        result['calibrated_sensor.json'].append({'token': 'cal-'+channel, 'sensor_token': 'sensor-'+channel})
        for s in range(2):
            for i in range(5):
                sample = f'f{s}-{i}'
                result['sample_data.json'].append({'token': f'{channel}-{sample}', 'sample_token': sample,
                    'calibrated_sensor_token': 'cal-'+channel, 'ego_pose_token': 'pose-'+sample,
                    'is_key_frame': True, 'timestamp': (s*10+i+1)*1_000_000,
                    'width': 4 if camera else 0, 'height': 3 if camera else 0, 'fileformat': 'jpg' if camera else 'pcd',
                    'filename': 'samples/'+channel+'/'+sample+('.jpg' if camera else '.pcd.bin'),
                    'prev': f'{channel}-f{s}-{i-1}' if i else '', 'next': f'{channel}-f{s}-{i+1}' if i < 4 else ''})
    return result


def streams(values):
    return {k: io.BytesIO(encoded(v)) for k,v in values.items()}


def catalog(values):
    anchors = clock.population(values, ['scene-0', 'scene-1'])
    rows = {r['token']:r for r in values['sample_data.json']}
    for a in anchors:
        a['keyframe_metadata'] = {}
        for c in sensors.CHANNELS:
            r = rows[c+'-'+a['sample_token']]
            a['keyframe_metadata'][c] = {'metadata_state': 'present', 'sample_data_token': r['token'],
                'capture_timestamp_us': r['timestamp'], **{k:r[k] for k in ('filename','calibrated_sensor_token','ego_pose_token')}}
    return {'artifact_id': 'reiyah.perception-inputs.catalog', 'version': '0.1.0', 'anchors': anchors}


def selected():
    return [{'anchor_id': 'one', 'sample_token': 'f0-2'}, {'anchor_id': 'two', 'sample_token': 'f1-2'}]


def identity_file(path, data):
    result = source(path, data)
    del result['state']
    return result


def make_request(root, values=None):
    values = scene_fixture() if values is None else values
    meta = identity_file(root/'metadata.tgz', meta_bytes(values))
    cat = catalog(values); cat['sources'] = {'metadata': dict(meta)}
    inventory = {'artifact_id': 'reiyah.perception-windows.assets', 'version': '0.1.0', 'assets': []}
    return {'artifact_id': 'reiyah.perception-windows.request', 'version': '0.1.0',
        'catalog': identity_file(root/'catalog.json', encoded(cat)), 'metadata': meta,
        'inventory': identity_file(root/'inventory.json', encoded(inventory)),
        'raw_root': str(root/'raw'), 'anchors': selected()}


def jpeg():
    from PIL import Image
    out = io.BytesIO()
    Image.new('RGB', (4,3), color=(40,60,80)).save(out, format='JPEG')
    return out.getvalue()


class WindowTests(unittest.TestCase):
    def rejected(self, call, code):
        with self.assertRaises(Invalid) as caught:
            call()
        self.assertEqual(caught.exception.code, code)

    def test_full_clock_windows_preserve_both_endpoints_and_all_channels(self):
        values = scene_fixture()
        actual, chosen = timeline.clock_selection(streams(values), catalog(values), selected())
        groups = timeline.sensor_rows(streams(values), actual)
        result = timeline.windows(groups, chosen)
        self.assertEqual([r['anchor_id'] for r in result], ['one','two'])
        for w in result:
            self.assertEqual(set(w['channels']), set(sensors.CHANNELS))
            for c in w['channels'].values():
                self.assertEqual(c['capture_count'], 5)
                self.assertEqual(c['start_boundary']['state'], 'bracketed')
                self.assertEqual(c['end_boundary']['state'], 'bracketed')
                self.assertEqual(c['timing']['max_inter_capture_gap_us'], 1_000_000)
                self.assertEqual(c['continuous_temporal_coverage'], 'not_established')

    def test_non_keyframe_capture_is_required_and_outside_neighbor_is_not(self):
        v = scene_fixture()
        rows = v['sample_data.json']
        right = next(r for r in rows if r['token'] == 'CAM_FRONT-f0-2')
        left = next(r for r in rows if r['token'] == right['prev'])
        extra = {**right, 'token': 'new-sweep', 'timestamp': 2_500_000, 'is_key_frame': False,
                 'filename': 'sweeps/CAM_FRONT/middle.jpg', 'prev': left['token'], 'next': right['token']}
        left['next'] = right['prev'] = extra['token']; rows.append(extra)
        actual, chosen = timeline.clock_selection(streams(v), catalog(v), selected())
        result = timeline.windows(timeline.sensor_rows(streams(v), actual), chosen)
        self.assertEqual(result[0]['channels']['CAM_FRONT']['capture_count'], 6)
        self.assertEqual(result[0]['channels']['CAM_FRONT']['captures'][2]['sample_data_token'], 'new-sweep')
        # A scene-start request keeps the negative context; it is never shortened.
        actual, chosen = timeline.clock_selection(streams(v), catalog(v), [{'anchor_id':'start','sample_token':'f0-0'}])
        result = timeline.windows(timeline.sensor_rows(streams(v), actual), chosen)[0]
        self.assertEqual(result['context_window_us'], [-1_000_000,3_000_000])
        self.assertFalse(result['has_declared_scene_context'])
        self.assertEqual(result['channels']['CAM_FRONT']['start_boundary']['state'], 'recorded_stream_endpoint')
        self.assertFalse(any(r['capture_timestamp_us'] > 3_000_000 for r in result['channels']['CAM_FRONT']['captures']))

    def test_broken_links_repeated_times_and_omitted_sweeps_reject(self):
        for defect in ('link','time','omission','cross_scene'):
            v = scene_fixture(); a = clock.population(v, ['scene-0','scene-1'])
            if defect == 'link': v['sample_data.json'][1]['prev'] = ''
            if defect == 'time': v['sample_data.json'][1]['timestamp'] = v['sample_data.json'][0]['timestamp']
            if defect == 'omission': del v['sample_data.json'][1]
            if defect == 'cross_scene': v['sample_data.json'][0]['prev'] = v['sample_data.json'][5]['token']
            with self.subTest(defect=defect):
                self.rejected(lambda: timeline.sensor_rows(streams(v), a), 'WINDOW_CHAIN')

    def test_duplicate_capture_path_bad_dimensions_and_wrong_channel_reject(self):
        for defect in ('token','path','dimensions','channel'):
            v = scene_fixture(); a = clock.population(v, ['scene-0','scene-1'])
            if defect == 'token': v['sample_data.json'].append(v['sample_data.json'][0])
            if defect == 'path': v['sample_data.json'][1]['filename'] = v['sample_data.json'][0]['filename']
            if defect == 'dimensions': v['sample_data.json'][0]['width'] = True
            if defect == 'channel': v['sample_data.json'][0]['filename'] = 'samples/CAM_FRONT/f0-0.pcd.bin'
            with self.subTest(defect=defect):
                self.rejected(lambda: timeline.sensor_rows(streams(v), a), 'WINDOW_METADATA')

    def test_clock_population_and_keyframe_substitution_reject(self):
        for defect in ('clock','population','keyframe'):
            v = scene_fixture(); cat = catalog(v)
            if defect == 'clock': cat['anchors'][2]['anchor_timestamp_us'] += 1
            if defect == 'population': del cat['anchors'][1]
            if defect == 'keyframe': cat['anchors'][2]['keyframe_metadata']['LIDAR_TOP']['capture_timestamp_us'] += 1
            def run():
                actual, chosen = timeline.clock_selection(streams(v),cat,selected())
                return timeline.windows(timeline.sensor_rows(streams(v),actual),chosen)
            with self.subTest(defect=defect): self.rejected(run,'WINDOW_CATALOG')

    def test_unknown_duplicate_or_empty_selection_rejects(self):
        v = scene_fixture()
        for selection in ([], selected()*2, [{'anchor_id':'x','sample_token':'unknown'}],
                          [{'anchor_id':'x','sample_token':'f0-2'}, {'anchor_id':'y','sample_token':'f0-2'}]):
            self.rejected(lambda: timeline.clock_selection(streams(v),catalog(v),selection),'WINDOW_SELECTION')

    def test_malformed_clock_states_and_capture_identity_fail_with_diagnostics(self):
        v = scene_fixture()
        for field,value in (('context_window_us',[True,5]), ('has_declared_scene_context',1), ('keyframe_metadata',[])):
            cat = catalog(v); cat['anchors'][2][field] = value
            self.rejected(lambda: timeline.clock_selection(streams(v),cat,selected()), 'WINDOW_CATALOG')
        v['sample_data.json'][0]['sample_token'] = []
        self.rejected(lambda: timeline.sensor_rows(streams(v),clock.population(v,['scene-0'])), 'WINDOW_METADATA')

    def test_resource_limit_rejects_without_returning_partial_timeline(self):
        v = scene_fixture()
        with patch.object(timeline,'MAX_SELECTED_ROWS',1):
            self.rejected(lambda: timeline.sensor_rows(streams(v),clock.population(v,['scene-0'])), 'WINDOW_METADATA')

    def test_absent_channel_stays_empty_without_borrowing(self):
        v = scene_fixture(); cat = catalog(v)
        v['sample_data.json'] = [r for r in v['sample_data.json'] if r['calibrated_sensor_token'] != 'cal-CAM_FRONT']
        for a in cat['anchors']: a['keyframe_metadata']['CAM_FRONT'] = {'metadata_state':'missing'}
        actual, chosen = timeline.clock_selection(streams(v),cat,selected())
        result = timeline.windows(timeline.sensor_rows(streams(v),actual),chosen)
        c = result[0]['channels']['CAM_FRONT']
        self.assertEqual(c['capture_count'],0)
        self.assertIsNone(c['timing']['capture_span_us'])
        self.assertEqual(c['start_boundary']['state'],'no_recorded_stream')

    def test_inventory_is_closed_bounded_and_preserves_unavailable(self):
        def inv(rows): return {'artifact_id':'reiyah.perception-windows.assets','version':'0.1.0','assets':rows}
        row = {'filename':'samples/LIDAR_TOP/x.pcd.bin','state':'retained','byte_size':20,'sha256':'a'*64}
        for rows in ([row,row], [{**row,'byte_size':True}], [{**row,'extra':0}], [{**row,'sha256':None}]):
            self.rejected(lambda: payloads.inventory(inv(rows)), 'WINDOW_INVENTORY')
        result = payloads.inventory(inv([{'filename':'x','state':'unavailable','reason':'not retained'}]))
        self.assertEqual(result['x']['state'],'unavailable')
        for path in ('../x','/x','x//y','x/./y','x\\y','x\0y'):
            self.rejected(lambda: payloads.inventory(inv([{**row,'filename':path}])), 'WINDOW_PATH')

    def test_lidar_stride_empty_and_each_nonfinite_field_reject(self):
        self.assertEqual(payloads.decode_points(struct.pack('<5f',0,1,2,3,4))['point_count'],1)
        for data in (b'',b'x'*19,b'x'*21):
            self.rejected(lambda:payloads.decode_points(data),'WINDOW_LIDAR_LAYOUT')
        for i in range(5):
            vals=[0.0]*5; vals[i]=float('nan') if i%2 else float('inf')
            self.rejected(lambda:payloads.decode_points(struct.pack('<5f',*vals)),'WINDOW_LIDAR_NONFINITE')

    def test_jpeg_full_decode_rejects_header_truncation_and_metadata_shape(self):
        data=jpeg()
        self.assertTrue(payloads.decode_image(data,4,3)['full_pixel_decode'])
        self.rejected(lambda:payloads.decode_image(data[:-2],4,3),'WINDOW_JPEG_ENVELOPE')
        self.rejected(lambda:payloads.decode_image(data[:100]+b'\xff\xd9',4,3),'WINDOW_IMAGE_DECODE')
        self.rejected(lambda:payloads.decode_image(data,5,3),'WINDOW_IMAGE_SHAPE')
        from PIL import ImageFile
        with patch.object(ImageFile,'LOAD_TRUNCATED_IMAGES',True):
            self.rejected(lambda:payloads.decode_image(data,4,3),'WINDOW_DECODER_CONFIGURATION')

    def test_payload_identity_missingness_mutation_and_symlinks(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name); (root/'sub').mkdir(); data=struct.pack('<5f',1,2,3,4,5)
            p=root/'sub/x';p.write_bytes(data)
            spec={'filename':'sub/x','state':'retained','byte_size':20,'sha256':hashlib.sha256(data).hexdigest()}
            record={'filename':'sub/x'}
            fd=os.open(root,os.O_RDONLY|os.O_DIRECTORY)
            try:
                self.assertEqual(payloads.inspect(fd,record,{},'LIDAR_TOP')['custody_state'],'not_listed')
                good=payloads.inspect(fd,record,{'sub/x':spec},'LIDAR_TOP')
                self.assertEqual(good['payload_state'],'decoded')
                p.write_bytes(data[:-1]);bad=payloads.inspect(fd,record,{'sub/x':spec},'LIDAR_TOP')
                self.assertEqual(bad['diagnostic'],'WINDOW_ASSET_SIZE')
                p.write_bytes(b'x'*20);bad=payloads.inspect(fd,record,{'sub/x':spec},'LIDAR_TOP')
                self.assertEqual(bad['diagnostic'],'WINDOW_ASSET_DIGEST')
                p.unlink();self.assertEqual(payloads.inspect(fd,record,{'sub/x':spec},'LIDAR_TOP')['custody_state'],'missing')
                (root/'outside').write_bytes(data);p.symlink_to(root/'outside')
                self.assertEqual(payloads.inspect(fd,record,{'sub/x':spec},'LIDAR_TOP')['custody_state'],'invalid')
                p.unlink();(root/'sub').rmdir();(root/'sub').symlink_to(root,target_is_directory=True)
                self.assertEqual(payloads.inspect(fd,record,{'sub/x':spec},'LIDAR_TOP')['custody_state'],'invalid')
            finally:os.close(fd)

    def test_decoding_consumes_verified_bytes_not_mutable_file(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);data=struct.pack('<5f',1,2,3,4,5);p=root/'x';p.write_bytes(data)
            spec={'filename':'x','state':'retained','byte_size':20,'sha256':hashlib.sha256(data).hexdigest()}
            fd=os.open(root,os.O_RDONLY|os.O_DIRECTORY); original=payloads.decode_points
            def decoder(raw):
                p.write_bytes(b'bad');return original(raw)
            try:
                with patch.object(payloads,'decode_points',decoder):
                    self.assertEqual(payloads.inspect(fd,{'filename':'x'},{'x':spec},'LIDAR_TOP')['payload_state'],'decoded')
            finally:os.close(fd)

    def test_decoder_unavailability_and_corruption_keep_different_states(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);data=b'raw';(root/'x').write_bytes(data)
            spec={'filename':'x','state':'retained','byte_size':3,'sha256':hashlib.sha256(data).hexdigest()}
            record={'filename':'x','width':4,'height':3};fd=os.open(root,os.O_RDONLY|os.O_DIRECTORY)
            try:
                for code,state in (('WINDOW_DECODER_UNAVAILABLE','not_checked'),('WINDOW_IMAGE_DECODE','sensor_invalid')):
                    with patch.object(payloads,'decode_image',side_effect=Invalid(code,'test')):
                        result=payloads.inspect(fd,record,{'x':spec},'CAM_FRONT')
                        self.assertEqual(result['custody_state'],'verified');self.assertEqual(result['payload_state'],state)
                nofile={'filename':'x','state':'unavailable','reason':'not retrieved'}
                self.assertEqual(payloads.inspect(fd,record,{'x':nofile},'CAM_FRONT')['custody_state'],'unavailable')
            finally:os.close(fd)

    def test_whole_report_keeps_unavailable_windows_and_source_identity(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);(root/'raw').mkdir(); req=make_request(root)
            result=windows.build(req)
            self.assertEqual(result['summary']['distinct_required_payloads'],70)
            self.assertEqual(result['summary']['custody_states'],{'not_listed':70})
            self.assertEqual(result['summary']['complete_recorded_windows'],0)
            self.assertIsNone(result['selected_study_cohort'])
            self.assertEqual(result['physical_coverage'],'not_established')
            self.assertEqual(len(result['windows']),2)
            req['metadata']['sha256']='0'*64
            self.rejected(lambda:windows.build(req),'WINDOW_CATALOG')

    def test_complete_decoded_files_do_not_assert_physical_review_readiness(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);(root/'raw').mkdir();req=make_request(root)
            inv=json.loads((root/'inventory.json').read_bytes()); image=jpeg();point=struct.pack('<5f',0,1,2,3,4)
            for row in scene_fixture()['sample_data.json']:
                data=image if row['fileformat']=='jpg' else point
                path=root/'raw'/row['filename'];path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
                inv['assets'].append({'filename':row['filename'],'state':'retained','byte_size':len(data),'sha256':hashlib.sha256(data).hexdigest()})
            req['inventory']=identity_file(root/'inventory.json',encoded(inv))
            result=windows.build(req)
            self.assertEqual(result['summary']['complete_recorded_windows'],2)
            self.assertEqual(result['summary']['payload_states'],{'decoded':70})
            self.assertEqual(result['summary']['repeated_verified_digest_groups'],2)
            self.assertEqual(result['windows'][0]['reference_review_readiness'],'not_established')

    def test_cli_failed_request_does_not_write_and_success_never_overwrites(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);(root/'raw').mkdir();req=make_request(root)
            p=root/'request.json';data=encoded(req);p.write_bytes(data);out=root/'out.json'
            args=['--request',str(p),'--request-sha256',hashlib.sha256(data).hexdigest(),'--output',str(out)]
            with patch.object(windows,'sys') as system:
                system.platform=__import__('sys').platform;system.byteorder=__import__('sys').byteorder
                self.assertEqual(windows.main(args),0)
                before=out.read_bytes();self.assertEqual(windows.main(args),2);self.assertEqual(out.read_bytes(),before)
                args[3]='0'*64;args[-1]=str(root/'absent.json')
                self.assertEqual(windows.main(args),2);self.assertFalse((root/'absent.json').exists())

    def test_cli_code_change_guard_prevents_report(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name); p=root/'request.json';p.write_bytes(encoded({}));out=root/'out.json'
            args=['--request',str(p),'--request-sha256',hashlib.sha256(p.read_bytes()).hexdigest(),'--output',str(out)]
            with patch.object(windows,'runtime',side_effect=[{'test':1},{'test':2}]), patch.object(windows,'build',return_value={}), patch.object(windows,'sys'):
                self.assertEqual(windows.main(args),2)
            self.assertFalse(out.exists())
