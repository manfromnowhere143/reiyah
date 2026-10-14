#!/usr/bin/env python3
"""Separate synthetic runtime/freeze custody tests; no live runtime edits or model data."""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import time
import unittest

C=None
BASE=None


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


class Controls(unittest.TestCase):
    def setUp(self):
        self.root=Path(tempfile.mkdtemp(prefix=self._testMethodName+'-',dir=BASE));self.venv=self.root/'authored-venv';self.venv.mkdir()
        self.module=self.venv/'module.py';self.module.write_text('# authored inert file\n')
        self.record=self.venv/'package.RECORD';self.record.write_text('authored fixture RECORD bytes\n')
        python=Path(sys.executable).resolve()
        self.before={'status':'passed','failures':[],'unrecorded_files':[],'venv':str(self.venv),'checked_files':[{'path':self.module.name,'sha256':sha(self.module),'bytes':self.module.stat().st_size,'record_match':True}],'records':[{'path':self.record.name,'sha256':sha(self.record)}],'excluded_record_entries':[],'hashed_entries_checked':1,'record_count':1,'runtime_pins':{str(python):{'sha256':sha(python),'bytes':python.stat().st_size}},'python_entrypoint':sys.executable,'python_resolved_identity':str(python),'limitations':['Authored two-file fixture only'],'at':'2026-10-14T01:00:00+00:00'}
        self.after=copy.deepcopy(self.before);self.after['at']='2026-10-14T01:01:00+00:00'
    def run_runtime(self):return C.verify_runtime(self.before,self.after,time.monotonic()+10)
    def reject(self,mutate):
        mutate()
        with self.assertRaises((ValueError,KeyError,TypeError,FileNotFoundError)):self.run_runtime()
    def both(self,key,value):self.before[key]=copy.deepcopy(value);self.after[key]=copy.deepcopy(value)
    def test_valid_declared_fixture_bytes(self):self.assertEqual(self.run_runtime()['hashed_entries'],1)
    def test_actual_declared_runtime_file_changed(self):self.reject(lambda:self.module.write_text('changed after reports\n'))
    def test_actual_record_file_changed(self):self.reject(lambda:self.record.write_text('changed RECORD\n'))
    def test_after_audit_changed_metadata(self):self.reject(lambda:self.after.update(record_count=2))
    def test_boolean_hashed_count_rejected(self):self.reject(lambda:self.both('hashed_entries_checked',True))
    def test_duplicate_runtime_path_rejected(self):
        def mutate():self.both('records',[{'path':self.module.name,'sha256':sha(self.module)}])
        self.reject(mutate)
    def test_empty_runtime_roster_rejected(self):
        def mutate():self.both('checked_files',[]);self.both('hashed_entries_checked',0)
        self.reject(mutate)
    def test_reported_unrecorded_file_not_silently_accepted(self):self.reject(lambda:self.both('unrecorded_files',['other.py']))
    def test_runtime_symlink_refused_even_if_bytes_match(self):
        def mutate():
            destination=self.venv/'other.py';self.module.rename(destination);self.module.symlink_to(destination)
        self.reject(mutate)
    def test_runtime_relative_escape_refused(self):
        def mutate():
            for d in (self.before,self.after):d['checked_files'][0]['path']='../outside.py'
        self.reject(mutate)
    def test_false_record_match_rejected(self):
        def mutate():
            for d in (self.before,self.after):d['checked_files'][0]['record_match']=False
        self.reject(mutate)
    def test_boolean_current_file_size_rejected(self):
        def mutate():
            for d in (self.before,self.after):d['checked_files'][0]['bytes']=True
        self.reject(mutate)
    def test_resolved_interpreter_must_be_declared_pin(self):
        def mutate():
            p=self.venv/'interpreter';p.write_bytes(b'authored inert interpreter marker')
            self.both('runtime_pins',{str(p):{'sha256':sha(p),'bytes':p.stat().st_size}})
        self.reject(mutate)
    def test_runtime_after_cannot_precede_before(self):self.reject(lambda:self.after.update(at='2026-10-14T00:59:00+00:00'))
    def test_runtime_audit_timestamp_must_be_parseable(self):self.reject(lambda:self.after.update(at='not a timestamp'))
    def test_before_report_cannot_be_reused_as_after_path(self):
        owner=Path(C.__file__).resolve().parent.parent;base=owner/'candidate/research/multiorg-reference-admission'
        files={'supervisor':base/'0.6.1/monitor/supervise.py','worker':base/'0.6.0/complete_pair.py','numerical_checker':base/'0.6.0/check_pair.py'}
        sources={}
        for key,source in files.items():
            target=self.root/(key+'.py');target.write_bytes(source.read_bytes());sources[key]={'path':str(target),'sha256':sha(target)}
        for key in ('manifest','protocol','capacity_plan','runtime_before'):
            target=self.root/(key+'.json');target.write_text('{}');sources[key]={'path':str(target),'sha256':sha(target)}
        paths={key:str(self.root/(key+'-destination')) for key in ('output','outer','stdout','stderr','runtime_after','freeze')};paths['runtime_after']=sources['runtime_before']['path']
        contract=self.root/'consumer-contract.json';contract.write_text(json.dumps({'artifact_id':'reiyah.multiorg.resource-consumer-contract','version':'0.1.0','sources':sources,'paths':paths,'python_entrypoint':sys.executable,'outer_wall_limit_seconds':660}))
        with self.assertRaises(ValueError):C.load_contract(owner,contract,sha(contract),time.monotonic()+10)

    def freeze(self):
        p=self.root/'source.py';p.write_text('# authored source\n');f=self.root/'freeze.json';f.write_text(json.dumps({'bindings':{'source.py':{'sha256':sha(p),'bytes':p.stat().st_size}}}));return p,f
    def test_freeze_missing_required_binding_rejected(self):
        p,f=self.freeze()
        with self.assertRaises(ValueError):C.verify_freeze(self.root,f,sha(f),{str(self.root/'absent.py'):'0'*64},time.monotonic()+10)
    def test_freeze_changed_current_bytes_rejected(self):
        p,f=self.freeze();expected=sha(p);p.write_text('# mutated after freeze\n')
        with self.assertRaises(ValueError):C.verify_freeze(self.root,f,sha(f),{str(p):expected},time.monotonic()+10)
    def test_freeze_boolean_size_rejected(self):
        p,f=self.freeze();f.write_text(json.dumps({'bindings':{'source.py':{'sha256':sha(p),'bytes':True}}}))
        with self.assertRaises(ValueError):C.verify_freeze(self.root,f,sha(f),{str(p):sha(p)},time.monotonic()+10)


