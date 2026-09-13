"""Compare compilation with full losses from coordinate-based partial injections.

This is a bounded synthetic compiler check, not a research-lane planner. The
normalizer, exact rational representation and input parser remain shared premises.
"""
import hashlib
from itertools import product
import json
from pathlib import Path
import sys
import time

if __name__ == '__main__':
    sys.path.insert(0, sys.argv[1])
from tools import perception_reference as compiler
from tools.perception_decision import checker, contract, kernel


def matching(detections, objects):
    def search(i, used):
        if i == len(detections):
            return 0
        best = search(i+1, used)
        _, kind, point = detections[i]
        for j, (_, label, xy) in enumerate(objects):
            if j not in used and kind == label and sum((a-b)**2 for a, b in zip(point, xy)) < 4:
                best = max(best, 1+search(i+1, used | {j}))
        return best
    return search(0, set())


def direct(args):
    spec, case, normals, catalog = args
    rows = []
    fn, fp = [contract.rational(case['loss'][k]) for k in ('false_negative', 'false_positive')]
    normal = {r['anchor_id']: r for r in normals}
    clock = {r['sample_token']: r for r in catalog['anchors']}
    for world in spec['worlds']:
        references = {a['anchor_id']: a for a in world['anchors']}
        total, details = 0, []
        for anchor in case['anchors']:
            name = anchor['id']
            records = {r['detection']['id']: r['record'] for r in normal[name]['qualified_records']}
            row = clock[normal[name]['sample_token']]
            ego = [contract.rational(q) for q in row['nominal_ego_xy']['value']]
            objects = []
            for obj in references[name]['objects']:
                assert obj['state'] == 'point' and obj['timestamp_us'] == row['anchor_timestamp_us']
                xy = tuple(contract.rational(q) for q in obj['xy'])
                if obj['class'] != 'outside_target' and sum((x-y)**2 for x, y in zip(xy, ego)) <= 2500:
                    objects.append((obj['id'], obj['class'], xy))
            detections = {}
            for role in ('base', 'additions'):
                assert anchor[role]['state'] == 'observed'
                detections[role] = [(r['id'], records[r['id']]['class'],
                                     tuple(contract.rational(q) for q in records[r['id']]['xy']))
                                    for r in anchor[role]['value']]
            base = detections['base']; augmented = base+detections['additions']
            m0, m1 = matching(base, objects), matching(augmented, objects)
            loss0 = fn*(len(objects)-m0)+fp*(len(base)-m0)
            loss1 = fn*(len(objects)-m1)+fp*(len(augmented)-m1)
            total += contract.rational(anchor['weight'])*(loss0-loss1)
            edges = sorted([d, o] for d, kind, point in augmented for o, label, xy in objects
                           if kind == label and sum((a-b)**2 for a, b in zip(point, xy)) < 4)
            details.append({'anchor_id': name, 'objects': sorted(o for o, _, _ in objects),
                            'edges': edges, 'base_matching': m0, 'augmented_matching': m1,
                            'loss_base': contract.wire(loss0), 'loss_augmented': contract.wire(loss1)})
        rows.append({'world_id': world['id'], 'weighted_delta': contract.wire(total), 'anchors': details})
    values = [contract.rational(r['weighted_delta']) for r in rows]
    return {'worlds': rows, 'bounds': {'lower': contract.wire(min(values)), 'upper': contract.wire(max(values))}}


def graph_checks(compiled, receipt, expected):
    encodings = {w['world_id']: {q['variable']: q['value'] for q in w['when']} for w in receipt['world_encodings']}
    variables = compiled['model']['variables']
    admitted = {tuple(bits) for bits in product((False, True), repeat=len(variables))
                if all(any(dict(zip(variables, bits))[q['variable']] == q['value'] for q in clause)
                       for clause in compiled['model']['clauses'])}
    assert len(encodings) == len(expected['worlds'])
    assert admitted == {tuple(w[v] for v in variables) for w in encodings.values()}
    checked, open_rows = 0, []
    refs = {a['id']: a['reference'] for a in compiled['anchors']}
    for w in expected['worlds']:
        assignment = encodings[w['world_id']]
        active = lambda row: all(assignment[q['variable']] == q['value'] for q in row['when'])
        for a in w['anchors']:
            ref = refs[a['anchor_id']]
            if ref['state'] == 'open':
                open_rows.append([w['world_id'], a['anchor_id']]); continue
            mappings = [m for m in receipt['object_mapping'] if m['world_id'] == w['world_id'] and m['anchor_id'] == a['anchor_id']]
            names = {m['graph_id']: m['object_id'] for m in mappings}
            assert len(names) == len(mappings) == len(a['objects'])
            objects = {o['id'] for o in ref['objects'] if active(o)}
            assert sorted(names[o] for o in objects) == a['objects']
            edges = sorted([e['detection'], names[e['object']]] for e in ref['edges'] if e['object'] in objects and active(e))
            assert edges == a['edges']
            checked += 1
    return {'finite_world_anchor_graphs_checked': checked, 'open_world_anchor_rows': open_rows}


