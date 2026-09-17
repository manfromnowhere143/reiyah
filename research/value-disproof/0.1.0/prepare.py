"""Prepare an explicitly exposed development set; never read reserved corrections."""
import ast
from copy import deepcopy
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
from compare import ROOT, encoded, put, sha, utc
from tools.perception_revision import contract


def main():
    start = time.perf_counter(); area = Path(sys.argv[1]).resolve()
    base = area.parent
    mono = base / 'engine-monotone-audit-2026-09-17-pqt93y5g/sources'
    research = base / 'opus-audit-sufficiency-2026-09-16-d38b4f32'
    linear = base / 'engine-linear-bounds-2026-09-17-9pp_3nju/private/assay-02'
    historical = json.loads((area/'sources/PLAN_COST_EXPERIMENT.json').read_bytes())
    tree = ast.parse((area/'sources/engine_localization_exchange.py').read_text())
    functions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in {'rat', 'sha', 'digest_record', 'build'}]
    assert len(functions) == 4
    namespace = {'Fraction': Fraction, 'hashlib': hashlib, 'json': json}
    exec(compile(ast.Module(body=functions, type_ignores=[]), 'pinned_representation_adapter', 'exec'), namespace)
    inputs = area/'inputs'; cases = []; sources = []

    def read_source(path):
        data = path.read_bytes()
        sources.append({'path': str(path), 'bytes': len(data), 'sha256': sha(data),
                        'exposure': 'previously_exposed_development',
                        'custody': 'prior_local_checkpoint; raw upstream acquisition not rerun'})
        return data

    def add(cid, value, family='deletion', **extra):
        contract.validate(value)
        path = inputs/(cid+'.json')
        # PREPARATION_PROBE may already hold these exact bytes; refuse disagreement.
        data = contract.encoded(value)
        if path.exists():
            assert path.read_bytes() == data, cid
        else:
            path.write_bytes(data)
        cases.append({'id': cid, 'family': family, 'input': str(path.relative_to(area)),
                      'input_sha256': sha(data), **extra})

    for cid, name in [('first','FIRST_INPUT.json'), ('second','SECOND_INPUT.json'), ('forty','FORTY_INPUT.json')]:
        add(cid, json.loads(read_source(mono/name)), comparison_kind='preserved_base_addition')
    for cid in historical['cases']['census_sample']:
        raw = json.loads(read_source(research/'private/census-units'/(cid+'.json')))
        value, _ = namespace['build'](raw, '1/2')
        add(cid, value, comparison_kind='preserved_base_addition')

    replacement = json.loads(read_source(mono/'REPLACEMENT_INPUT.json'))
    add('standalone-replacement', replacement, comparison_kind='independent_archived_detector_replacement_not_chronological_revision')
    reverse = deepcopy(replacement)
    reverse['comparison_id'] += '-reverse'
    for anchor in reverse['anchors']:
        anchor['output_a'], anchor['output_b'] = anchor['output_b'], anchor['output_a']
    add('standalone-replacement-reverse', reverse, comparison_kind='derived_reverse_of_same_replacement_not_independent_case')

    for cid, directory, names in [
        ('forty-position', linear, ('forty.input.json', 'forty.geometry.json', 'forty.linear.json')),
        ('public-position', ROOT/'research/perception-revision/0.1.0/linear-example', ('input.json','geometry.json','coefficients.json'))]:
        value = json.loads(read_source(directory/names[0]))
        extras = {}
        for key, name in zip(('geometry','linear'), names[1:]):
            data = read_source(directory/name); path = inputs/(cid+'.'+key+'.json')
            path.write_bytes(data)
            extras[key] = str(path.relative_to(area)); extras[key+'_sha256'] = sha(data)
        add(cid, value, 'position_zero_query', comparison_kind='addition_position_family', **extras)
        if cid == 'forty-position':
            changed = deepcopy(value); changed['loss']['tolerance'] = contract.wire(Fraction(1,2))
            add('forty-position-tolerance-half', changed, 'position_zero_query',
                comparison_kind='threshold_sensitivity_control_not_independent_case', **extras)

    plan = {'artifact_id': 'reiyah.value-disproof.plan', 'version': '0.1.0',
            'frozen_utc': utc(), 'evaluation_kind': 'exposed_development_not_holdout',
            'selection_exposure': 'All 15 old cost cases retained. Direct-pool floors inspected in PREPARATION_PROBE before this freeze.',
            'engine_commit': '38a50ec014cc83e86ea6f247df803ded2971b386',
            'research_commit': 'b3125c4a97c0029a1f70aba7d0ab5105a9b3d233',
            'cases': cases, 'arms': ['A','B','C'],
            'arm_definitions': {
                'A': 'Direct matching endpoints, then adjacency. Conventional independent endpoint matcher for additions; public native legacy/components for replacements. Shared linear proofs for positions.',
                'B': 'Exactly A selector and information; native checked stopping. Exact monotone endpoints for additions; legacy/components for replacements; shared linear proofs for positions.',
                'C': 'Exactly B stopping. Use direct construction when it attains necessary count floor; otherwise pinned conventional IHS functions with current exact monotone adversary. Replacement selector remains A because no replacement IHS implementation is admitted.'},
            'stopping': 'supported iff lower > tolerance; excluded iff upper <= tolerance; otherwise query or retain unresolved. An audit insufficiency witness alone is not an excluded decision.',
            'information': 'Only original exposed graph and already revealed observations enter selection/stopping. No corrected alternatives or reserved data. Oracle is a separate interface, not a process security boundary.',
            'oracle': 'Every deletion answer present, exact within declared deletion family, hypothetical and not a measured annotation. Position rows use zero answers and existing bound coefficients.',
            'budgets': {'max_queries': 512, 'batch': 10, 'seconds_per_arm_case': 120,
                        'ihs_solver_seconds_per_call': 10,
                        'wall_budget_rule': 'checked between atomic stopping/selection calls; final call overshoot retained',
                        'position_queries': 0, 'native_work_limit': 2000000},
            'checkpoints': 'q=0, after each batch, with a shortened batch ending exactly at necessary confirmation floor. First checked decision on this schedule, not hypothetical intermediate stopping.',
            'cache': 'Cold per arm/case. All may reuse bound original inputs and coefficients; exact query duplicates reject. Every distinct prefix is checked. No cross-arm answer transfer or free proof preparation claim.',
            'randomness': 'None in selector ordering; pinned MILP implementation/ties retained with ordered histories.',
            'costs': {'observations': 'unit counts, not prices', 'actual_local_times': ['selection','stopping','wall','preparation','tests','replays'],
                      'human_preparation': None, 'human_review': None, 'engineering_integration': 'session elapsed is available, human rate/time unmeasured',
                      'full_economic_cost': None, 'monetary_rates': None,
                      'linear_optimizer_preparation': 'reused historical coefficient artifact, original acquisition/optimization cost not remeasured; common sunk input for all arms'},
            'case_accounting': 'Every assigned arm/case retained, including failures, resource limits, unresolved outcomes and zero-query draws. Reverse/threshold variants and shared scenes are dependent.',
            'sources': sources, 'preparation_seconds': time.perf_counter()-start,
            'scope': 'Fixed membership/class/eligibility deletion family or fixed position family. No actual corrections, no human costs, no chronological modern revisions, no platform investment gate passed.'}
    put(area/'PLAN.json', plan)
    put(area/'FREEZE.json', {'plan_sha256':sha((area/'PLAN.json').read_bytes()),
                           'driver_sha256':sha((Path(__file__).parent/'compare.py').read_bytes()),
                           'prepare_sha256':sha(Path(__file__).read_bytes()), 'utc':utc()})
    print(json.dumps({'cases':len(cases),'arms':3,'plan_sha256':sha((area/'PLAN.json').read_bytes())}))


if __name__ == '__main__':
    main()
