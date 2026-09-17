"""Post-run, predeclared geometric adverse search; never feeds the selectors."""
from collections import Counter
from copy import deepcopy
from fractions import Fraction
import json
from pathlib import Path
import sys
import time
from common import (ARMS, FAMILIES, VERSION, conventional_measure, decision, digest, file_digest,
                    interval, linked, native_measure, need, put, q, w, wire_interval)


def change(refs, operation):
    result = deepcopy(refs)
    if operation['kind'] in ('delete', 'replace'):
        need(sum(r['id'] == operation['removed'] for r in result) == 1, 'Invalid deletion/replacement subject')
        result = [r for r in result if r['id'] != operation['removed']]
    if operation['kind'] in ('insert', 'replace'):
        result.append(deepcopy(operation['added']))
    return result


def variants(image, refs):
    for ref in refs:
        yield {'kind':'delete','removed':ref['id']}
    geometries = {}
    for role in ('output_a','output_b'):
        for row in image[role]['value']:
            geometries.setdefault(digest(row['xyxy']), row['xyxy'])
    for index, xyxy in enumerate(geometries.values()):
        added = {'id':'adverse:'+image['id']+':'+str(index),'xyxy':deepcopy(xyxy),
                 'record_sha256':digest({'basis':'hypothetical_one_edit', 'image':image['id'], 'xyxy':xyxy})}
        yield {'kind':'insert','added':added}
        for ref in refs:
            yield {'kind':'replace','removed':ref['id'],'added':added}


