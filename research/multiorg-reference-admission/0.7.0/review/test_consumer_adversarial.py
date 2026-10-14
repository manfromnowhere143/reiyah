#!/usr/bin/env python3
"""Independently authored receipt/journal mutations; no empirical records or models."""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import time
import unittest

G=None


def fixture():
    plan={'artifact_id':'reiyah.resource-admission.capacity-plan','version':'0.1.0','free_disk_floor_bytes':4294967296,'output_budget_bytes':268435456,'margin_bytes':3221225472,'max_output_files':10000,'preflight_samples':2,'sample_period_seconds':.2,'max_sample_gap_seconds':2}
    rows=[];elapsed=[0,.2,.4,.5,.8];duration=.01;pid=123
    for i,phase in enumerate(['preflight','preflight','before_launch','running','final']):
        pre=i<3;disk={'available_bytes':20*1024**3,'free_including_reserved_bytes':21*1024**3,'total_bytes':100*1024**3,'fragment_bytes':4096,'measurement':'statvfs_f_bavail_times_f_frsize; no purgeable estimate'}
        out={'file_count':3,'logical_bytes':1024,'allocated_bytes':12288,'walk_seconds':.001,'measurement':'sum st_size and st_blocks*512; shared/extents/metadata/APFS purgeable or exclusive deletion yield not measured'}
        slack=plan['max_output_files']*(disk['fragment_bytes']-1);budget=plan['output_budget_bytes']+slack;remaining=budget-max(out['logical_bytes'],out['allocated_bytes'])
        rows.append({'sequence':i,'phase':phase,'unix_time_ns':1700000000000000000+int(elapsed[i]*1e9),'elapsed_seconds':elapsed[i],'worker_elapsed_seconds':None if pre else .05 if phase=='running' else .25,'worker_pid':None if pre else pid,'disk':disk,'output':out,'rss_bytes':None if phase!='running' else 1024,'rss_state':'not_launched' if pre else 'observed' if phase=='running' else 'worker_exited_before_observation','errors':[],'gap_seconds':None if i==0 else elapsed[i]-elapsed[i-1],'duration_seconds':duration,'prospective_allocation_budget_bytes':budget,'allocation_rounding_allowance_bytes':slack,'remaining_allocation_budget_bytes':remaining,'required_available_bytes':plan['free_disk_floor_bytes']+plan['margin_bytes']+(budget if pre else remaining)})
    receipt={'artifact_id':'reiyah.resource-admission.supervisor-receipt','version':'0.1.0','status':'complete','returncode':0,'termination_reason':None,'worker_pid':pid,'worker_launched':True,'peak_sampled_rss_bytes':1024,'runner_sha256':G.WORKER,'manifest_sha256':'1'*64,'capacity_plan_sha256':'2'*64,'supervisor_sha256':G.SUPERVISOR,'policy_sha256':G.POLICY,'capacity_plan':plan,'observation_provider_mode':'system','memory_boundary':'sampled_RSS_not_hard_address_space_or_process_tree_limit','network_boundary':'worker_only_host_observer_outside_sandbox','capacity_boundary':'admission_observations_not_reservation_or_continuous_floor_guarantee','output_budget_scope':'logical byte cap across worker output directory plus process log, policy, samples and receipt; two transient64KiB receipt links and next8KiB sample reserved in observed budget checks','allocation_budget_scope':'logical cap plus max_output_files*(filesystem fragment_bytes-1) rounding allowance; metadata, shared extents and APFS-exclusive allocation remain unmeasured; margin is additional and no physical guarantee is made','bindings_verified_before_launch':True,'bindings_unchanged_after_worker':True,'receipt_compatibility':'new schema; historical pair checkers not qualified for this supervisor','receipt_publication':'exclusive pending write and file fsync before no-overwrite hard-link publication; no directory-fsync or crash-durability claim; pending file alone is not an accepted receipt','sample_journal':'attempt.resources.jsonl','log':'attempt.log','sample_errors':[],'sampling_gaps':[],'resource_caps':copy.deepcopy(G.CAPS),'admission_required_available_bytes':rows[-1]['prospective_allocation_budget_bytes']+plan['free_disk_floor_bytes']+plan['margin_bytes'],'limits':{'wall_seconds':600,'memory_bytes':3221225472},'command':['authored fixture only'],'result_sha256':'3'*64,'resource_samples_sha256':'4'*64,'sample_count':5,'wall_seconds':1.0,'worker_wall_seconds':.25,'receipt_persisted':True}
    outer={'artifact_id':'reiyah.resource-admission.outer-execution','version':'0.1.0','returncode':0,'timed_out':False,'wall_seconds':1.2,'command':['authored outer fixture'],'freeze_sha256':'5'*64,'supervisor_sha256':G.SUPERVISOR,'manifest_sha256':'1'*64,'stdout_sha256':'6'*64,'stderr_sha256':'7'*64,'worker_log_sha256':'9'*64,'worker_log_bytes':0}
    expected={'outer_wall_limit_seconds':660,'outer':copy.deepcopy(outer),'receipt':copy.deepcopy(receipt)}
    return receipt,copy.deepcopy(receipt),outer,rows,expected


