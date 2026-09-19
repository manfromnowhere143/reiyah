"""Exact-rational declared ALPHA and conventional interval comparators, v0.1.0."""
from fractions import Fraction as F
import hashlib,json,math

ARMS=('fixed_half','alpha_d10','alpha_d100')
NONRESPONSE={'missing','unmeasured','out_of_distribution','sensor_invalid','abstained'}
def require(c,reason):
    if not c:raise ValueError(reason)
def rational(s):
    require(type(s) is str,'rational_string')
    try:v=F(s)
    except (ValueError,ZeroDivisionError):raise ValueError('rational_value')
    require(str(v)==s,'rational_canonical');return v
def validate(p):
    require(set(p)=={'id','kind','units'},'population_properties')
    require(type(p['id']) is str and p['id'] and p['kind'] in ('exhaustive','sampled'),'population_identity')
    require(type(p['units']) is list and 0<len(p['units'])<=64,'population_size')
    ids=set()
    for u in p['units']:
        require(set(u)=={'id','bound','lower','upper','status'},'unit_properties')
        require(type(u['id']) is str and u['id'] and u['id'] not in ids,'unit_identity');ids.add(u['id'])
        b,l,h=map(rational,(u['bound'],u['lower'],u['upper']))
        require(b>=0 and -b<=l<=h<=b,'unit_range')
        require(u['status'] in NONRESPONSE|{'observed','reference_interval'},'unit_status')
        if u['status']=='observed':require(l==h,'observed_interval')
        if u['status'] in NONRESPONSE:require((l,h)==(-b,b),'unavailable_interval')
def choose(lo,hi):
    return 'supported' if lo>0 else 'excluded' if hi<=0 else 'unresolved'
def stake(arm,m,S,t):
    require(arm in ARMS,'unknown_arm')
    if not 0<m<1:return F(0)
    if arm=='fixed_half':return 1/(2*m)
    d=10 if arm=='alpha_d10' else 100
    eps=F(math.isqrt((1<<48)//(d+t)),8*(1<<24))
    eta=min(F(1),max((F(3*d,4)+S)/(d+t),m+eps))
    return (eta-m)/(m*(1-m))
def update(e,m,x,lam):
    if e is None or m<0 or (m==0 and x>0):return None
    if m==0 or m>=1:return e
    f=1+lam*(x-m);require(f>=0,'negative_factor')
    return e*f
def txt(v):return 'null_impossible' if v is None else str(v)
def crossed(v):return v is None or v>=40
class Population:
    def __init__(self,p):
        validate(p);self.p=p
        self.b=[F(u['bound']) for u in p['units']]
        self.l=[F(u['lower']) for u in p['units']];self.h=[F(u['upper']) for u in p['units']]
        self.active=[i for i,b in enumerate(self.b) if b>0];self.n=len(self.active)
        self.M=max(self.b);self.totalb=sum(self.b)
    def interval(self,seen):
        remain=self.totalb-sum(self.b[i] for i in seen)
        return sum((self.l[i] for i in seen),F(0))-remain,sum((self.h[i] for i in seen),F(0))+remain
    def exact_priority(self):
        order=sorted(self.active,key=lambda i:(-self.b[i],self.p['units'][i]['id']))
        for t in range(self.n+1):
            d=choose(*self.interval(order[:t]))
            if d!='unresolved' or t==self.n:return {'queries':t,'decision':d}
    def path(self,arm,order,rep):
        require(len(order)==self.n and len(set(order))==self.n and set(order)==set(self.active),'order_membership')
        require(arm in ARMS,'unknown_arm')
        S=[F(0),F(0)];wealth=[F(1),F(1)];ever=[False,False]
        stop=None;exact=None;trace=hashlib.sha256()
        for t in range(self.n+1):
            lo,hi=self.interval(order[:t]);decision=choose(lo,hi)
            e=[txt(x) for x in wealth]
            trace.update((json.dumps([t,str(lo),str(hi),*e],separators=(',',':'))+'\n').encode())
            cross=list(map(crossed,wealth));ever=[a or b for a,b in zip(ever,cross)]
            if exact is None and (decision!='unresolved' or t==self.n):exact=[t,decision]
            if stop is None:
                reason=None
                if decision!='unresolved':state,reason=decision,'logical'
                elif t==self.n:state,reason='unresolved','residual_reference'
                elif all(cross):state,reason='unresolved','statistical_conflict'
                elif cross[0]:state,reason='supported','statistical'
                elif cross[1]:state,reason='excluded','statistical'
                if reason:stop=[t,state,reason,*e]
            if t<self.n:
                i=order[t];xs=[(self.l[i]+self.M)/(2*self.M),(self.M-self.h[i])/(2*self.M)]
                for k,x in enumerate(xs):
                    m=(F(self.n,2)-S[k])/(self.n-t);lam=stake(arm,m,S[k],t)
                    wealth[k]=update(wealth[k],m,x,lam);S[k]+=x
        return {'population':self.p['id'],'arm':arm,'replicate':rep,'queries':stop[0],'decision':stop[1],'reason':stop[2],'wealth_at_stop':stop[3:],'exact_queries':exact[0],'exact_decision':exact[1],'crossed':ever,'trace_sha256':trace.hexdigest()}
