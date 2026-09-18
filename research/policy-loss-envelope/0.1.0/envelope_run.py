"""Freeze, execute and independently verify the nominal envelope study."""
import argparse
from collections import Counter
from datetime import datetime,timezone
from fractions import Fraction as Q
import json
from pathlib import Path
import resource
import shutil
import sys
import time

from envelope_check import verify
from envelope_math import best,compare,require
from envelope_sources import MODELS,check_bindings,load_curve,put,read,sha


def utc():return datetime.now(timezone.utc).isoformat()


def freeze(area,output):
    require(not output.exists(),'Envelope freeze directory exists');output.mkdir(parents=True)
    implementation=output/'implementation';implementation.mkdir();here=Path(__file__).resolve().parent
    candidate=here.parents[2];bindings={}
    def add(path,role):
        path=path.resolve();require(path.is_file(),'Missing envelope input')
        bindings[str(path)]={'path':str(path),'bytes':path.stat().st_size,'sha256':sha(path),'role':role}
    for path in sorted(here.iterdir()):
        if path.suffix=='.py' or path.name=='PLAN.md':
            add(path,'frozen_implementation');shutil.copyfile(path,implementation/path.name)
    source=candidate/'research/operating-policy/0.1.0'
    for name in ('detector-curves.csv','summary.json','PLAN.md','MATHEMATICS.md','SOURCES.md','DISTRIBUTION.md'):
        add(source/name,'verified_preceding_scalar_curve_and_scope')
    for name in ('README.md','summary.json','DISTRIBUTION.md'):
        add(candidate/'research/public-predictions/0.1.0'/name,'original_comparison_and_source_conditions')
    add(area/'private/run_phase.py','network_denied_phase_launcher');add(Path(sys.executable),'selected_python_executable')
    for module in list(sys.modules.values()):
        name=getattr(module,'__file__',None)
        if name and Path(name).is_file():add(Path(name),'loaded_runtime_or_implementation')
    for path in sorted((area/'logs').glob('envelope-controls-*-COMPLETED.json')):
        add(path,'pre_run_controls');add(path.with_name(path.name.replace('-COMPLETED.json','.stderr')),'control_diagnostics')
    frozen={'artifact_id':'reiyah.policy-loss-envelope.freeze','version':'0.1.0','status':'exploratory',
        'frozen_utc':utc(),'models':list(MODELS),'population':64,'references':305,'curve_cells':[299,220],
        'maximum_phase_seconds':1200,'maximum_lines_per_model':600,'maximum_constraints_per_model':360000,
        'maximum_final_cells':10000,'reserved_images_closed':1433,'already_exposed_development':True,
        'python_version':sys.version,'curve_path':str(source/'detector-curves.csv'),'bindings':list(bindings.values())}
    put(output/'FREEZE.json',frozen)
    print(json.dumps({'freeze_sha256':sha(output/'FREEZE.json'),'bindings':len(bindings),'frozen_utc':frozen['frozen_utc']}))


def run(frozen,output):
    require(not output.exists(),'Envelope run output exists');output.mkdir(parents=True)
    tick=time.perf_counter();start=utc();curves=load_curve(frozen['curve_path'])
    result=compare(curves[0]['lines'],curves[1]['lines'],64)
    require([best(c['lines'],Q(1,2))[0]*2 for c in curves]==[207,210],'Prior unit-loss minima changed')
    result.update(artifact_id='reiyah.policy-loss-envelope.results',version='0.1.0',status='exploratory',
        models=list(MODELS),curve_sha256=sha(frozen['curve_path']),source_cells=[len(c['lines']) for c in curves],
        source_threshold_domains=[c['threshold_domains'] for c in curves],
        started_utc=start,finished_utc=utc(),seconds=time.perf_counter()-tick,
        peak_resident_bytes_macos=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        decisions_by_partition_kind={kind:dict(Counter(c['envelope_comparison'] for c in result['partition'] if c['kind']==kind))
                                    for kind in ('point','open_interval')},
        new_images=0,new_inference_calls=0,reserved_images_closed=1433)
    check_bindings(frozen);put(output/'RESULTS.json',result)
    print(json.dumps({'cells':len(result['partition']),'breakpoints':len(result['breakpoints']),
                      'source_cells':result['source_cells'],'seconds':result['seconds'],
                      'decisions':result['decisions_by_partition_kind']}))


def check(frozen,run,output):
    require(not output.exists(),'Envelope verification output exists');output.mkdir(parents=True)
    tick=time.perf_counter();start=utc();curves=load_curve(frozen['curve_path']);result=read(run/'RESULTS.json')
    require(result['population']==64 and result['models']==list(MODELS),'Result scope differs')
    require(result['curve_sha256']==sha(frozen['curve_path']) and result['source_cells']==[299,220]
            and result['source_threshold_domains']==[c['threshold_domains'] for c in curves],'Source association differs')
    report=verify(curves[0]['lines'],curves[1]['lines'],result)
    require(result['decisions_by_partition_kind']=={kind:dict(Counter(c['envelope_comparison'] for c in result['partition'] if c['kind']==kind))
                                    for kind in ('point','open_interval')},'Decision count differs')
    check_bindings(frozen)
    report.update(artifact_id='reiyah.policy-loss-envelope.verification',version='0.1.0',
        results_sha256=sha(run/'RESULTS.json'),started_utc=start,finished_utc=utc(),seconds=time.perf_counter()-tick,
        all_source_curve_identities_and_coverage_checked=True,
        peak_resident_bytes_macos=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    put(output/'VERIFICATION.json',report);print(json.dumps(report))


def main():
    p=argparse.ArgumentParser();p.add_argument('--area',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--freeze-only',action='store_true');p.add_argument('--freeze',type=Path);p.add_argument('--verify-run',type=Path)
    args=p.parse_args()
    if args.freeze_only:freeze(args.area.resolve(),args.output.resolve());return
    require(args.freeze is not None,'Freeze required');frozen=read(args.freeze);check_bindings(frozen)
    if args.verify_run:check(frozen,args.verify_run,args.output)
    else:run(frozen,args.output)


if __name__=='__main__':main()