class Controls(unittest.TestCase):
    def good(self):
        f=fixture();self.assertEqual(G.validate_success(*f)['status'],'resource_receipt_and_journal_checked');return f
    def reject(self,mutate):
        f=fixture();mutate(f)
        with self.assertRaises((ValueError,KeyError,TypeError)):G.validate_success(*f)
    def test_authored_valid_record(self):self.good()
    def test_nonzero_outer_rejected_with_complete_receipt(self):self.reject(lambda f:f[2].update(returncode=1))
    def test_boolean_outer_returncode_rejected(self):self.reject(lambda f:f[2].update(returncode=False))
    def test_outer_timeout_rejected(self):self.reject(lambda f:f[2].update(timed_out=True))
    def test_returned_record_disagrees_after_cleanup_failure(self):self.reject(lambda f:f[1].update(status='failed',receipt_persisted=False))
    def test_self_consistent_wrong_supervisor_rejected(self):
        def m(f):
            for x in (f[0],f[1],f[2],f[4]['outer'],f[4]['receipt']):x['supervisor_sha256']='8'*64
        self.reject(m)
    def test_self_consistent_wrong_worker_rejected(self):
        def m(f):
            for x in (f[0],f[1],f[4]['receipt']):x['runner_sha256']='8'*64
        self.reject(m)
    def test_persisted_pending_only_not_success(self):
        def m(f):f[0]['receipt_persisted']=False;f[1]['receipt_persisted']=False
        self.reject(m)
    def test_resource_stop_cannot_be_hidden_by_exit_zero(self):
        def m(f):f[0]['termination_reason']='disk_floor';f[1]['termination_reason']='disk_floor'
        self.reject(m)
    def test_fabricated_peak_not_max_samples(self):
        def m(f):f[0]['peak_sampled_rss_bytes']=512;f[1]['peak_sampled_rss_bytes']=512
        self.reject(m)
    def test_bool_sample_sequence_not_integer(self):self.reject(lambda f:f[3][1].update(sequence=True))
    def test_reserved_capacity_not_available(self):self.reject(lambda f:f[3][3]['disk'].update(available_bytes=0))
    def test_self_consistent_understated_required_headroom(self):self.reject(lambda f:f[3][3].update(required_available_bytes=4294967296))
    def test_missing_final_sample_rejected(self):
        def m(f):f[3].pop();f[0]['sample_count']=4;f[1]['sample_count']=4
        self.reject(m)
    def test_reordered_phases_rejected(self):self.reject(lambda f:f[3][2].update(phase='running'))
    def test_sample_error_not_erased_by_empty_receipt_errors(self):self.reject(lambda f:f[3][3]['errors'].append('RSS unavailable'))
    def test_slow_sample_rejected(self):self.reject(lambda f:f[3][3].update(duration_seconds=3))
    def test_overlapping_sample_rejected(self):self.reject(lambda f:f[3][2].update(duration_seconds=.2))
    def test_invented_worker_origin_before_prelaunch_rejected(self):self.reject(lambda f:f[3][3].update(worker_elapsed_seconds=.2))
    def test_worker_finishes_after_final_sample_rejected(self):
        def m(f):
            for x in (f[0],f[1]):x['worker_wall_seconds']=.5
            f[3][-1]['worker_elapsed_seconds']=.5
        self.reject(m)
    def test_final_sample_cannot_claim_worker_still_observed(self):self.reject(lambda f:f[3][-1].update(rss_state='observed',rss_bytes=1024))
    def test_worker_log_identity_mismatch_rejected(self):
        def m(f):f[0]['log']='different.log';f[1]['log']='different.log'
        self.reject(m)
    def test_outer_worker_log_digest_mismatch_rejected(self):self.reject(lambda f:f[2].update(worker_log_sha256='a'*64))
    def test_outer_worker_log_boolean_length_rejected(self):self.reject(lambda f:f[2].update(worker_log_bytes=False))
    def test_duplicate_json_key_rejected(self):
        with self.assertRaises(ValueError):G.parse(b'{"status":"failed","status":"complete"}')
    def test_missing_final_newline_rejected(self):
        with self.assertRaises(ValueError):G.journal_rows(b'{}')
    def test_nonfinite_json_rejected(self):
        with self.assertRaises(ValueError):G.parse(b'{"value":NaN}')


def main():
    global G
    p=argparse.ArgumentParser();p.add_argument('--gate',required=True);p.add_argument('--report',required=True);a=p.parse_args()
    path=Path(a.gate);before=path.read_bytes();spec=importlib.util.spec_from_file_location('reviewed_resource_gate',path);G=importlib.util.module_from_spec(spec);spec.loader.exec_module(G)
    t=time.monotonic();result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
    report={'artifact_id':'reiyah.capacity-recovery.consumer-adversarial-controls','version':'0.1.0','status':'passed' if result.wasSuccessful() else 'failed','cases':result.testsRun,'wall_seconds':time.monotonic()-t,'gate_sha256':hashlib.sha256(before).hexdigest(),'gate_unchanged':path.read_bytes()==before,'controls_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'failures':[str(t)+': '+e for t,e in result.failures],'errors':[str(t)+': '+e for t,e in result.errors],'scope':'Independently authored synthetic receipt/journal mutation fixtures only. No model, annotation, actual execution or empirical prediction files.'}
    with Path(a.report).open('x') as f:json.dump(report,f,indent=2);f.write('\n')
    return 0 if result.wasSuccessful() else 1


if __name__=='__main__':raise SystemExit(main())
