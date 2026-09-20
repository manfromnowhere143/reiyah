"""Authored finite and adversarial controls; no empirical source loading."""
from copy import deepcopy
from fractions import Fraction
from itertools import product
from pathlib import Path
import argparse,json
from source_io import require,w
from construct import complete,measured_world,legacy_digest
from check import validate_world,verify_native,matching

def rectangle(identity,coords):
    body={'id':identity,'xyxy':list(map(w,coords))}
    basis={'basis':'optional-reference-hypothesis',**body} if identity.startswith('timing-unknown:') else body
    return {**body,'record_sha256':legacy_digest(basis)}
def image(a,b,width=400,height=100):
    return {'id':'authored','ordinal':0,'width':width,'height':height,'image_sha256':'0'*64,'policy_sha256':'1'*64,'reference_input_state':'available','output_a':{'state':'observed','value':a},'output_b':{'state':'observed','value':b}}
def run():
    passed=[]
    def reject(name,fn):
        try:fn()
        except (ValueError,AssertionError,ZeroDivisionError,KeyError,TypeError) as exc:passed.append({'id':name,'expected_rejection':type(exc).__name__});return
        raise AssertionError('forgery accepted: '+name)
    a=rectangle('prediction:a',(0,0,100,100));b=rectangle('prediction:b',(200,0,300,100));im=image([a],[b]);ids=['u0','u1','u2']
    pool=[(0,0,100,100),(200,0,300,100),(100,0,101,25)]
    count=0;cache={}
    for budget in range(4):
        for used in range(budget+1):
            for choices in product(range(len(pool)),repeat=used):
                parent=[rectangle('timing-unknown:'+u,pool[i]) for u,i in zip(ids,choices)]
                new,added=complete(im,[],ids[:budget],parent)
                require(validate_world(im,[],ids[:budget],parent,new)==added,'completion invalid')
                key=measured_world(im,new,cache);require(verify_native(key,cache[key])==matching(im,parent),'finite matching changed');count+=1
    passed.append({'id':'all_ordered_optional_worlds_budgets_0_to_3','cases':count,'native_worlds':len(cache)})
    low=[rectangle('timing-unknown:u0',pool[0])];high=[rectangle('timing-unknown:u0',pool[1])]
    lo,_=complete(im,[],ids[:2],low);hi,_=complete(im,[],ids[:2],high)
    require([r['id'] for r in lo]==[r['id'] for r in hi] and matching(im,lo)['delta']==w(-2) and matching(im,hi)['delta']==w(2),'opposing same-presence control fails')
    passed.append({'id':'same_presence_opposing_decisions','cases':1})
    empty=image([],[]);out,_=complete(empty,[],ids,[]);require(matching(empty,out)['delta']==w(0),'empty outputs differ');passed.append({'id':'zero_predictions_retains_census','cases':1})
    narrow=image([rectangle('prediction:n',(0,0,Fraction(1,10000),25))],[])
    out,_=complete(narrow,[],['u0'],[]);validate_world(narrow,[],['u0'],[],out);passed.append({'id':'tiny_positive_width','cases':1})
    known=[rectangle('reference:k',(0,0,100,100))];out,_=complete(im,known,ids,known);validate_world(im,known,ids,known,out);passed.append({'id':'known_prefix_preserved','cases':1})
    reject('unavailable_prediction',lambda:complete({**im,'output_a':{'state':'unavailable','reason':'missing'}},[],ids,[]))
    reject('duplicate_census',lambda:complete(im,[],['u0','u0'],[]))
    reject('foreign_identity',lambda:complete(im,[],['u1'],low))
    reject('known_changed',lambda:complete(im,known,ids,[]))
    reject('reference_cap',lambda:complete(im,[],['u'+str(i).zfill(3) for i in range(129)],[]))
    reject('short_canvas',lambda:complete(image([],[],height=24),[],ids,[]))
    reject('missing_present_identity',lambda:validate_world(im,[],ids[:2],low,lo[:-1]))
    repeat=deepcopy(lo);repeat[-1]=deepcopy(repeat[0]);reject('duplicate_reference',lambda:validate_world(im,[],ids[:2],low,repeat))
    edges=deepcopy(lo);edges[-1]=rectangle(edges[-1]['id'],pool[0]);reject('padding_matching_edge',lambda:validate_world(im,[],ids[:2],low,edges))
    short=deepcopy(lo);short[-1]=rectangle(short[-1]['id'],(0,0,1,24));reject('ineligible_height',lambda:validate_world(im,[],ids[:2],low,short))
    off=deepcopy(lo);off[-1]=rectangle(off[-1]['id'],(-1,0,0,25));reject('outside_canvas',lambda:validate_world(im,[],ids[:2],low,off))
    altered=deepcopy(lo);altered[0]['xyxy'][0]=w(1);reject('changed_inherited_geometry',lambda:validate_world(im,[],ids[:2],low,altered))
    forged=deepcopy(lo);forged[-1]['record_sha256']='0'*64;reject('forged_provenance',lambda:validate_world(im,[],ids[:2],low,forged))
    key=measured_world(im,lo,cache);record=deepcopy(cache[key]);record['measurement']['delta']=w(7);reject('forged_matching',lambda:verify_native(key,record))
    record=deepcopy(cache[key]);record['proof']['graph_sha256']='0'*64;reject('wrong_native_operand',lambda:verify_native(key,record))
    record=deepcopy(cache[key]);record['proof']['payload']['result']['bounds']['upper']=w(7);reject('forged_native_bound',lambda:verify_native(key,record))
    reject('wrong_proof_identity',lambda:verify_native('0'*64,cache[key]))
    return {'artifact_id':'reiyah.observation-contract.controls','version':'0.1.0','passed':passed,'count':len(passed),'failures':[]}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output');args=p.parse_args();result=run()
    with Path(args.output).open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print({'controls':result['count'],'failed':0})
