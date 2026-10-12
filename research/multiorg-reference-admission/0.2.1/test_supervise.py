"""Authored synthetic workers only; no model/image access or network requests."""
import hashlib
import json
import os
import shutil
from pathlib import Path
import sys
import tempfile
import unittest
import venv
import supervise

WORKER = '''import argparse,json,pathlib,socket,time,sys
p=argparse.ArgumentParser();p.add_argument('--worker',action='store_true');p.add_argument('--manifest');p.add_argument('--output');a=p.parse_args()
m=json.loads(pathlib.Path(a.manifest).read_text());mode=json.loads(pathlib.Path(m['protocol']['path']).read_text())['mode']
if mode=='timeout':time.sleep(30)
if mode=='memory':
 data=bytearray(100*1024*1024)
 for i in range(0,len(data),4096):data[i]=1
 time.sleep(30)
if mode=='failure':print('retained intentional failure',flush=True);sys.exit(7)
r={'status':'complete','synthetic':True,'python_prefix':sys.prefix}
if mode=='network':
 try:
  s=socket.socket();s.connect(('127.0.0.1',9));r['network_denied']=False
 except PermissionError:r['network_denied']=True
 assert r['network_denied'] is True
out=pathlib.Path(a.output);out.mkdir();(out/'result.json').write_text(json.dumps(r))
time.sleep(.1)
'''


class Controls(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='reiyah-supervisor-control-')
        self.owner = Path(self.tmp.name)
        self.worker = self.owner/'worker.py'; self.worker.write_text(WORKER)
        self.sha = hashlib.sha256(self.worker.read_bytes()).hexdigest()

    def tearDown(self):
        archive=os.environ.get("REIYAH_SUPERVISOR_CONTROL_ARCHIVE")
        if archive:
            destination=Path(archive)/self._testMethodName
            destination.parent.mkdir(parents=True,exist_ok=True)
            shutil.copytree(self.owner,destination)
        self.tmp.cleanup()

    def run_case(self, mode, wall=5, memory=268435456, sha=None, python=None):
        protocol=self.owner/'protocol.json';protocol.write_text(json.dumps({'mode':mode}))
        manifest=self.owner/'manifest.json';manifest.write_text(json.dumps({
            'protocol':{'path':str(protocol),'sha256':hashlib.sha256(protocol.read_bytes()).hexdigest()},
            'images':[],'models':{},'limits':{'wall_seconds':wall,'memory_bytes':memory}}))
        result=supervise.supervise(self.owner,manifest,self.worker,sha or self.sha,python or sys.executable,
                                   self.owner/'output',sample_seconds=.025,free_disk_floor=0)
        self.assertEqual(json.loads((self.owner/'output.process.json').read_text()),result)
        pid=result['worker_pid']
        if pid:
            with self.assertRaises(ProcessLookupError):os.kill(pid,0)
        return result

    def test_normal_completion_and_rss(self):
        r=self.run_case('normal');self.assertEqual(r['status'],'complete');self.assertEqual(r['returncode'],0)
        self.assertIsNone(r['termination_reason']);self.assertGreater(r['peak_sampled_rss_bytes'],0)

    def test_wall_timeout_kills_exact_worker(self):
        r=self.run_case('timeout',wall=.2);self.assertEqual(r['status'],'failed')
        self.assertEqual(r['termination_reason'],'wall_limit');self.assertEqual(r['returncode'],-9)

    def test_memory_threshold_kills_exact_worker(self):
        r=self.run_case('memory',memory=40*1024*1024);self.assertEqual(r['status'],'failed')
        self.assertEqual(r['termination_reason'],'memory_limit');self.assertGreater(r['peak_sampled_rss_bytes'],40*1024*1024)

    def test_worker_network_denied_host_observer_works(self):
        r=self.run_case('network');self.assertEqual(r['status'],'complete')
        self.assertTrue(json.loads((self.owner/'output/result.json').read_text())['network_denied'])

    def test_worker_exit_failure_retained(self):
        r=self.run_case('failure');self.assertEqual(r['status'],'failed');self.assertEqual(r['returncode'],7)
        self.assertEqual(r['termination_reason'],'worker_exit')
        self.assertIn('retained intentional failure',(self.owner/'output.log').read_text())

    def test_symlinked_environment_entrypoint_preserved(self):
        env=self.owner/'env'
        venv.EnvBuilder(with_pip=False).create(env)
        interpreter=env/'bin/python'
        r=self.run_case('normal',python=interpreter)
        self.assertEqual(r['status'],'complete')
        self.assertEqual(r['command'][3],str(interpreter))
        body=json.loads((self.owner/'output/result.json').read_text())
        self.assertEqual(Path(body['python_prefix']).resolve(),env.resolve())

    def test_hash_tamper_rejected_before_spawn(self):
        r=self.run_case('normal',sha='0'*64);self.assertEqual(r['status'],'failed')
        self.assertIsNone(r['worker_pid']);self.assertIn('digest mismatch',r['error'])


if __name__=='__main__':unittest.main(verbosity=2)
