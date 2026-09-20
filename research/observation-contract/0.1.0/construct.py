"""Complete optional censuses with isolated references; no search or inference."""
from fractions import Fraction
from pathlib import Path
import argparse,sys,time
from source_io import ROOT,PACKET,ROLES,load_sources,context,guard,put,read,require,digest,q,w,binding
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'research/operating-policy/0.1.0'))
from operating_math import measured_world
from compare_math import validate_rows,validate_canvas,iou
from admission import digest as legacy_digest

def complete(image,known,unknown,references):
    require(unknown==sorted(set(unknown)),'invalid census')
    require(references[:len(known)]==known,'known references changed')
    require(all(image[r]['state']=='observed' for r in ROLES),'unavailable predictions')
    require(len(known)+len(unknown)<=128,'reference cap')
    validate_rows(references);validate_canvas(references,image)
    allowed={'timing-unknown:'+u for u in unknown}
    optional=references[len(known):];present={r['id'] for r in optional}
    require(len(present)==len(optional) and present<=allowed,'unknown identity reused or foreign')
    predictions=[r for role in ROLES for r in image[role]['value']]
    areas=[(q(r['xyxy'][2])-q(r['xyxy'][0]))*(q(r['xyxy'][3])-q(r['xyxy'][1])) for r in predictions]
    require(image['height']>=25 and image['width']>0 and all(a>0 for a in areas),'null rectangle premise invalid')
    width=min([Fraction(1),Fraction(image['width'])]+[a/100 for a in areas])
    geometry=list(map(w,(0,0,width,25)));added=[]
    for identity in sorted(allowed-present):
        body={'id':identity,'xyxy':geometry}
        added.append({**body,'record_sha256':legacy_digest({'basis':'optional-reference-hypothesis',**body})})
    validate_rows(known+optional+added);validate_canvas(added,image)
    require(all(iou(a,b)<Fraction(1,2) for a in added for b in predictions),'padding has a matching edge')
    return references+added,[r['id'] for r in added]

def job_identity(image,known,unknown,parent_key):
    return digest({'image':image,'known':known,'unknown':unknown,'parent_proof':parent_key})

def run(area):
    area=Path(area);freeze=guard(area);d=load_sources();a=read(area/'ALLOCATION.json')
    require(d['targets']==a['targets'] and d['pairs']==[tuple(z) for z in a['pairs']] and d['bindings']==a['bindings'],'allocation differs')
    start=time.perf_counter();jobs={};cache={};rows=[]
    for target in d['targets']:
        row=d['parent'][target['section']][target['index']];endpoints=[]
        for endpoint,oldkeys in enumerate(row['world_proof_keys']):
            keys=[]
            require(len(oldkeys)==len(row['state_keys'])==row['allocated_images'],'parent membership differs')
            for state_key,parent_key in zip(row['state_keys'],oldkeys):
                image,known,unknown=context(d,state_key,row['family']);key=job_identity(image,known,unknown,parent_key)
                if key not in jobs:
                    require(len(jobs)<freeze['max_jobs'],'job cap')
                    try:
                        parent=d['proofs'][parent_key];require(parent['image']==image,'source proof image differs')
                        completed,added=complete(image,known,unknown,parent['references'])
                        newkey=measured_world(image,completed,cache)
                        require(cache[newkey]['measurement']==parent['measurement'],'completion changed loss')
                        jobs[key]={'state':'complete','parent_proof':parent_key,'new_proof':newkey,'added_ids':added,'census':unknown,'known_sha256':digest(known)}
                    except Exception as exc:
                        jobs[key]={'state':'failed','parent_proof':parent_key,'error':type(exc).__name__+': '+str(exc)}
                keys.append(key)
            endpoints.append(keys)
        complete_row=all(jobs[k]['state']=='complete' for side in endpoints for k in side)
        attained=None
        if complete_row:
            attained=[w(sum((q(cache[jobs[k]['new_proof']]['measurement']['delta']) for k in side),Fraction())/row['allocated_images']) for side in endpoints]
            require(attained==row['attained'] and q(attained[0])<=0<q(attained[1]),'opposing decisions changed')
        rows.append({**target,'state':'same_presence_opposite_decisions' if complete_row else 'incomplete_inherited_evidence_retained','jobs':endpoints,'attained':attained})
    proof_records=[]
    for key,record in sorted(cache.items()):
        path=area/'proofs'/(key+'.json');put(path,record);proof_records.append({'key':key,**binding(path)})
    result={'artifact_id':'reiyah.observation-contract.results','version':'0.1.0','status':'exploratory','freeze_sha256':binding(PACKET/'freeze.json')['sha256'],'rows':rows,'jobs':jobs,'proofs':proof_records,'parent_rows':[{'section':section,'index':i,'sha256':digest(row),'decision':row['decision']} for section in ('primary_rows','anchor_rows') for i,row in enumerate(d['parent'][section])],'seconds':time.perf_counter()-start,'reserved_outcomes_accessed':0,'new_image_reads':0,'new_model_calls':0,'human_seconds':None,'economic_saving':None}
    put(area/'RESULTS.json',result)
    print({'rows':len(rows),'jobs':len(jobs),'new_proofs':len(cache),'failed_jobs':sum(j['state']!='complete' for j in jobs.values()),'seconds':result['seconds']})
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('area');run(parser.parse_args().area)
