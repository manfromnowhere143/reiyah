"""Critical controls run before freezing actual allocation; v0.1.0."""
from copy import deepcopy
from fractions import Fraction as F
from itertools import permutations
import json
from methods import Population,validate,stake,update
from check import Reference,VerificationError
def main():
    base={'id':'control','kind':'exhaustive','units':[{'id':str(i),'bound':'1','lower':v,'upper':v,'status':'observed'} for i,v in enumerate(['1','-1/2','1/2','-1'])]}
    checks=[]
    def reject(name,call,expected):
        try:call()
        except ValueError as e:assert str(e)==expected,(name,str(e),expected)
        else:raise AssertionError(name+' accepted')
        checks.append({'id':name,'passed':True,'expected_rejection':expected})
    def change(f):p=deepcopy(base);f(p);return p
    invalid=[
      ('unknown_property',lambda p:p.update(extra=1),'population_properties'),
      ('duplicate_identity',lambda p:p['units'][1].update(id='0'),'unit_identity'),
      ('float_endpoint',lambda p:p['units'][0].update(lower=0.5),'rational_string'),
      ('noncanonical_endpoint',lambda p:p['units'][0].update(lower='2/2'),'rational_canonical'),
      ('negative_bound',lambda p:p['units'][0].update(bound='-1'),'unit_range'),
      ('reversed_interval',lambda p:p['units'][0].update(lower='1',upper='-1'),'unit_range'),
      ('unknown_status',lambda p:p['units'][0].update(status='good'),'unit_status'),
      ('missing_as_point',lambda p:p['units'][0].update(status='missing'),'unavailable_interval'),
      ('observed_as_interval',lambda p:p['units'][0].update(lower='0'),'observed_interval')]
    for name,f,reason in invalid:
        for label,fn in [('producer',validate),('checker',Reference)]:reject(label+'_'+name,lambda f=f,fn=fn:fn(change(f)),reason)
    ref=Reference(base);row=ref.expected('alpha_d10',[0,1,2,3],0)
    for k,v in [('queries',0),('decision','supported'),('wealth_at_stop',['999','999']),('trace_sha256','0'*64),('exact_queries',0),('crossed',[True,True])]:
        bad={**row,k:v};reject('forged_'+k,lambda bad=bad:ref.verify_row(bad,[0,1,2,3]),'path_'+k)
    reject('repeated_query',lambda:ref.expected('alpha_d10',[0,0,2,3],0),'order_membership')
    reject('unknown_arm',lambda:Population(base).path('oracle',[0,1,2,3],0),'unknown_arm')
    for arm in ('fixed_half','alpha_d10','alpha_d100'):
        for order in permutations(range(4)):
            produced=Population(base).path(arm,list(order),0);ref.verify_row(produced,list(order))
        for m in (F(1,100),F(1,2),F(99,100)):
            lam=stake(arm,m,F(0),0)
            assert 0<=lam<=1/m
            assert update(F(1),m,F(0),lam)>=0 and update(F(1),m,F(1),lam)>=0
    checks.append({'id':'all_control_orders_and_support_extremes','passed':True})
    assert update(F(1),F(0),F(0),F(0))==1
    assert update(F(1),F(0),F(1),F(0)) is None
    assert update(F(0),F(-1),F(0),F(0)) is None
    assert update(F(3),F(1),F(1),F(0))==3
    assert update(F(0),F(1,2),F(1),F(1))==0
    checks.append({'id':'singular_means_and_zero_wealth','passed':True})
    for v in ('1','-1','0'):
        p=deepcopy(base)
        for u in p['units']:u.update(lower=v,upper=v)
        for arm in ('fixed_half','alpha_d10','alpha_d100'):
            x=Population(p).path(arm,[0,1,2,3],0);Reference(p).verify_row(x,[0,1,2,3])
        assert x['decision']==('supported' if v=='1' else 'excluded')
    checks.append({'id':'boundary_census_and_strict_tie','passed':True})
    p=deepcopy(base)
    for u in p['units']:u.update(lower='-1',upper='1',status='missing')
    for arm in ('fixed_half','alpha_d10','alpha_d100'):
        x=Population(p).path(arm,[0,1,2,3],0);Reference(p).verify_row(x,[0,1,2,3]);assert x['queries']==4 and x['decision']=='unresolved'
    checks.append({'id':'nonresponse_retains_residual_uncertainty','passed':True})
    p=deepcopy(base)
    for u in p['units']:u.update(bound='0',lower='0',upper='0')
    x=Population(p).path('alpha_d10',[],0);Reference(p).verify_row(x,[]);assert x['queries']==0
    checks.append({'id':'zero_bounds_keep_membership_no_query','passed':True})
    print(json.dumps({'version':'0.1.0','passed':True,'checks':checks},indent=2))
if __name__=='__main__':main()
