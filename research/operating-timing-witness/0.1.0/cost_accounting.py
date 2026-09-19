"""Finite process interval union; nested/tool timers remain distinct."""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
from decimal import Decimal
import json
from pathlib import Path
import shutil


def span(start, end):
    a=datetime.fromisoformat(start.replace('Z','+00:00')); b=datetime.fromisoformat(end.replace('Z','+00:00'))
    if a.tzinfo is None or b.tzinfo is None or b<a: raise ValueError('Invalid UTC interval')
    return a,b


def seconds(delta):
    return Decimal(delta.days*86400+delta.seconds)+Decimal(delta.microseconds)/Decimal(1000000)


def interval_union(rows):
    intervals=sorted(span(r['started_utc'],r['finished_utc']) for r in rows)
    merged=[]
    for start,end in intervals:
        if merged and start<=merged[-1][1]:merged[-1]=(merged[-1][0],max(end,merged[-1][1]))
        else:merged.append((start,end))
    return sum((seconds(end-start) for start,end in merged),Decimal(0))


def collect(session, include_running=False):
    rows=[]; running=[]
    for path in sorted((session/'logs').glob('*-STARTED.json')):
        start=json.loads(path.read_text()); end=path.with_name(path.name.replace('-STARTED','-COMPLETED'))
        if not end.exists():
            running.append(start['stage']); continue
        r=json.loads(end.read_text())
        if any(r[k]!=start[k] for k in start):raise ValueError('Start/end identity differs')
        if not Decimal(str(r['seconds'])).is_finite() or r['seconds']<0:raise ValueError('Invalid timer')
        span(r['started_utc'],r['finished_utc'])
        rows.append({k:r[k] for k in ('stage','category','budget','started_utc','finished_utc','seconds','exit_code','error')})
    if running and not include_running:raise ValueError('Unclosed phases: '+str(running))
    setup=json.loads((session/'logs/setup.json').read_text())
    rows.append({'stage':'owned-candidate-setup','category':'setup','budget':None,
                 'started_utc':setup['started_utc'],'finished_utc':setup['finished_utc'],'seconds':setup['seconds'],
                 'exit_code':0,'error':None})
    if len({r['stage'] for r in rows})!=len(rows):raise ValueError('Duplicate outer phase')
    return rows,running


def account(session, output, tool_snapshot=None):
    rows,running=collect(session,include_running=True)
    duration=sum((Decimal(str(r['seconds'])) for r in rows),Decimal(0))
    timestamp_sum=sum((seconds(span(r['started_utc'],r['finished_utc'])[1]-span(r['started_utc'],r['finished_utc'])[0]) for r in rows),Decimal(0))
    union=interval_union(rows); groups=defaultdict(list)
    for row in rows:groups[row['category']].append(row)
    budgets={family:sum((Decimal(str(r['seconds'])) for r in rows if r['budget']==family),Decimal(0)) for family in ('search','verification')}
    if any(value>1200 for value in budgets.values()):raise ValueError('Cumulative actual-data ceiling exceeded')
    owner=json.loads((session/'OWNER.json').read_text()); clock=json.loads((session/'CLOCK_RECONCILIATION.json').read_text())
    occupied=sum(p.stat().st_size for folder in ('private','logs','candidate/research/operating-timing-witness')
                 for p in (session/folder).rglob('*') if p.is_file())
    free=shutil.disk_usage(session).free
    if occupied>=2**30 or free<5*2**30:raise ValueError('Storage boundary violated')
    value={'artifact_id':'reiyah.operating-timing-witness.costs','version':'0.1.0',
        'snapshot_utc':datetime.now(timezone.utc).isoformat(),'phase_start_utc':clock['phase_start_utc'],
        'instrumentation_start_utc':owner['phase_start_utc'],'outer_events':len(rows),
        'statuses':dict(Counter('completed' if r['exit_code']==0 and not r['error'] else 'failed' for r in rows)),
        'outer_duration_sum_seconds':str(duration),'utc_interval_union_seconds':str(union),
        'utc_interval_duration_sum_seconds':str(timestamp_sum),'utc_overlap_seconds':str(timestamp_sum-union),
        'categories':{k:{'events':len(v),'duration_sum_seconds':str(sum((Decimal(str(r['seconds'])) for r in v),Decimal(0))),
                         'utc_interval_union_seconds':str(interval_union(v))} for k,v in sorted(groups.items())},
        'cumulative_actual_search_seconds':str(budgets['search']),
        'cumulative_actual_verification_seconds':str(budgets['verification']),
        'per_budget_ceiling_seconds':1200,'phase_events':rows,'unclosed_events_outside_cutoff':running,
        'cutoff':'All completed supervised phases plus owned-candidate setup at this snapshot. Current accounting process and later actions are outside it.',
        'nested_timers':'Scientific internal timers, native checks and synthetic supervisor children are included in their enclosing phase, never added again.',
        'duration_only_tool_reports':None,'initial_checkout_apparent_bytes':owner['candidate_apparent_bytes'],
        'new_research_apparent_bytes_at_snapshot':occupied,'free_bytes_at_snapshot':free,
        'research_byte_ceiling':2**30,'free_space_floor_bytes':5*2**30,
        'new_download_bytes':0,'new_inference_calls':0,'paid_compute':False,
        'human_seconds':None,'model_service_cost':None,'full_economic_cost':None,'total_useful_seconds':None,
        'original_assignment_start_utc':'2026-09-17T22:28:16+00:00','original_excluded_seconds':'44963.785396',
        'old_ten_hour_assignment':'completed; no timers added to this new phase'}
    if tool_snapshot:
        source=json.loads(tool_snapshot.read_text()); reports=source['reports']
        value['duration_only_tool_reports']={'count':len(reports),'reported_seconds_sum_not_added_to_process_union':str(sum((Decimal(str(r['wall_time_seconds'])) for r in reports),Decimal(0))),
            'nonzero_exit_reports':sum(r.get('exit_code') not in (None,0) for r in reports),
            'scope':'Tool-reported invocation/wait durations, including setup/reads and nested process launch/wait reports. No full execution intervals; no independent additive work total.',
            'retained_snapshot_sha256':__import__('hashlib').sha256(tool_snapshot.read_bytes()).hexdigest()}
    with output.open('x') as f:json.dump(value,f,indent=2,sort_keys=True);f.write('\n')
    print({k:value[k] for k in ('outer_events','statuses','utc_interval_union_seconds','cumulative_actual_search_seconds','cumulative_actual_verification_seconds')})


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('session',type=Path);p.add_argument('output',type=Path);p.add_argument('--tool-snapshot',type=Path)
    account(**vars(p.parse_args()))
