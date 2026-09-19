"""Separate enumeration checker, version 0.1.0. No producer imports."""
from pathlib import Path
from fractions import Fraction as Q
from itertools import product
from math import factorial
import csv
import hashlib
import json
import sys

class VerificationError(ValueError):
    pass

def need(condition, reason):
    if not condition:
        raise VerificationError(reason)

class Reference:
    def __init__(self, population):
        self.pop = population
        self.units = population['units']
        self.w = tuple(Q(u['weight']) for u in self.units)
        self.s = tuple(Q(u['proxy']) for u in self.units)
        self.active = tuple(i for i,w in enumerate(self.w) if w != 0)
        self.tau = Q(population['threshold'])
        self.values = (tuple((Q(u['lower'])+1)/2 for u in self.units),
                       tuple((1-Q(u['upper']))/2 for u in self.units))
        self.proxy = (tuple((x+1)/2 for x in self.s), tuple((1-x)/2 for x in self.s))
        self.target = ((1+self.tau)/2, (1-self.tau)/2)
        self.totals = tuple(sum(w*x for w,x in zip(self.w,v)) for v in self.values)
        self.logic_cache = {}
        self.step_cache = {}
        self.factor_support_checks = 0
        self.conditional_mean_checks = 0
        self.null_drift_checks = 0

    def exact(self, observed):
        key=frozenset(observed)
        if key not in self.logic_cache:
            choices=[]
            for i,u in enumerate(self.units):
                choices.append((Q(u['lower']),Q(u['upper'])) if i in key else (Q(-1),Q(1)))
            # Separate conventional path: evaluate every box vertex, not endpoint sums.
            scores=[sum(w*x for w,x in zip(self.w,world)) for world in product(*choices)]
            low,high=min(scores),max(scores)
            decision='supported' if low>self.tau else 'excluded' if high<=self.tau else 'unresolved'
            self.logic_cache[key]=(decision,low,high)
        return self.logic_cache[key]

    def step(self, observed, arm):
        key=(frozenset(observed),arm)
        if key in self.step_cache:return self.step_cache[key]
        seen=key[0]; remaining=[i for i in self.active if i not in seen]
        need(bool(remaining),'no_remaining_sample')
        raw={i:Q(1) if arm=='uniform' else self.w[i] for i in remaining}
        if arm in ('proxy','proxy_cv'):
            raw={i:x*(Q(1,8)+(1+self.s[i])/2) for i,x in raw.items()}
        need(arm in ('uniform','weight','proxy','proxy_cv'),'unknown_arm')
        norm=sum(raw.values());q={i:x/norm for i,x in raw.items()}
        need(sum(q.values())==1 and min(q.values())>0,'probability_mass')
        by_direction=[]
        for direction in range(2):
            x=self.values[direction];p=self.proxy[direction]
            observed_total=sum(self.w[i]*x[i] for i in seen)
            null_remaining=self.target[direction]-observed_total
            correction=sum(self.w[i]*p[i] for i in remaining) if arm=='proxy_cv' else Q(0)
            def score(i,v):
                return self.w[i]*v/q[i] if arm!='proxy_cv' else correction+self.w[i]*(v-p[i])/q[i]
            possible={i:(score(i,Q(0)),score(i,Q(1))) for i in remaining}
            floor=min(min(v) for v in possible.values())
            gap=null_remaining-floor
            bet=Q(1,2*gap) if gap>0 else Q(0)
            factors={i:Q(1)+bet*(score(i,x[i])-null_remaining) for i in remaining}
            for i,endpoints in possible.items():
                for endpoint in endpoints:
                    need(1+bet*(endpoint-null_remaining)>=0,'factor_support_negative')
                    self.factor_support_checks+=1
            true_remaining=sum(self.w[i]*x[i] for i in remaining)
            need(sum(q[i]*score(i,x[i]) for i in remaining)==true_remaining,'importance_correction_mean')
            self.conditional_mean_checks+=1
            if self.totals[direction]<=self.target[direction]:
                need(sum(q[i]*factors[i] for i in remaining)<=1,'null_supermartingale_drift')
                self.null_drift_checks+=1
            by_direction.append(factors)
        answer=(q,by_direction[0],by_direction[1])
        self.step_cache[key]=answer
        return answer

    def expected(self, arm, order_string):
        order=tuple(int(i) for i in order_string)
        need(len(order)==len(self.active) and set(order)==set(self.active),'order_membership')
        probability=Q(1);wealth=[Q(1),Q(1)];cross=[False,False]
        exact_stop=None;stat_stop=None
        for t in range(len(order)+1):
            prefix=order[:t]
            decision,_,_=self.exact(prefix)
            if exact_stop is None and decision!='unresolved':exact_stop=(t,decision)
            if stat_stop is None:
                why=None;state=None
                if decision!='unresolved':state,why=decision,'logical'
                elif t==len(order):state,why='unresolved','residual_reference'
                elif wealth[0]>=40 and wealth[1]>=40:state,why='unresolved','statistical_conflict'
                elif wealth[0]>=40:state,why='supported','statistical'
                elif wealth[1]>=40:state,why='excluded','statistical'
                if why is not None:stat_stop=(t,state,why,*wealth)
            cross=[cross[d] or wealth[d]>=40 for d in range(2)]
            if t<len(order):
                i=order[t];q,lo,hi=self.step(prefix,arm)
                probability*=q[i];wealth[0]*=lo[i];wealth[1]*=hi[i]
        if exact_stop is None:exact_stop=(len(order),'unresolved')
        return {'population':self.pop['id'],'arm':arm,'order':order_string,'probability':str(probability),
                'exact_stop':str(exact_stop[0]),'exact_decision':exact_stop[1],
                'stat_stop':str(stat_stop[0]),'stat_decision':stat_stop[1],'stat_reason':stat_stop[2],
                'e_lower_at_stop':str(stat_stop[3]),'e_upper_at_stop':str(stat_stop[4]),
                'lower_ever_crossed':str(int(cross[0])),'upper_ever_crossed':str(int(cross[1]))}

    def verify_row(self,row):
        expected=self.expected(row['arm'],row['order'])
        for key,value in expected.items():need(row.get(key)==value,'path_'+key)
        need(set(row)==set(expected),'unknown_path_property')
        return expected

