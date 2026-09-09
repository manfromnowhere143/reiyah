"""Disclosure noninterference, complete population, decoder boundaries and seals."""
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

from tools.perception_decision.contract import Invalid, encoded, wire
from tools.perception_geometry import bind
from tools.perception_observation import contract, formats, package
from tools.perception_observation import __main__ as cli
from tools.perception_windows import __main__ as windows
from tests.test_perception_geometry import values
from tests.test_perception_windows import identity_file, jpeg, make_request


def fixture(root):
    (root/'raw').mkdir()
    data = values(); wr = make_request(root, data)
    inv = {'artifact_id': 'reiyah.perception-windows.assets', 'version': '0.1.0', 'assets': []}
    jpg, points = jpeg(), struct.pack('<10f', 1, 2, 3, 4, 5, -1, -2, -3, 8, 9)
    for row in data['sample_data.json']:
        raw = jpg if row['width'] else points
        path = root/'raw'/row['filename']; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(raw)
        inv['assets'].append({'filename': row['filename'], 'state': 'retained',
                             'byte_size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})
    wr['inventory'] = identity_file(root/'inventory.json', encoded(inv))
    report = windows.build(wr)
    win = identity_file(root/'windows.json', encoded(report))
    gr = {'artifact_id': 'reiyah.perception-geometry.request', 'version': '0.1.0',
          'window_report': win, 'catalog': wr['catalog'], 'metadata': wr['metadata']}
    geometry = identity_file(root/'geometry.json', encoded(bind.build(gr)))
    return {'artifact_id': 'reiyah.perception-observation.request', 'version': '0.1.0',
            'package_id': 'a'*32, 'window_report': win, 'geometry_report': geometry,
            'inventory': wr['inventory'], 'raw_root': str(root/'raw')}


def read(spec):
    return json.loads(Path(spec['path']).read_bytes())


def replace(req, role, value):
    req[role] = identity_file(Path(req[role]['path']), encoded(value))


def rebind_window(req, value):
    replace(req, 'window_report', value)
    g = read(req['geometry_report']); g['inputs']['window_report'] = req['window_report']
    replace(req, 'geometry_report', g)


def tree(path):
    return {str(p.relative_to(path)):p.read_bytes() for p in path.rglob('*') if p.is_file()}


class ObservationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name); self.req = fixture(self.root)
        self.out, self.custody = self.root/'reviewer', self.root/'custody.private.json'

    def rejected(self, fn, code):
        with self.assertRaises(Invalid) as caught:
            fn()
        self.assertEqual(caught.exception.code, code)

    def build(self):
        return package.build(self.req, self.out, self.custody)

    def test_full_pipeline_neutral_ids_exact_population_and_raw_roundtrip(self):
        result = self.build()
        self.assertEqual(result['summary']['evidence_states'], {'delivered':70})
        checked = package.verify(self.out, result['seal_sha256'])
        self.assertTrue(checked['disclosure_verified'])
        self.assertEqual(checked['summary']['human_review'], 'not_established')
        custody = json.loads(self.custody.read_bytes())
        for r in custody['captures']:
            raw = (self.root/'raw'/r['source']['filename']).read_bytes()
            spec = r['disclosed_evidence']['asset']; disclosed = (self.out/spec['filename']).read_bytes()
            if r['source']['channel'] == 'LIDAR_TOP':
                self.assertEqual(disclosed.split(b'end_header\n',1)[1], raw)
            else:
                self.assertEqual(disclosed, raw)
        manifest = (self.out/'manifest.json').read_bytes()
        for token in (b'scene_token',b'sample_token',b'ego_pose_token',b'is_key_frame',b'filename":"samples/',
                      b'anchor_timestamp_us',b'pointpillars',b'annotations',str(self.root).encode()):
            self.assertNotIn(token, manifest)

    def test_forbidden_private_metadata_is_noninterfering(self):
        original = self.build(); original_tree = tree(self.out)
        w = read(self.req['window_report'])
        w.update(detector='secret-model-v2', scores=[12345], annotations=['forbidden'], limits=['private-path'])
        w['windows'][0]['channels']['CAM_FRONT']['captures'][0]['payload']['diagnostic'] = 'secret-label'
        rebind_window(self.req, w)
        g = read(self.req['geometry_report'])
        g['limits'] = ['forbidden']; g['source_identities'] = [['private-predictor','private-hash']]
        for row in g['captures'].values():
            row['nominal_sensor_to_global']['reasons'] = ['private-label']
        replace(self.req, 'geometry_report', g)
        other = package.build(self.req, self.root/'other', self.root/'other-custody.json')
        self.assertEqual(original['seal_sha256'], other['seal_sha256'])
        self.assertEqual(original_tree, tree(self.root/'other'))
        self.assertNotEqual(self.custody.read_bytes(), (self.root/'other-custody.json').read_bytes())

    def test_absolute_clock_origin_and_source_filenames_are_noninterfering(self):
        self.build(); first=tree(self.out)
        w=read(self.req['window_report']);g=read(self.req['geometry_report']);inv=read(self.req['inventory'])
        shift=1_000_000_000
        renames={r['filename']:f'renamed/input-{i:04d}' for i,r in enumerate(inv['assets'])}
        for r in inv['assets']:
            old=r['filename'];new=renames[old];path=self.root/'raw'/new;path.parent.mkdir(exist_ok=True)
            (self.root/'raw'/old).rename(path);r['filename']=new
        replace(self.req,'inventory',inv);w['inputs']['inventory']=self.req['inventory']
        for window in w['windows']:
            window['anchor_timestamp_us']+=shift
            window['context_window_us']=[t+shift for t in window['context_window_us']]
            for group in window['channels'].values():
                for row in group['captures']:
                    row['capture_timestamp_us']+=shift;row['filename']=renames[row['filename']]
        for window in g['windows']:
            window['anchor_timestamp_us']+=shift
            window['context_window_us']=[t+shift for t in window['context_window_us']]
        for row in g['captures'].values():row['capture_timestamp_us']+=shift
        replace(self.req,'window_report',w);g['inputs']['window_report']=self.req['window_report']
        replace(self.req,'geometry_report',g)
        package.build(self.req,self.root/'shifted',self.root/'shifted-custody.json')
        self.assertEqual(first,tree(self.root/'shifted'))

    def test_raw_change_after_prior_decode_is_detected_before_disclosure(self):
        row=read(self.req['inventory'])['assets'][0];path=self.root/'raw'/row['filename']
        raw=bytearray(path.read_bytes());raw[0]^=1;path.write_bytes(raw)
        self.assertEqual(self.build()['summary']['evidence_states'],{'delivered':69,'invalid':1})

    def test_missing_unavailable_unlisted_corrupt_and_withheld_keep_captures(self):
        inv = read(self.req['inventory'])
        one,two,three,four = inv['assets'][:4]
        (self.root/'raw'/one['filename']).unlink()
        inv['assets'][1] = {'filename':two['filename'],'state':'unavailable','reason':'private reason'}
        inv['assets'].remove(three)
        (self.root/'raw'/four['filename']).write_bytes(b'corrupt')
        camera = next(r for r in inv['assets'] if '.jpg' in r['filename'])
        path = self.root/'raw'/camera['filename']; data = path.read_bytes()
        data = data[:2]+b'\xff\xfe\x00\x09private'+data[2:]; path.write_bytes(data)
        camera.update(byte_size=len(data),sha256=hashlib.sha256(data).hexdigest())
        replace(self.req, 'inventory', inv)
        w=read(self.req['window_report']); w['inputs']['inventory']=self.req['inventory']; rebind_window(self.req,w)
        result=self.build(); states=result['summary']['evidence_states']
        self.assertEqual(states,{'delivered':65,'missing':1,'unavailable':1,'not_listed':1,'invalid':1,'withheld':1})
        self.assertEqual(result['summary']['capture_occurrences'],70)
        self.assertTrue(package.verify(self.out,result['seal_sha256'])['disclosure_verified'])

    def test_nonfinite_lidar_is_sensor_invalid_without_zero_imputation(self):
        inv=read(self.req['inventory']); row=inv['assets'][0]; raw=struct.pack('<5f',1,2,3,4,float('nan'))
        (self.root/'raw'/row['filename']).write_bytes(raw)
        row.update(byte_size=len(raw),sha256=hashlib.sha256(raw).hexdigest());replace(self.req,'inventory',inv)
        w=read(self.req['window_report']);w['inputs']['inventory']=self.req['inventory'];rebind_window(self.req,w)
        self.assertEqual(self.build()['summary']['evidence_states'],{'delivered':69,'sensor_invalid':1})

    def test_decoder_absence_is_not_checked(self):
        with patch.object(formats,'camera',side_effect=Invalid('WINDOW_DECODER_UNAVAILABLE','missing')):
            result=self.build()
        self.assertEqual(result['summary']['evidence_states'],{'delivered':10,'not_checked':60})

    def test_raw_symlink_is_invalid_and_no_target_bytes_are_disclosed(self):
        row=read(self.req['inventory'])['assets'][0];path=self.root/'raw'/row['filename']
        target=self.root/'outside';target.write_bytes(path.read_bytes());path.unlink();path.symlink_to(target)
        self.assertEqual(self.build()['summary']['evidence_states'],{'delivered':69,'invalid':1})

    def test_request_closed_and_malformed_identifiers(self):
        for key,value in [('extra','hint'),('package_id',True),('package_id','study-42')]:
            r=deepcopy(self.req);r[key]=value
            self.rejected(lambda:package.build(r,self.out,self.custody),'OBS_REQUEST')

    def test_wrong_upstream_identity_rejected_before_output(self):
        g=read(self.req['geometry_report']);g['inputs']['window_report']['sha256']='f'*64;replace(self.req,'geometry_report',g)
        self.rejected(self.build,'OBS_BINDING');self.assertFalse(self.out.exists())

    def test_geometry_capture_omission_and_cross_channel_join_rejected(self):
        original=read(self.req['geometry_report'])
        for defect in ('omission','channel','pose','clock','order','duplicate','extra'):
            g=deepcopy(original);key=next(iter(g['captures']))
            if defect=='omission':g['windows'][0]['captures'].pop()
            if defect=='channel':g['captures'][key]['channel']='CAM_FRONT'
            if defect=='pose':g['captures'][key]['ego_pose_token']='other'
            if defect=='clock':g['captures'][key]['capture_timestamp_us']=True
            if defect=='order':g['windows'][0]['captures'].reverse()
            if defect=='duplicate':g['windows'][0]['captures'].append(g['windows'][0]['captures'][0])
            if defect=='extra':g['captures']['extra']=g['captures'][key]
            replace(self.req,'geometry_report',g)
            with self.subTest(defect=defect):self.rejected(self.build,'OBS_BINDING')

    def test_boundary_and_relative_time_are_never_replaced_by_zero(self):
        g=read(self.req['geometry_report']);g['windows'][0]['captures'][0]['capture_minus_anchor_us']=False
        replace(self.req,'geometry_report',g);self.rejected(self.build,'OBS_BINDING')

    def test_unavailable_geometry_keeps_evidence_and_no_matrix(self):
        g=read(self.req['geometry_report']);r=g['windows'][0]['captures'][0]
        r['nominal_sensor_to_anchor_ego']={'state':'unavailable','matrix':None,'reasons':['private reason']}
        replace(self.req,'geometry_report',g);result=self.build()
        m=json.loads((self.out/'manifest.json').read_bytes())
        self.assertEqual(m['windows'][0]['channels']['LIDAR_TOP']['captures'][0]['sensor_to_anchor_ego'],{'state':'unavailable'})
        self.assertEqual(result['summary']['evidence_states'],{'delivered':70})

    def test_matrix_bool_noncanonical_handedness_and_unknown_fields_reject(self):
        g=read(self.req['geometry_report']);original=deepcopy(g)
        for defect in ('bool','noncanonical','handedness','extra'):
            g=deepcopy(original);m=g['windows'][0]['captures'][0]['nominal_sensor_to_anchor_ego']['matrix']
            if defect=='bool':m[0][0]['numerator']=True
            if defect=='noncanonical':m[0][0]={'numerator':'2','denominator':'2'}
            if defect=='handedness':m[0][0]={'numerator':'-1','denominator':'1'}
            if defect=='extra':m[0][0]['note']='hint'
            replace(self.req,'geometry_report',g)
            with self.subTest(defect=defect):
                self.rejected(self.build,'INVALID_RATIONAL' if defect=='noncanonical' else 'OBS_MATRIX')

    def test_consumer_rejects_extra_manifest_fields_and_aliases(self):
        self.build();original=json.loads((self.out/'manifest.json').read_bytes())
        for defect in ('root','capture','duplicate','unreferenced','bool','time'):
            m=deepcopy(original)
            if defect=='root':m['predictions']=[]
            if defect=='capture':m['captures'][0]['object_hint']='car'
            if defect=='duplicate':m['captures'][1]['id']=m['captures'][0]['id']
            if defect=='unreferenced':m['windows'][0]['channels']['LIDAR_TOP']['captures'].pop(0)
            if defect=='bool':m['captures'][10]['image_shape'][0]=True
            if defect=='time':m['windows'][0]['channels']['LIDAR_TOP']['captures'][0]['time_offset_us']=2_000_001
            with self.subTest(defect=defect):self.rejected(lambda:contract.validate(m),'OBS_SCHEMA')

    def test_no_population_clipping_for_resource_limit(self):
        with patch.object(contract,'MAX_TOTAL',100):self.rejected(self.build,'OBS_LIMIT')
        self.assertFalse(self.out.exists())

    def test_custody_inside_package_refused(self):
        self.rejected(lambda:package.build(self.req,self.out,self.out/'private/custody.json'),'OBS_CUSTODY')
        self.assertFalse(self.out.exists())

    def test_outputs_cannot_be_reused_even_if_empty(self):
        self.out.mkdir();self.rejected(self.build,'OUTPUT_EXISTS')
        self.out.rmdir();self.custody.write_bytes(b'');self.rejected(self.build,'OUTPUT_EXISTS')

    def test_interrupted_build_is_unsealed_and_unusable(self):
        original=package.atomic_write
        def fail(path,data):
            if Path(path).name=='READ_ME.txt':raise OSError('simulated interruption')
            original(path,data)
        with patch.object(package,'atomic_write',side_effect=fail):
            with self.assertRaises(OSError):self.build()
        self.assertFalse((self.out/'SEAL.json').exists())
        self.rejected(lambda:package.verify(self.out,'a'*64),'OBS_FILE_SET')
        self.rejected(self.build,'OUTPUT_EXISTS')

    def test_runtime_change_leaves_no_custody_or_seal(self):
        with patch.object(package,'runtime',side_effect=[{'v':1},{'v':2}]):
            self.rejected(self.build,'OBS_CODE_CHANGED')
        self.assertFalse((self.out/'SEAL.json').exists());self.assertFalse(self.custody.exists())

    def test_seal_substitution_detected_by_separately_expected_digest(self):
        r=self.build();p=self.out/'SEAL.json';p.write_bytes(p.read_bytes()+b' ')
        self.rejected(lambda:package.verify(self.out,r['seal_sha256']),'OBS_FILE_IDENTITY')

    def test_file_mutation_and_extra_hidden_files_rejected(self):
        r=self.build();asset=next((self.out/'assets').iterdir());raw=asset.read_bytes();asset.write_bytes(raw+b'x')
        self.rejected(lambda:package.verify(self.out,r['seal_sha256']),'OBS_FILE_IDENTITY')
        asset.write_bytes(raw);extra=self.out/'assets/annotations.json';extra.write_text('{}')
        self.rejected(lambda:package.verify(self.out,r['seal_sha256']),'OBS_FILE_SET')
        extra.unlink();(self.out/'private').mkdir()
        self.rejected(lambda:package.verify(self.out,r['seal_sha256']),'OBS_FILE_SET')

    def test_asset_directory_symlink_rejected(self):
        r=self.build();original=self.out/'assets';renamed=self.root/'other-assets';original.rename(renamed);original.symlink_to(renamed)
        with self.assertRaises(OSError):package.verify(self.out,r['seal_sha256'])

    def test_cli_verifier_requires_expected_seal_and_returns_no_readiness_claim(self):
        r=self.build()
        self.assertEqual(cli.main(['verify','--package',str(self.out),'--seal-sha256',r['seal_sha256']]),0)
        self.assertEqual(cli.main(['verify','--package',str(self.out),'--seal-sha256','bad']),2)


class DisclosureFormatTests(unittest.TestCase):
    def rejected(self, data):
        with self.assertRaises(Invalid) as caught:formats.jpeg_profile(data)
        self.assertEqual(caught.exception.code,'OBS_JPEG_PROFILE')

    def test_jpeg_pixels_unchanged(self):
        data=jpeg();self.assertEqual(formats.camera(data,4,3),data)

    def test_jpeg_app_comment_after_scan_and_concatenation_rejected(self):
        data=jpeg()
        for tag in (0xe0,0xe1,0xe2,0xfe,0xdb):
            segment=bytes([255,tag])+b'\x00\x09private'
            with self.subTest(tag=tag):self.rejected(data[:-2]+segment+data[-2:])
        for suffix in (b'private',data,b'\0'):
            self.rejected(data+suffix)
        for tag in (0xe1,0xe2,0xfe):
            self.rejected(data[:2]+bytes([255,tag])+b'\x00\x09private'+data[2:])

    def test_jpeg_thumbnail_second_app_missing_app_and_progressive_withheld(self):
        data=jpeg();thumbnail=bytearray(data);thumbnail[18]=1
        self.rejected(bytes(thumbnail));self.rejected(data[:20]+data[2:20]+data[20:]);self.rejected(data[:2]+data[20:])
        from PIL import Image
        stream=io.BytesIO();Image.new('RGB',(4,3)).save(stream,format='JPEG',progressive=True);self.rejected(stream.getvalue())

    def test_jpeg_truncated_segment_unknown_marker_and_missing_eoi_rejected(self):
        data=jpeg()
        for value in (b'',b'\xff\xd8',data[:-1],data[:4]+b'\xff\xff'+data[6:],data[:2]+b'\xff\x01'+data[2:]):
            self.rejected(value)

    def test_point_wrapper_preserves_every_field_and_rejects_wrong_count(self):
        raw=struct.pack('<10f',1,-2,3,4,5,6,7,-8,9,10);ply,n=formats.lidar(raw)
        self.assertEqual(n,2);self.assertEqual(ply[len(formats.ply_header(n)):],raw);formats.verify_ply(ply,n)
        for data,count in ((ply,1),(ply,True),(ply+b'x',n),(ply.replace(b'float x',b'float q'),n)):
            with self.assertRaises(Invalid):formats.verify_ply(data,count)


if __name__ == '__main__':
    unittest.main()