def run(args):
    start = time.perf_counter(); expected = direct(args); direct_seconds = time.perf_counter()-start
    start = time.perf_counter(); compiled, receipt = compiler.compile_model(*args); compile_seconds = time.perf_counter()-start
    start = time.perf_counter(); packet = kernel.produce(compiled); kernel_seconds = time.perf_counter()-start
    start = time.perf_counter(); checker.check(compiled, packet); checker_seconds = time.perf_counter()-start
    comparison = graph_checks(compiled, receipt, expected)
    spec = args[0]
    eligible = {(w['world_id'], a['anchor_id']): set(a['objects']) for w in expected['worlds'] for a in w['anchors']}
    source_rows = [{'world_id': w['id'], 'anchor_id': a['anchor_id'], 'object_id': o['id'],
                    'record_sha256': o['record_sha256'], 'members': o['members']}
                   for w in spec['worlds'] for a in w['anchors'] for o in a['objects']
                   if o['id'] in eligible[w['id'], a['anchor_id']]]
    assert [{k: v for k, v in m.items() if k != 'graph_id'} for m in receipt['object_mapping']] == source_rows
    assert receipt['reference_semantic_sha256'] == hashlib.sha256(contract.encoded(spec)).hexdigest()
    finite = not comparison['open_world_anchor_rows']
    if finite:
        assert packet['result']['bounds'] == expected['bounds']
    else:
        assert contract.rational(packet['result']['bounds']['lower']) <= contract.rational(expected['bounds']['lower'])
        assert contract.rational(packet['result']['bounds']['upper']) >= contract.rational(expected['bounds']['upper'])
    comparison['source_mapping_rows_checked'] = len(source_rows)
    return {'compiled': compiled, 'compilation': receipt, 'checked_packet': packet, 'direct': expected,
            'graph_checks': comparison,
            'size': {'compiled_bytes': len(contract.encoded(compiled)), 'compilation_bytes': len(contract.encoded(receipt)),
                     'graph_objects': {a['id']: len(a['reference'].get('objects', [])) for a in compiled['anchors']},
                     'graph_edges': {a['id']: len(a['reference'].get('edges', [])) for a in compiled['anchors']},
                     'mapping_rows': len(receipt['object_mapping'])},
            'timing': {'direct_seconds': direct_seconds, 'compile_seconds': compile_seconds,
                       'kernel_seconds': kernel_seconds, 'checker_seconds': checker_seconds}}


if __name__ == '__main__':
    inputs, output = Path(sys.argv[2]), Path(sys.argv[3])
    selected = json.loads(Path(__file__).with_name('cases.json').read_bytes())['cases']
    assert {p.name for p in inputs.iterdir()} == {r['filename'] for r in selected}
    output.mkdir()
    summaries = {}
    for row in selected:
        path = inputs/row['filename']; raw = path.read_bytes()
        assert len(raw) == row['byte_size'] and hashlib.sha256(raw).hexdigest() == row['sha256']
        args = json.loads(raw)
        results = run(args)
        costs = results.pop('timing')
        results['input_sha256'] = hashlib.sha256(raw).hexdigest()
        (output/path.name).write_bytes(contract.encoded(results))
        (output/(path.stem+'.cost.json')).write_bytes(contract.encoded(costs))
        summaries[path.stem] = {'result': results['checked_packet']['result'], 'direct_bounds': results['direct']['bounds'],
                               'size': results['size'], 'geometry_comparisons_budgeted': results['compilation']['geometry_comparisons_budgeted'],
                               'graph_checks': results['graph_checks'], 'costs': costs}
    print(json.dumps(summaries, sort_keys=True))
