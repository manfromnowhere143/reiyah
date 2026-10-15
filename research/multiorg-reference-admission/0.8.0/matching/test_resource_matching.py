#!/usr/bin/env python3
"""Authored resource-to-matching custody failures; no empirical records."""
import argparse
import copy
import json
from pathlib import Path
import tempfile
import time
import traceback
import input_gate as g
import test_matching as fixtures
import authored_resource as ar


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--repository',required=True);parser.add_argument('--output',required=True)
    a=parser.parse_args();start=time.monotonic();passed=[];failure=None
    mutations=[
        ('wrong_consumer_identity',lambda o:o['pair_checker'].update(consumer_sha256='0'*64),'qualified resource component'),
        ('wrong_resource_gate_identity',lambda o:o['pair_checker'].update(resource_gate_sha256='0'*64),'qualified resource component'),
        ('wrong_numerical_identity',lambda o:o['pair_checker'].update(numerical_checker_sha256='0'*64),'qualified resource component'),
        ('legacy_report_cannot_replace_wrapper',lambda o:o['pair_checker'].update(artifact_id='reiyah.multiorg.complete-pair-check',version='0.6.0'),'resource wrapper identity'),
        ('wrapper_cannot_impersonate_numerical_checker',lambda o:o['pair_checker'].update(checker_sha256=g.sha(b'authored')),'impersonate'),
        ('wrapper_bool_completion_refused',lambda o:o['pair_checker'].update(complete_pairs=True),'resource wrapper completion'),
        ('wrong_consumer_contract',lambda o:o['pair_checker'].update(contract_sha256='0'*64),'prospective resource contract'),
        ('resource_summary_not_sufficient',lambda o:o['pair_checker']['resource_admission'].update(samples=7),'resource gate recomputation'),
        ('runtime_unknown_refused',lambda o:o['pair_checker']['runtime'].update(status='unknown'),'qualified runtime'),
        ('input_tensor_roster_incomplete',lambda o:o['pair_checker']['input_reconstruction'].update(tensor_count=311),'input reconstruction'),
        ('nested_partial_not_complete',lambda o:o['pair_checker']['numerical_result'].update(status='failed_attempt_partial_ledger_checked'),'nested complete'),
        ('nested_failed_state_not_empty',lambda o:o['pair_checker']['numerical_result'].update(failure_sha256='a'*64),'nested complete'),
        ('nested_orphan_not_dropped',lambda o:o['pair_checker']['numerical_result'].update(unbound_partial_array_files=['one.npy']),'nested complete'),
        ('nested_terminal_refusal_preserved',lambda o:o['pair_checker']['numerical_result'].update(terminal_semantic_refusal='high invalid'),'nested complete'),
        ('nested_wrong_endpoint',lambda o:o['pair_checker']['numerical_result'].update(scope='complete storage'),'nested numerical endpoint'),
        ('nested_observation_roster_not_replaced',lambda o:o['pair_checker']['numerical_result'].update(observations=[]),'checker exact observation'),
        ('consumer_outer_exit_nonzero',lambda o:o['checker_execution'].update(returncode=1),'successful resource consumer'),
        ('consumer_outer_exit_bool',lambda o:o['checker_execution'].update(returncode=False),'successful resource consumer'),
        ('consumer_outer_timeout',lambda o:o['checker_execution'].update(timed_out=True),'successful resource consumer'),
        ('consumer_wall_bound',lambda o:o['checker_execution'].update(wall_seconds=331),'consumer execution wall'),
        ('consumer_wrong_command',lambda o:o['checker_execution']['command'].pop(0),'consumer execution command'),
        ('consumer_wrong_freeze_binding',lambda o:o['checker_execution'].update(freeze_sha256='a'*64),'consumer execution component'),
        ('consumer_unknown_execution_field',lambda o:o['checker_execution'].update(assumed_complete=True),'resource consumer execution schema'),
        ('persisted_false_refused',lambda o:o['supervisor'].update(receipt_persisted=False),'receipt receipt_persisted'),
        ('stop_cause_cannot_exit_zero',lambda o:o['supervisor'].update(termination_reason='disk_floor'),'supervisor complete identity'),
        ('sample_gap_error_refused',lambda o:o['supervisor'].update(sampling_gaps=[1]),'no resource observations'),
        ('new_resource_limits_cannot_relax',lambda o:o['supervisor'].update(limits={'wall_seconds':601,'memory_bytes':3221225472}),'receipt expected limits'),
        ('failed_inference_not_complete_pair',lambda o:o['pair'].update(status='failed'),'complete exact-version'),
    ]
    try:
        for name,mutate,text in mutations:
            with tempfile.TemporaryDirectory(prefix='resource-authored-',dir=g.HERE) as temp:
                root=Path(temp);d,c,_=fixtures.fixture(root,a.repository);m=json.loads(Path(d['path']).read_bytes())
                fixtures.rewrite_bundle(root,m,1,mutate)
                fixtures.rejected(lambda:g.admit_pair(m['pairs'][1],c['profiles'][1]),text)
            passed.append(name)
        for name in ('supervisor_outer_nonzero','journal_truncated','journal_gap_out_of_bounds','journal_wrong_pid','worker_log_same_size_altered','observation_missing','consumer_policy_altered','freeze_binding_removed'):
            with tempfile.TemporaryDirectory(prefix='resource-authored-',dir=g.HERE) as temp:
                root=Path(temp);d,c,_=fixtures.fixture(root,a.repository);m=json.loads(Path(d['path']).read_bytes());b=m['pairs'][1]
                objs={k:json.loads(Path(b[k]['path']).read_bytes()) for k in ('pair','supervisor','pair_checker','checker_execution')}
                obs=objs['pair_checker']['observations'];text=''
                if name=='supervisor_outer_nonzero':
                    p=Path(obs['outer']['path']);v=json.loads(p.read_bytes());v['returncode']=1;ar.persist(p,v);text='outer successful'
                elif name.startswith('journal_'):
                    p=Path(obs['journal']['path']);raw=p.read_bytes()
                    if name=='journal_truncated':raw=raw[:-1];text='complete bounded newline-terminated journal'
                    else:
                        rows=[json.loads(x) for x in raw.splitlines()]
                        if name=='journal_gap_out_of_bounds':rows[3]['gap_seconds']=3;text='sample gap'
                        else:rows[3]['worker_pid']=124;text='sample PID'
                        raw=b''.join(g.resource_module(c['profiles'][1]).canonical(r)+b'\n' for r in rows)
                    p.write_bytes(raw);objs['supervisor']['resource_samples_sha256']=ar.sha(p)
                elif name=='worker_log_same_size_altered':
                    p=Path(obs['worker_log']['path']);p.write_bytes(b'X'*p.stat().st_size);text='outer worker_log_sha256'
                elif name=='observation_missing':
                    del objs['pair_checker']['observations']['runtime_after'];text='resource observation roster'
                elif name=='consumer_policy_altered':
                    policy=Path(json.loads(Path(b['resource_contract']['path']).read_bytes())['paths']['freeze']).parent/'execution/shared/check.sandbox.sb'
                    policy.write_bytes(b'(version 1)(allow default)');text='consumer network policy'
                else:
                    p=Path(json.loads(Path(b['resource_contract']['path']).read_bytes())['paths']['freeze']);value=json.loads(p.read_bytes());value['bindings'].pop('consumer/resource_gate.py');ar.persist(p,value)
                    objs['pair_checker']['freeze_sha256']=ar.sha(p);objs['checker_execution']['freeze_sha256']=ar.sha(p)
                    op=Path(obs['outer']['path']);outer=json.loads(op.read_bytes());outer['freeze_sha256']=ar.sha(p);ar.persist(op,outer);text='frozen consumer component'
                ar.rewrite(root,m,b,objs)
                fixtures.rejected(lambda:g.admit_pair(b,c['profiles'][1]),text)
            passed.append(name)
    except Exception as exc:failure={'exception':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc()}
    report={'status':'passed' if failure is None else 'failed','count':len(passed),'controls':passed,'failure':failure,'wall_seconds':time.monotonic()-start,
        'source_sha256':g.sha(Path(__file__).read_bytes()),'admission_sha256':g.sha(Path(g.__file__).read_bytes()),'contract_sha256':g.CONTRACT_SHA,
        'scope':'Authored resource receipt/journal, wrapper and nested numeric records only. No empirical outputs or annotations, no inference.'}
    with Path(a.output).open('xb') as stream:stream.write(g.canonical(report))
    print(json.dumps({'status':report['status'],'passed':len(passed)}));raise SystemExit(0 if failure is None else 1)


if __name__=='__main__':main()
