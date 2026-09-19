"""Independently compare every public cell with retained checked result bytes."""
import argparse
from collections import Counter
import csv
from fractions import Fraction
from pathlib import Path
import re

from timing_witness import bound_read, file_binding, put, q, read, require


def fraction(text):
    require(re.fullmatch(r'-?\d+/[1-9]\d*',text) is not None,'Non-rational table encoding')
    return Fraction(text)


def verify(session, area, public, output):
    f=read(area/'FREEZE.json'); r=read(area/'analysis/RESULTS.json'); v=read(area/'VERIFICATION.json')
    a=read(f['allocation']); parent=read(Path(f['prior'])/'private/operating-witness-01/analysis/RESULTS.json')
    summary=read(public/'summary.json')
    require(v['results_sha256']==file_binding(area/'analysis/RESULTS.json')['sha256'],'Verification binding changed')
    for b in f['bindings']: require(file_binding(b['path'])==b,'Frozen dependency changed during packaging')
    require(summary['results_sha256']==v['results_sha256'] and summary['verification_sha256']==file_binding(area/'VERIFICATION.json')['sha256']
            and summary['public_csv_sha256']==file_binding(public/'results.csv')['sha256'],'Public source identity differs')
    with (public/'results.csv').open(newline='') as stream: rows=list(csv.DictReader(stream))
    require(len(rows)==7707,'Public row count differs'); cursor=0
    targets={tuple(x) for x in a['target_rows']}; labels={(x['section'],x['index']):x['classification'] for x in r['target_classifications']}
    for section in ('primary_rows','anchor_rows'):
        for index, source in enumerate(r[section]):
            row=rows[cursor];cursor+=1;old=parent[section][index]
            require(row['section']==section and int(row['row_index'])==index,'Public row identity differs')
            for key in ('case_id','group','family','decision'):require(row[key]==source[key],'Public category differs: '+key)
            require(int(row['allocated_images'])==len(source['membership']) and int(row['blocked_image_count'])==len(source['blocked_images']),'Public allocation differs')
            require(row['selected_target']==str((section,index) in targets) and row['target_outcome']==labels.get((section,index),''),'Target outcome differs')
            require(row['previous_evidence']==(old['evidence'] or '') and row['evidence']==(source['evidence'] or ''),'Evidence label differs')
            if section=='primary_rows':require(row['cell_id']==source['cell_id'] and row['threshold']=='','Primary cutoff identity differs')
            else:require(row['cell_id']=='' and fraction(row['threshold'])==q(source['threshold']),'Anchor cutoff identity differs')
            for prefix, values in [('mean',source['bounds']),('previous_attained',old['attained']),('attained',source['attained'])]:
                for j,suffix in enumerate(('lower','upper')):
                    text=row[prefix+'_'+suffix]
                    require(text=='' if values is None else fraction(text)==q(values[j]),'Public rational or missing state differs')
        require(summary['counts'][section]=={'decisions':dict(Counter(x['decision'] for x in r[section])),
                'evidence':dict(Counter(x['evidence'] or 'input_blocked' for x in r[section]))},'Public totals differ')
    fields={'target_classifications':'target_classifications','pair_states':'pair_states','unique_searches':'unique_searches',
            'unique_pools':'unique_pools','search_stops':'search_stops','new_endpoint_proofs_checked':'new_proofs_checked',
            'unique_flow_measurements_checked':'unique_flow_measurements_checked','improved_pair_endpoints':'improved_pair_endpoints',
            'inherited_proofs_exact_bound':'inherited_proofs_exact_bound','unique_native_proofs_checked':'unique_native_proofs_checked'}
    for public_key,private_key in fields.items():require(summary[public_key]==v[private_key],'Public verification count differs')
    for public_key,private_key in [('changed_evidence_rows','changed_evidence_rows'),('refined_interval_rows','refined_interval_rows'),
                                  ('nontarget_refined_interval_rows','nontarget_refined_interval_rows'),('remaining_gap_rows','remaining_gap_rows')]:
        require(summary[public_key]==len(v[private_key]),'Public refinement count differs')
    require(summary['target_rows']==len(targets)==279 and summary['target_state_contract_pairs']==len(a['target_pairs'])==397
            and summary['target_filtered_states']==len({p[0] for p in a['target_pairs']})==356,'Target allocation differs')
    pools=[bound_read(e) for e in r['pools']]
    require(summary['pool_totals']=={k:sum(p[k] for p in pools) for k in ('base_count','axis_sweeps','axis_cells','unique_rectangles')},'Pool totals differ')
    require(summary['distinct_nonempty_neighborhoods_across_pools']==sum(len(p['neighborhoods']) for p in pools),'Neighborhood count differs')
    for row in summary['phase_costs']:
        log=read(session/'logs'/(row['stage']+'-COMPLETED.json'))
        require(all(row[k]==log[k] for k in row),'Published timer differs')
    require(summary['phase_start_utc']==read(session/'CLOCK_RECONCILIATION.json')['phase_start_utc'],'Start time differs')
    require(summary['instrumentation_start_utc']==read(session/'OWNER.json')['phase_start_utc'],'Instrumentation start differs')
    require(not summary['all_arbitrary_rectangles_searched'] and not summary['independent_scientific_replication']
            and summary['full_economic_cost'] is None and summary['human_seconds'] is None,'Scope inflation')
    # Public output includes only explicit scalar columns and aggregate summary.
    require(set(rows[0])=={'section','row_index','cell_id','threshold','case_id','group','family','allocated_images',
        'blocked_image_count','decision','previous_evidence','evidence','mean_lower','mean_upper','previous_attained_lower',
        'previous_attained_upper','attained_lower','attained_upper','selected_target','target_outcome'},'Unexpected public payload field')
    require('/Users/' not in str(summary),'Private path in summary')
    report={'artifact_id':'reiyah.operating-timing-witness.publication-check','version':'0.1.0',
        'all_7707_public_rows_checked':True,'all_279_targets_checked':True,'all_anchor_thresholds_exact':True,
        'all_frozen_bindings_unchanged':True,'public_csv_sha256':file_binding(public/'results.csv')['sha256'],
        'public_summary_sha256':file_binding(public/'summary.json')['sha256'],
        'all_source_and_count_bindings_match':True,'all_published_timers_checked':True,
        'no_actual_geometry_or_native_payload_in_public_outputs':True,'independent_scientific_replication':False}
    put(output,report);print(report)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for arg in ('session','area','public','output'):p.add_argument(arg,type=Path)
    verify(**vars(p.parse_args()))
