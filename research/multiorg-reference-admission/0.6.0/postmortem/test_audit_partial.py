"""Authored abrupt-record controls. No detector inference or empirical outputs."""
import copy
import hashlib
import json
from pathlib import Path
import selectors
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

OWNER=Path(__file__).resolve().parents[1]
SUPPORT=OWNER/'reference' if (OWNER/'reference/check_pair.py').exists() else OWNER
if '--support' in sys.argv:
    at=sys.argv.index('--support');SUPPORT=Path(sys.argv[at+1]).resolve();del sys.argv[at:at+2]
sys.path.insert(0,str(SUPPORT))
import check_pair as c
from test_check_pair import packet,write,descriptor
import audit_partial as a
import numpy as np


def interrupted(root,keep=1,orphan=False):
    ctx,process=packet(root)
    stems={model:c.digest(c.canonical([ctx['image_id'],model])) for model in ('faster','yolo')}
    for p in root.glob('*.json'):p.unlink()
    for folder in ('raw','admissions'):
        for p in (root/folder).glob('*'):
            if p.name.startswith(stems['yolo']+'-'):p.unlink()
            elif keep==1 and p.name.startswith(stems['faster']+'-1'):
                if not (orphan and p.suffix=='.npy'):p.unlink()
    process.update(status='failed',returncode=-9,termination_reason='disk_floor')
    process.pop('result_sha256')
    return ctx,process,stems


class Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.ctx,self.process,self.stems=interrupted(self.root)
    def tearDown(self):self.temp.cleanup()
    def run_audit(self):
        with patch.object(c,'scalar_nms',side_effect=AssertionError('whole-image NMS is forbidden')):
            return a.audit_saved(c,self.root,self.ctx,self.process,time.monotonic()+15)
    def raw(self,n=0):return self.root/'raw'/f'{self.stems["faster"]}-{n}.json'
    def admission(self,n=0):return self.root/'admissions'/f'{self.stems["faster"]}-{n}.json'
    def fresh(self,keep=2,orphan=False):
        self.temp.cleanup();self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.ctx,self.process,self.stems=interrupted(self.root,keep,orphan)
    def test_verified_prefix_stays_failed_and_unknown(self):
        r=self.run_audit();self.assertEqual(r['models'][0]['validated_capture_tiles'],1)
        self.assertEqual(r['models'][0]['verified_persisted_admissions'],1)
        self.assertEqual(r['models'][1]['validated_capture_tiles'],0)
        self.assertEqual(r['complete_pairs'],0);self.assertEqual(r['complete_model_endpoints'],0)
        self.assertIsNone(r['forward_accounting']['total_forward_starts']);self.assertIsNone(r['forward_accounting']['total_forward_completions'])
        self.assertFalse(r['inference_performed']);self.assertFalse(r['full_image_nms_performed']);self.assertFalse(r['reference_matching_performed'])
        self.assertEqual(r['unqualified_or_inflight_files'],[])
    def test_orphan_arrays_not_promoted(self):
        self.fresh(1,True);r=self.run_audit()
        self.assertEqual(r['models'][0]['validated_capture_tiles'],1);self.assertEqual(len(r['unqualified_or_inflight_files']),33)
    def test_raw_complete_admission_missing(self):
        self.fresh();self.admission(1).unlink();r=self.run_audit()
        self.assertEqual(r['models'][0]['validated_capture_tiles'],2);self.assertEqual(r['models'][0]['verified_persisted_admissions'],1)
        self.assertEqual(r['tiles'][-1]['producer_admission'],'missing');self.assertEqual(r['complete_pairs'],0)
    def test_torn_final_raw_json(self):
        self.fresh();self.raw(1).write_text('{"image_id":');self.admission(1).unlink();r=self.run_audit()
        self.assertEqual(r['models'][0]['validated_capture_tiles'],1);self.assertEqual(r['rejected_receipts'][0]['stage'],'raw_receipt')
        self.assertEqual(len(r['unqualified_or_inflight_files']),34)
    def test_torn_final_array(self):
        self.fresh();record=json.loads(self.raw(1).read_bytes());p=self.root/record['raw_outputs'][0]['file'];p.write_bytes(p.read_bytes()[:-1]);r=self.run_audit()
        self.assertEqual(r['models'][0]['validated_capture_tiles'],1);self.assertEqual(r['rejected_receipts'][0]['stage'],'raw_arrays')
    def test_torn_admission_preserves_capture_only(self):
        self.fresh();self.admission(1).write_text('{');r=self.run_audit()
        self.assertEqual(r['models'][0]['validated_capture_tiles'],2);self.assertEqual(r['models'][0]['verified_persisted_admissions'],1)
        self.assertEqual(r['tiles'][-1]['producer_admission'],'invalid_or_incomplete')
    def test_shifted_tensor_origin_names_counts_and_boolean(self):
        original=json.loads(self.raw().read_bytes())
        for mutation in ('tensor','origin','names','count','boolean','rowprefix'):
            obj=copy.deepcopy(original)
            if mutation=='tensor':obj['tensor']['c_order_data_sha256']='f'*64
            if mutation=='origin':obj['rescaled_column']=256
            if mutation=='names':obj['raw_outputs'].reverse()
            if mutation=='count':obj['observed_detection_rows']+=1
            if mutation=='boolean':obj['ordinal']=False
            if mutation=='rowprefix':obj['all_raw_rows_completed_before_tile']=1
            write(self.raw(),obj)
            with self.subTest(mutation=mutation):
                r=self.run_audit();self.assertEqual(r['models'][0]['validated_capture_tiles'],0);self.assertEqual(len(r['rejected_receipts']),1)
        write(self.raw(),original)
    def test_high_invalid_is_refusal_not_empty(self):
        self.fresh();ys=self.stems['yolo'];root=self.root
        arrays={'dets':np.array([[[0,0,0,0,.9]]],np.float32),'labels':np.zeros((1,1),np.int64)}
        ledger=json.loads(self.raw(0).read_bytes());ledger.update(model='yolo',model_variant=c.VARIANTS['yolo'],resized_side=416,
            tensor={**self.ctx['tensors'][2]['tensor'],'observation_time':'before_session_run'},observed_detection_rows=1)
        ledger['raw_outputs']=[descriptor(root/'raw'/f'{ys}-0-{i}.npy',x,n,root) for i,(n,x) in enumerate(arrays.items())]
        write(root/'raw'/f'{ys}-0.json',ledger);r=self.run_audit()
        self.assertEqual(r['models'][1]['validated_capture_tiles'],0);self.assertEqual(r['rejected_receipts'][0]['stage'],'tile_semantics')
        self.assertIn('high-score',r['rejected_receipts'][0]['reason']);self.assertEqual(r['complete_pairs'],0)
    def test_missing_or_duplicate_ordinal_refused(self):
        original=self.raw().read_bytes();self.raw().unlink();self.raw(1).write_bytes(original)
        with self.assertRaisesRegex(ValueError,'contiguous'):self.run_audit()
        self.raw(1).unlink();self.raw().write_bytes(original)
        (self.root/'raw'/f'{self.stems["faster"]}-00.json').write_bytes(original)
        with self.assertRaisesRegex(ValueError,'canonical'):self.run_audit()
    def test_continuation_after_unadmitted_tile_refused(self):
        self.fresh();self.admission().unlink()
        with self.assertRaisesRegex(ValueError,'continued'):self.run_audit()
    def test_success_or_terminal_record_cannot_promote(self):
        self.process.update(status='complete',returncode=0,termination_reason=None)
        with self.assertRaisesRegex(ValueError,'specific abrupt'):self.run_audit()
        self.process.update(status='failed',returncode=-9,termination_reason='disk_floor')
        for name in ('result.json','failure.json'):
            p=self.root/name;p.write_text('{}')
            with self.assertRaisesRegex(ValueError,'terminal'):self.run_audit()
            p.unlink()
    def test_process_identity_policy_and_resources(self):
        original=copy.deepcopy(self.process)
        for key,value in {'runner_sha256':'0'*64,'manifest_sha256':'0'*64,'policy_sha256':'0'*64,
            'network_boundary':'unconfined','returncode':False,'result_sha256':'0'*64,'peak_sampled_rss_bytes':3221225473,
            'wall_seconds':float('inf')}.items():
            self.process={**original,key:value}
            with self.subTest(key=key),self.assertRaises(ValueError):self.run_audit()
        self.process=original
    def test_symlink_refused(self):
        (self.root/'raw'/'link.npy').symlink_to(self.raw())
        with self.assertRaisesRegex(ValueError,'symlink'):self.run_audit()
    def test_duplicate_key_rejected_as_unqualified(self):
        self.raw().write_text('{"ordinal":0,"ordinal":1}');r=self.run_audit()
        self.assertEqual(r['models'][0]['validated_capture_tiles'],0);self.assertIn('duplicate',r['rejected_receipts'][0]['reason'])
    def test_inventory_binding_and_change(self):
        inv=a.inventory(c,self.root,time.monotonic()+5);owner=self.root.parent
        files={str((self.root/k).relative_to(owner)):{'sha256':v['sha256'],'bytes':v['bytes']} for k,v in inv.items()}
        record={'artifact_id':'reiyah.multiorg.terminated-attempt.inventory','version':'0.6.0','status':'inventory_only_not_output_admission',
            'files':files,'file_count':35,'total_bytes':sum(v['bytes'] for v in files.values()),'raw_numpy_files':33,'raw_ledger_files':1,
            'worker_admission_files':1,'worker_terminal_record_present':False}
        a.termination_inventory(c,owner,self.root,record,inv)
        record['worker_terminal_record_present']=0
        with self.assertRaises(ValueError):a.termination_inventory(c,owner,self.root,record,inv)
        before=a.inventory
        def changing(*args):
            result=before(*args)
            if changing.calls:result['authored_mutation']={'file':'x','bytes':0,'sha256':'0'*64}
            changing.calls+=1;return result
        changing.calls=0
        with patch.object(a,'inventory',side_effect=changing),self.assertRaisesRegex(ValueError,'changed'):self.run_audit()
    def test_frozen_source_bindings_cannot_change(self):
        with tempfile.TemporaryDirectory() as directory:
            owner=Path(directory);(owner/'reference').mkdir();(owner/'implementation').mkdir()
            data={'reference/check_pair.py':b'authored checker','implementation/complete_pair.py':b'authored worker','manifest.json':b'authored manifest'}
            for name,raw in data.items():(owner/name).write_bytes(raw)
            bindings={name:{'sha256':c.digest(raw),'bytes':len(raw)} for name,raw in data.items()}
            cs=bindings['reference/check_pair.py']['sha256'];ws=bindings['implementation/complete_pair.py']['sha256']
            freeze={'artifact_id':'reiyah.multiorg.selected-cohort.execution-freeze','version':'0.6.0','pair_worker_sha256':ws,'pair_checker_sha256':cs,'bindings':bindings}
            fp=owner/'freeze.json';write(fp,freeze);ctx={'manifest_sha256':bindings['manifest.json']['sha256']}
            with patch.multiple(a,CHECKER_SHA=cs,WORKER_SHA=ws):
                self.assertEqual(a.frozen_bindings(c,owner,fp,c.digest(fp.read_bytes()),owner/'manifest.json',ctx,time.monotonic()+5),3)
                (owner/'reference/check_pair.py').write_bytes(b'changed')
                with self.assertRaises(ValueError):a.frozen_bindings(c,owner,fp,c.digest(fp.read_bytes()),owner/'manifest.json',ctx,time.monotonic()+5)
    def test_actual_sigkill_authored_writer(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            child=subprocess.Popen([sys.executable,'-B',__file__,'--support',str(SUPPORT),'--authored-child',str(root)],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            try:
                with selectors.DefaultSelector() as selector:
                    selector.register(child.stdout,selectors.EVENT_READ);self.assertTrue(selector.select(4),'authored child ready before deadline')
                    self.assertEqual(child.stdout.readline(),b'READY\n')
                child.send_signal(signal.SIGKILL);child.wait(timeout=2);self.assertEqual(child.returncode,-9)
                # Context is metadata from the same authored fixture, reconstructed separately.
                with tempfile.TemporaryDirectory() as second:
                    ctx,process,_=interrupted(Path(second))
                process['returncode']=child.returncode
                with patch.object(c,'scalar_nms',side_effect=AssertionError('no whole-image NMS')):
                    report=a.audit_saved(c,root,ctx,process,time.monotonic()+10)
                self.assertEqual(report['models'][0]['verified_persisted_admissions'],1)
                self.assertEqual(report['complete_pairs'],0);self.assertIsNone(report['forward_accounting']['total_forward_starts'])
                self.assertFalse((root/'result.json').exists());self.assertFalse((root/'failure.json').exists())
            finally:
                if child.poll() is None:child.kill();child.wait(timeout=2)
                child.stdout.close();child.stderr.close()


if __name__=='__main__':
    if len(sys.argv)==3 and sys.argv[1]=='--authored-child':
        interrupted(Path(sys.argv[2]));print('READY',flush=True);time.sleep(5);sys.exit(3)
    unittest.main(verbosity=2)