def verify(freeze_path, run_path, output):
    root=Path(__file__).resolve().parent
    freeze=json.loads(freeze_path.read_text())
    for name,expected in freeze['files'].items():
        need(hashlib.sha256((root/name).read_bytes()).hexdigest()==expected,'freeze_'+name)
    fixture=json.loads((root/'fixtures.json').read_text())
    need((fixture['alpha_per_procedure_population'],fixture['alpha_per_direction'],fixture['bet_fraction'])==('1/20','1/40','1/2'),'error_allocation')
    need(len(fixture['populations'])==28,'allocation_count')
    refs={p['id']:Reference(p) for p in fixture['populations']}
    result=json.loads((run_path/'result.json').read_text())
    need(result['freeze_sha256']==hashlib.sha256(freeze_path.read_bytes()).hexdigest(),'run_freeze_binding')
    need(result['paths_sha256']==hashlib.sha256((run_path/'paths.csv').read_bytes()).hexdigest(),'paths_digest')
    aggregate={};unique=set();rows=0
    with (run_path/'paths.csv').open(newline='') as stream:
        for row in csv.DictReader(stream):
            key=(row['population'],row['arm'],row['order'])
            need(key not in unique,'duplicate_path');unique.add(key)
            need(row['population'] in refs,'unallocated_population')
            ref=refs[row['population']];ref.verify_row(row);rows+=1
            group=key[:2]
            if group not in aggregate:aggregate[group]={'orders':0,'mass':Q(0),'exact':Q(0),'stat':Q(0),'false':Q(0),'early':Q(0),'statistical':Q(0),'lower_cross':Q(0),'upper_cross':Q(0),'either_false_endpoint':Q(0)}
            g=aggregate[group];pr=Q(row['probability']);g['orders']+=1;g['mass']+=pr
            g['exact']+=pr*int(row['exact_stop']);g['stat']+=pr*int(row['stat_stop'])
            truth=ref.exact(ref.active)[0]
            if row['stat_decision']!='unresolved' and row['stat_decision']!=truth:g['false']+=pr
            if int(row['stat_stop'])<int(row['exact_stop']):g['early']+=pr
            if row['stat_reason']=='statistical':g['statistical']+=pr
            false_lower=ref.totals[0]<=ref.target[0] and row['lower_ever_crossed']=='1'
            false_upper=ref.totals[1]<=ref.target[1] and row['upper_ever_crossed']=='1'
            if false_lower:g['lower_cross']+=pr
            if false_upper:g['upper_cross']+=pr
            if false_lower or false_upper:g['either_false_endpoint']+=pr
    need(rows==result['path_rows'],'row_count')
    need(len(aggregate)==28*4,'group_allocation')
    summaries=[]
    for (pid,arm),g in sorted(aggregate.items()):
        ref=refs[pid];truth,lo,hi=ref.exact(ref.active)
        need(g['orders']==factorial(len(ref.active)),'all_permutations')
        need(g['mass']==1,'total_probability')
        need(g['lower_cross']<=Q(1,40) and g['upper_cross']<=Q(1,40),'one_sided_error_exceeded')
        need(g['either_false_endpoint']<=Q(1,20) and g['false']<=Q(1,20),'two_sided_error_exceeded')
        wanted={'population':pid,'arm':arm,'orders':g['orders'],'full_interval':[str(lo),str(hi)],'full_decision':truth,
                'expected_exact_queries':str(g['exact']),'expected_stat_queries':str(g['stat']),
                'false_decision_probability':str(g['false']),'early_stop_probability':str(g['early']),
                'statistical_decision_probability':str(g['statistical'])}
        matches=[s for s in result['summaries'] if s['population']==pid and s['arm']==arm]
        need(matches==[wanted],'producer_summary')
        deterministic_order=''.join(str(i) for i in sorted(ref.active,key=lambda i:(-ref.w[i],i)))
        det=ref.expected('weight',deterministic_order)
        summaries.append({**wanted,'false_lower_cross_probability':str(g['lower_cross']),
                          'false_upper_cross_probability':str(g['upper_cross']),
                          'either_false_endpoint_probability':str(g['either_false_endpoint']),
                          'conventional_weight_priority_queries':int(det['exact_stop']),
                          'nonresponse_units':[u['id'] for u in ref.units if u['status']!='observed']})
    report={'document_id':'reiyah.sequential-audit.check','version':'0.1.0','status':'exploratory','passed':True,
            'freeze_sha256':result['freeze_sha256'],'paths_sha256':result['paths_sha256'],'populations':28,'arms':4,
            'checked_path_rows':rows,'checked_groups':len(aggregate),
            'factor_support_checks':sum(r.factor_support_checks for r in refs.values()),
            'conditional_mean_checks':sum(r.conditional_mean_checks for r in refs.values()),
            'null_drift_checks':sum(r.null_drift_checks for r in refs.values()),
            'scope':'Exact enumeration of authored populations and all sampling orders; same-session separate code path, not independent scientific replication.',
            'guarantee_scope':'Per fixed population and separately registered arm. No simultaneous family guarantee across 112 comparisons.',
            'summaries':summaries}
    need(not output.exists(),'output_already_exists')
    output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='summaries'},indent=2))

if __name__=='__main__':verify(*map(Path,sys.argv[1:]))
