#!/usr/bin/env python3
"""Authored cohort admission/composition controls; no new empirical inputs."""
import argparse
import copy
from decimal import Decimal
from fractions import Fraction
import json
from itertools import product
from pathlib import Path
import platform
import tempfile
import time
import traceback
from unittest.mock import patch
import input_gate as g
import match_analysis as producer
import check_matching as checker


def rejected(action, text):
    try: action()
    except Exception as exc:
        assert text in str(exc), (text, str(exc))
    else: raise AssertionError('unexpected acceptance: ' + text)


def detections(count, geometry=(10, 10, 11, 11), model='faster'):
    return [(model + '-' + str(i), tuple(Fraction(v) for v in geometry), 'a' * 64) for i in range(count)]


def row(index=0):
    return {'id':index,'tile_ordinal':0,'original_row_index':index,'box_xyxy':[0,0,2,2],'score':Decimal('.75')}


def image(model,rows,profile):
    return {'artifact_id':'reiyah.multiorg.complete-analysis-image','version':profile['version'],'status':'complete',
        'image_id':profile['image_id'],'model':model,'model_variant':g.VARIANTS[model],'model_source_sha256':g.MODEL_PINS[model],
        'completion_scope':g.SCOPE,'storage_output_status':g.STORAGE,'tile_count_expected':profile['tiles'],
        'tile_count_completed':profile['tiles'],'image_shape_hw':profile['image_shape_hw'],'rescaled_shape_hw':profile['rescaled_shape_hw'],
        'raw_onnx_rows':len(rows),'analysis_predictions':rows,'empty_analysis':not bool(rows),'protocol_sha256':profile['protocol_sha256']}


def persisted(path,value):
    path.write_text(json.dumps(value,sort_keys=True,separators=(',',':'),default=lambda v:float(v) if isinstance(v,Decimal) else None)+'\n')
    return {'path':str(path),'sha256':g.sha(path.read_bytes())}


def authored_contract(repository):
    contract,deps=g.dependencies(repository);contract=copy.deepcopy(contract)
    # Development controls can be prepared before final execution digests exist.
    # Final qualification additionally records whether the real profiles are ready.
    contract['profiles_status']='complete_prospective_bindings'
    for profile in contract['profiles']:
        for key in ('image_sha256','worker_sha256','checker_sha256','protocol_sha256','manifest_sha256','image_contract_sha256'):
            if profile[key]=='PENDING':profile[key]='d'*64
        if profile['image_shape_hw'] is None:profile['image_shape_hw']=[5720,6385]
        if profile['rescaled_shape_hw'] is None:profile['rescaled_shape_hw']=[2860,3192]
        if profile['tiles'] is None:profile['tiles']=156
    return contract,deps