def main():
    global C,BASE
    p=argparse.ArgumentParser();p.add_argument('--consumer',required=True);p.add_argument('--archive',required=True);p.add_argument('--report',required=True);a=p.parse_args()
    source=Path(a.consumer);BASE=Path(a.archive);BASE.mkdir(parents=True,exist_ok=False);sys.path.insert(0,str(source.parent))
    spec=importlib.util.spec_from_file_location('reviewed_consumer',source);C=importlib.util.module_from_spec(spec);spec.loader.exec_module(C)
    before=source.read_bytes();t=time.monotonic();result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Controls))
    report={'artifact_id':'reiyah.capacity-recovery.runtime-adversarial-controls','version':'0.1.0','status':'passed' if result.wasSuccessful() else 'failed','cases':result.testsRun,'wall_seconds':time.monotonic()-t,'consumer_sha256':hashlib.sha256(before).hexdigest(),'consumer_unchanged':source.read_bytes()==before,'gate_sha256':sha(Path(C.g.__file__)),'controls_sha256':sha(Path(__file__)),'failures':[str(t)+': '+e for t,e in result.failures],'errors':[str(t)+': '+e for t,e in result.errors],'scope':'Authored inert temporary files and fixture audit reports only; current Python binary read/hash only, no live runtime mutation, models, annotation or empirical output files.'}
    with Path(a.report).open('x') as f:json.dump(report,f,indent=2);f.write('\n')
    return 0 if result.wasSuccessful() else 1


if __name__=='__main__':raise SystemExit(main())
