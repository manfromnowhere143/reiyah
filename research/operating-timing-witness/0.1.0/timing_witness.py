"""Thin optional-world adaptation on retained filtered operating operands."""
import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
from fractions import Fraction
import os
import json
from pathlib import Path
import shutil
import signal
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
for folder in ('operating-policy', 'reference-witness'):
    sys.path.insert(0, str(ROOT / 'research' / folder / '0.1.0'))
from operating_sources import ROLES, digest, file_binding, put, q, read, require, w
from operating_math import aggregate, measured_world
from witness_pool import build_pool, iou
from witness_search import search
from timing_bounds import world_references
from compare_math import validate_canvas, validate_rows

PARTIAL = ('current_partial', 'union_partial')


def put(path, value):
    """Refuse each research write before either storage limit would be crossed."""
    raw = (json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+'\n').encode()
    if 'REIYAH_RESEARCH_ROOT' in os.environ:
        root = Path(os.environ['REIYAH_RESEARCH_ROOT'])
        size = sum(p.stat().st_size for folder in ('private','logs','candidate/research/operating-timing-witness')
                   for p in (root/folder).rglob('*') if p.is_file())
        require(size+len(raw) < 2**30-1024*1024, 'Research storage ceiling; reserve 1 MiB for supervisor receipt')
        require(shutil.disk_usage(root).free-len(raw) >= 5*2**30, 'Free-space floor')
    with Path(path).open('xb') as handle: handle.write(raw)


def targets(parent):
    rows = [(s, i, r) for s in ('primary_rows', 'anchor_rows')
            for i, r in enumerate(parent[s]) if r['evidence'] == 'bound_gap']
    require(all(r['family'] in PARTIAL for _, _, r in rows), 'Unexpected remaining gap family')
    pairs = sorted({(key, r['family']) for _, _, r in rows for key in r['state_keys']})
    return rows, pairs


def bound_read(entry):
    require(file_binding(entry['path']) == {k: entry[k] for k in ('path', 'bytes', 'sha256')}, 'Dependent source bytes changed')
    return read(entry['path'])


def load_parent(prior):
    prior = Path(prior)
    parent_path = prior / 'private/operating-witness-01/analysis/RESULTS.json'
    verification_path = prior / 'private/operating-witness-01/VERIFICATION.json'
    parent = read(parent_path); checked = read(verification_path)
    require(checked['results_sha256'] == file_binding(parent_path)['sha256']
            and checked['all_7707_parent_rows_checked'] and checked['all_universal_decisions_unchanged'], 'Parent check absent')
    policy = read(prior / 'private/operating-policy-01/runs/operating-01/RESULTS.json')
    states = {e['key']: bound_read(e) for e in policy['state_records']}
    proofs = {e['key']: bound_read(e) for e in policy['proof_records']}
    banks = {e['image_id']: bound_read(e) for e in policy['world_banks']}
    for e in parent['refined_states']: states[e['key']] = bound_read(e)['state']
    for e in parent['new_proofs']:
        value = bound_read(e)
        if e['key'] in proofs:
            require(all(proofs[e['key']][k] == value[k] for k in ('image', 'references', 'measurement', 'proof')), 'Inherited collision')
        proofs[e['key']] = value
    temporal = read(prior / 'private/reference-witness-01/runs/witness-01/RESULTS.json')
    images = {e['image_id']: bound_read(e) for e in temporal['image_records']}
    return parent, states, proofs, banks, images


def context(state, bank, temporal, family):
    require(family in PARTIAL, 'Nonpartial target')
    value = state['analysis']['families'][family]; census = bank['temporal'][family.removesuffix('_partial')]
    require(value['state'] == census['state'] == 'available', 'Unavailable input census')
    unknown = census['unknown_ids']
    require(type(unknown) is list and unknown == sorted(set(unknown))
            and census['unknown_count'] == len(unknown), 'Invalid unknown census')
    known = bank['worlds'][bank['known_world']]
    require(known == temporal['known_references'], 'Known geometry binding differs')
    require(unknown == temporal[family.removesuffix('_partial')+'_unknown_instances'], 'Unknown identity binding differs')
    bases = deepcopy(temporal['candidate_pool']['rectangles'])
    for scope in ('current', 'union'):
        record = bank['temporal'][scope]
        if record['state'] == 'available':
            for key in record['worlds']:
                references = bank['worlds'][key]
                require(references[:len(known)] == known, 'Bank changes known references')
                bases.extend(r['xyxy'] for r in references[len(known):])
    bases = [list(map(w, values)) for values in sorted({tuple(map(q, row)) for row in bases})]
    return known, unknown, bases