def main(area):
    area = Path(area).resolve(); tick = time.perf_counter()
    visible = json.loads((area/'inputs/visible.json').read_text())
    images = {im['id']:im for im in visible['images']}
    run_dir = area/'runs/assay-01'
    results = json.loads((run_dir/'RESULTS.json').read_text())
    need(len(results['rows']) == 984 and (run_dir/'REPLAY.json').exists(), 'Analyze only after complete run and replay')
    analysis_dir = area/'runs/analysis-01'; analysis_dir.mkdir()
    nominal = {}; original = {}; extremes = {}; checked_witnesses = []; candidates = 0
    for im in visible['images']:
        iid = im['id']
        if not linked(im):
            continue
        refs = json.loads((area/'oracle'/(iid+'.json')).read_text())['answer']
        nominal[iid] = conventional_measure(im,refs)
        original[iid] = conventional_measure(im,im['original_reference'])
        n = q(nominal[iid]['delta'])
        low = high = n; low_op = high_op = None; attempted = 0
        if im['output_a']['value'] or im['output_b']['value']:
            for operation in variants(im,refs):
                if attempted == 4096:
                    break
                attempted += 1
                actual = q(conventional_measure(im,change(refs,operation))['delta'])
                if actual < low:
                    low, low_op = actual, operation
                if actual > high:
                    high, high_op = actual, operation
        candidates += attempted
        extremes[iid] = {'nominal':w(n),'minimum_found':w(low),'maximum_found':w(high),
                         'minimum_edit':low_op,'maximum_edit':high_op,'candidates':attempted}
        for direction, target, operation in [('minimum',low,low_op),('maximum',high,high_op)]:
            if operation is not None:
                altered = change(refs,operation)
                measured = native_measure(im,altered)
                need(q(measured['delta']) == target, 'Adverse independent/native matching mismatch')
                payload = {'image_id':iid,'direction':direction,'operation':operation,
                           'observed_reference_sha256':digest(refs),'altered_references':altered,'measurement':measured}
                name = iid+'.'+direction+'.json'; put(analysis_dir/name,payload)
                checked_witnesses.append({'path':name,'sha256':file_digest(analysis_dir/name)})
    put(analysis_dir/'EXTREMES.json',extremes)
    full = []; full_index = {}
    for case in visible['cases']:
        members = [images[i] for i in case['images']]
        complete = all(linked(im) for im in members)
        n = sum(q(nominal[im['id']]['delta']) for im in members)/len(members) if complete else None
        for family in FAMILIES:
            bounds = interval(members,nominal,family)
            row = {'case_id':case['id'],'group':case['group'],'family':family,'nominal_delta':None if n is None else w(n),
                   'full_observation_bounds':wire_interval(bounds),'full_observation_decision':decision(bounds),
                   'opposite_decision_witness':False,'alternative_delta':None,'edits':[]}
            if complete and family != 'exact_publisher' and decision(bounds) == 'unresolved':
                target = 'minimum' if n > 0 else 'maximum'
                changes = [(im['id'],q(extremes[im['id']][target+'_found'])-q(nominal[im['id']]['delta'])) for im in members]
                if family == 'one_edit_global':
                    chosen = [min(changes,key=lambda x:x[1]) if n > 0 else max(changes,key=lambda x:x[1])]
                else:
                    chosen = changes
                alternative = n + sum(effect for _,effect in chosen)/len(members)
                opposite = alternative <= 0 if n > 0 else alternative > 0
                if opposite:
                    row['opposite_decision_witness'] = True; row['alternative_delta'] = w(alternative)
                    row['edits'] = [{'image_id':iid,'direction':target} for iid,effect in chosen if effect]
                    # Each edit is in the per-image family; global is at most one.
                    need(family != 'one_edit_global' or len(row['edits']) <= 1, 'Global budget exceeded')
            full.append(row); full_index[(case['id'],family)] = row
    for entry in results['rows']:
        result = entry['result']; row = full_index[(result['case_id'],result['family'])]
        if result['decision'] in ('supported','excluded'):
            n = q(row['nominal_delta'])
            need((n > 0) == (result['decision'] == 'supported'), 'Reported stop rejects an admitted nominal world')
            need(not row['opposite_decision_witness'], 'Accepted decision contradicted by one-edit witness')
    put(analysis_dir/'FULL_OBSERVATIONS.json',full)
    put(analysis_dir/'WITNESS_INDEX.json',checked_witnesses)
    summaries = []
    for family in FAMILIES:
        for group in ['singleton','block','complete_cohort','admitted_cohort','all_dependent_cases']:
            for arm in ARMS:
                rows = [e['result'] for e in results['rows'] if e['result']['family']==family and e['result']['arm']==arm
                        and (e['result']['group']==group or group=='all_dependent_cases')]
                ambiguity = [r for r in full if r['family']==family and (r['group']==group or group=='all_dependent_cases')]
                summaries.append({'family':family,'group':group,'arm':arm,'cases':len(rows),
                    'decisions':dict(Counter(r['decision'] for r in rows)), 'queries':sum(r['queries'] for r in rows),
                    'zero_query_decisions':sum(r['queries']==0 and r['decision'] in ('supported','excluded') for r in rows),
                    'full_observation_unresolved':sum(r['full_observation_decision']=='unresolved' for r in ambiguity),
                    'proven_instrument_ambiguities':sum(r['opposite_decision_witness'] for r in ambiguity),
                    'timing':{key:sum(r['timing'][key] for r in rows) for key in rows[0]['timing']}})
    public_rows = []
    for entry in results['rows']:
        result = entry['result']; truth = full_index[(result['case_id'],result['family'])]
        public_rows.append({k:result[k] for k in ['case_id','group','arm','family','decision','queries','query_budget','bounds','stop_reason']}
                           | {'opposite_decision_witness':truth['opposite_decision_witness']})
    # IDs here are experiment ordinals; no source IDs, coordinates or source rows go into Git.
    report = {'artifact_id':'reiyah.correction-observation.summary','version':VERSION,'status':'exploratory',
        'source_scope':'Previously exposed development; 64 images, 58 linked, six blocked; dependent case groups.',
        'assigned_rows':len(public_rows),'source_cases':82,'one_edit_candidates':candidates,
        'native_checked_extreme_witnesses':len(checked_witnesses), 'summaries':summaries, 'rows':public_rows,
        'original_to_corrected_strict_decision_changes':sum((q(original[i]['delta'])>0)!=(q(nominal[i]['delta'])>0) for i in nominal),
        'compute_seconds':{'experiment':results['seconds'],'analysis':time.perf_counter()-tick},
        'human_cost':None,'total_cost':None,'reserved_outcomes_opened':False,
        'decision':'Stop selection/stopping superiority claims on this family. Product economics inconclusive; no platform expansion.'}
    put(analysis_dir/'SUMMARY.json',report)
    print(json.dumps({k:v for k,v in report.items() if k not in ('summaries','rows')}))
    for row in summaries:
        if row['arm']=='A' and row['group']=='all_dependent_cases':
            print(json.dumps(row))


if __name__ == '__main__':
    main(sys.argv[1])
