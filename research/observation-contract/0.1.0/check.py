"""Separate geometry, augmenting-path matching and native-certificate checking.

Does not import the completion producer or trust its declared padding geometry.
"""
from pathlib import Path
from fractions import Fraction
import argparse,sys,time
from source_io import ROOT,PACKET,ROLES,load_sources,context,guard,put,read,require,digest,q,w,binding
sys.path.insert(0,str(ROOT))
for folder in ('reference-timing','public-predictions'):sys.path.insert(0,str(ROOT/'research'/folder/'0.1.0'))
from timing_certificate import matching
from axis_certificate import exact_iou
from compare_math import graph,checker
from admission import digest as legacy_digest

def validate_world(image,known,unknown,parent,completed):
    require(unknown==sorted(set(unknown)),'invalid census')
    require(parent[:len(known)]==known and completed[:len(parent)]==parent,'known/parent world altered')
    require(len(completed)==len(known)+len(unknown)<=128,'complete census/reference cap differs')
    allowed={'timing-unknown:'+u for u in unknown}
    require(len({r['id'] for r in completed})==len(completed),'repeated reference identity')
    require({r['id'] for r in completed[len(known):]}==allowed,'full optional census differs')
    require(all(image[r]['state']=='observed' for r in ROLES),'unavailable predictions')
    for r in completed:
        require(set(r)=={'id','xyxy','record_sha256'},'rectangle properties differ')
        require(len(r['xyxy'])==4,'coordinate arity differs')
        x0,y0,x1,y1=map(q,r['xyxy'])
        require(0<=x0<x1<=image['width'] and 0<=y0<y1<=image['height'] and y1-y0>=25,'ineligible geometry')
    for r in completed[len(known):]:
        require(r['record_sha256']==legacy_digest({'basis':'optional-reference-hypothesis','id':r['id'],'xyxy':r['xyxy']}),'optional provenance differs')
    for r in completed[len(parent):]:
        for role in ROLES:
            for p in image[role]['value']:
                require(exact_iou(list(map(q,r['xyxy'])),list(map(q,p['xyxy'])))<Fraction(1,2),'added matching edge')
    return [r['id'] for r in completed[len(parent):]]

def verify_native(key,record):
    require(key==legacy_digest({'image':record['image'],'references':record['references']}),'proof identity differs')
    direct=matching(record['image'],record['references'])
    require(record['measurement']==direct,'matching differs')
    native=graph(record['image'],record['references']);payload=record['proof']['payload']
    require(record['proof']['graph_sha256']==legacy_digest(native),'native operand binding differs')
    checker.check(native,payload)
    require(payload['result']['enclosure_kind']=='exact_for_finite_model' and payload['result']['bounds']['lower']==payload['result']['bounds']['upper']==direct['delta'],'native result differs')
    return direct

def run(area):
    area=Path(area);guard(area);d=load_sources();a=read(area/'ALLOCATION.json');r=read(area/'RESULTS.json');tick=time.perf_counter()
    require(d['targets']==a['targets'] and d['bindings']==a['bindings'],'source allocation differs')
    require(r['freeze_sha256']==binding(PACKET/'freeze.json')['sha256'],'result freeze differs')
    expected=[{'section':section,'index':i,'sha256':digest(row),'decision':row['decision']} for section in ('primary_rows','anchor_rows') for i,row in enumerate(d['parent'][section])]
    require(r['parent_rows']==expected and len(expected)==7707,'parent rows changed')
    proofs={};measures={}
    for e in r['proofs']:
        require(binding(e['path'])=={k:e[k] for k in ('path','bytes','sha256')},'new proof bytes differ')
        require(e['key'] not in proofs,'duplicate proof')
        proofs[e['key']]=read(e['path']);measures[e['key']]=verify_native(e['key'],proofs[e['key']])
    require(len(r['rows'])==len(d['targets']),'target dropped')
    seen=set();used_proofs=set();old_measurements={};succeeded=0;incomplete=0;added_total=0
    for target,out in zip(d['targets'],r['rows']):
        require({k:out[k] for k in target}==target,'target identity changed')
        row=d['parent'][target['section']][target['index']];deltas=[];presence=[];all_complete=True
        require(len(out['jobs'])==len(row['world_proof_keys'])==2,'endpoint omitted')
        for j in (0,1):
            require(len(out['jobs'][j])==len(row['membership'])==row['allocated_images']==len(row['state_keys']),'member omitted')
            total=Fraction();signature=[]
            for key,sk,pk,iid in zip(out['jobs'][j],row['state_keys'],row['world_proof_keys'][j],row['membership']):
                image,known,unknown=context(d,sk,row['family'])
                require(image['id']==iid and key==digest({'image':image,'known':known,'unknown':unknown,'parent_proof':pk}),'job source binding differs')
                job=r['jobs'][key];require(job['parent_proof']==pk,'inherited endpoint substituted')
                if job['state']!='complete':
                    require(job['state']=='failed' and bool(job.get('error')),'failure omitted');all_complete=False;seen.add(key);continue
                np=job['new_proof'];record=proofs[np];parent=d['proofs'][pk];used_proofs.add(np)
                require(record['image']==parent['image']==image,'prediction image changed')
                require(job['census']==unknown and job['known_sha256']==digest(known),'census/known binding differs')
                if key not in seen:
                    added=validate_world(image,known,unknown,parent['references'],record['references'])
                    require(added==job['added_ids'],'padding identity differs');added_total+=len(added)
                    if pk not in old_measurements:old_measurements[pk]=matching(image,parent['references'])
                    require(old_measurements[pk]==parent['measurement']==measures[np],'completion changes matching ranks')
                seen.add(key);total+=q(measures[np]['delta'])
                signature.append((iid,sorted(x['id'] for x in record['references'][len(known):])))
            deltas.append(w(total/row['allocated_images']));presence.append(signature)
        if all_complete:
            require(out['state']=='same_presence_opposite_decisions' and out['attained']==deltas==row['attained'],'attained aggregate changed')
            require(presence[0]==presence[1] and q(deltas[0])<=0<q(deltas[1]),'presence distinguishes worlds or decision does not oppose')
            require(q(row['bounds'][0])<=q(deltas[0])<=q(deltas[1])<=q(row['bounds'][1]),'inherited bound contradicted');succeeded+=1
        else:require(out['state']=='incomplete_inherited_evidence_retained' and out['attained'] is None,'incomplete result overstated');incomplete+=1
    require(seen==set(r['jobs']) and used_proofs==set(proofs),'extra unallocated job/proof')
    report={'artifact_id':'reiyah.observation-contract.verification','version':'0.1.0','status':'exploratory','results_sha256':binding(area/'RESULTS.json')['sha256'],'same_presence_opposite_decisions':succeeded,'incomplete':incomplete,'parent_rows_unchanged':len(expected),'checked_jobs':len(seen),'new_native_proofs_checked':len(proofs),'parent_matching_recomputations':len(old_measurements),'added_references_across_distinct_jobs':added_total,'seconds':time.perf_counter()-tick,'independent_scientific_replication':False}
    put(area/'VERIFICATION.json',report);print(report)
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('area');run(parser.parse_args().area)