def fixture(root,repository):
    contract,deps=authored_contract(repository);sources=root/'references';sources.mkdir()
    ref_images=[];bundles=[]
    for index,profile in enumerate(contract['profiles']):
        identity=profile['image_id'];annotations=[]
        for procedure,count in g.COUNTS[identity].items():
            data={str(i):[[10*i,10*i],[10*i+2,10*i],[10*i+2,10*i+2],[10*i,10*i+2]] for i in range(count)}
            filename=str(index)+'-'+procedure+'.json';d=persisted(sources/filename,data)
            annotations.append({'procedure':procedure,'source_path':'authored/'+filename,'local_path':filename,
                'sha256':d['sha256'],'byte_size':(sources/filename).stat().st_size,'transport_valid':True})
        ref_images.append({'tiff_path':identity,'annotations':annotations})
        folder=root/('pair-'+str(index));folder.mkdir();observations=[]
        for model in g.MODELS:
            value=image(model,[row()] if model=='faster' else [],profile);d=persisted(folder/(model+'.json'),value)
            observations.append({'file':Path(d['path']).name,'sha256':d['sha256'],'bytes':Path(d['path']).stat().st_size,
                'image_id':identity,'model':model,'model_variant':g.VARIANTS[model],'analysis_count':len(value['analysis_predictions']),
                'raw_onnx_rows':value['raw_onnx_rows'],'completion_scope':g.SCOPE})
        pins={'image':profile['image_sha256'],'protocol':profile['protocol_sha256'],**g.MODEL_PINS}
        pair={'artifact_id':'reiyah.multiorg.complete-analysis-pair','version':profile['version'],'status':'complete','stage':'complete',
            'completion_scope':g.SCOPE,'storage_output_status':g.STORAGE,'model_variants':g.VARIANTS,
            'image_id':identity,'image_contract_sha256':profile['image_contract_sha256'],
            'forward_passes_started':2*profile['tiles'],'forward_passes_completed':2*profile['tiles'],
            'tile_coverage':{m:{'captured':profile['tiles'],'admitted':profile['tiles'],'complete':True} for m in g.MODELS},
            'runner_sha256':profile['worker_sha256'],'manifest_sha256':profile['manifest_sha256'],'protocol_sha256':profile['protocol_sha256'],
            'source_bindings':{k:{'sha256':v} for k,v in pins.items()},'observations':observations}
        pd=persisted(folder/'pair.json',pair)
        sup=persisted(folder/'process.json',{'status':'complete','returncode':0,'termination_reason':None,'runner_sha256':profile['worker_sha256'],
            'manifest_sha256':profile['manifest_sha256'],'result_sha256':pd['sha256']})
        check={'status':'complete_pair_verified','complete_pairs':1,'result_sha256':pd['sha256'],'process_receipt_sha256':sup['sha256'],
            'manifest_sha256':profile['manifest_sha256'],'checker_sha256':profile['checker_sha256'],'source_bindings':pins,'observations':observations}
        if profile['version']=='0.6.0':
            check.update(artifact_id='reiyah.multiorg.complete-pair-check',version='0.6.0',image_id=identity,image_contract_sha256=profile['image_contract_sha256'])
        cd=persisted(folder/'check.json',check)
        ce=persisted(folder/'check-process.json',{'returncode':0,'report_sha256':cd['sha256'],'checker_sha256':profile['checker_sha256']})
        bundles.append({'image_id':identity,'pair':pd,'supervisor':sup,'pair_checker':cd,'checker_execution':ce})
    rm=persisted(root/'references.json',{'artifact_id':'reiyah.multiorg.annotation-manifest','version':'0.1.0',
        'images':ref_images+[{'tiff_path':'authored-'+str(i),'annotations':[]} for i in range(51)]})
    contract['reference_manifest_sha256']=rm['sha256']
    manifest={'artifact_id':'reiyah.multiorg.selected-cohort-matching-input','version':'0.6.0','contract_sha256':g.CONTRACT_SHA,
        'pairs':bundles,'reference_manifest':rm,'reference_root':str(sources)}
    return persisted(root/'input.json',manifest),contract,deps


