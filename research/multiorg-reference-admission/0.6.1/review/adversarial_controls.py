#!/usr/bin/env python3
"""Separately authored resource-guard controls. No model, image or empirical output access."""
import argparse
import hashlib
import importlib.util
import json
import io
import os
from contextlib import redirect_stdout
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

GUARD = None
ARCHIVE = None
REPORT = None

WORKER = '''import argparse,json,pathlib,time
p=argparse.ArgumentParser();p.add_argument('--worker',action='store_true');p.add_argument('--manifest');p.add_argument('--output');a=p.parse_args()
m=json.loads(pathlib.Path(a.manifest).read_text());mode=json.loads(pathlib.Path(m['protocol']['path']).read_text())['mode']
out=pathlib.Path(a.output);out.mkdir()
time.sleep(.35)
if mode!='missing_terminal':(out/'result.json').write_text(json.dumps({'status':'complete','authored_fixture':True}))
'''


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


class Controls(unittest.TestCase):
    def setUp(self):
        self.root=Path(tempfile.mkdtemp(prefix=self._testMethodName+'-',dir=ARCHIVE))
        self.output=self.root/'attempt'
        self.protocol=self.root/'protocol.json';self.protocol.write_text(json.dumps({'mode':'normal'}))
        self.worker=self.root/'fixture_worker.py';self.worker.write_text(WORKER)
        self.manifest=self.root/'manifest.json'
        self.manifest.write_text(json.dumps({'protocol':{'path':str(self.protocol),'sha256':sha(self.protocol)},'images':[{'id':'authored fixture','source':{'path':str(self.protocol),'sha256':sha(self.protocol)}}],'models':{},'limits':{'wall_seconds':5,'memory_bytes':64*1024**2}}))
        self.capacity=self.root/'capacity.json'
        self.plan={'artifact_id':'reiyah.resource-admission.capacity-plan','version':'0.1.0','free_disk_floor_bytes':4*1024**3,'output_budget_bytes':16*1024**2,'margin_bytes':1024**2,'preflight_samples':2,'sample_period_seconds':.1,'max_sample_gap_seconds':2,'max_output_files':1000}
        self.save_plan()
    def save_plan(self):self.capacity.write_text(json.dumps(self.plan))
    def disk(self,path):return {'available_bytes':16*1024**3,'free_including_reserved_bytes':20*1024**3,'total_bytes':40*1024**3,'fragment_bytes':4096,'measurement':'authored fixture; not actual storage'}
    def run_case(self,**kw):
        return GUARD.supervise(self.root,self.manifest,self.worker,sha(self.worker),sys.executable,self.output,self.capacity,sha(self.capacity),disk_provider=kw.pop('disk_provider',self.disk),rss_provider=kw.pop('rss_provider',lambda pid:1024),**kw)
    def assert_refused(self,r):self.assertEqual(r['status'],'refused');self.assertFalse(r['worker_launched']);self.assertIsNone(r['worker_pid'])
    def rows(self):return [json.loads(line) for line in self.output.with_suffix('.resources.jsonl').read_text().splitlines()]
    def fake(self):
        out=self.output
        class Process:
            pid=99999999
            returncode=None
            killed=False
            def poll(this):return this.returncode
            def kill(this):this.killed=True;this.returncode=-9
            def wait(this,timeout=None):return this.returncode
        return Process()

    def test_boolean_budget_fields_refused(self):
        for key in self.plan:
            if key in ('artifact_id','version'):continue
            with self.subTest(key=key):
                saved=self.plan[key];self.plan[key]=True;self.save_plan()
                with self.assertRaises(ValueError):GUARD.capacity_plan(self.capacity,sha(self.capacity))
                self.plan[key]=saved
        self.save_plan()

    def test_duplicate_capacity_key_refused(self):
        text=self.capacity.read_text();self.capacity.write_text(text[:-1]+',"margin_bytes":1}')
        with self.assertRaises(ValueError):GUARD.capacity_plan(self.capacity,sha(self.capacity))

    def test_nonfinite_and_negative_budgets_refused(self):
        for key,value in [('sample_period_seconds',float('nan')),('max_sample_gap_seconds',float('inf')),('output_budget_bytes',-1),('free_disk_floor_bytes',0)]:
            with self.subTest(key=key):
                previous=self.plan[key];self.plan[key]=value;self.save_plan()
                with self.assertRaises(ValueError):GUARD.capacity_plan(self.capacity,sha(self.capacity))
                self.plan[key]=previous

    def test_purgeable_or_reserved_capacity_not_counted(self):
        def provider(path):
            value=self.disk(path);value['available_bytes']=0;return value
        result=self.run_case(disk_provider=provider);self.assert_refused(result)
        self.assertEqual(result['trigger_sample']['disk']['available_bytes'],0)
        self.assertGreater(result['trigger_sample']['disk']['free_including_reserved_bytes'],self.plan['free_disk_floor_bytes'])

    def test_disk_sample_failure_prevents_launch(self):
        def provider(path):raise OSError('authored unavailable capacity')
        result=self.run_case(disk_provider=provider);self.assert_refused(result)
        self.assertIsNone(result['trigger_sample']['disk']);self.assertTrue(result['sample_errors'])

    def test_malformed_boolean_disk_observation_prevents_launch(self):
        def provider(path):
            value=self.disk(path);value['available_bytes']=True;return value
        result=self.run_case(disk_provider=provider);self.assert_refused(result)
        self.assertIsNone(result['trigger_sample']['disk'])

    def test_preexisting_log_is_not_overwritten(self):
        p=self.output.with_suffix('.log');p.write_text('retain these bytes')
        with self.assertRaises(ValueError):self.run_case()
        self.assertEqual(p.read_text(),'retain these bytes')

    def test_dangling_output_symlink_refused(self):
        self.output.symlink_to(self.root/'absent')
        with self.assertRaises(ValueError):self.run_case()
        self.assertTrue(self.output.is_symlink());self.assertFalse((self.root/'absent').exists())

    def test_output_collision_during_preflight_refused(self):
        calls=0
        def provider(path):
            nonlocal calls
            calls+=1
            if calls==2:self.output.mkdir()
            return self.disk(path)
        result=self.run_case(disk_provider=provider);self.assert_refused(result)
        self.assertTrue(self.output.is_dir())

    def test_log_open_failure_does_not_launch(self):
        original=Path.open
        def opened(path,*args,**kw):
            if path==self.output.with_suffix('.log') and args and args[0]=='xb':raise OSError('authored log write failure')
            return original(path,*args,**kw)
        with patch.object(Path,'open',opened):result=self.run_case()
        self.assert_refused(result);self.assertIn('authored log',result['error'])

    def test_journal_failure_before_launch_refuses(self):
        with patch.object(GUARD.Journal,'append',side_effect=OSError('authored journal failure')):result=self.run_case()
        self.assert_refused(result);self.assertIsNotNone(result['termination_reason'])

    def test_journal_failure_while_running_stops_worker(self):
        process=self.fake();original=GUARD.Journal.append
        def append(journal,row):
            if row['phase']=='running':raise OSError('authored running journal failure')
            return original(journal,row)
        with patch.object(GUARD.subprocess,'Popen',return_value=process),patch.object(GUARD.Journal,'append',append):result=self.run_case()
        self.assertEqual(result['status'],'failed');self.assertTrue(process.killed);self.assertIn('authored running journal',result['error'])

    def test_resource_stop_and_exit_zero_stays_failed(self):
        process=self.fake();calls=0
        def disk(path):
            nonlocal calls
            calls+=1;value=self.disk(path)
            if calls==4:value['available_bytes']=0
            return value
        def rss(pid):process.returncode=0;return 1024
        with patch.object(GUARD.subprocess,'Popen',return_value=process):result=self.run_case(disk_provider=disk,rss_provider=rss)
        self.assertEqual(result['returncode'],0);self.assertEqual(result['status'],'failed');self.assertIsNotNone(result['termination_reason'])
        self.assertEqual(result['trigger_sample']['disk']['available_bytes'],0)

    def test_live_rss_failure_stops_worker(self):
        process=self.fake()
        def rss(pid):raise OSError('authored RSS failure')
        with patch.object(GUARD.subprocess,'Popen',return_value=process):result=self.run_case(rss_provider=rss)
        self.assertEqual(result['status'],'failed');self.assertTrue(process.killed)
        self.assertEqual(result['trigger_sample']['rss_state'],'error_live_worker');self.assertIsNone(result['peak_sampled_rss_bytes'])

    def test_exit_between_polls_not_fabricated_as_zero_rss(self):
        process=self.fake();calls=0
        def rss(pid):
            nonlocal calls
            calls+=1
            if calls==1:return 1024
            self.output.mkdir();(self.output/'result.json').write_text(json.dumps({'status':'complete','authored':True}))
            process.returncode=0;raise OSError('owned worker exited')
        with patch.object(GUARD.subprocess,'Popen',return_value=process):result=self.run_case(rss_provider=rss)
        self.assertEqual(result['status'],'complete');self.assertEqual(result['peak_sampled_rss_bytes'],1024)
        rows=self.rows();exited=[x for x in rows if x['rss_state']=='worker_exited_during_observation'];self.assertEqual(len(exited),1);self.assertIsNone(exited[0]['rss_bytes']);self.assertEqual(exited[0]['errors'],[])

    def test_missing_terminal_is_not_complete(self):
        self.protocol.write_text(json.dumps({'mode':'missing_terminal'}))
        m=json.loads(self.manifest.read_text());m['protocol']['sha256']=sha(self.protocol);m['images'][0]['source']['sha256']=sha(self.protocol);self.manifest.write_text(json.dumps(m))
        result=self.run_case();self.assertEqual(result['returncode'],0);self.assertEqual(result['status'],'failed');self.assertNotIn('result_sha256',result)

    def test_receipt_fsync_failure_never_publishes_final_receipt(self):
        original_fsync=GUARD.os.fsync;original_supervise=GUARD.supervise
        receipt=self.output.with_suffix('.process.json');pending=self.output.with_suffix('.process.pending')
        def fsync(fd):
            if pending.exists() and os.fstat(fd).st_ino==pending.stat().st_ino:raise OSError('authored receipt fsync failure after bytes')
            return original_fsync(fd)
        def supervise(*args,**kw):return original_supervise(*args,**kw,disk_provider=self.disk,rss_provider=lambda pid:1024)
        argv=['supervise.py','--owner',str(self.root),'--manifest',str(self.manifest),'--runner',str(self.worker),'--runner-sha256',sha(self.worker),'--python',sys.executable,'--output',str(self.output),'--capacity-plan',str(self.capacity),'--capacity-plan-sha256',sha(self.capacity)]
        stdout=io.StringIO()
        with patch.object(GUARD.os,'fsync',fsync),patch.object(GUARD,'supervise',supervise),patch.object(sys,'argv',argv),redirect_stdout(stdout):code=GUARD.main()
        returned=json.loads(stdout.getvalue());unaccepted=json.loads(pending.read_text())
        self.assertEqual(code,1);self.assertEqual(returned['status'],'failed');self.assertFalse(returned['receipt_persisted'])
        self.assertFalse(receipt.exists());self.assertEqual(unaccepted['status'],'complete')
        self.assertIn('authored receipt fsync failure',returned['receipt_persistence_error'])

    def test_final_receipt_publication_collision_never_overwrites(self):
        final=self.output.with_suffix('.process.json');original=GUARD.os.link
        def link(src,dst,*args,**kw):
            if Path(dst)==final:final.write_text('authored competing final receipt')
            return original(src,dst,*args,**kw)
        with patch.object(GUARD.os,'link',link):result=self.run_case()
        self.assertEqual(result['status'],'failed');self.assertFalse(result['receipt_persisted'])
        self.assertEqual(final.read_text(),'authored competing final receipt')

    def test_slow_observation_refuses_before_launch(self):
        self.plan['max_sample_gap_seconds']=.1;self.save_plan()
        def disk(path):time.sleep(.12);return self.disk(path)
        result=self.run_case(disk_provider=disk);self.assert_refused(result)
        self.assertIn('sample_duration',result['trigger_sample']['errors'])

    def test_receipt_write_failure_returns_non_success(self):
        original=Path.open
        def opened(path,*args,**kw):
            if path==self.output.with_suffix('.process.pending') and args and args[0]=='xb':raise OSError('authored receipt write failure')
            return original(path,*args,**kw)
        with patch.object(Path,'open',opened):result=self.run_case()
        self.assertFalse(result['receipt_persisted']);self.assertEqual(result['status'],'failed');self.assertFalse(self.output.with_suffix('.process.json').exists())