def seed_worlds(state, known, unknown, pool, proofs, family):
    predictions = {r['id']: r for role in ROLES for r in state['image'][role]['value']}
    lookup = {tuple(n): i for i, n in enumerate(pool['neighborhoods'])}; seeds = []
    for key in state['analysis']['families'][family]['proof_keys']:
        record = proofs[key]; references = record['references']
        require(record['image'] == state['image'] and references[:len(known)] == known, 'Seed world binding differs')
        optional = references[len(known):]; ids = [r['id'] for r in optional]
        require(len(ids) == len(set(ids)) and set(ids) <= {'timing-unknown:'+u for u in unknown}, 'Seed census differs')
        indices = []
        for row in optional:
            n = tuple(k for k, pred in sorted(predictions.items()) if iou(pred, row) >= Fraction(1, 2))
            if n:
                require(n in lookup, 'Seed neighborhood absent'); indices.append(lookup[n])
        seeds.append({'indices': sorted(indices), 'measurement': record['measurement']})
    return seeds


def search_identity(image, known, unknown, pool, seeds, bounds):
    return digest({'image': image, 'known': known, 'unknown': unknown, 'pool': pool, 'seeds': seeds, 'bounds': bounds})


def refine(state, bank, temporal, family, inherited_proofs, new_proofs, pools, searches, pair):
    updated = deepcopy(state); previous = state['analysis']['families'][family]
    known, unknown, bases = context(state, bank, temporal, family)
    if previous['attained'] == previous['bounds']:
        return updated, {'state': 'inherited_exact', 'new_search': False}
    pool_key = digest({'image': state['image'], 'known': known, 'bases': bases})
    if pool_key not in pools: pools[pool_key] = build_pool(state['image'], known, bases)
    pool = pools[pool_key]; seeds = seed_worlds(state, known, unknown, pool, inherited_proofs, family)
    key = search_identity(state['image'], known, unknown, pool, seeds, previous['bounds'])
    reused = None
    if key in searches:
        reused, found = searches[key]
    else:
        found = search(state['image'], known, unknown, pool, seeds)
        searches[key] = (pair, found)
    require(found['bounds'] == previous['bounds'], 'Search changes universal bound')
    chosen = []; attained = []; endpoints = []; improved = []
    for i, world in enumerate(found['worlds']):
        references = world_references(known, unknown, world['indices'], pool['rectangles'])
        validate_rows(references); validate_canvas(references, state['image'])
        proof_key = measured_world(state['image'], references, new_proofs)
        require(new_proofs[proof_key]['measurement'] == world['measurement'], 'Search/native disagreement')
        value = q(world['measurement']['delta'])
        require(q(previous['bounds'][0]) <= value <= q(previous['bounds'][1]), 'COUNTEREXAMPLE to inherited bound')
        better = value < q(previous['attained'][i]) if i == 0 else value > q(previous['attained'][i])
        chosen.append(proof_key if better else previous['proof_keys'][i]); improved.append(better)
        attained.append(world['measurement']['delta'] if better else previous['attained'][i])
        operations = [{'operation': 'optional_eligible', 'instance': u, 'candidate_index': index}
                      for u, index in zip(unknown, world['indices'])]
        endpoints.append({'proof_key': proof_key, 'operations': operations,
                          'absent_or_ineligible': unknown[len(world['indices']):]})
    updated['analysis']['families'][family] = {**previous, 'attained': attained, 'proof_keys': chosen}
    detail = {'state': 'complete', 'new_search': reused is None, 'pool_key': pool_key,
              'search_key': key, 'reused_from': reused, 'seeds': seeds, 'search': found,
              'endpoints': endpoints, 'improved_endpoints': improved}
    return updated, detail


def prepare(prior, output):
    parent, states, proofs, banks, temporal = load_parent(prior); rows, pairs = targets(parent)
    require(len(rows) == 279 and Counter(s for s, _, _ in rows) == {'primary_rows': 224, 'anchor_rows': 55}, 'Target count differs')
    require(len(pairs) == 397 and len({k for k, _ in pairs}) == 356, 'State allocation differs')
    search_pairs = []
    for key, family in pairs:
        state = states[key]; context(state, banks[state['image']['id']], temporal[state['image']['id']], family)
        value = state['analysis']['families'][family]
        if value['attained'] != value['bounds']: search_pairs.append([key, family])
    require(len(search_pairs) == 100, 'Search allocation differs')
    value = {'artifact_id': 'reiyah.operating-timing-witness.allocation', 'version': '0.1.0',
             'target_rows': [[s, i] for s, i, _ in rows], 'target_pairs': [list(p) for p in pairs],
             'search_pairs': search_pairs, 'parent_rows': sum(len(parent[s]) for s in ('primary_rows', 'anchor_rows')),
             'parent_unique_states': len(states), 'parent_unique_proofs': len(proofs),
             'created_utc': datetime.now(timezone.utc).isoformat(), 'new_search_outcomes': False}
    put(output, value); return value


