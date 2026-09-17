"""Exact closed-ball geometry premises over an existing comparison (0.1.0)."""
from .contract import (DIRECTORY, MAX_INPUT_BYTES, MAX_WORK, ROLES, encoded, rational,
                       require, schema_check, unique)

REQUEST_SCHEMA = DIRECTORY / 'localization-request.schema.json'
WITNESS_SCHEMA = DIRECTORY / 'localization-witness.schema.json'
VERSION = '0.1.0'
MAX_COORDINATE = 10_000_000
MAX_EDGES = 2048


def point(values):
    result = tuple(rational(v) for v in values)
    require(all(abs(v) <= MAX_COORDINATE for v in result),
            'LOCALIZATION_COORDINATE', 'Coordinate or shift exceeds the magnitude limit')
    return result


def squared_distance(a, b):
    return sum((x - y) ** 2 for x, y in zip(a, b))


def edge_bounds(distance_squared, threshold, radius):
    """Strict edge threshold, inclusive displacement radius; no square roots."""
    return (radius < threshold and distance_squared < (threshold - radius) ** 2,
            distance_squared < (threshold + radius) ** 2)


def validate_request(case, request):
    require(len(encoded(request)) <= MAX_INPUT_BYTES, 'INPUT_SIZE', 'Geometry request exceeds byte limit')
    schema_check(request, REQUEST_SCHEMA)
    require(request['comparison_id'] == case['comparison_id'], 'LOCALIZATION_COMPARISON', 'Wrong comparison')
    require(request['reference_context_sha256'] == case['reference_context_sha256'],
            'LOCALIZATION_CONTEXT', 'Reference context changed')
    threshold = rational(request['threshold'])
    require(0 < threshold <= MAX_COORDINATE, 'LOCALIZATION_THRESHOLD', 'Positive bounded threshold required')
    unique([a['id'] for a in request['anchors']], 'geometry anchors')
    supplied = {a['id']: a for a in request['anchors']}
    require(set(supplied) == {a['id'] for a in case['anchors']},
            'LOCALIZATION_MEMBERSHIP', 'Every comparison anchor must be represented')
    for anchor in case['anchors']:
        row = supplied[anchor['id']]
        unique([d['id'] for d in row['detections']], 'geometry detections')
        unique([o['id'] for o in row['references']], 'geometry references')
        known = {d['id']: d['record_sha256'] for role in ROLES for d in anchor[role].get('value', [])}
        declared = {d['id']: d['record_sha256'] for d in row['detections']}
        require(known == declared, 'LOCALIZATION_MEMBERSHIP', 'Detection geometry has missing, invented or rebound records')
        require({o['id'] for o in row['references']} == {o['id'] for o in anchor['reference'].get('objects', [])},
                'LOCALIZATION_MEMBERSHIP', 'Reference geometry has missing or invented records')
        for item in row['detections'] + row['references']:
            point(item['xy'])
        for item in row['references']:
            require(0 <= rational(item['radius']) <= MAX_COORDINATE,
                    'LOCALIZATION_RADIUS', 'Residual radius must be nonnegative and bounded')
    return request


def prepare(case, request):
    """Build a sound graph envelope or an explicit unavailable outcome."""
    validate_request(case, request)
    if any(a[r]['state'] != 'observed' for a in case['anchors'] for r in ROLES):
        return 'unavailable_outputs', None
    if any(a['reference']['state'] != 'finite' for a in case['anchors']):
        return 'open_references', None
    if case['model']['variables'] or case['model']['clauses']:
        return 'conditional_reference_model', None
    byid = {a['id']: a for a in request['anchors']}
    pairs = sum(len(r['detections']) * len(r['references']) for r in request['anchors'])
    if 3 * pairs > MAX_WORK:
        return 'geometry_work_limit', None
    threshold = rational(request['threshold'])
    rows = []
    for anchor in case['anchors']:
        source = byid[anchor['id']]
        dets = {d['id']: (d['class'], point(d['xy'])) for d in source['detections']}
        refs = {o['id']: (o['class'], point(o['xy']), rational(o['radius'])) for o in source['references']}
        nominal, guaranteed, possible = set(), set(), set()
        for did, (dc, dxy) in dets.items():
            for oid, (oc, oxy, radius) in refs.items():
                if dc != oc:
                    continue
                distance = squared_distance(dxy, oxy)
                if distance < threshold ** 2:
                    nominal.add((did, oid))
                must, may = edge_bounds(distance, threshold, radius)
                if must:
                    guaranteed.add((did, oid))
                if may:
                    possible.add((did, oid))
        require(nominal == {(e['detection'], e['object']) for e in anchor['reference']['edges']},
                'LOCALIZATION_NOMINAL_GRAPH', 'Exact nominal geometry differs from the bound comparison graph')
        if len(possible) > MAX_EDGES:
            return 'possible_edge_limit', None
        rows.append({'anchor': anchor, 'detections': dets, 'references': refs,
                     'guaranteed': guaranteed, 'possible': possible,
                     'a': {d['id'] for d in anchor['output_a']['value']},
                     'b': {d['id'] for d in anchor['output_b']['value']}})
    return None, {'rows': rows, 'geometry_work': 3 * pairs, 'pairs': pairs}


def matching_work(prepared, displaced=None):
    # Explicit shifts require a fourth full adjacency calculation after the
    # nominal / guaranteed / possible comparisons used by both proof routes.
    work = prepared['geometry_work'] + (prepared['pairs'] if displaced is not None else 0)
    for row in prepared['rows']:
        for role, graph in (('a', row['possible']), ('b', row['guaranteed'])):
            edges = graph if displaced is None else displaced[row['anchor']['id']]
            count = sum(d in row[role] for d, _ in edges)
            work += 2 * (len(row[role]) + 1) * (len(row['references']) + count + 1)
    return work


def displacement_graphs(request, prepared, candidate):
    require(len(encoded(candidate)) <= MAX_INPUT_BYTES, 'INPUT_SIZE', 'Displacement witness exceeds byte limit')
    schema_check(candidate, WITNESS_SCHEMA)
    unique([(r['anchor'], r['object']) for r in candidate['displacements']], 'displacement records')
    anchors = {r['anchor']['id']: r for r in prepared['rows']}
    shifts = {}
    for entry in candidate['displacements']:
        aid, oid = entry['anchor'], entry['object']
        require(aid in anchors and oid in anchors[aid]['references'], 'LOCALIZATION_WITNESS_ENDPOINT', 'Unknown displaced reference')
        shift = point(entry['shift'])
        radius = anchors[aid]['references'][oid][2]
        require(sum(v * v for v in shift) <= radius * radius,
                'LOCALIZATION_WITNESS_RADIUS', 'Displacement exceeds the supplied residual radius')
        shifts[aid, oid] = shift
    threshold = rational(request['threshold'])
    result = {}
    for aid, row in anchors.items():
        edges = set()
        for oid, (oc, oxy, _) in row['references'].items():
            delta = shifts.get((aid, oid), (0, 0))
            new = tuple(x + v for x, v in zip(oxy, delta))
            for did, (dc, dxy) in row['detections'].items():
                if dc == oc and squared_distance(new, dxy) < threshold ** 2:
                    edges.add((did, oid))
        require(row['guaranteed'] <= edges <= row['possible'],
                'LOCALIZATION_ENVELOPE', 'Admitted displacement contradicts the graph envelope')
        result[aid] = edges
    return result
