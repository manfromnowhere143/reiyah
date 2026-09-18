"""Retain every verified scalar domain and partition cell in public tables."""
import argparse
from collections import Counter
import csv
from datetime import datetime,timezone
from pathlib import Path

from envelope_math import require
from envelope_sources import check_bindings,put,read,sha


def csv_write(path,rows):
    with path.open('x',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]),lineterminator='\n')
        writer.writeheader();writer.writerows(rows)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--area',type=Path,required=True);args=parser.parse_args()
    root=args.area.resolve();base=root/'private/policy-loss-envelope-01';here=Path(__file__).resolve().parent
    frozen=read(base/'FREEZE.json');check_bindings(frozen)
    result=read(base/'analysis/RESULTS.json');checked=read(base/'verification/VERIFICATION.json')
    require(checked['results_sha256']==sha(base/'analysis/RESULTS.json') and checked['all_lines_verified']==519
            and checked['all_partition_cells_verified']==51,'Verified complete envelope required')
    domains=[]
    for model,envelope,thresholds in zip(result['models'],result['envelopes'],result['source_threshold_domains']):
        by_id={r['cell_id']:r for r in thresholds}
        for row in envelope['lines']:
            domain=row['minimizing_domain'];threshold=by_id[row['id']]
            domains.append({'model':model,'cell_id':row['id'],'false_positives':row['fp'],'misses':row['fn'],
                'state':row['state'],'penalty_left':domain[0] if domain else '',
                'penalty_right':domain[1] if domain else '',
                'penalty_boundaries_closed':domain is not None,
                **{k:v for k,v in threshold.items() if k!='cell_id'}})
    cells=[]
    for row in result['partition']:
        cells.append({k:' '.join(map(str,v)) if isinstance(v,list) else v for k,v in row.items()})
    csv_write(here/'optimizer-domains.csv',domains);csv_write(here/'penalty-partition.csv',cells)
    phases=[]
    for path in sorted((root/'logs').glob('envelope-*-COMPLETED.json')):
        record=read(path);phases.append({k:record[k] for k in ('stage','started_utc','finished_utc','seconds','exit_code','error')})
    recovery=read(root/'private/storage-recovery-01/COMPLETED.json')
    summary={'artifact_id':'reiyah.policy-loss-envelope.public-summary','version':'0.1.0','status':'exploratory',
        'snapshot_utc':datetime.now(timezone.utc).isoformat(),'models':result['models'],'allocated_images':64,
        'eligible_projected_references':305,'source_threshold_cells':[299,220],
        'freeze_sha256':sha(base/'FREEZE.json'),'frozen_utc':frozen['frozen_utc'],'frozen_bindings':len(frozen['bindings']),
        'results_sha256':sha(base/'analysis/RESULTS.json'),'verification_sha256':sha(base/'verification/VERIFICATION.json'),
        'source_curve_sha256':result['curve_sha256'],'partition_cells':len(cells),'breakpoints':result['breakpoints'],
        'optimizer_states':[dict(Counter(r['state'] for r in e['lines'])) for e in result['envelopes']],
        'linear_constraints_checked':[e['checked_constraints'] for e in result['envelopes']],
        'decisions_by_partition_kind':result['decisions_by_partition_kind'],
        'fixed_cutoff_comparison_changed_cells':sum(r['comparison_changes'] for r in result['partition']),
        'new_lower_region':{'penalty_share_left':'0','penalty_share_right':'1/17','both_boundaries_open':True,
                            'miss_to_fp_ratio_left':'0','miss_to_fp_ratio_right':'1/16'},
        'tie_penalty_shares':['0','1/17'],'old_lower_region':{'penalty_share_left':'1/17',
                         'penalty_share_right':'1','left_closed':False,'right_closed':True},
        'controls':{'unit_tests':13,'exhaustive_three_line_sets':729,'exhaustive_two_model_allocations':256,
                    'synthetic_full_pipeline_cells':519},
        'verification':{k:checked[k] for k in ('all_lines_verified','all_partition_cells_verified',
            'continuum_dominance_endpoint_checks','independent_lower_hull_segments','all_optimizer_ties_retained')},
        'phase_cost_snapshot_before_publication':phases,
        'startup_failure':{'stage':'envelope-verify-01','error':'ENOSPC before STARTED receipt creation',
            'verification_child_launched':False,'tool_wall_seconds':'0.414131541',
            'secondary_result_view_tool_wall_seconds':'0.246422958',
            'tool_times_added_to_phase_union':False},
        'storage_recovery':{k:recovery[k] for k in ('archive_bytes','original_file_bytes',
            'all_archived_bytes_read_back_before_removal','frozen_input_paths_in_scope','seconds')},
        'storage_scope':'Completed synthetic cached-audit output copies only; exact lossless archive retained privately',
        'analysis_peak_resident_bytes_macos':result['peak_resident_bytes_macos'],
        'verification_peak_resident_bytes_macos':checked['peak_resident_bytes_macos'],
        'all_rows_retained':True,'independent_scientific_replication':False,
        'thresholds_selected_for_deployment':False,'uncertain_reference_pairs_evaluated':False,
        'new_image_reads':0,'new_model_calls':0,'new_downloads':0,'reserved_images_closed':1433,
        'human_seconds':None,'full_economic_cost':None}
    put(here/'summary.json',summary)
    print({'optimizer_rows':len(domains),'partition_rows':len(cells),'summary_sha256':sha(here/'summary.json')})


if __name__=='__main__':main()
