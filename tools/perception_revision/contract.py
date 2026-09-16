"""Shared strict input semantics; no matching algorithm or physical authority."""
import copy
import hashlib
from itertools import product
from pathlib import Path

from jsonschema import Draft202012Validator
from tools.perception_decision.contract import (
    Invalid, MAX_INPUT_BYTES, MAX_PACKET_BYTES, MAX_WORLDS, MAX_WORK,
    encoded, load as load_bytes, parse, rational, wire,
    validate as validate_addition,
)

DIRECTORY = Path(__file__).resolve().parents[2] / 'research/perception-revision/0.1.0'
SCHEMA = DIRECTORY / 'input.schema.json'
AUDIT_SCHEMA = DIRECTORY / 'audit-request.schema.json'
ROLES = ('output_a', 'output_b')
MAX_AUDIT_VARIANTS = 4096


def require(condition, code, detail):
    if not condition:
        raise Invalid(code, detail)


def unique(values, detail):
    require(len(values) == len(set(values)), 'DUPLICATE_ID', detail)


def schema_check(value, path):
    error = next(Draft202012Validator(parse(path.read_bytes())).iter_errors(value), None)
    if error:
        raise Invalid('INPUT_SCHEMA', '/'.join(map(str, error.absolute_path)) + ': ' + error.message[:500])


def enabled(literals, world):
    return all(world[item['variable']] is item['value'] for item in literals)


def admitted(model, world):
    return all(any(world[item['variable']] is item['value'] for item in clause)
               for clause in model['clauses'])


def worlds(model):
    for bits in product((False, True), repeat=len(model['variables'])):
        env = dict(zip(model['variables'], bits))
        if admitted(model, env):
            yield bits, env


def validate(case):
    schema_check(case, SCHEMA)
    variables = case['model']['variables']
    unique(variables, 'model variables')
    variable_set = set(variables)

    def literals(items):
        names = [item['variable'] for item in items]
        unique(names, 'Repeated variable in condition or clause')
        require(set(names) <= variable_set, 'UNKNOWN_VARIABLE', 'Undeclared reference variable')

    for clause in case['model']['clauses']:
        literals(clause)
    assignment = case['model'].get('feasible_assignment')
    if assignment is not None:
        require(len(assignment) == len(variables), 'ASSIGNMENT_SIZE', 'One Boolean per variable')
        require(admitted(case['model'], dict(zip(variables, assignment))),
                'INVALID_MODEL_WITNESS', 'Assignment violates a clause')
    require(all(rational(v) >= 0 for v in case['loss'].values()), 'NEGATIVE_LOSS', 'Nonnegative penalties and tolerance required')
    unique([a['id'] for a in case['anchors']], 'anchor identifiers')
    weights = [rational(a['weight']) for a in case['anchors']]
    require(all(w >= 0 for w in weights) and sum(weights) == 1,
            'POPULATION_WEIGHTS', 'Nonnegative common weights must sum to one')
    for a in case['anchors']:
        identities = {}
        complete = True
        for role in ROLES:
            complete &= a[role]['state'] == 'observed'
            if a[role]['state'] == 'observed':
                rows = a[role]['value']
                unique([d['id'] for d in rows], a['id'] + ':' + role)
                for row in rows:
                    key, digest = row['id'], row['record_sha256']
                    require(key not in identities or identities[key] == digest,
                            'COMMON_OUTPUT_IDENTITY', 'A shared detection ID has different record bytes')
                    identities[key] = digest
        ref = a['reference']
        if ref['state'] == 'open':
            continue
        objects = [o['id'] for o in ref['objects']]
        unique(objects, a['id'] + ':objects')
        unique([(e['detection'], e['object']) for e in ref['edges']], a['id'] + ':edges')
        for row in ref['objects'] + ref['edges']:
            literals(row['when'])
        for edge in ref['edges']:
            require(edge['object'] in objects and (not complete or edge['detection'] in identities),
                    'UNKNOWN_ENDPOINT', a['id'] + ':unknown graph endpoint')
    return case


