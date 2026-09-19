"""Export every checked scalar outcome, without private worlds or proofs."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import csv
from pathlib import Path

from timing_witness import file_binding, put, q, read, require


def rational(value):
    if value is None: return ''
    value = q(value)
    return str(value.numerator)+'/'+str(value.denominator)


def public_rows(result, parent, allocation):
    targets = {tuple(r) for r in allocation['target_rows']}
    labels = {(r['section'], r['index']): r['classification'] for r in result['target_classifications']}
    records = []
    for section in ('primary_rows', 'anchor_rows'):
        for i, row in enumerate(result[section]):
            old = parent[section][i]
            record = {k: row.get(k, '') for k in ('cell_id','case_id','group','family','allocated_images','decision')}
            record.update(section=section, row_index=i, threshold=rational(row.get('threshold')),
                blocked_image_count=len(row['blocked_images']), previous_evidence=old['evidence'] or '',
                evidence=row['evidence'] or '', selected_target=(section,i) in targets, target_outcome=labels.get((section,i),''))
            for prefix, values in [('mean', row['bounds']), ('previous_attained', old['attained']), ('attained', row['attained'])]:
                for j, suffix in enumerate(('lower','upper')):
                    record[prefix+'_'+suffix] = '' if values is None else rational(values[j])
            records.append(record)
    return records


def publish(session, area, output):
    frozen=read(area/'FREEZE.json'); allocation=read(frozen['allocation'])
    result=read(area/'analysis/RESULTS.json'); verification=read(area/'VERIFICATION.json')
    require(verification['results_sha256']==file_binding(area/'analysis/RESULTS.json')['sha256']
            and verification['all_7707_parent_rows_checked'] and verification['all_universal_decisions_unchanged'], 'Unverified results')
    parent=read(Path(frozen['prior'])/'private/operating-witness-01/analysis/RESULTS.json')
    records=public_rows(result,parent,allocation)
    fields=['section','row_index','cell_id','threshold','case_id','group','family','allocated_images','blocked_image_count',
            'decision','previous_evidence','evidence','mean_lower','mean_upper','previous_attained_lower','previous_attained_upper',
            'attained_lower','attained_upper','selected_target','target_outcome']
    with (output/'results.csv').open('x',newline='') as f:
        writer=csv.DictWriter(f,fields,lineterminator='\n'); writer.writeheader(); writer.writerows(records)
    counts={s:{'decisions':dict(Counter(r['decision'] for r in result[s])),
               'evidence':dict(Counter(r['evidence'] or 'input_blocked' for r in result[s]))} for s in ('primary_rows','anchor_rows')}
    pools=[read(e['path']) for e in result['pools']]
    costs=[]
    for path in sorted((session/'logs').glob('*-COMPLETED.json')):
        r=read(path)
        costs.append({k:r[k] for k in ('stage','category','budget','started_utc','finished_utc','seconds','exit_code','error','cumulative_seconds')})
    summary={'artifact_id':'reiyah.operating-timing-witness.summary','version':'0.1.0','status':'exploratory',
        'snapshot_utc':datetime.now(timezone.utc).isoformat(),'selected_main':'340864c891e825ee3ebc39e172aa76b96f3a68a9',
        'phase_start_utc':read(session/'CLOCK_RECONCILIATION.json')['phase_start_utc'],
        'instrumentation_start_utc':read(session/'OWNER.json')['phase_start_utc'],
        'freeze_sha256':file_binding(area/'FREEZE.json')['sha256'],'frozen_utc':frozen['frozen_utc'],'frozen_bindings':len(frozen['bindings']),
        'results_sha256':file_binding(area/'analysis/RESULTS.json')['sha256'],'verification_sha256':file_binding(area/'VERIFICATION.json')['sha256'],
        'public_csv_sha256':file_binding(output/'results.csv')['sha256'],
        'previous_outcomes_known':True,'all_parent_rows':len(records),'parent_unique_states':allocation['parent_unique_states'],
        'target_rows':len(allocation['target_rows']),'target_filtered_states':len({p[0] for p in allocation['target_pairs']}),
        'target_state_contract_pairs':len(allocation['target_pairs']),'allocated_nonexact_pairs':len(allocation['search_pairs']),
        'target_classifications':verification['target_classifications'],'counts':counts,
        'pair_states':verification['pair_states'],'unique_searches':verification['unique_searches'],
        'unique_pools':verification['unique_pools'],'search_stops':verification['search_stops'],
        'new_endpoint_proofs_checked':verification['new_proofs_checked'],'unique_native_proofs_checked':verification['unique_native_proofs_checked'],
        'inherited_proofs_exact_bound':verification['inherited_proofs_exact_bound'],
        'unique_flow_measurements_checked':verification['unique_flow_measurements_checked'],
        'improved_pair_endpoints':verification['improved_pair_endpoints'],
        'changed_evidence_rows':len(verification['changed_evidence_rows']),
        'refined_interval_rows':len(verification['refined_interval_rows']),
        'nontarget_refined_interval_rows':len(verification['nontarget_refined_interval_rows']),
        'remaining_gap_rows':len(verification['remaining_gap_rows']),
        'failed_search_pairs':len(verification['failures']),
        'pool_totals':{key:sum(p[key] for p in pools) for key in ('base_count','axis_sweeps','axis_cells','unique_rectangles')},
        'distinct_nonempty_neighborhoods_across_pools':sum(len(p['neighborhoods']) for p in pools),
        'all_universal_decisions_unchanged':True,'all_arbitrary_rectangles_searched':False,
        'synthetic_scientific_tests':31,'supervisor_tests':3,'tiny_exhaustive_comparisons':96,'synthetic_case_compositions':56,
        'cost_cutoff_scope':'Completed supervised phases preceding initial public packaging; later costs are retained separately.',
        'phase_costs':costs,'internal_search_seconds_nested':result['seconds'],
        'internal_verification_seconds_nested':verification['seconds'],
        'native_check_seconds_nested':verification['native_check_seconds'],
        'original_start_utc':'2026-09-17T22:28:16+00:00','prior_excluded_seconds':'44963.785396',
        'prior_ten_hour_assignment':'completed; unchanged','new_image_reads':0,'new_model_calls':0,'new_download_bytes':0,
        'reserved_images_closed':1433,'human_seconds':None,'full_economic_cost':None,'total_useful_seconds':None,
        'independent_scientific_replication':False,'gate_a_operator_accepted':False,
        'engine_source':'38a50ec014cc83e86ea6f247df803ded2971b386'}
    require('/Users/' not in str(summary),'Private path in public summary')
    put(output/'summary.json',summary)
    print({'rows':len(records),'targets':summary['target_classifications'],'nontarget_refinements':summary['nontarget_refined_interval_rows']})


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for arg in ('session','area','output'):p.add_argument(arg,type=Path)
    publish(**vars(p.parse_args()))
