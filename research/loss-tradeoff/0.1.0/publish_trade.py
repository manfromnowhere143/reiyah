"""Export all verified weighted rows and exact continuum cells as derived data."""
import argparse,csv,io,json
from datetime import datetime,timezone
from pathlib import Path

from trade_sources import file_digest,read


def rational(value):
    return None if value is None else value['numerator']+'/'+value['denominator']


def table(path,rows):
    stream=io.StringIO(newline=''); writer=csv.DictWriter(stream,fieldnames=list(rows[0]),lineterminator='\n')
    writer.writeheader();writer.writerows(rows);path.write_text(stream.getvalue())


def publish(area,destination):
    run=area/'runs/trade-01'; result=read(run/'RESULTS.json'); verification=read(run/'VERIFICATION.json')
    if verification['results_sha256']!=file_digest(run/'RESULTS.json') or not verification['all_complete_rows_verified']:
        raise ValueError('Result does not match successful verification')
    displayed=[]; cells=[]; primary=[]; aggregates=[]
    for row in result['rows']:
        base={key:row[key] for key in ('case_id','group','family','state','allocated_images')}
        for entry in row['grid']:
            displayed.append({**base,'share':rational(entry['share']),
                'miss_fp_ratio':'miss_only' if entry.get('ratio_kind')=='miss_only' else rational(entry.get('miss_fp_ratio')),
                'lower':rational(entry['bounds'][0]) if entry['bounds'] else None,
                'upper':rational(entry['bounds'][1]) if entry['bounds'] else None,
                'decision':entry['decision'],'opposite_worlds':entry['opposite_worlds']})
        for index,cell in enumerate(row['continuum'] or []):
            cells.append({**base,'cell':index,'left':rational(cell['left']),'right':rational(cell['right']),
                'point':cell['point'],'representative':rational(cell['representative']),
                'lower_at_representative':rational(cell['bounds'][0]),'upper_at_representative':rational(cell['bounds'][1]),
                'decision':cell['decision']})
        if row['group']=='primary':
            primary.append({**base,'source':None if row['source'] is None else
                {key:row['source'][key] for key in ('unit_bounds','count_difference')},
                'grid':row['grid'],'continuum':row['continuum']})
    for family in result['families']:
        for p in result['shares']:
            rows=[row for row in displayed if row['family']==family['id'] and row['share']==rational(p)]
            if len(rows)!=73:raise ValueError('Aggregate omits an allocated case')
            aggregates.append({'family':family['id'],'share':p,'cases':len(rows),
                'decisions':{state:sum(row['decision']==state for row in rows) for state in ('supported','excluded','unresolved')},
                'analysis_incomplete':sum(row['state']=='analysis_incomplete' for row in rows)})
    if len(displayed)!=12483 or len(cells)!=result['continuum_cells'] or len(primary)!=19:
        raise ValueError('Public report allocation differs')
    receipts=[]
    for path in sorted((area.parents[1]/'logs').glob('trade-*-COMPLETED.json')):
        value=read(path);receipts.append({'name':path.name,'sha256':file_digest(path),**{key:value[key] for key in
            ('started_utc','finished_utc','seconds','exit_code')}})
    summary={'artifact_id':'reiyah.loss-tradeoff.public-summary','version':'0.1.0','status':'exploratory',
        'derived_data_terms':'CC BY-NC-SA 4.0 and retained Motional Dataset Terms; see DISTRIBUTION.md',
        'inputs':{name:file_digest(path) for name,path in [('freeze',area/'FREEZE.json'),('results',run/'RESULTS.json'),('verification',run/'VERIFICATION.json')]},
        'policy':result['policy'],'families':result['families'],'shares':result['shares'],
        'allocated_images':64,'dependent_cases':73,'case_family_rows':1387,'displayed_rows':len(displayed),
        'continuum_cells':len(cells),'failures':result['failures'],'nominal_counts':result['nominal_counts'],
        'primary':primary,'all_case_summaries':aggregates,'verification_totals':verification['totals'],
        'displayed_decisions':verification['displayed_decisions'],'synthetic_controls':24,
        'internal_analysis_seconds':result['seconds'],'nested_source_admission_seconds':result['source_admission']['seconds'],
        'internal_verification_seconds':verification['seconds'],'known_process_receipts':receipts,
        'cost_snapshot_utc':datetime.now(timezone.utc).isoformat(),'new_inference_calls':0,'new_download_bytes':0,
        'new_geometry_searches':0,'reserved_outcomes_accessed':0,'human_seconds':None,'full_economic_cost':None,
        'independent_scientific_replication':False}
    destination.mkdir(parents=True,exist_ok=True)
    (destination/'summary.json').write_text(json.dumps(summary,sort_keys=True,indent=2)+'\n')
    table(destination/'results.csv',displayed);table(destination/'continuum.csv',cells)
    return {'displayed_rows':len(displayed),'continuum_cells':len(cells),'primary_families':len(primary)}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--area',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();print(json.dumps(publish(args.area.resolve(),args.output.resolve())))
