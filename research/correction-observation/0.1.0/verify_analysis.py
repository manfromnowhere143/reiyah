"""Check full-audit bounds, geometric worlds and every composed ambiguity witness."""
from copy import deepcopy
from fractions import Fraction
import json
from pathlib import Path
import sys
import time
from common import (FAMILIES, ROLES, VERSION, checker, conventional_measure, decision, digest,
                    file_digest, linked, native_graph, need, open_interval, put, q, w, wire_interval)


def changed(refs, removed, added):
    need(removed is None or sum(r['id']==removed for r in refs)==1,'Invalid edit subject')
    answer = [r for r in refs if r['id']!=removed]
    if added is not None:
        need(added['id'] not in {r['id'] for r in answer},'Duplicate added identity')
        answer.append(added)
    return answer


def main(area):
    area = Path(area).resolve(); tick = time.perf_counter()
    visible = json.loads((area/'inputs/visible.json').read_text())
    images = {im['id']:im for im in visible['images']}
    cases = {case['id']:case for case in visible['cases']}
    for name in ['FREEZE.json','REFINEMENT_FREEZE.json']:
        for entry in json.loads((area/name).read_text())['bindings']:
            need(file_digest(area/entry['path'])==entry['sha256'],'Frozen file changed')
    count = 0
    def check_measured(im,refs,measured):
        nonlocal count
        actual = conventional_measure(im,refs)
        need(actual['ranks']==measured['ranks'] and actual['delta']==measured['delta'],'Flow disagreement')
        graph = native_graph(im,refs)
        need(digest(graph)==measured['graph_sha256'],'Proof subject changed')
        checker.check(graph,measured['payload']); count += 1
        return q(actual['delta'])
    initial_dir = area/'runs/analysis-01'
    for entry in json.loads((initial_dir/'WITNESS_INDEX.json').read_text()):
        path = initial_dir/entry['path']; need(file_digest(path)==entry['sha256'],'Initial witness bytes changed')
        record = json.loads(path.read_text()); iid = record['image_id']
        refs = json.loads((area/'oracle'/(iid+'.json')).read_text())['answer']
        need(digest(refs)==record['observed_reference_sha256'],'Initial observed reference changed')
        op = record['operation']; need(op['kind'] in ('insert','delete','replace'),'Unknown edit')
        need(set(op)==({'kind','added'} if op['kind']=='insert' else {'kind','removed'} if op['kind']=='delete' else
                       {'kind','removed','added'}),'Invalid edit fields')
        altered = changed(refs,op.get('removed'),op.get('added'))
        need(altered==record['altered_references'],'Initial witness requires extra edits')
        check_measured(images[iid],altered,record['measurement'])
    initial_checked = count
    directory = area/'runs/refinement-01'
    results = json.loads((directory/'RESULTS.json').read_text())
    records = {}; lower = {}; upper = {}; nominal = {}; witness_delta = {}
    for iid,im in images.items():
        if not linked(im):
            continue
        record = json.loads((directory/(iid+'.json')).read_text()); records[iid] = record
        refs = json.loads((area/'oracle'/(iid+'.json')).read_text())['answer']
        need(digest(refs)==record['subject_reference_sha256'],'Refinement observation changed')
        any_output = any(im[role]['value'] for role in ROLES)
        expected = [None]+[r['id'] for r in refs] if any_output else [None]
        need([base['removed'] for base in record['bases']]==expected,'A deletion world was omitted')
        aa,bb = (len(im[role]['value']) for role in ROLES)
        los=[];his=[]
        for base in record['bases']:
            delta = check_measured(im,changed(refs,base['removed'],None),base['measurement'])
            ma,mb = base['measurement']['ranks']
            los.append(2*mb-2*min(aa,ma+1)-bb+aa)
            his.append(2*min(bb,mb+1)-2*ma-bb+aa)
            if base['removed'] is None:
                nominal[iid] = delta
                need(base['measurement']==record['nominal'],'Nominal identity changed')
        initial = open_interval(im)
        lower[iid],upper[iid] = max(initial[0],min(los)),min(initial[1],max(his))
        need(record['edit_bounds']==wire_interval((lower[iid],upper[iid])),'Refined bound not entailed')
        for direction in ['minimum','maximum']:
            if direction not in record['witnesses']:
                need(q(record[direction+'_found'])==nominal[iid],'Absent witness improved the nominal value')
                witness_delta[(iid,direction)] = nominal[iid]
                continue
            witness = record['witnesses'][direction]; world = witness['world']
            need(set(world)=={'removed','added'} and (world['removed'] is not None or world['added'] is not None),
                 'Not one admissible record edit')
            altered = changed(refs,world['removed'],world['added'])
            need(altered==witness['altered_references'],'Witness requires undeclared edits')
            actual = check_measured(im,altered,witness['measurement'])
            need(actual==q(record[direction+'_found']) and lower[iid]<=actual<=upper[iid], 'Witness value changed')
            witness_delta[(iid,direction)] = actual
    allocated = {(cid,family) for cid in cases for family in FAMILIES}; seen=set(); compositions=0
    for row in results['full_observation_rows']:
        key = row['case_id'],row['family']; need(key in allocated and key not in seen,'Duplicate/unknown full-audit row');seen.add(key)
        members = cases[key[0]]['images']; family = key[1]
        if any(not linked(images[i]) for i in members):
            need(row['decision']=='input_blocked' and row['bounds'] is None,'Missing output was hidden')
            continue
        size = len(members); n = sum(nominal[i] for i in members)/size
        if family=='exact_publisher':
            bounds = n,n
        elif family=='one_edit_per_image':
            bounds = sum(lower[i] for i in members)/size,sum(upper[i] for i in members)/size
        else:
            bounds = n-max(nominal[i]-lower[i] for i in members)/size,n+max(upper[i]-nominal[i] for i in members)/size
        need(row['bounds']==wire_interval(bounds) and row['decision']==decision(bounds) and q(row['nominal_delta'])==n,
             'Full-audit composition mismatch')
        if row['opposite_decision_witness']:
            edits = row['edits']; ids=[e['image_id'] for e in edits]
            need(set(ids)<=set(members) and len(set(ids))==len(ids),'Invalid edited membership')
            need(family!='exact_publisher' and (family!='one_edit_global' or len(edits)<=1),'Residual budget exceeded')
            alternative = n+sum(witness_delta[(e['image_id'],e['direction'])]-nominal[e['image_id']] for e in edits)/size
            need(alternative==q(row['alternative_delta']) and (alternative<=0 if n>0 else alternative>0),
                 'Claimed alternative does not reverse the strict decision')
            compositions += 1
    need(seen==allocated,'A full-audit case was omitted')
    need(count-initial_checked==results['native_checked_packets'],'Proof count differs')
    # Post-hoc corollary from checked worlds, not another selector experiment.
    members = cases['linked-58']['images']; n = sum(nominal[i] for i in members)
    need(n>0,'Corollary requires the recorded positive nominal margin')
    effects = sorted((witness_delta[(i,'minimum')]-nominal[i],i) for i in members)
    selected=[]; total=n
    for effect,iid in effects:
        if total<=0: break
        if effect<0:
            selected.append({'image_id':iid,'direction':'minimum','effect':w(effect)});total+=effect
    one_edit_lower = n-max(nominal[i]-lower[i] for i in members)
    need(one_edit_lower>0 and total<=0 and len(selected)==2,'Two-edit minimum corollary failed')
    corollary = {'artifact_id':'reiyah.correction-observation.two-edit-corollary','version':VERSION,
                 'status':'exploratory_post_hoc','case_id':'linked-58','nominal_delta':w(n/len(members)),
                 'all_single_edit_lower':w(one_edit_lower/len(members)), 'adverse_delta':w(total/len(members)),
                 'edits':selected,'minimum_arbitrary_edits_to_exclude_strict_improvement':2,
                 'scope':'Fixed outputs and eligible geometric reference edits; no physical error frequency or customer risk claim.'}
    put(directory/'TWO_EDIT_COROLLARY.json',corollary)
    report = {'artifact_id':'reiyah.correction-observation.analysis-verification','version':VERSION,
              'initial_native_witnesses':initial_checked,'refinement_native_packets':count-initial_checked,
              'full_observation_rows':len(seen),'checked_opposite_decision_compositions':compositions,
              'two_edit_minimum_verified':True,'seconds':time.perf_counter()-tick}
    put(directory/'VERIFICATION.json',report)
    print(json.dumps(report))


if __name__=='__main__':
    main(sys.argv[1])
