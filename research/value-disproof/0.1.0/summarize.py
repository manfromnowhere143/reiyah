"""Retain every assigned outcome; derive comparisons only after history replay."""
from fractions import Fraction
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parent))
from compare import encoded,sha,put,contract


def main():
    area=Path(sys.argv[1]).resolve();destination=Path(sys.argv[2])
    plan=json.loads((area/'PLAN.json').read_bytes())
    paths=[area/'runs/comparison-01',area/'runs/interaction-01']
    rows=[];bindings=[];replays=[]
    for path in paths:
        raw=(path/'RESULTS.json').read_bytes();result=json.loads(raw)
        replay=json.loads((path/'REPLAY.json').read_bytes())
        assert replay['status']=='pass' and replay['result_sha256']==sha(raw)
        rows+=result['rows'];replays.append(replay)
        bindings.append({'results_sha256':sha(raw),'replay_sha256':sha((path/'REPLAY.json').read_bytes())})
    by_key={(r['case'],r['arm']):r for r in rows};comparison=[]
    for spec in plan['cases']:
        cid=spec['id'];current={arm:by_key[cid,arm] for arm in 'ABCD'}
        for left,right in [('A','B'),('C','D')]:
            def history(arm):
                path=paths[1] if arm=='D' else paths[0]
                return [tuple(json.loads(line)[k] for k in ('sequence','anchor','object','subject_sha256','answer','requested_precision','residual_uncertainty'))
                        for line in (path/(cid+'--'+arm)/'history.jsonl').read_bytes().splitlines()]
            assert history(left)==history(right),(cid,left,right)
            assert current[left]['status']==current[right]['status']
            assert current[left]['final_bounds']==current[right]['final_bounds']
        floor=current['A'].get('necessary_confirmation_floor')
        if floor is not None:
            case=json.loads((area/spec['input']).read_bytes())
            weights={contract.rational(a['weight']) for a in case['anchors']};assert len(weights)==1
            fn,fp=(contract.rational(case['loss'][k]) for k in ('false_negative','false_positive'))
            offset=sum(contract.rational(a['weight'])*fp*(len(a['output_b']['value'])-len(a['output_a']['value'])) for a in case['anchors'])
            ratio=(contract.rational(case['loss']['tolerance'])+offset)/((fn+fp)*next(iter(weights)))
            assert floor==max(0,ratio.numerator//ratio.denominator+1)
        comparison.append({'case':cid,'kind':spec['comparison_kind'],'family':spec['family'],
                           'queries':{a:r['queries'] for a,r in current.items()},
                           'statuses':{a:r['status'] for a,r in current.items()},
                           'bounds':{a:r['final_bounds'] for a,r in current.items()},
                           'necessary_confirmation_floor':floor})
    totals={}
    for arm in 'ABCD':
        selected=[r for r in rows if r['arm']==arm]
        adds=[r for r in selected if r.get('necessary_confirmation_floor') is not None]
        totals[arm]={'all_queries':sum(r['queries'] for r in selected),
                     'addition_queries':sum(r['queries'] for r in adds),
                     'resolved':sum(r['status'] in ('supported','excluded') for r in selected),
                     'assigned':len(selected), 'recorded_operation_seconds':sum(r['wall_seconds'] for r in selected),
                     'selection_seconds':sum(r.get('selection_seconds',0) for r in selected),
                     'stopping_seconds_deletion_only':sum(r.get('stopping_seconds',0) for r in selected),
                     'human_cost':None,'full_economic_cost':None}
    floor=sum(r['necessary_confirmation_floor'] or 0 for r in comparison)
    summary={'artifact_id':'reiyah.value-disproof.summary','version':'0.1.0',
             'engine_commit':plan['engine_commit'],'research_commit':plan['research_commit'],
             'plan_sha256':sha((area/'PLAN.json').read_bytes()),'bindings':bindings,
             'decision':'inconclusive_for_product_value; stop_selection_superiority_claim_on_this_development_family',
             'cases':comparison,'totals':totals,'addition_confirmation_floor_sum':floor,
             'addition_direct_baseline_best_possible_query_factor':str(Fraction(totals['A']['addition_queries'],floor)),
             'addition_C_vs_B_query_factor':str(Fraction(totals['B']['addition_queries'],totals['C']['addition_queries'])),
             'C_vs_conventional_D_query_factor':'1',
             'direct_attains_floor_cases':sum(r['necessary_confirmation_floor'] is not None and r['queries']['A']==r['necessary_confirmation_floor'] for r in comparison),
             'histories_identical_for_stopping_ablation':[['A','B'],['C','D']],
             'replay':{k:sum(r[k] for r in replays) for k in ['rows','queries','stopping_points','proofs','conventional_native_agreements']},
             'first_failure':'Preparation path resolution failed before experiment execution; retained prepare.stderr, corrected with absolute area resolution.',
             'timing_limits':'Single local runs; D overlapped correctness replay. Preparation, imports, source acquisition, engineering and humans are not all contained in per-arm timings. No economic ratio is derived.',
             'cost_ledger':{'local_preparation_seconds':plan['preparation_seconds'],
                            'experiment_main_seconds':[json.loads((p/'RESULTS.json').read_bytes())['campaign_seconds'] for p in paths],
                            'history_replay_seconds':[r['seconds'] for r in replays],
                            'public_replay_seconds':sum(r['seconds'] for r in json.loads((area/'PUBLIC_REPLAY.json').read_bytes())),
                            'human_preparation_seconds':None,'human_review_seconds':None,'human_adjudication_seconds':None,
                            'engineering_integration_seconds':None,'historical_optimizer_seconds':None,'cold_start_import_seconds':None,
                            'real_cost_rates':None,'paid_services_used':False},
             'limits':['Exposed dependent development units, not held-out revisions.',
                       'Presence answers synthetic; no actual correction or human saving measured.',
                       'Replacement outputs from distinct old models, not chronological checkpoints.',
                       'Both replacement directions unresolved at 512 queries; threshold control uses zero-query ceiling.',
                       'No reserved corrections read; no method frozen for reserved outcomes.',
                       'No observed critical rejection-control failure in targeted tests; the 1000-control pilot gate was not run.',
                       'No measured missed-regression, false-reuse, customer-demand or total-cost advantage.']}
    put(destination,summary)
    print(json.dumps({'totals':totals,'floor':floor,'replay':summary['replay']},indent=2))


if __name__=='__main__':main()