def main():
    global GUARD,ARCHIVE,REPORT
    parser=argparse.ArgumentParser();parser.add_argument('--supervisor',required=True);parser.add_argument('--archive',required=True);parser.add_argument('--report',required=True);args=parser.parse_args()
    source=Path(args.supervisor);ARCHIVE=Path(args.archive);ARCHIVE.mkdir(parents=True,exist_ok=False);REPORT=Path(args.report)
    spec=importlib.util.spec_from_file_location('resource_guard_under_review',source);GUARD=importlib.util.module_from_spec(spec);spec.loader.exec_module(GUARD)
    start=time.monotonic();suite=unittest.defaultTestLoader.loadTestsFromTestCase(Controls);result=unittest.TextTestRunner(verbosity=2).run(suite)
    report={'artifact_id':'reiyah.resource-admission.adversarial-controls','version':'0.1.0','supervisor_sha256':sha(source),'controls_sha256':sha(Path(__file__)),'cases_run':result.testsRun,'status':'passed' if result.wasSuccessful() else 'failed','failures':[str(x[0])+': '+x[1] for x in result.failures],'errors':[str(x[0])+': '+x[1] for x in result.errors],'wall_seconds':time.monotonic()-start,'scope':'Authored tiny workers and injected providers/process races; no model/image inputs, inference or empirical output access. Retained test fixtures remain private.','network':'No requested network operation; production worker enters unchanged network-denial policy.'}
    REPORT.write_text(json.dumps(report,indent=2)+'\n');return 0 if result.wasSuccessful() else 1


if __name__=='__main__':raise SystemExit(main())
