"""Authored resource controls, real tiny sandboxed workers, no model execution."""
import copy
import errno
import hashlib
import json
import os
from pathlib import Path
import signal
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
import supervise as s

WORKER='''import argparse,errno,json,os,socket,sys,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--worker',action='store_true');p.add_argument('--manifest');p.add_argument('--output');a=p.parse_args()
m=json.loads(Path(a.manifest).read_bytes());config=json.loads(Path(m['protocol']['path']).read_bytes());out=Path(a.output);out.mkdir()
(out/'started.json').write_text(json.dumps({'pid':os.getpid()}))
denied=False
try:
 c=socket.socket();c.settimeout(.1);c.connect(('127.0.0.1',9))
except OSError as exc:denied=exc.errno in (errno.EPERM,errno.EACCES)
finally:c.close()
mode=config['mode']
if mode=='filecap':
 with (out/'bounded.bin').open('wb') as f:
  for _ in range(32):f.write(b'x'*1024);f.flush()
if mode=='log':print('x'*4096,flush=True)
time.sleep(config['sleep'])
if mode=='exit':sys.exit(3)
if mode=='missing':sys.exit(0)
if mode=='mutate':Path(m['images'][0]['source']['path']).write_bytes(b'changed source')
(out/'result.json').write_text(json.dumps({'status':'complete','network_denied':denied,'fixture_only':True}))
'''


def write(path,obj):path.write_bytes(s.encode(obj))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def healthy_disk(path):return {'available_bytes':8*1024**3,'free_including_reserved_bytes':8*1024**3,'total_bytes':16*1024**3,'fragment_bytes':4096,'measurement':'authored injected capacity, not actual free space'}


class Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.owner=Path(self.temp.name).resolve();self.output=self.owner/'run'
        self.worker=self.owner/'worker.py';self.worker.write_text(WORKER)
        self.protocol=self.owner/'protocol.json';self.data=self.owner/'image.bin';self.data.write_bytes(b'authored source')
        self.manifest=self.owner/'manifest.json';self.capacity=self.owner/'capacity.json'
        self.plan={'artifact_id':'reiyah.resource-admission.capacity-plan','version':'0.1.0','free_disk_floor_bytes':s.FLOOR,
            'output_budget_bytes':1024**2,'margin_bytes':1024**2,'max_output_files':100,'preflight_samples':2,
            'sample_period_seconds':.1,'max_sample_gap_seconds':2}
        write(self.capacity,self.plan);self.config={'mode':'complete','sleep':.25};self.setup_manifest()
    def tearDown(self):self.temp.cleanup()
    def setup_manifest(self,wall=3,memory=3*1024**3):
        write(self.protocol,self.config)
        ptr=lambda p:{'path':str(p),'sha256':sha(p)}
        self.m={'protocol':ptr(self.protocol),'images':[{'id':'authored','source':ptr(self.data)}],'models':{},'limits':{'wall_seconds':wall,'memory_bytes':memory}}
        write(self.manifest,self.m)
    def run_guard(self,**kwargs):
        return s.supervise(self.owner,self.manifest,self.worker,sha(self.worker),sys.executable,self.output,self.capacity,sha(self.capacity),disk_provider=kwargs.pop('disk_provider',healthy_disk),**kwargs)
    def rows(self):return [json.loads(x) for x in self.output.with_suffix('.resources.jsonl').read_bytes().splitlines()]
    def test_complete_tiny_worker_network_denied_and_durable_samples(self):
        r=self.run_guard();self.assertEqual(r['status'],'complete',r);self.assertTrue(r['receipt_persisted']);self.assertEqual(r['returncode'],0)
        self.assertTrue(json.loads((self.output/'result.json').read_bytes())['network_denied'])
        rows=self.rows();self.assertEqual(rows[0]['phase'],'preflight');self.assertIn('before_launch',[v['phase'] for v in rows]);self.assertIn('running',[v['phase'] for v in rows]);self.assertEqual(rows[-1]['phase'],'final')
        self.assertEqual([x['sequence'] for x in rows],list(range(len(rows))));self.assertEqual(r['resource_samples_sha256'],sha(self.output.with_suffix('.resources.jsonl')))
        self.assertTrue(r['bindings_unchanged_after_worker']);self.assertEqual(r['observation_provider_mode'],'authored_injected')
        self.assertLess(sum(p.stat().st_size for p in self.owner.rglob('*') if p.is_file()),1024**2)
    def test_preflight_low_capacity_no_worker(self):
        def low(path):return {**healthy_disk(path),'available_bytes':s.FLOOR-1}
        r=self.run_guard(disk_provider=low);self.assertEqual(r['status'],'refused');self.assertFalse(r['worker_launched']);self.assertFalse(self.output.exists())
        self.assertEqual(r['trigger_sample']['disk']['available_bytes'],s.FLOOR-1);self.assertEqual(r['termination_reason'],'capacity_admission')
    def test_before_launch_capacity_refusal(self):
        count=0
        def disk(path):
            nonlocal count
            count+=1;return {**healthy_disk(path),'available_bytes':s.FLOOR-1 if count>=3 else 8*1024**3}
        r=self.run_guard(disk_provider=disk);self.assertFalse(r['worker_launched']);self.assertEqual(r['trigger_sample']['phase'],'before_launch')
    def test_running_disk_drop_exact_trigger_and_owned_kill(self):
        self.config['sleep']=2;self.setup_manifest();count=0
        def disk(path):
            nonlocal count
            count+=1;return {**healthy_disk(path),'available_bytes':s.FLOOR-17 if count>=4 else 8*1024**3}
        r=self.run_guard(disk_provider=disk);self.assertEqual(r['termination_reason'],'disk_floor');self.assertEqual(r['returncode'],-signal.SIGKILL)
        self.assertEqual(r['trigger_sample']['disk']['available_bytes'],s.FLOOR-17);self.assertEqual(r['trigger_sample']['phase'],'running')
        self.assertEqual(r['trigger_sample']['worker_pid'],r['worker_pid']);self.assertEqual(r['status'],'failed');self.assertNotIn('result_sha256',r)
    def test_running_remaining_budget_before_bare_floor(self):
        self.config['sleep']=2;self.setup_manifest();count=0
        def disk(path):
            nonlocal count
            count+=1;return {**healthy_disk(path),'available_bytes':s.FLOOR+1 if count>=4 else 8*1024**3}
        r=self.run_guard(disk_provider=disk);self.assertEqual(r['termination_reason'],'remaining_capacity');self.assertGreater(r['trigger_sample']['disk']['available_bytes'],s.FLOOR)
    def test_disk_error_is_unknown_not_zero(self):
        def bad(path):raise OSError('authored unavailable capacity')
        r=self.run_guard(disk_provider=bad);self.assertFalse(r['worker_launched']);self.assertIsNone(r['trigger_sample']['disk']);self.assertTrue(r['sample_errors'])
    def test_bool_budget_floor_and_gap_refused(self):
        for key,value in {'free_disk_floor_bytes':s.FLOOR-1,'output_budget_bytes':True,'margin_bytes':False,'preflight_samples':True,'sample_period_seconds':True,'max_sample_gap_seconds':False,'max_output_files':True}.items():
            p={**self.plan,key:value};write(self.capacity,p)
            with self.subTest(key=key),self.assertRaises(ValueError):self.run_guard()
        write(self.capacity,self.plan)
    def test_capacity_digest_refusal(self):
        with self.assertRaisesRegex(ValueError,'capacity plan digest'):
            s.supervise(self.owner,self.manifest,self.worker,sha(self.worker),sys.executable,self.output,self.capacity,'f'*64,disk_provider=healthy_disk)
    def test_preflight_gap_failure(self):
        count=0
        def slow(path):
            nonlocal count
            count+=1
            if count==1:time.sleep(.3)
            return healthy_disk(path)
        self.plan['max_sample_gap_seconds']=.2;write(self.capacity,self.plan)
        r=self.run_guard(disk_provider=slow);self.assertFalse(r['worker_launched']);self.assertIn('sample_duration',r['trigger_sample']['errors'])
    def test_running_rss_observation_error_kills(self):
        self.config['sleep']=2;self.setup_manifest()
        def bad(pid):raise OSError('authored ps failure')
        r=self.run_guard(rss_provider=bad);self.assertEqual(r['status'],'failed');self.assertEqual(r['termination_reason'],'resource_observation_failed');self.assertIsNone(r['peak_sampled_rss_bytes'])
    def test_memory_and_wall_limits(self):
        self.config['sleep']=2;self.setup_manifest(memory=1024)
        r=self.run_guard(rss_provider=lambda pid:2048);self.assertEqual(r['termination_reason'],'memory_limit');self.assertEqual(r['returncode'],-signal.SIGKILL)
        self.output=self.owner/'wall';self.setup_manifest(wall=.15)
        r=self.run_guard();self.assertEqual(r['termination_reason'],'wall_limit');self.assertEqual(r['returncode'],-signal.SIGKILL)
    def test_missing_terminal_not_complete(self):
        self.config['mode']='missing';self.setup_manifest();r=self.run_guard()
        self.assertEqual(r['status'],'failed');self.assertEqual(r['returncode'],0);self.assertNotIn('result_sha256',r)
    def test_source_mutation_after_launch_refused(self):
        self.config['mode']='mutate';self.setup_manifest();r=self.run_guard()
        self.assertEqual(r['status'],'failed');self.assertIn('bound input changed',r['error']);self.assertNotIn('result_sha256',r)
    def test_log_bound_scaled_mechanism(self):
        self.config.update(mode='log',sleep=2);self.setup_manifest()
        with patch.object(s,'MAX_LOG',1024):r=self.run_guard()
        self.assertEqual(r['termination_reason'],'log_budget');self.assertEqual(r['returncode'],-signal.SIGKILL)
    def test_fsize_kernel_bound_scaled_mechanism(self):
        self.config.update(mode='filecap',sleep=0);self.setup_manifest()
        with patch.object(s,'CHILD_FSIZE',4096):r=self.run_guard()
        self.assertEqual(r['status'],'failed');self.assertNotEqual(r['returncode'],0)
        self.assertLessEqual((self.output/'bounded.bin').stat().st_size,4096)
    def test_journal_write_failure_cannot_launch(self):
        with patch.object(s.Journal,'append',side_effect=OSError('authored durable journal write failure')):r=self.run_guard()
        self.assertFalse(r['worker_launched']);self.assertNotEqual(r['status'],'complete');self.assertIn('final_observation_error',r)
    def test_exclusive_artifacts_and_symlinks_refused(self):
        path=self.output.with_suffix('.resources.jsonl');path.write_bytes(b'preserve')
        with self.assertRaises(ValueError):self.run_guard()
        self.assertEqual(path.read_bytes(),b'preserve');path.unlink()
        self.output.symlink_to(self.owner/'missing')
        with self.assertRaises(ValueError):self.run_guard()
    def test_dangling_output_created_during_preflight_refused(self):
        count=0
        def disk(path):
            nonlocal count
            count+=1
            if count==3:self.output.symlink_to(self.owner/'missing')
            return healthy_disk(path)
        r=self.run_guard(disk_provider=disk);self.assertFalse(r['worker_launched']);self.assertNotEqual(r['status'],'complete')
    def test_output_budget_and_rounding_declared(self):
        self.plan['output_budget_bytes']=s.MAX_RECEIPT;write(self.capacity,self.plan);r=self.run_guard()
        self.assertFalse(r['worker_launched']);self.assertEqual(r['termination_reason'],'output_budget')
        self.assertEqual(r['trigger_sample']['allocation_rounding_allowance_bytes'],100*4095)
    def test_allocated_logical_measurement(self):
        self.output.mkdir();path=self.output/'tiny.bin';path.write_bytes(b'a')
        obj=s.output_observation(self.output,[]);self.assertEqual(obj['logical_bytes'],1);self.assertEqual(obj['allocated_bytes'],path.stat().st_blocks*512)
        self.assertIn('not measured',obj['measurement'])
    def test_existing_venv_entrypoint_not_resolved(self):
        entry=self.owner/'venv-python';entry.symlink_to(sys.executable)
        r=s.supervise(self.owner,self.manifest,self.worker,sha(self.worker),entry,self.output,self.capacity,sha(self.capacity),disk_provider=healthy_disk)
        self.assertEqual(r['status'],'complete',r);self.assertEqual(r['command'][3],str(entry))
    def test_standalone_harmless_probe_fixture(self):
        self.worker.write_bytes(Path(__file__).with_name('tiny_worker.py').read_bytes());r=self.run_guard()
        self.assertEqual(r['status'],'complete',r)
        result=json.loads((self.output/'result.json').read_bytes());self.assertEqual(result['model_inference_calls'],0);self.assertEqual(result['dataset_reads'],0);self.assertEqual(result['network_calls'],0)
    def test_receipt_fsync_failure_never_publishes_final(self):
        actual=s.os.fsync
        def fail_receipt(fd):
            if self.output.with_suffix('.process.pending').exists():raise OSError('authored receipt fsync failure')
            return actual(fd)
        with patch.object(s.os,'fsync',side_effect=fail_receipt):r=self.run_guard()
        self.assertEqual(r['status'],'failed');self.assertFalse(r['receipt_persisted'])
        self.assertFalse(self.output.with_suffix('.process.json').exists());self.assertTrue(self.output.with_suffix('.process.pending').exists())
    def test_pending_cleanup_failure_is_not_success(self):
        actual=Path.unlink;pending=self.output.with_suffix('.process.pending')
        def fail_pending(path,*args,**kwargs):
            if path==pending:raise OSError('authored pending cleanup failure')
            return actual(path,*args,**kwargs)
        with patch.object(Path,'unlink',new=fail_pending):r=self.run_guard()
        self.assertEqual(r['status'],'failed');self.assertFalse(r['receipt_persisted']);self.assertTrue(r['final_receipt_exists_after_persistence_error'])
        self.assertTrue(pending.exists());self.assertTrue(self.output.with_suffix('.process.json').exists())


if __name__=='__main__':unittest.main(verbosity=2)
