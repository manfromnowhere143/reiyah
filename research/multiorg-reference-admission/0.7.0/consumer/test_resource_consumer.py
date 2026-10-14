"""Authored consumer controls; no empirical records, models or producer imports."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import time
import unittest
import resource_gate as g
import check_pair_resource as wrapper


def fixture():
    plan={'artifact_id':'reiyah.resource-admission.capacity-plan','version':'0.1.0','free_disk_floor_bytes':4*1024**3,'output_budget_bytes':1024**2,
        'margin_bytes':1024**2,'max_output_files':100,'preflight_samples':2,'sample_period_seconds':.1,'max_sample_gap_seconds':2}
    rows=[]
    for i,(phase,elapsed) in enumerate(zip(['preflight','preflight','before_launch','running','running','final'],[0.,.2,.21,.23,.43,.6])):
        pre=phase in ('preflight','before_launch');observed=phase=='running';budget=plan['output_budget_bytes']+100*4095;remaining=budget-4096
        row={'sequence':i,'phase':phase,'unix_time_ns':10**18+i*10**8,'elapsed_seconds':elapsed,'worker_elapsed_seconds':None if pre else (.35 if phase=='final' else elapsed-.22),
            'worker_pid':None if pre else 123,'disk':{'available_bytes':8*1024**3,'free_including_reserved_bytes':9*1024**3,'total_bytes':16*1024**3,'fragment_bytes':4096,'measurement':'statvfs_f_bavail_times_f_frsize; no purgeable estimate'},
            'output':{'file_count':3,'logical_bytes':1000,'allocated_bytes':4096,'walk_seconds':.0001,'measurement':'authored summed block observation'},
            'rss_bytes':1000000 if observed else None,'rss_state':'not_launched' if pre else 'observed' if observed else 'worker_exited_before_observation',
            'errors':[],'gap_seconds':None if i==0 else elapsed-rows[-1]['elapsed_seconds'],'duration_seconds':.001,
            'prospective_allocation_budget_bytes':budget,'allocation_rounding_allowance_bytes':409500,'remaining_allocation_budget_bytes':remaining,
            'required_available_bytes':plan['free_disk_floor_bytes']+plan['margin_bytes']+(budget if pre else remaining)}
        rows.append(row)
    receipt={k:'authored scope' for k in g.RECEIPT_KEYS}
    receipt.update(artifact_id='reiyah.resource-admission.supervisor-receipt',version='0.1.0',status='complete',returncode=0,termination_reason=None,
        worker_pid=123,worker_launched=True,peak_sampled_rss_bytes=1000000,runner_sha256=g.WORKER,manifest_sha256='1'*64,capacity_plan_sha256='2'*64,
        supervisor_sha256=g.SUPERVISOR,policy_sha256=g.POLICY,capacity_plan=plan,observation_provider_mode='system',network_boundary='worker_only_host_observer_outside_sandbox',
        bindings_verified_before_launch=True,bindings_unchanged_after_worker=True,sample_journal='run.resources.jsonl',log='run.log',sample_errors=[],sampling_gaps=[],
        resource_caps=g.CAPS,admission_required_available_bytes=plan['free_disk_floor_bytes']+plan['margin_bytes']+rows[-1]['prospective_allocation_budget_bytes'],
        limits={'wall_seconds':600,'memory_bytes':3221225472},command=['authored worker command'],result_sha256='3'*64,resource_samples_sha256='4'*64,
        sample_count=6,wall_seconds=.7,worker_wall_seconds=.35,receipt_persisted=True)
    outer={'artifact_id':'reiyah.resource-admission.outer-execution','version':'0.1.0','returncode':0,'timed_out':False,'wall_seconds':1.,'command':['authored supervisor command'],
        'freeze_sha256':'5'*64,'supervisor_sha256':g.SUPERVISOR,'manifest_sha256':'1'*64,'stdout_sha256':'6'*64,'stderr_sha256':'7'*64,'worker_log_sha256':'8'*64,'worker_log_bytes':0}
    expected={'outer_wall_limit_seconds':660,'outer':{k:outer[k] for k in ('command','freeze_sha256','supervisor_sha256','manifest_sha256','stdout_sha256','stderr_sha256','worker_log_sha256','worker_log_bytes')},
        'receipt':{k:receipt[k] for k in ('manifest_sha256','capacity_plan_sha256','capacity_plan','result_sha256','resource_samples_sha256','sample_journal','log','command','limits')}}
    return copy.deepcopy((receipt,outer,rows,expected))


class GateTests(unittest.TestCase):
    def setUp(self):self.receipt,self.outer,self.rows,self.expected=fixture()
    def check(self):return g.validate_success(self.receipt,copy.deepcopy(self.receipt),self.outer,self.rows,self.expected)
    def test_positive_authored_complete_records(self):self.assertEqual(self.check()['status'],'resource_receipt_and_journal_checked')
    def test_complete_file_with_nonzero_outer_exit_refused(self):
        self.outer['returncode']=1
        with self.assertRaisesRegex(ValueError,'outer successful'):self.check()
    def test_returned_retained_receipts_must_match(self):
        returned=copy.deepcopy(self.receipt);returned['receipt_persisted']=False
        with self.assertRaisesRegex(ValueError,'returned'):g.validate_success(self.receipt,returned,self.outer,self.rows,self.expected)
    def test_false_boolean_exit_and_missing_fields(self):
        for target,key in ((self.outer,'returncode'),(self.receipt,'returncode'),(self.rows[0],'sequence')):
            old=target[key];target[key]=False
            with self.subTest(key=key),self.assertRaises(ValueError):self.check()
            target[key]=old
        del self.receipt['receipt_persisted']
        with self.assertRaisesRegex(ValueError,'schema'):self.check()
    def test_injected_provider_or_wrong_worker_cannot_self_consistently_pass(self):
        for key,value in [('observation_provider_mode','authored_injected'),('runner_sha256','0'*64),('supervisor_sha256','0'*64),('termination_reason','disk_floor')]:
            old=self.receipt[key];self.receipt[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):self.check()
            self.receipt[key]=old
    def test_truncated_duplicate_and_nonfinite_journal(self):
        raw=b''.join(g.canonical(r)+b'\n' for r in self.rows)
        self.assertEqual(len(g.journal_rows(raw)),6)
        for wrong in (raw[:-1],b'{"a":1,"a":2}\n'*4,b'{"x":NaN}\n'*4):
            with self.subTest(raw=wrong[:40]),self.assertRaises(ValueError):g.journal_rows(wrong)
    def test_missing_reordered_duplicated_samples(self):
        old=copy.deepcopy(self.rows)
        for mode in ('missing','order','duplicate','phase'):
            self.rows=copy.deepcopy(old)
            if mode=='missing':self.rows.pop(3)
            elif mode=='order':self.rows[3],self.rows[4]=self.rows[4],self.rows[3]
            elif mode=='duplicate':self.rows[4]=copy.deepcopy(self.rows[3])
            else:self.rows[3]['phase']='stop'
            with self.subTest(mode=mode),self.assertRaises(ValueError):self.check()
    def test_bounds_unknowns_and_peak_mismatch(self):
        old=copy.deepcopy(self.rows)
        for key,value in [('gap_seconds',3),('duration_seconds',3),('rss_bytes',None),('errors',['disk unavailable'])]:
            self.rows=copy.deepcopy(old);self.rows[3][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):self.check()
        self.rows=old;self.receipt['peak_sampled_rss_bytes']=1000001
        with self.assertRaisesRegex(ValueError,'peak'):self.check()
    def test_worker_clock_cannot_begin_before_prelaunch(self):
        for row in self.rows[3:5]:row['worker_elapsed_seconds']=row['elapsed_seconds']-.1
        with self.assertRaisesRegex(ValueError,'began before'):self.check()
    def test_resource_budget_cannot_be_renamed_to_success(self):
        self.rows[0]['disk']['available_bytes']=4*1024**3+1
        with self.assertRaisesRegex(ValueError,'capacity'):self.check()
    def test_wrong_sample_arithmetic_and_pid(self):
        self.rows[3]['required_available_bytes']-=1
        with self.assertRaisesRegex(ValueError,'arithmetic'):self.check()
        self.rows[3]['required_available_bytes']+=1;self.rows[3]['worker_pid']=124
        with self.assertRaisesRegex(ValueError,'PID'):self.check()
    def test_unknown_fields_rejected(self):
        self.outer['silent_fallback']=False
        with self.assertRaisesRegex(ValueError,'schema'):self.check()


class CustodyTests(unittest.TestCase):
    def setUp(self):self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name).resolve()
    def tearDown(self):self.temp.cleanup()
    def write(self,name,obj):
        p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(g.canonical(obj)+b'\n');return p
    def test_freeze_hash_required_membership_and_current_bytes(self):
        p=self.write('source.json',{'source':'authored'});pin={'sha256':g.hash_file(p,time.monotonic()+5),'bytes':p.stat().st_size}
        f=self.write('freeze.json',{'bindings':{'source.json':pin}});h=g.hash_file(f,time.monotonic()+5)
        self.assertEqual(wrapper.verify_freeze(self.root,f,h,{str(p):pin['sha256']},time.monotonic()+5),1)
        p.write_bytes(b'changed')
        with self.assertRaises(ValueError):wrapper.verify_freeze(self.root,f,h,{str(p):pin['sha256']},time.monotonic()+5)
    def test_runtime_comparison_and_current_files(self):
        v=self.root/'runtime';v.mkdir();source=v/'module.py';source.write_bytes(b'authored');record=v/'RECORD';record.write_bytes(b'authored record')
        interp=Path(sys.executable).resolve();cfg=v/'pyvenv.cfg';cfg.write_bytes(b'authored config')
        pin=lambda p:{'sha256':g.hash_file(p,time.monotonic()+10),'bytes':p.stat().st_size}
        before={'at':'2026-10-14T00:00:00+00:00','status':'passed','venv':str(v),'python_entrypoint':str(interp),'python_resolved_identity':str(interp),'record_count':1,'hashed_entries_checked':1,
            'records':[{'path':'RECORD','sha256':pin(record)['sha256']}],'checked_files':[{'path':'module.py',**pin(source),'record_match':True}],
            'excluded_record_entries':[{'path':'RECORD','reason':'unhashed'}],'runtime_pins':{str(cfg):pin(cfg),str(interp):pin(interp)},'unrecorded_files':[],'failures':[],'limitations':'Authored small roster; not real runtime qualification.'}
        after={**before,'at':'2026-10-14T00:00:01+00:00'};self.assertEqual(wrapper.verify_runtime(before,after,time.monotonic()+10)['hashed_entries'],1)
        wrong=copy.deepcopy(after);wrong['failures']=['change']
        with self.assertRaises(ValueError):wrapper.verify_runtime(before,wrong,time.monotonic()+10)
        source.write_bytes(b'altered')
        with self.assertRaises(ValueError):wrapper.verify_runtime(before,after,time.monotonic()+10)
    def test_path_escape_and_symlinks(self):
        p=self.root/'link';p.symlink_to(self.root/'missing')
        for path in (p,self.root/'..'/'outside'):
            with self.subTest(path=str(path)),self.assertRaises(ValueError):g.confined(self.root,path)
    def test_final_inventory_observes_all_regular_files(self):
        output=self.root/'output';output.mkdir();(output/'raw').mkdir();(output/'raw'/'one').write_bytes(b'123');extra=self.root/'journal';extra.write_bytes(b'45')
        r=wrapper.final_inventory(output,[extra],time.monotonic()+5);self.assertEqual([r['file_count'],r['logical_bytes']],[2,5])
        (output/'raw'/'link').symlink_to(extra)
        with self.assertRaises(ValueError):wrapper.final_inventory(output,[extra],time.monotonic()+5)


if __name__=='__main__':unittest.main(verbosity=2)
