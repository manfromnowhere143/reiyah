#!/usr/bin/env python3
"""Authored native-boundary and mocked admission controls; no empirical inputs."""
import argparse
import copy
from decimal import Decimal
from fractions import Fraction
import json
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


def image(model, rows):
    return {'artifact_id': 'reiyah.multiorg.complete-analysis-image', 'version': '0.5.0', 'status': 'complete',
        'image_id': g.IMAGE, 'model': model, 'model_variant': g.VARIANTS[model], 'model_source_sha256': g.PINS[model],
        'completion_scope': g.SCOPE, 'storage_output_status': g.STORAGE,
        'tile_count_expected': 156, 'tile_count_completed': 156,
        'image_shape_hw': [5720, 6385], 'rescaled_shape_hw': [2860, 3192], 'raw_onnx_rows': len(rows),
        'analysis_predictions': rows, 'empty_analysis': not bool(rows)}


def row(index=0):
    return {'id': index, 'tile_ordinal': 0, 'original_row_index': index, 'box_xyxy': [0, 0, 2, 2], 'score': Decimal('0.75')}


def persisted(path, value):
    # Only the authored fixture writer converts the exact .75 score for JSON.
    def decimal(v):
        if isinstance(v, Decimal): return float(v)
        raise TypeError(type(v).__name__)
    path.write_text(json.dumps(value, sort_keys=True, separators=(',', ':'), default=decimal) + '\n')
    return {'path': str(path), 'sha256': g.sha(path.read_bytes())}