def rewrite_bundle(root,m,index,mutate):
    b=m['pairs'][index];objs={k:json.loads(Path(b[k]['path']).read_bytes()) for k in ('pair','supervisor','pair_checker','checker_execution')}
    mutate(objs)
    b['pair']=persisted(Path(b['pair']['path']),objs['pair']);objs['supervisor']['result_sha256']=b['pair']['sha256']
    b['supervisor']=persisted(Path(b['supervisor']['path']),objs['supervisor'])
    objs['pair_checker']['result_sha256']=b['pair']['sha256'];objs['pair_checker']['process_receipt_sha256']=b['supervisor']['sha256']
    b['pair_checker']=persisted(Path(b['pair_checker']['path']),objs['pair_checker'])
    objs['checker_execution']['report_sha256']=b['pair_checker']['sha256']
    b['checker_execution']=persisted(Path(b['checker_execution']['path']),objs['checker_execution'])
    return persisted(root/'input.json',m)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--repository',required=True);parser.add_argument('--output',required=True)
    a=parser.parse_args();started=time.monotonic();passed=[];failure=None
    def case(name,action):action();passed.append(name)
    try:
        n=g.native(a.repository);flow=checker.oracle();contract,_=authored_contract(a.repository);profile=contract['profiles'][0]
        refs=[('r0',tuple(map(Fraction,(0,0,2,2))))]
        def fixed(aa,bb=None,rr=None):return n.fixed_case(g.IMAGES[0],'t0',aa,[] if bb is None else bb,refs if rr is None else rr,'c'*64)[0]
        def eof():
            b=(g.HERE/'maxflow_reference.py').read_bytes();assert b.endswith(b'\n') and not b.endswith(b'\n\n')
        case('normalized_reference_single_EOF_before_freeze',eof)
        for count in (129,1024):
            def boundary(count=count):
                cell=fixed(detections(count));assert cell['tp_a']==0 and cell['detections_a']==count
                assert flow.matching([d[1] for d in detections(count)],[r[1] for r in refs])==0
            case('native_and_oracle_accept_'+str(count)+'_detections',boundary)
        case('1025_detections_refused',lambda:rejected(lambda:fixed(detections(1025)),'cap exceeded'))
        case('129_references_refused',lambda:rejected(lambda:fixed([],rr=[('r'+str(i),refs[0][1]) for i in range(129)]),'cap exceeded'))
        case('combined_edge_cap_preserved',lambda:rejected(lambda:fixed(detections(1024,(0,0,2,2)),rr=[('r'+str(i),refs[0][1]) for i in range(3)]),'edge cap'))
        def work():
            rr=[refs[0]]+[('r'+str(i),tuple(map(Fraction,(10*i,10*i,10*i+2,10*i+2)))) for i in range(1,128)]
            rejected(lambda:fixed(detections(1024,(0,0,2,2)),rr=rr),'screening-work cap')
        case('native_work_cap_preserved',work)
        def exact_half():
            assert fixed(detections(1,(0,0,1,2)))['tp_a']==flow.matching([(0,0,1,2)],[(0,0,2,2)])==1
            assert fixed(detections(1,(0,0,1,1)))['tp_a']==flow.matching([(0,0,1,1)],[(0,0,2,2)])==0
        case('exact_IoU_boundary',exact_half)
        def augment():
            aa=[('faster-0',tuple(map(Fraction,(0,0,3,2))),'a'*64),('faster-1',tuple(map(Fraction,(0,0,2,2))),'b'*64)]
            rr=refs+[('r1',tuple(map(Fraction,(1,0,3,2))))]
            assert fixed(aa,rr=rr)['tp_a']==flow.matching([x[1] for x in aa],[x[1] for x in rr])==2
        case('non_greedy_augmenting_path',augment)
        def duplicate_geometry():
            aa=detections(3,(0,0,2,2));rr=[('r0',refs[0][1]),('r1',refs[0][1])]
            assert fixed(aa,rr=rr)['tp_a']==flow.matching([x[1] for x in aa],[x[1] for x in rr])==2
        case('duplicate_geometry_keeps_distinct_source_identities',duplicate_geometry)
        case('complete_observed_empty_is_allowed',lambda:g.analysis_rows(image('faster',[],profile),'faster',profile))
        def image_mutation(name,change,text):
            def action():
                obj=image('faster',[row()],profile);change(obj);rejected(lambda:g.analysis_rows(obj,'faster',profile),text)
            case(name,action)
        image_mutation('missing_not_empty',lambda x:x.pop('analysis_predictions'),'missing or native')
        image_mutation('wrong_image_identity',lambda x:x.update(image_id=g.IMAGES[1]),'image/model')
        image_mutation('wrong_version',lambda x:x.update(version='0.6.0'),'complete image')
        image_mutation('wrong_model_variant',lambda x:x.update(model_variant='original'),'variant/source')
        image_mutation('wrong_model_digest',lambda x:x.update(model_source_sha256='0'*64),'variant/source')
        image_mutation('storage_claim_not_synthesized',lambda x:x.update(storage_predictions=[]),'analysis-only')
        image_mutation('missing_tile',lambda x:x.update(tile_count_completed=155),'tile counts')
        image_mutation('bool_count_not_integer',lambda x:x.update(tile_count_completed=True),'tile counts')
        image_mutation('duplicate_detection_ID',lambda x:x.update(raw_onnx_rows=2,analysis_predictions=[row(),row()]),'analysis identity')
        image_mutation('strict_score_half',lambda x:x['analysis_predictions'][0].update(score=Decimal('.5')),'strict analysis')
        image_mutation('high_geometry_refusal',lambda x:x['analysis_predictions'][0].update(box_xyxy=[0,0,0,2]),'positive exact')
        image_mutation('native_coordinate_cap',lambda x:x['analysis_predictions'][0].update(box_xyxy=[0,0,10000001,2]),'coordinate domain')
        def adapter_cap():
            assert len(g.analysis_rows(image('faster',[row(i) for i in range(1024)],profile),'faster',profile))==1024
            rejected(lambda:g.analysis_rows(image('faster',[row(i) for i in range(1025)],profile),'faster',profile),'native detection cap')
        case('analysis_adapter1024_boundary',adapter_cap)
        def composition():
            matrices=[[[0,0,0]]*4,[[-1,-1,-1]]*4,[[1,1,1]]*4,
                [[-3,2,2],[2,-3,2],[2,2,-3],[-2,-2,-2]],[[0,1,1]]*4,[[1,3,5],[2,4,6],[3,5,7],[4,6,8]]]
            statuses=['inconclusive_global_unresolved','no_observed_fragility','no_observed_fragility','coupling_fragility','inconclusive_global_unresolved','no_observed_fragility']
            for matrix,status in zip(matrices,statuses):
                cells=[{'tiff_path':im,'procedure':proc,'delta':str(matrix[i][j])+'/1'} for i,im in enumerate(g.IMAGES) for j,proc in enumerate(g.PROCEDURES)]
                expected=checker.compose(cells);actual=n.compose(cells,list(g.IMAGES),True);assert expected==actual and expected['primary_status']==status
                all81=[sum(Fraction(matrix[i][choice[i]]) for i in range(4))/4 for choice in product(range(3),repeat=4)]
                global3=[sum(Fraction(matrix[i][j]) for i in range(4))/4 for j in range(3)]
                assert Fraction(expected['imagewise']['lower'])==min(all81) and Fraction(expected['imagewise']['upper'])==max(all81)
                assert Fraction(expected['global']['lower'])==min(global3) and Fraction(expected['global']['upper'])==max(global3)
                assert [x['tiff_path'] for x in expected['imagewise']['lower_choices']]==list(g.IMAGES)
                rejected(lambda:checker.compose(cells[:-1]),'four-by-three')
                rejected(lambda:checker.compose(cells+[cells[0]]),'duplicate')
        case('exact_G_P_against81_choices_null_fragility_zero_and_missing',composition)
        def profile_controls():
            g.validate_profiles(contract)
            for key,value,text in [('tiles',155,'lattice'),('version','0.5.0','version'),('image_sha256','PENDING','digest')]:
                bad=copy.deepcopy(contract);bad['profiles'][1][key]=value;rejected(lambda:g.validate_profiles(bad),text)
            bad=copy.deepcopy(contract);bad['profiles'][1],bad['profiles'][2]=bad['profiles'][2],bad['profiles'][1]
            rejected(lambda:g.validate_profiles(bad),'per-image version')
        case('explicit_profiles_version_lattice_hash_and_order',profile_controls)
        def end_to_end():
            with tempfile.TemporaryDirectory(prefix='authored-',dir=g.HERE) as tmp:
                root=Path(tmp);d,c,deps=fixture(root,a.repository)
                with patch.object(g,'dependencies',return_value=(c,deps)):
                    result=producer.run(d['path'],d['sha256'],a.repository,root/'matched');rp=root/'matched/result.json'
                    checked=checker.run(d['path'],d['sha256'],a.repository,rp,g.sha(rp.read_bytes()))
                    assert checked['status']=='passed' and len(checked['cells'])==12 and len(result['native_packets'])==12
                    assert result['global']['lower']==result['global']['upper']=='-1/1' and result['primary_status']=='no_observed_fragility'
                    original=rp.read_bytes()
                    for key in ('producer_sha256','admission_sha256'):
                        obj=json.loads(original);obj[key]='0'*64;rp.write_bytes(g.canonical(obj))
                        rejected(lambda:checker.run(d['path'],d['sha256'],a.repository,rp,g.sha(rp.read_bytes())),'implementation provenance')
                    obj=json.loads(original);obj['cells'][4]['tp_a']=0;rp.write_bytes(g.canonical(obj))
                    rejected(lambda:checker.run(d['path'],d['sha256'],a.repository,rp,g.sha(rp.read_bytes())),'independent cell tp_a')
                    rejected(lambda:g.load_inputs(d['path'],'0'*64,a.repository),'bound file digest')
        case('mocked_four_pair_twelve_native_cases_oracle_and_tamper',end_to_end)
        def admission_controls():
            for kind in ('missing_pair','duplicate_pair','extra_pair','checker','worker','manifest','failed','image_contract','wrong_reference_bytes'):
                with tempfile.TemporaryDirectory(prefix='authored-',dir=g.HERE) as tmp:
                    root=Path(tmp);d,c,deps=fixture(root,a.repository);m=json.loads(Path(d['path']).read_bytes())
                    if kind=='missing_pair':m['pairs'].pop();d=persisted(root/'input.json',m);text='four complete'
                    elif kind=='duplicate_pair':m['pairs'][2]=m['pairs'][1];d=persisted(root/'input.json',m);text='selected pair roster'
                    elif kind=='extra_pair':m['pairs'].append(m['pairs'][0]);d=persisted(root/'input.json',m);text='four complete'
                    elif kind=='wrong_reference_bytes':
                        (root/'references/1-t0.json').write_bytes(b'{}');text='bound file digest'
                    else:
                        def change(o):
                            if kind=='checker':o['pair_checker']['checker_sha256']=o['checker_execution']['checker_sha256']='e'*64
                            elif kind=='worker':o['pair']['runner_sha256']=o['supervisor']['runner_sha256']='e'*64
                            elif kind=='manifest':o['pair']['manifest_sha256']=o['supervisor']['manifest_sha256']=o['pair_checker']['manifest_sha256']='e'*64
                            elif kind=='failed':o['pair']['status']='failed'
                            else:o['pair']['image_contract_sha256']='e'*64
                        d=rewrite_bundle(root,m,1,change)
                        text={'checker':'qualified pair worker/checker','worker':'qualified pair worker/checker','manifest':'prospective pair manifest','failed':'complete exact-version','image_contract':'selected-image contract'}[kind]
                    with patch.object(g,'dependencies',return_value=(c,deps)):
                        rejected(lambda:g.load_inputs(d['path'],d['sha256'],a.repository),text)
        case('cohort_and_receipt_membership_identity_failure_reference_tampering',admission_controls)
    except Exception as exc:failure={'exception':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc()}
    real_contract,_=g.dependencies(a.repository)
    report={'status':'passed' if failure is None else 'failed','count':len(passed),'controls':passed,'failure':failure,
        'wall_seconds':time.monotonic()-started,'python':platform.python_version(),'scripts':{p.name:g.sha(p.read_bytes()) for p in g.HERE.glob('*.py')},
        'contract_sha256':g.CONTRACT_SHA,'prospective_profiles_complete':real_contract['profiles_status']=='complete_prospective_bindings',
        'scope':'Authored geometry, twelve-case composition and mocked complete-pair/checker receipts only. Reference-manifest hash replaced only in authored fixture; prospective placeholder pins replaced only for development controls. No new empirical predictions or annotation payloads read, no inference.'}
    with Path(a.output).open('xb') as stream:stream.write(g.canonical(report))
    print(json.dumps({'status':report['status'],'passed':len(passed)}))
    if failure:print(failure['traceback']);return 1
    return 0


if __name__=='__main__':raise SystemExit(main())
