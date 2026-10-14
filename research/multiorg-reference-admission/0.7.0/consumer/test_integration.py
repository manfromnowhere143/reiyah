"""Authored full custody integration with unchanged numerical output checking.

Only numerical bind_inputs is replaced with the explicitly authored two-tile
fixture context. No empirical source is admitted by this control, and no model
or producer function is imported. All per-tile/global numerical checks run.
"""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import time
import types
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
OWNER=HERE.parent
SUPPORT=OWNER/'candidate/research/multiorg-reference-admission/0.6.0'
SUPERVISOR=OWNER/'candidate/research/multiorg-reference-admission/0.6.1/monitor/supervise.py'
for flag,name in (('--support','SUPPORT'),('--supervisor','SUPERVISOR')):
    if flag in sys.argv:
        i=sys.argv.index(flag);globals()[name]=Path(sys.argv[i+1]).resolve();del sys.argv[i:i+2]
sys.path.insert(0,str(SUPPORT))
import check_pair as numerical
from test_check_pair import packet
from test_resource_consumer import fixture
import resource_gate as gate


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,obj):p.write_bytes(gate.canonical(obj)+b'\n')
def load(p,name):
    mod=types.ModuleType(name);mod.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),mod.__dict__);return mod


class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.owner=Path(self.tmp.name).resolve();self.out=self.owner/'run';self.out.mkdir()
        self.ctx,_=packet(self.out);self.cdir=self.owner/'consumer';self.cdir.mkdir();self.ref=self.owner/'reference';self.ref.mkdir()
        for n in ('resource_gate.py','check_pair_resource.py'):shutil.copyfile(HERE/n,self.cdir/n)
        for n in ('check_pair.py','admit_tile.py','reference_core.py','reconstruct_inputs.py'):shutil.copyfile(SUPPORT/n,self.ref/n)
        shutil.copyfile(SUPPORT/'complete_pair.py',self.owner/'worker.py');shutil.copyfile(SUPERVISOR,self.owner/'supervise.py')
        self.g=load(self.cdir/'resource_gate.py','authored_gate')
        with patch.dict(sys.modules,{'resource_gate':self.g}):self.w=load(self.cdir/'check_pair_resource.py','authored_wrapper')
        self.protocol=self.owner/'protocol.json';write(self.protocol,{'authored_only':True})
        self.manifest=self.owner/'manifest.json';write(self.manifest,{'protocol':{'path':str(self.protocol),'sha256':sha(self.protocol)},'images':[],'models':{},'limits':{'wall_seconds':600,'memory_bytes':3221225472}})
        self.ctx.update(manifest=json.loads(self.manifest.read_bytes()),manifest_sha256=sha(self.manifest),protocol_sha256=sha(self.protocol),runner_sha256=gate.WORKER,input_reconstruction={'status':'authored fixture context only; no empirical image admitted'})
        result=json.loads((self.out/'result.json').read_bytes());result.update(manifest=self.ctx['manifest'],manifest_sha256=self.ctx['manifest_sha256'],protocol_sha256=self.ctx['protocol_sha256'],runner_sha256=gate.WORKER)
        for observation in result['observations']:
            p=self.out/observation['file'];obj=json.loads(p.read_bytes());obj['protocol_sha256']=sha(self.protocol);write(p,obj);observation.update(sha256=sha(p),bytes=p.stat().st_size)
        write(self.out/'result.json',result)
        self.receipt,self.outer,self.rows,_=fixture();self.capacity=self.owner/'capacity.json';write(self.capacity,self.receipt['capacity_plan'])
        # Small authored audit uses existing read-only declared runtime files;
        # it does not claim the full historical distribution census was rerun.
        venv=Path(sys.prefix);cfg=venv/'pyvenv.cfg'
        import importlib.metadata
        record=Path(importlib.metadata.distribution('numpy')._path)/'RECORD';interpreter=Path(sys.executable).resolve()
        pin=lambda p:{'sha256':sha(p),'bytes':p.stat().st_size}
        audit={'at':'2001-09-09T01:46:39+00:00','status':'passed','venv':str(venv),'python_entrypoint':str(Path(sys.executable).absolute()),'python_resolved_identity':str(interpreter),
            'record_count':1,'hashed_entries_checked':1,'records':[{'path':str(record.relative_to(venv)),'sha256':sha(record)}],
            'checked_files':[{'path':str(cfg.relative_to(venv)),**pin(cfg),'record_match':True}],
            'excluded_record_entries':[{'path':str(record.relative_to(venv)),'reason':'unhashed RECORD entry'}],
            'runtime_pins':{str(interpreter):pin(interpreter),str(cfg):pin(cfg)},'unrecorded_files':[],'failures':[],'limitations':'Authored reduced audit fixture, not the empirical runtime census.'}
        self.before=self.owner/'before.json';self.after=self.owner/'after.json';write(self.before,audit);write(self.after,{**audit,'at':'2001-09-09T01:46:42+00:00'})
        self.cp=self.owner/'contract.json';self.fp=self.owner/'freeze.json';self.op=self.owner/'outer.json';self.stdout=self.owner/'stdout';self.stderr=self.owner/'stderr';self.stderr.write_bytes(b'')
        sourcepaths={'supervisor':self.owner/'supervise.py','worker':self.owner/'worker.py','numerical_checker':self.ref/'check_pair.py','manifest':self.manifest,'protocol':self.protocol,'capacity_plan':self.capacity,'runtime_before':self.before}
        self.contract={'artifact_id':'reiyah.multiorg.resource-consumer-contract','version':'0.1.0','sources':{k:{'path':str(v),'sha256':sha(v)} for k,v in sourcepaths.items()},
            'paths':{k:str(v) for k,v in {'output':self.out,'outer':self.op,'stdout':self.stdout,'stderr':self.stderr,'runtime_after':self.after,'freeze':self.fp}.items()},
            'python_entrypoint':str(Path(sys.executable).absolute()),'outer_wall_limit_seconds':660}
        write(self.cp,self.contract)
        pins=[*sourcepaths.values(),self.cp,self.cdir/'resource_gate.py',self.cdir/'check_pair_resource.py',self.ref/'admit_tile.py',self.ref/'reference_core.py',self.ref/'reconstruct_inputs.py']
        write(self.fp,{'bindings':{str(p.relative_to(self.owner)):{'sha256':sha(p),'bytes':p.stat().st_size} for p in pins}})
        self.policy=self.out.with_suffix('.sandbox.sb');self.policy.write_bytes(b'(version 1)\n(allow default)\n(deny network*)\n');self.log=self.out.with_suffix('.log');self.log.write_bytes(b'')
        python=self.contract['python_entrypoint']
        self.outer.update(command=[python,'-B',str(sourcepaths['supervisor']),'--owner',str(self.owner),'--manifest',str(self.manifest),'--runner',str(sourcepaths['worker']),
            '--runner-sha256',gate.WORKER,'--python',python,'--output',str(self.out),'--capacity-plan',str(self.capacity),'--capacity-plan-sha256',sha(self.capacity)],
            freeze_sha256=sha(self.fp),manifest_sha256=sha(self.manifest),worker_log_sha256=sha(self.log),worker_log_bytes=0)
        self.receipt.update(manifest_sha256=sha(self.manifest),capacity_plan_sha256=sha(self.capacity),result_sha256=sha(self.out/'result.json'),
            command=['/usr/bin/sandbox-exec','-f',str(self.policy),python,'-B',str(sourcepaths['worker']),'--worker','--manifest',str(self.manifest),'--output',str(self.out)])
        self.publish()
    def tearDown(self):self.tmp.cleanup()
    def publish(self):
        journal=self.out.with_suffix('.resources.jsonl');rp=self.out.with_suffix('.process.json')
        if rp.exists():rp.unlink()
        prefix=b''.join(gate.canonical(r)+b'\n' for r in self.rows[:-1]);journal.write_bytes(prefix)
        current=self.w.final_inventory(self.out,[journal,self.policy,self.log],time.monotonic()+5)
        self.rows[-1]['output'].update({k:current[k] for k in ('file_count','logical_bytes','allocated_bytes')})
        r=self.rows[-1];plan=self.receipt['capacity_plan'];budget=r['prospective_allocation_budget_bytes'];remaining=max(0,budget-max(current['logical_bytes'],current['allocated_bytes']))
        r.update(remaining_allocation_budget_bytes=remaining,required_available_bytes=plan['free_disk_floor_bytes']+plan['margin_bytes']+remaining)
        journal.write_bytes(prefix+gate.canonical(r)+b'\n');self.receipt['resource_samples_sha256']=sha(journal)
        write(rp,self.receipt);write(self.stdout,self.receipt);self.outer.update(stdout_sha256=sha(self.stdout),stderr_sha256=sha(self.stderr));write(self.op,self.outer)
    def check(self):
        original=self.w.bound_module
        def authored_binding(path,sha,name):
            module=original(path,sha,name)
            def fixture_context(*args):return self.ctx
            module.bind_inputs=fixture_context
            return module
        with patch.object(self.w,'bound_module',side_effect=authored_binding):
            return self.w.execute(self.owner,self.cp,sha(self.cp),sha(self.fp),time.monotonic()+30)
    def test_full_wrapper_and_real_unchanged_numeric_fixture(self):
        result=self.check();self.assertEqual(result['complete_pairs'],1);self.assertEqual(result['numerical_result']['raw_array_files_checked'],70)
        self.assertEqual([r['analysis_count'] for r in result['numerical_result']['models']],[4,2]);self.assertEqual(result['numerical_checker_sha256'],gate.NUMERICAL)
        self.assertEqual(result['consumer_sha256'],sha(self.cdir/'check_pair_resource.py'))
    def test_outer_failure_blocks_before_numerical_import(self):
        self.outer['returncode']=1;write(self.op,self.outer)
        with patch.object(self.w,'bound_module',side_effect=AssertionError('numerical checker must not run')),self.assertRaisesRegex(ValueError,'outer successful'):
            self.w.execute(self.owner,self.cp,sha(self.cp),sha(self.fp),time.monotonic()+30)
    def test_same_length_log_change_is_bound(self):
        self.log.write_bytes(b'one');self.outer.update(worker_log_sha256=sha(self.log),worker_log_bytes=3);self.publish();self.log.write_bytes(b'two')
        with self.assertRaisesRegex(ValueError,'worker_log_sha256'):self.check()
    def test_numerical_raw_tamper_is_not_just_metadata_admission(self):
        p=next((self.out/'raw').glob('*.npy'));raw=bytearray(p.read_bytes());raw[-1]^=1;p.write_bytes(raw)
        with self.assertRaisesRegex(ValueError,'digest'):self.check()
    def test_extra_output_file_breaks_final_inventory(self):
        (self.out/'unreported.txt').write_bytes(b'unreported')
        with self.assertRaisesRegex(ValueError,'final logical'):self.check()


if __name__=='__main__':unittest.main(verbosity=2)
