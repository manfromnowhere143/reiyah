"""Slope-ordered lower hull and continuum certificates, independent of domains."""
from fractions import Fraction as Q

from envelope_math import require


def evaluate(row,p):return (1-p)*row['fp']+p*row['fn']


def lower_hull(lines):
    # Equal slopes need the smallest intercept; exact ties are recovered from
    # all original lines at boundaries and probes, including point-only lines.
    slopes={}
    for row in lines:
        slope=row['fn']-row['fp'];intercept=row['fp']
        slopes[slope]=min(intercept,slopes.get(slope,intercept))
    hull=[]
    for slope,intercept in sorted(slopes.items(),reverse=True):
        start=None
        while hull:
            previous=hull[-1];start=Q(intercept-previous['intercept'],previous['slope']-slope)
            if previous['start'] is None or start>previous['start']:break
            hull.pop()
        hull.append({'slope':slope,'intercept':intercept,'start':start if hull else None})
    segments=[]
    for i,row in enumerate(hull):
        start=Q(0) if row['start'] is None else max(Q(0),row['start'])
        end=Q(1) if i+1==len(hull) else min(Q(1),hull[i+1]['start'])
        if start<end:segments.append({'left':start,'right':end,'slope':row['slope'],'intercept':row['intercept']})
    require(segments and segments[0]['left']==0 and segments[-1]['right']==1,'Hull coverage incomplete')
    require(all(a['right']==b['left'] for a,b in zip(segments,segments[1:])),'Hull gap')
    return segments


def sign(value):
    if value<0:return 'old_lower'
    if value>0:return 'new_lower'
    return 'tie'


def verify(old,new,result):
    require(result['population']>0,'Invalid denominator');hulls=[lower_hull(rows) for rows in (old,new)]
    require(result['fixed_cutoff_delta_total_coefficients']==[old[0]['fp']-new[0]['fp'],
        old[0]['fn']-old[0]['fp']-new[0]['fn']+new[0]['fp']],'Fixed-cutoff coefficients differ')
    require(result['thresholds_selected_for_deployment'] is False
            and result['uncertain_reference_pairs_evaluated'] is False,'Scope claim differs')
    points=list(map(Q,result['breakpoints']));cells=result['partition']
    require(points==sorted(set(points)) and points[0]==0 and points[-1]==1,'Penalty domain differs')
    require(len(cells)==len(points)*2-1,'Partition allocation differs')
    for role,rows in enumerate((old,new)):
        reported=result['envelopes'][role]['lines'];require([r['id'] for r in reported]==[r['id'] for r in rows],
                                                         'Envelope line allocation differs')
        # Derive each line's entire equality domain against the independently
        # built envelope, including isolated hull-boundary and endpoint ties.
        for line,domain in zip(rows,reported):
            active=[]
            for segment in hulls[role]:
                lo,hi=segment['left'],segment['right']
                d0=evaluate(line,lo)-(segment['intercept']+segment['slope']*lo)
                d1=evaluate(line,hi)-(segment['intercept']+segment['slope']*hi)
                require(d0>=0 and d1>=0,'Hull lies above an original line')
                if d0==0:active.append(lo)
                if d1==0:active.append(hi)
            expected=[str(min(active)),str(max(active))] if active else None
            require(domain['minimizing_domain']==expected,'Minimizing domain differs from lower hull')
            state='never_minimal' if expected is None else 'point_only' if expected[0]==expected[1] else 'interval'
            require(domain['state']==state and domain['fp']==line['fp'] and domain['fn']==line['fn'],'Line state differs')
    checks=0
    for i,cell in enumerate(cells):
        point=i//2;kind='point' if i%2==0 else 'open_interval'
        lo=points[point];hi=lo if kind=='point' else points[point+1];probe=(lo+hi)/2
        require(cell['id']=='penalty-'+str(i).zfill(4) and cell['kind']==kind
                and Q(cell['left'])==lo and Q(cell['right'])==hi
                and cell['left_closed']==cell['right_closed']==(kind=='point'),'Partition cell coverage differs')
        coefficients=[];mins=[]
        for role,rows in enumerate((old,new)):
            values=[evaluate(r,probe) for r in rows];minimum=min(values)
            winners=[r for r,v in zip(rows,values) if v==minimum]
            require([r['id'] for r in winners]==cell[['old_minimizers','new_minimizers'][role]],'Optimizer tie set differs')
            representative=winners[0];coef=[representative['fp'],representative['fn']-representative['fp']]
            require(coef==cell[['old_loss_coefficients','new_loss_coefficients'][role]],'Loss coefficient differs')
            coefficients.append(coef);mins.append(minimum)
            for other in rows:
                require(evaluate(other,lo)>=evaluate(representative,lo)
                        and evaluate(other,hi)>=evaluate(representative,hi),'Optimizer lacks continuum dominance')
                checks+=2
                if kind=='open_interval' and other in winners:
                    require(evaluate(other,lo)==evaluate(representative,lo)
                            and evaluate(other,hi)==evaluate(representative,hi),'Interior tie not affine identity')
        delta=[coefficients[0][j]-coefficients[1][j] for j in range(2)]
        require(delta==cell['delta_total_coefficients'],'Difference coefficients disagree')
        require([str(Q(v,result['population'])) for v in delta]==cell['delta_mean_coefficients'],'Normalization differs')
        require(Q(cell['probe'])==probe and Q(cell['delta_mean_at_probe'])==(mins[0]-mins[1])/result['population'],
                'Probe value differs')
        expected=sign(mins[0]-mins[1]);require(cell['envelope_comparison']==expected,'Sign differs')
        for bound in (lo,hi):
            v=delta[0]+delta[1]*bound
            require(v>=0 if expected=='new_lower' else v<=0 if expected=='old_lower' else v==0,'Sign not valid throughout cell')
        fixed=evaluate(old[0],probe)-evaluate(new[0],probe)
        require(cell['fixed_cutoff_comparison']==sign(fixed) and cell['comparison_changes']==(sign(fixed)!=expected),
                'Fixed-cutoff comparison differs')
        for bound in (lo,hi):
            v=evaluate(old[0],bound)-evaluate(new[0],bound)
            require(v>=0 if fixed>0 else v<=0 if fixed<0 else v==0,'Fixed-cutoff sign not valid throughout cell')
        require(cell['strict_new_improvement']==('supported_nominal' if expected=='new_lower' else 'excluded_nominal'),
                'Strict decision differs')
    return {'all_lines_verified':len(old)+len(new),'all_partition_cells_verified':len(cells),
            'continuum_dominance_endpoint_checks':checks,'independent_lower_hull_segments':[len(h) for h in hulls],
            'all_optimizer_ties_retained':True,'independent_scientific_replication':False}