def freeze(prior, area, allocation, controls, supervisor, runtime):
    require(not area.exists(), 'Freeze area already exists'); area.mkdir(parents=True)
    paths = {Path(allocation), Path(supervisor), Path(runtime).resolve()}
    paths.add(Path(supervisor).with_name('test_phase.py'))
    session = Path(supervisor).resolve().parents[1]
    paths.add(session/'OWNER.json')
    for suffix in ('-STARTED.json', '-COMPLETED.json', '.stdout', '.stderr'):
        paths.add(session/'logs'/('supervisor-controls-03'+suffix))
    require(read(session/'logs/supervisor-controls-03-COMPLETED.json')['exit_code'] == 0, 'Supervisor controls failed')
    prior = Path(prior)
    for name in ('operating-witness-01', 'operating-policy-01', 'reference-witness-01'):
        f = prior / 'private' / name / 'FREEZE.json'; paths.add(f)
        for b in read(f)['bindings']:
            require(file_binding(b['path']) == b, 'Historical frozen source changed'); paths.add(Path(b['path']))
    parent, _, _, _, _ = load_parent(prior)
    paths.update([prior/'private/operating-witness-01/analysis/RESULTS.json', prior/'private/operating-witness-01/VERIFICATION.json'])
    for field in ('refined_states', 'new_proofs'): paths.update(Path(e['path']) for e in parent[field])
    for suffix in ('-STARTED.json', '-COMPLETED.json', '.stdout', '.stderr'):
        paths.add(Path(str(controls)+suffix))
    require(read(str(controls)+'-COMPLETED.json')['exit_code'] == 0, 'Controls failed')
    for folder in ('operating-timing-witness', 'operating-policy', 'reference-witness', 'reference-timing',
                   'reference-translation', 'public-predictions'):
        paths.update((ROOT/'research'/folder/'0.1.0').glob('*.py'))
    for module in list(sys.modules.values()):
        path = getattr(module, '__file__', None)
        if path and Path(path).is_file() and Path(path).resolve().is_relative_to(ROOT): paths.add(Path(path).resolve())
    for family in ('perception-decision','perception-revision'):
        paths.update((ROOT/'research'/family/'0.1.0').glob('*.schema.json'))
    paths.add(Path(__file__).with_name('PLAN.md'))
    value = {'artifact_id': 'reiyah.operating-timing-witness.freeze', 'version': '0.1.0',
             'frozen_utc': datetime.now(timezone.utc).isoformat(), 'prior': str(prior),
             'allocation': str(allocation), 'bindings': [file_binding(p) for p in sorted(paths)],
             'previous_outcomes_known': True, 'new_actual_search_outcomes': False,
             'limits': {'rectangles': 100000, 'neighborhoods': 4096, 'measurements': 50000,
                        'references': 128, 'cumulative_search_seconds': 1200, 'cumulative_verification_seconds': 1200}}
    put(area/'FREEZE.json', value)
    print({'freeze_sha256': file_binding(area/'FREEZE.json')['sha256'], 'bindings': len(paths)}, flush=True)


def sources(area):
    frozen = read(area/'FREEZE.json')
    for binding in frozen['bindings']:
        require(file_binding(binding['path']) == binding, 'Frozen source or implementation changed')
    parent, states, proofs, banks, temporal = load_parent(frozen['prior'])
    rows, pairs = targets(parent); allocation = read(frozen['allocation'])
    require(allocation['target_rows'] == [[s, i] for s, i, _ in rows]
            and allocation['target_pairs'] == [list(p) for p in pairs], 'Frozen allocation differs')
    return frozen, allocation, parent, states, proofs, banks, temporal


