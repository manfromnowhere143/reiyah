"""CPU process/filesystem controls; no third-party video or model imports."""
import ast
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import extract

ROOT = Path(__file__).resolve().parents[3]


class ExtractionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.out = self.root/'output'
        self.plan = {'artifact_id':'reiyah.extraction-plan','version':'0.1.0','fps':'2/5','clips':[]}
        for cid in ('one','two'):
            clip = {'id':cid,'expected_frames':2}
            for role in extract.ROLES:
                source = self.root/(cid+'-'+role+'.mp4')
                source.write_bytes((cid+'-'+role).encode())
                clip[role] = {'path':str(source),'sha256':extract.fingerprint(source)['sha256']}
            self.plan['clips'].append(clip)

    def fake(self, argv, **kwargs):
        self.assertIn('-xerror',argv)
        self.assertIn('-nostdin',argv)
        self.assertEqual(argv[argv.index('-protocol_whitelist')+1],'file')
        for n in (1,2):
            Path(argv[-1] % n).write_bytes(b'authored-frame-'+str(n).encode())
        return SimpleNamespace(returncode=0)

    def run_plan(self, runner=None):
        with patch.object(extract.subprocess,'run',side_effect=runner or self.fake):
            return extract.run(self.plan,self.out,sys.executable)

    def pairs(self):
        return extract.require_complete(self.plan,self.out,extract.sha((self.out/'ledger.json').read_bytes()))

    def blocked(self, ledger, reason=None):
        self.assertEqual(ledger['accounting_status'],'blocked')
        self.assertEqual(len(ledger['clips']),len(self.plan['clips']))
        if reason:
            reasons=[s['reason'] for c in ledger['clips'] for s in c['streams'].values()]
            self.assertIn(reason,reasons)
        with self.assertRaises(extract.Invalid):
            self.pairs()

    def test_complete_declared_cohort_and_pair_binding(self):
        ledger=self.run_plan()
        self.assertEqual(ledger['accounting_status'],'complete')
        self.assertEqual(ledger['measurement_status'],'not_performed')
        self.assertEqual(ledger['synchronization'],'not_established')
        self.assertEqual(len(self.pairs()),4)

    def test_missing_gaze_preserves_membership_and_other_clip(self):
        Path(self.plan['clips'][0]['gaze']['path']).unlink()
        ledger=self.run_plan()
        self.blocked(ledger,'source_missing')
        self.assertEqual(ledger['clips'][0]['streams']['gaze']['state'],'missing')
        self.assertEqual(ledger['clips'][1]['state'],'processed')

    def test_input_identity_change_before_extraction(self):
        Path(self.plan['clips'][0]['camera']['path']).write_bytes(b'changed')
        self.blocked(self.run_plan(),'source_identity_or_empty_input')

    def test_failed_process_with_apparently_complete_frames_is_blocked(self):
        def fail(argv,**kwargs):
            self.fake(argv,**kwargs)
            kwargs['stderr'].write(b'authored decoder failure')
            return SimpleNamespace(returncode=7)
        ledger=self.run_plan(fail)
        self.blocked(ledger,'extraction_process_failed')
        self.assertTrue((self.out/'one/camera/frames/frame-000001.jpg').exists())
        self.assertIn(b'authored decoder failure',(self.out/'one/camera/stderr.txt').read_bytes())

    def test_zero_exit_without_frames_is_blocked(self):
        self.blocked(self.run_plan(lambda *a,**k: SimpleNamespace(returncode=0)), 'frame_membership_mismatch')

    def test_equal_shortened_streams_do_not_mean_complete(self):
        for clip in self.plan['clips']: clip['expected_frames']=3
        self.blocked(self.run_plan(),'frame_membership_mismatch')

    def test_missing_one_frame_pair_is_blocked(self):
        def short(argv,**kwargs):
            result=self.fake(argv,**kwargs)
            if 'gaze' in Path(argv[-1]).parts:
                Path(argv[-1] % 2).unlink()
            return result
        self.blocked(self.run_plan(short),'frame_membership_mismatch')

    def test_gaps_and_extra_frames_are_blocked(self):
        def gap(argv,**kwargs):
            result=self.fake(argv,**kwargs)
            Path(argv[-1] % 2).rename(argv[-1] % 3)
            return result
        self.blocked(self.run_plan(gap),'frame_membership_mismatch')
        self.out=self.root/'extra'
        def extra(argv,**kwargs):
            result=self.fake(argv,**kwargs); Path(argv[-1] % 3).write_bytes(b'extra'); return result
        self.blocked(self.run_plan(extra),'frame_membership_mismatch')

    def test_empty_frame_is_blocked(self):
        def empty(argv,**kwargs):
            result=self.fake(argv,**kwargs); Path(argv[-1] % 1).write_bytes(b''); return result
        self.blocked(self.run_plan(empty),'empty_frame_file')

    def test_timeout_and_process_start_failure_are_distinct(self):
        def timeout(argv,**kwargs): raise subprocess.TimeoutExpired(argv,kwargs['timeout'])
        self.blocked(self.run_plan(timeout),'extraction_timeout')
        self.out=self.root/'start-failure'
        def noexec(*args,**kwargs): raise OSError('authored start failure')
        self.blocked(self.run_plan(noexec),'extraction_process_failed')

    def test_source_changed_during_extraction_is_blocked(self):
        def mutate(argv,**kwargs):
            result=self.fake(argv,**kwargs)
            Path(argv[argv.index('-i')+1]).write_bytes(b'mutated during read')
            return result
        self.blocked(self.run_plan(mutate),'source_changed')

    def test_changed_frame_rejected_at_consumption(self):
        self.run_plan()
        (self.out/'one/gaze/frames/frame-000001.jpg').write_bytes(b'changed later')
        with self.assertRaises(extract.Invalid): self.pairs()

    def test_changed_source_rejected_at_consumption(self):
        self.run_plan()
        Path(self.plan['clips'][0]['camera']['path']).write_bytes(b'changed later')
        with self.assertRaises(extract.Invalid): self.pairs()

    def test_changed_process_log_rejected_at_consumption(self):
        self.run_plan()
        (self.out/'one/camera/stderr.txt').write_bytes(b'changed later')
        with self.assertRaises(extract.Invalid): self.pairs()

    def test_omitted_clip_and_promoted_status_rejected_even_if_rebound(self):
        ledger=self.run_plan()
        shortened=deepcopy(ledger); shortened['clips'].pop()
        for forged in (shortened,dict(ledger,measurement_status='succeeded')):
            (self.out/'ledger.json').write_bytes(extract.encoded(forged))
            with self.assertRaises(extract.Invalid): self.pairs()

    def test_wrong_plan_and_ledger_digest_reject(self):
        self.run_plan()
        with self.assertRaises(extract.Invalid):
            extract.require_complete(self.plan,self.out,'0'*64)
        self.plan['fps']='1/2'
        with self.assertRaises(extract.Invalid): self.pairs()

    def test_existing_output_is_never_overwritten(self):
        self.out.mkdir(); marker=self.out/'keep'; marker.write_bytes(b'original')
        with self.assertRaises(FileExistsError): self.run_plan()
        self.assertEqual(marker.read_bytes(),b'original')

    def test_invalid_plans_reject_before_output_creation(self):
        variants=[]
        for fps in ('0','-1','NaN','0.4','2/4',True):
            p=deepcopy(self.plan);p['fps']=fps;variants.append(p)
        p=deepcopy(self.plan);p['clips'].append(p['clips'][0]);variants.append(p)
        for count in (0,None,True,-1):
            p=deepcopy(self.plan);p['clips'][0]['expected_frames']=count;variants.append(p)
        p=deepcopy(self.plan);p['unexpected']=1;variants.append(p)
        p=deepcopy(self.plan);p['clips']=[];variants.append(p)
        p=deepcopy(self.plan);p['clips'][0]['id']='../escape';variants.append(p)
        for plan in variants:
            with self.subTest(plan=plan):
                with self.assertRaises(extract.Invalid): extract.run(plan,self.out,sys.executable)
                self.assertFalse(self.out.exists())

    def test_historical_bug_control_without_torch_import(self):
        source=ROOT/'human-channel/tools/h5_cross_agent_joint.py'
        tree=ast.parse(source.read_text())
        function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='extract')
        module=ast.Module(body=[function],type_ignores=[])
        scope={'subprocess':subprocess}
        exec(compile(module,str(source),'exec'),scope)
        with patch.object(subprocess,'run',return_value=SimpleNamespace(returncode=7)) as mocked:
            self.assertIsNone(scope['extract']('authored-input','authored-output',0.4))
        self.assertFalse(mocked.call_args.kwargs['check'])
        # This proves the code path ignores a nonzero return, not that an old run failed.

    def test_duplicate_json_fields_are_rejected(self):
        for raw in (b'{"fps":"1","fps":"2"}', b'{"clip":{"id":"one","id":"two"}}'):
            with self.assertRaises(extract.Invalid): extract.decode(raw)

    def test_unknown_ledger_fields_are_rejected(self):
        ledger=self.run_plan(); ledger['safety']='supported'
        (self.out/'ledger.json').write_bytes(extract.encoded(ledger))
        with self.assertRaises(extract.Invalid): self.pairs()

    def test_unreadable_frame_entry_is_rejected(self):
        def directory(argv,**kwargs):
            result=self.fake(argv,**kwargs)
            Path(argv[-1] % 3).mkdir()
            return result
        self.blocked(self.run_plan(directory),'unreadable_frame')

    def test_source_symlink_is_rejected(self):
        source=Path(self.plan['clips'][0]['camera']['path'])
        saved=source.with_suffix('.original'); source.rename(saved); source.symlink_to(saved)
        self.blocked(self.run_plan(),'source_unreadable')


if __name__=='__main__':
    unittest.main()