def validate_request(case, request):
    schema_check(request, AUDIT_SCHEMA)
    require(request['comparison_id'] == case['comparison_id'], 'AUDIT_COMPARISON', 'Wrong comparison')
    require(request['reference_context_sha256'] == case['reference_context_sha256'],
            'AUDIT_REFERENCE_CONTEXT', 'Reference interpretation/custody context changed')
    keys = [(o['anchor'], o['object']) for o in request['observations']]
    unique(keys, 'An observation cannot be repeated or contradicted')
    anchors = {a['id']: a for a in case['anchors']}
    for aid, oid in keys:
        require(aid in anchors and anchors[aid]['reference']['state'] == 'finite'
                and oid in {o['id'] for o in anchors[aid]['reference']['objects']},
                'AUDIT_ENDPOINT', 'Observation has an unknown or open-reference endpoint')
    return request


def load(path, digest):
    return validate(load_bytes(path, digest, MAX_INPUT_BYTES, validate_input=False))


def graph(anchor, env, removed=frozenset()):
    present = {o['id'] for o in anchor['reference']['objects']
               if enabled(o['when'], env) and (anchor['id'], o['id']) not in removed}
    edges = {(e['detection'], e['object']) for e in anchor['reference']['edges']
             if e['object'] in present and enabled(e['when'], env)}
    return present, edges


def capacity(case):
    count = 1 << len(case['model']['variables'])
    work = 1 + len(case['model']['variables']) + sum(map(len, case['model']['clauses']))
    for a in case['anchors']:
        if a['reference']['state'] == 'finite':
            ref = a['reference']
            work += sum(len(row['when']) for row in ref['objects'] + ref['edges'])
            # Each matcher sees only its own output vertices and eligible edges.
            # Count all potential guarded edges; never use an observed easy world
            # to reduce the screening budget for other joint worlds.
            for role in ROLES:
                nodes = {d['id'] for d in a[role].get('value', [])}
                edge_count = sum(e['detection'] in nodes for e in ref['edges'])
                work += 2 * (len(nodes) + 1) * (len(ref['objects']) + edge_count + 1)
    return count, work


def anchor_bounds(anchor, fn, fp):
    aa, bb = ({d['id'] for d in anchor[role]['value']} for role in ROLES)
    p, q = len(aa - bb), len(bb - aa)
    return -fn * p - fp * q, fn * q + fp * p


def from_addition(case, reference_context_sha256=None):
    """Explicit adapter for observed legacy outputs; keeps their declared suppression."""
    validate_addition(case)
    require(all(a[r]['state'] == 'observed' for a in case['anchors'] for r in ('base', 'additions')),
            'ADAPTER_OUTPUT_UNAVAILABLE', 'Cannot construct an augmented output from unavailable detections')
    result = copy.deepcopy(case)
    result['artifact_id'] = 'reiyah.perception-revision.input'
    context = {'cohort_id': case['cohort_id'], 'model': case['model'],
               'reference_objects': [(a['id'], a['reference'].get('objects')) for a in case['anchors']],
               'assumptions': case['assumptions'], 'evidence_kind': case['evidence_kind']}
    result['reference_context_sha256'] = reference_context_sha256 or hashlib.sha256(encoded(context)).hexdigest()
    for a in result['anchors']:
        a['output_a'] = a.pop('base')
        a['output_b'] = {'state': 'observed', 'value': copy.deepcopy(a['output_a']['value']) + a.pop('additions')['value']}
    return validate(result)


def rebind_observations(previous, request, current):
    """Carry supplied premises only within the same declared reference context."""
    validate(previous)
    validate(current)
    validate_request(previous, request)
    require(previous['reference_context_sha256'] == current['reference_context_sha256']
            and previous['cohort_id'] == current['cohort_id'],
            'AUDIT_REFERENCE_CONTEXT', 'Observations require a new applicability assessment')
    result = copy.deepcopy(request)
    result['comparison_id'] = current['comparison_id']
    return validate_request(current, result)
