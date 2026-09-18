"""Exact minimizing domains for a finite collection of affine losses."""
from fractions import Fraction as Q

MAX_LINES=600
MAX_CONSTRAINTS=360000
MAX_CELLS=10000


def require(ok,message):
    if not ok:raise ValueError(message)


def validate(lines):
    require(type(lines) is list and 0<len(lines)<=MAX_LINES,'Invalid line allocation')
    require(len({r['id'] for r in lines})==len(lines),'Repeated line identity')
    require(all(type(r['fp']) is int and r['fp']>=0 and type(r['fn']) is int and r['fn']>=0
                for r in lines),'Invalid count')
    require(len(lines)**2<=MAX_CONSTRAINTS,'Constraint cap')


def coefficient(line):return line['fp'],line['fn']-line['fp']


def value(line,p):
    b,a=coefficient(line);return b+a*p


def best(lines,p):
    values=[value(r,p) for r in lines];lowest=min(values)
    return lowest,[r['id'] for r,v in zip(lines,values) if v==lowest]


def minimizing_domains(lines):
    validate(lines);domains=[];constraints=0
    for line in lines:
        left,right=Q(0),Q(1);b,a=coefficient(line);possible=True
        for other in lines:
            constraints+=1;c,d=coefficient(other);intercept,slope=b-c,a-d
            if slope==0:
                if intercept>0:possible=False;break
            else:
                boundary=Q(-intercept,slope)
                if slope>0:right=min(right,boundary)
                else:left=max(left,boundary)
            if left>right:possible=False;break
        domain=[str(left),str(right)] if possible else None
        domains.append({'id':line['id'],'fp':line['fp'],'fn':line['fn'],'minimizing_domain':domain,
                        'state':'never_minimal' if domain is None else 'point_only' if left==right else 'interval'})
    require(constraints<=MAX_CONSTRAINTS,'Constraint cap exceeded')
    return {'lines':domains,'checked_constraints':constraints,'all_allocated_lines_retained':True}


def verdict(v):return 'new_lower' if v>0 else 'old_lower' if v<0 else 'tie'


def compare(old,new,population):
    require(type(population) is int and population>0,'Invalid population')
    envelopes=[minimizing_domains(lines) for lines in (old,new)]
    points={Q(0),Q(1)}
    for envelope in envelopes:
        for row in envelope['lines']:
            if row['minimizing_domain'] is not None:points.update(map(Q,row['minimizing_domain']))
    fixed_b=old[0]['fp']-new[0]['fp']
    fixed_a=(old[0]['fn']-old[0]['fp'])-(new[0]['fn']-new[0]['fp'])
    if fixed_a:
        root=Q(-fixed_b,fixed_a)
        if 0<root<1:points.add(root)
    for left,right in zip(sorted(points),sorted(points)[1:]):
        middle=(left+right)/2
        ai=best(old,middle)[1][0];bi=best(new,middle)[1][0]
        a=next(r for r in old if r['id']==ai);b=next(r for r in new if r['id']==bi)
        intercept=a['fp']-b['fp'];slope=(a['fn']-a['fp'])-(b['fn']-b['fp'])
        if slope:
            root=Q(-intercept,slope)
            if left<root<right:points.add(root)
    points=sorted(points);require(2*len(points)-1<=MAX_CELLS,'Final partition cap')
    cells=[]
    for i,left in enumerate(points):
        pieces=[('point',left,left)]
        if i+1<len(points):pieces.append(('open_interval',left,points[i+1]))
        for kind,lo,hi in pieces:
            probe=(lo+hi)/2;old_value,old_ids=best(old,probe);new_value,new_ids=best(new,probe)
            a=next(r for r in old if r['id']==old_ids[0]);b=next(r for r in new if r['id']==new_ids[0])
            delta=[a['fp']-b['fp'],(a['fn']-a['fp'])-(b['fn']-b['fp'])]
            result=verdict(old_value-new_value);fixed=verdict(fixed_b+fixed_a*probe)
            cells.append({'id':'penalty-'+str(len(cells)).zfill(4),'kind':kind,'left':str(lo),'right':str(hi),
                'left_closed':kind=='point','right_closed':kind=='point',
                'old_minimizers':old_ids,'new_minimizers':new_ids,
                'old_loss_coefficients':list(coefficient(a)),'new_loss_coefficients':list(coefficient(b)),
                'delta_total_coefficients':delta,'delta_mean_coefficients':[str(Q(v,population)) for v in delta],
                'probe':str(probe),'delta_mean_at_probe':str((old_value-new_value)/population),
                'envelope_comparison':result,'fixed_cutoff_comparison':fixed,
                'comparison_changes':result!=fixed,
                'strict_new_improvement':'supported_nominal' if result=='new_lower' else 'excluded_nominal'})
    return {'envelopes':envelopes,'partition':cells,'breakpoints':[str(p) for p in points],
            'population':population,'fixed_cutoff_delta_total_coefficients':[fixed_b,fixed_a],
            'thresholds_selected_for_deployment':False,'uncertain_reference_pairs_evaluated':False}