def fixture(root, repository):
    contract, deps = g.dependencies(repository)
    sources = root / 'references'; sources.mkdir()
    annotations = []
    for procedure, count in g.COUNTS.items():
        data = {str(i): [[10*i, 10*i], [10*i+2, 10*i], [10*i+2, 10*i+2], [10*i, 10*i+2]] for i in range(count)}
        filename = procedure + '.json'; descriptor = persisted(sources / filename, data)
        annotations.append({'procedure': procedure, 'source_path': 'authored/' + filename, 'local_path': filename,
                            'sha256': descriptor['sha256'], 'byte_size': (sources / filename).stat().st_size, 'transport_valid': True})
    refs = {'artifact_id': 'reiyah.multiorg.annotation-manifest', 'version': '0.1.0',
            'images': [{'tiff_path': g.IMAGE, 'annotations': annotations}] + [{'tiff_path': 'authored-' + str(i), 'annotations': []} for i in range(54)]}
    rm = persisted(root / 'references.json', refs)
    observations = []
    for model in g.MODELS:
        value = image(model, [row()] if model == 'faster' else [])
        d = persisted(root / (model + '.json'), value)
        observations.append({'file': Path(d['path']).name, 'sha256': d['sha256'], 'bytes': Path(d['path']).stat().st_size,
            'image_id': g.IMAGE, 'model': model, 'model_variant': g.VARIANTS[model],
            'analysis_count': len(value['analysis_predictions']), 'raw_onnx_rows': value['raw_onnx_rows'], 'completion_scope': g.SCOPE})
    pair = {'artifact_id': 'reiyah.multiorg.complete-analysis-pair', 'version': '0.5.0', 'status': 'complete', 'stage': 'complete',
        'completion_scope': g.SCOPE, 'storage_output_status': g.STORAGE, 'model_variants': g.VARIANTS,
        'forward_passes_started': 312, 'forward_passes_completed': 312,
        'tile_coverage': {m: {'captured': 156, 'admitted': 156, 'complete': True} for m in g.MODELS},
        'runner_sha256': contract['qualified_pair_worker_sha256'], 'manifest_sha256': 'b'*64, 'source_bindings': {k: {'sha256': v} for k, v in g.PINS.items()},
        'observations': observations}
    pd = persisted(root / 'pair.json', pair)
    supervisor = persisted(root / 'process.json', {'status': 'complete', 'returncode': 0, 'termination_reason': None,
        'runner_sha256': contract['qualified_pair_worker_sha256'], 'manifest_sha256': 'b'*64, 'result_sha256': pd['sha256']})
    check = {'status': 'complete_pair_verified', 'complete_pairs': 1, 'result_sha256': pd['sha256'],
        'process_receipt_sha256': supervisor['sha256'], 'manifest_sha256': 'b'*64, 'checker_sha256': contract['qualified_pair_checker_sha256'],
        'source_bindings': g.PINS, 'observations': observations}
    cd = persisted(root / 'check.json', check)
    ce = persisted(root / 'check-process.json', {'returncode': 0, 'report_sha256': cd['sha256'], 'checker_sha256': contract['qualified_pair_checker_sha256']})
    manifest = {'artifact_id': 'reiyah.multiorg.analysis-matching-input', 'version': '0.5.0', 'contract_sha256': g.CONTRACT_SHA,
        'pair': pd, 'supervisor': supervisor, 'pair_checker': cd, 'checker_execution': ce,
        'reference_manifest': rm, 'reference_root': str(sources)}
    md = persisted(root / 'input.json', manifest)
    contract = copy.deepcopy(contract)
    contract['reference_manifest_sha256'] = rm['sha256']
    return md, contract, deps


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--repository', required=True); parser.add_argument('--output', required=True)
    a = parser.parse_args(); started = time.monotonic(); passed = []; failure = None
    def case(name, action):
        action(); passed.append(name)
    try:
        n = g.native(a.repository); flow = checker.oracle()
        refs = [('r0', (Fraction(0), Fraction(0), Fraction(2), Fraction(2)))]
        def fixed(aa, bb=None, rr=None):
            return n.fixed_case(g.IMAGE, 't0', aa, [] if bb is None else bb, refs if rr is None else rr, 'c'*64)[0]
        for count in (129, 1024):
            def boundary(count=count):
                cell = fixed(detections(count)); assert cell['detections_a'] == count and cell['tp_a'] == 0
                assert flow.matching([d[1] for d in detections(count)], [r[1] for r in refs]) == 0
            case('native_and_maxflow_accept_' + str(count) + '_detections', boundary)
        case('1025_detections_refused', lambda: rejected(lambda: fixed(detections(1025)), 'cap exceeded'))
        case('129_references_refused', lambda: rejected(lambda: fixed([], rr=[('r'+str(i), refs[0][1]) for i in range(129)]), 'cap exceeded'))
        case('combined_edges_over2048_refused', lambda: rejected(lambda: fixed(detections(1024, (0,0,2,2)), rr=[('r'+str(i),refs[0][1]) for i in range(3)]), 'edge cap'))
        def work():
            many = [refs[0]] + [('r'+str(i),(Fraction(10*i),Fraction(10*i),Fraction(10*i+2),Fraction(10*i+2))) for i in range(1,128)]
            rejected(lambda: fixed(detections(1024,(0,0,2,2)), rr=many), 'screening-work cap')
        case('native_work_cap_preserved', work)
        def half():
            yes = fixed(detections(1,(0,0,1,2))); no = fixed(detections(1,(0,0,1,1)))
            assert yes['tp_a'] == 1 and no['tp_a'] == 0
            assert flow.matching([(0,0,1,2)],[(0,0,2,2)]) == 1
            assert flow.matching([(0,0,1,1)],[(0,0,2,2)]) == 0
        case('exact_continuous_IoU_half_boundary', half)
        def augment():
            aa = [('faster-0',tuple(map(Fraction,(0,0,3,2))),'a'*64),('faster-1',tuple(map(Fraction,(0,0,2,2))),'b'*64)]
            rr = refs + [('r1',tuple(map(Fraction,(1,0,3,2))))]
            assert fixed(aa,rr=rr)['tp_a'] == flow.matching([x[1] for x in aa],[x[1] for x in rr]) == 2
        case('non_greedy_augmenting_path', augment)
        def duplicates():
            aa=detections(3,(0,0,2,2)); rr=[('r0',refs[0][1]),('r1',refs[0][1])]
            assert fixed(aa,rr=rr)['tp_a'] == flow.matching([x[1] for x in aa],[x[1] for x in rr]) == 2
        case('duplicate_geometry_preserves_distinct_identities', duplicates)
        def equal_loss():
            cells=[dict(fixed([]),procedure=p) for p in g.PROCEDURES]
            result=n.compose(cells,[g.IMAGE],False)
            assert result['global']['decision']=='unresolved' and result['global']['lower_procedure']=='t0'
            assert result['global']['lower']==result['imagewise']['lower']=='0/1'
            assert result['primary_status']=='inconclusive_incomplete_selected_cohort'
        case('strict_zero_and_lexical_tie_and_single_image_scope', equal_loss)
        case('complete_observed_empty_is_allowed',lambda: g.analysis_rows(image('faster',[]),'faster'))
        def mutate(name, change, text):
            def action():
                obj=image('faster',[row()]);change(obj)
                rejected(lambda: g.analysis_rows(obj,'faster'),text)
            case(name,action)
        mutate('missing_is_not_empty',lambda x:x.pop('analysis_predictions'),'missing or native')
        mutate('missing_model_is_not_empty',lambda x:x.update(status='failed'),'complete image')
        mutate('wrong_variant_refused',lambda x:x.update(model_variant='original'),'variant/source')
        mutate('wrong_model_digest_refused',lambda x:x.update(model_source_sha256='d'*64),'variant/source')
        mutate('complete_storage_claim_refused',lambda x:x.update(storage_predictions=[]),'analysis-only')
        mutate('incomplete_coverage_refused',lambda x:x.update(tile_count_completed=155),'tile counts')
        mutate('boolean_count_refused',lambda x:x.update(tile_count_completed=True),'tile counts')
        mutate('duplicate_prediction_ID_refused',lambda x:x.update(raw_onnx_rows=2,analysis_predictions=[row(),row()]),'analysis identity')
        mutate('analysis_score_equal_half_refused',lambda x:x['analysis_predictions'][0].update(score=Decimal('.5')),'strict analysis')
        mutate('nonpositive_high_geometry_refused',lambda x:x['analysis_predictions'][0].update(box_xyxy=[0,0,0,2]),'positive exact')
        mutate('coordinate_cap_preserved',lambda x:x['analysis_predictions'][0].update(box_xyxy=[0,0,10000001,2]),'coordinate domain')
        mutate('boolean_coordinate_refused',lambda x:x['analysis_predictions'][0].update(box_xyxy=[False,0,2,2]),'coordinate domain')
        def maximum_rows():
            obj=image('faster',[row(i) for i in range(1024)]);assert len(g.analysis_rows(obj,'faster'))==1024
            obj=image('faster',[row(i) for i in range(1025)])
            rejected(lambda:g.analysis_rows(obj,'faster'),'native detection cap')
        case('analysis_adapter1024_boundary',maximum_rows)
        def end_to_end():
            with tempfile.TemporaryDirectory(prefix='authored-',dir=g.HERE) as tmp:
                root=Path(tmp);d,contract,deps=fixture(root,a.repository)
                with patch.object(g,'dependencies',return_value=(contract,deps)):
                    result=producer.run(d['path'],d['sha256'],a.repository,root/'matched')
                    rp=root/'matched/result.json'; digest=g.sha(rp.read_bytes())
                    checked=checker.run(d['path'],d['sha256'],a.repository,rp,digest)
                    assert checked['status']=='passed' and len(checked['cells'])==3
                    assert result['global']['lower']==result['global']['upper']=='-1/1'
                    original=rp.read_bytes()
                    for key in ('producer_sha256','admission_sha256'):
                        obj=json.loads(original);obj[key]='0'*64;rp.write_bytes(g.canonical(obj))
                        rejected(lambda:checker.run(d['path'],d['sha256'],a.repository,rp,g.sha(rp.read_bytes())),'implementation provenance')
                    rp.write_bytes(original)
                    obj=json.loads(rp.read_bytes());obj['cells'][0]['tp_a']=0;rp.write_bytes(g.canonical(obj))
                    rejected(lambda:checker.run(d['path'],d['sha256'],a.repository,rp,g.sha(rp.read_bytes())),'independent cell tp_a')
                    rejected(lambda:g.load_inputs(d['path'],'0'*64,a.repository),'bound file digest')
        case('mocked_complete_admission_native_three_cases_oracle_and_tamper',end_to_end)
        def bad_admission():
            for name in ('result_digest','checker_failed','checker_execution_failed','pair_incomplete'):
                with tempfile.TemporaryDirectory(prefix='authored-',dir=g.HERE) as tmp:
                    root=Path(tmp);d,c,deps=fixture(root,a.repository);m=json.loads(Path(d['path']).read_bytes())
                    which='pair' if name=='pair_incomplete' else 'checker_execution' if name=='checker_execution_failed' else 'pair_checker'
                    target=Path(m[which]['path']);value=json.loads(target.read_bytes())
                    if name=='result_digest':value['result_sha256']='0'*64
                    elif name=='checker_failed':value['status']='failed_attempt_partial_ledger_checked'
                    elif name=='checker_execution_failed':value['returncode']=1
                    else:value['status']='failed'
                    m[which]=persisted(target,value);d=persisted(root/'input.json',m)
                    with patch.object(g,'dependencies',return_value=(c,deps)):
                        rejected(lambda:g.load_inputs(d['path'],d['sha256'],a.repository),
                            {'result_digest':'checker pair/process','checker_failed':'checker complete state','checker_execution_failed':'checker execution','pair_incomplete':'complete pair required'}[name])
        case('admission_result_hash_and_checker_and_execution_fail_closed',bad_admission)
        def self_consistent_wrong_code():
            for which in ('worker','checker'):
                with tempfile.TemporaryDirectory(prefix='authored-',dir=g.HERE) as tmp:
                    root=Path(tmp);d,c,deps=fixture(root,a.repository);m=json.loads(Path(d['path']).read_bytes())
                    pair=json.loads(Path(m['pair']['path']).read_bytes());sup=json.loads(Path(m['supervisor']['path']).read_bytes())
                    check=json.loads(Path(m['pair_checker']['path']).read_bytes());execution=json.loads(Path(m['checker_execution']['path']).read_bytes())
                    if which=='worker':pair['runner_sha256']=sup['runner_sha256']='d'*64
                    else:check['checker_sha256']=execution['checker_sha256']='d'*64
                    m['pair']=persisted(root/'pair.json',pair);sup['result_sha256']=m['pair']['sha256']
                    m['supervisor']=persisted(root/'process.json',sup)
                    check['result_sha256']=m['pair']['sha256'];check['process_receipt_sha256']=m['supervisor']['sha256']
                    m['pair_checker']=persisted(root/'check.json',check);execution['report_sha256']=m['pair_checker']['sha256']
                    m['checker_execution']=persisted(root/'check-process.json',execution);d=persisted(root/'input.json',m)
                    with patch.object(g,'dependencies',return_value=(c,deps)):
                        rejected(lambda:g.load_inputs(d['path'],d['sha256'],a.repository),'qualified pair '+which)
        case('internally_consistent_unqualified_worker_and_checker_rejected',self_consistent_wrong_code)
    except Exception as exc:
        failure={'exception':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc()}
    report={'status':'passed' if failure is None else 'failed','count':len(passed),'controls':passed,'failure':failure,
        'wall_seconds':time.monotonic()-started,'python':platform.python_version(),
        'scripts':{p.name:g.sha(p.read_bytes()) for p in g.HERE.glob('*.py')},'contract_sha256':g.CONTRACT_SHA,
        'scope':'Authored geometry/count boundaries and mocked complete-pair/checker receipts only. Reference-manifest digest is replaced only inside the authored admission fixture. Native dependencies and arithmetic are real, exact-bound and unchanged. No actual pair or source annotations read; no inference.'}
    with Path(a.output).open('xb') as stream:stream.write(g.canonical(report))
    print(json.dumps({'status':report['status'],'passed':len(passed)}))
    if failure:print(failure['traceback']);return 1
    return 0


if __name__=='__main__':raise SystemExit(main())