def run(area):
    started = datetime.now(timezone.utc).isoformat(); tick = time.perf_counter()
    frozen, allocation, parent, states, proofs, banks, temporal = sources(area)
    output = area/'analysis'; output.mkdir(); (output/'pairs').mkdir(); (output/'proofs').mkdir(); (output/'pools').mkdir()
    pools = {}; searches = {}; new = {}; entries = []; failures = {}; deadline = float(os.environ['REIYAH_PHASE_DEADLINE'])
    def expired(*_): raise TimeoutError('Cumulative search deadline reached')
    signal.signal(signal.SIGALRM, expired)
    for key, family in allocation['target_pairs']:
        pair = [key, family]; state = states[key]; iid = state['image']['id']
        prior_keys = set(new)
        try:
            value = state['analysis']['families'][family]
            if value['attained'] != value['bounds']:
                if time.monotonic() >= deadline: raise TimeoutError('Cumulative search deadline reached before allocated pair')
                signal.setitimer(signal.ITIMER_REAL, max(.001, deadline-time.monotonic()))
            updated, detail = refine(state, banks[iid], temporal[iid], family, proofs, new, pools, searches, pair)
        except Exception as exc:
            updated = state; detail = {'state': 'search_incomplete', 'new_search': True,
                'error': type(exc).__name__+': '+str(exc), 'retained_attempt_proof_keys': sorted(set(new)-prior_keys)}
            failures[key+':'+family] = detail['error']
            if 'COUNTEREXAMPLE' in str(exc): raise
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
        path = output/'pairs'/(key+'-'+family+'.json'); put(path, {'state': updated, 'refinement': detail})
        entries.append({'key': key, 'family': family, **file_binding(path)}); states[key] = updated
        for proof_key in sorted(set(new)-prior_keys): put(output/'proofs'/(proof_key+'.json'), new[proof_key])
    pool_records = []
    for key, pool in sorted(pools.items()):
        path = output/'pools'/(key+'.json'); put(path, pool); pool_records.append({'key': key, **file_binding(path)})
    put(output/'SEARCH_ATTEMPTS.json', [{'key': k, 'pair': pair, 'search': found}
                                      for k, (pair, found) in sorted(searches.items())])
    result = {}
    for section in ('primary_rows', 'anchor_rows'):
        result[section] = []
        for old in parent[section]:
            case = {'id': old['case_id'], 'group': old['group'], 'images': old['membership']}
            row = aggregate(case, old['family'], old['state_keys'], states)
            identity = 'cell_id' if section == 'primary_rows' else 'threshold'; row[identity] = old[identity]
            require(all(row[k] == old[k] for k in ('state', 'decision', 'bounds', 'membership', 'blocked_images')), 'Universal result changed')
            result[section].append(row)
    classifications = []
    for section, index in allocation['target_rows']:
        row = result[section][index]
        failed = [key+':'+row['family'] for key in row['state_keys'] if key+':'+row['family'] in failures]
        label = 'opposing_worlds_established' if row['evidence'] == 'opposite_worlds' else 'search_incomplete' if failed else 'still_bound_gap'
        classifications.append({'section': section, 'index': index, 'classification': label, 'failed_components': failed})
    result.update(artifact_id='reiyah.operating-timing-witness.results', version='0.1.0', status='exploratory',
        started_utc=started, finished_utc=datetime.now(timezone.utc).isoformat(), seconds=time.perf_counter()-tick,
        freeze_sha256=file_binding(area/'FREEZE.json')['sha256'], refined_pairs=entries, pools=pool_records,
        new_proofs=[{'key': k, **file_binding(output/'proofs'/(k+'.json'))} for k in sorted(new)],
        search_attempts=file_binding(output/'SEARCH_ATTEMPTS.json'),
        failures=failures, target_classifications=classifications,
        evidence_counts={s: dict(Counter(r['evidence'] or 'input_blocked' for r in result[s])) for s in ('primary_rows','anchor_rows')},
        new_image_reads=0, new_model_calls=0, new_download_bytes=0, reserved_outcomes_accessed=0,
        human_seconds=None, full_economic_cost=None, independent_scientific_replication=False)
    put(output/'RESULTS.json', result)
    print({'targets': dict(Counter(r['classification'] for r in classifications)), 'failures': failures,
           'new_proofs': len(new), 'pools': len(pools), 'searches': len(searches), 'seconds': result['seconds']}, flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(); sub = p.add_subparsers(dest='mode', required=True)
    prep = sub.add_parser('prepare'); prep.add_argument('prior', type=Path); prep.add_argument('output', type=Path)
    f = sub.add_parser('freeze')
    for arg in ('prior', 'area', 'allocation', 'controls', 'supervisor', 'runtime'): f.add_argument(arg, type=Path)
    r = sub.add_parser('run'); r.add_argument('area', type=Path)
    args = vars(p.parse_args()); mode = args.pop('mode')
    globals()[mode](**args)
