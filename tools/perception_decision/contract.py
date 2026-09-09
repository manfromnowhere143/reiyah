"""Strict parsing and semantic checks for the normalized research contract."""
from fractions import Fraction
import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator

MAX_INPUT_BYTES = 4 * 1024 * 1024
MAX_PACKET_BYTES = 16 * 1024 * 1024
MAX_WORLDS = 4096
MAX_WORK = 2_000_000
SCHEMA = Path(__file__).resolve().parents[2] / 'research/perception-decision/0.1.0/input.schema.json'


class Invalid(ValueError):
    def __init__(self, code, detail):
        super().__init__(detail)
        self.code, self.detail = code, detail

    def diagnostic(self):
        return {'code': self.code, 'detail': self.detail}


def _pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise Invalid('DUPLICATE_KEY', key)
        result[key] = value
    return result


def parse(data):
    def bad_number(value):
        raise Invalid('INVALID_NUMBER', value[:160])
    def integer(value):
        if len(value) > 64:
            raise Invalid('INVALID_NUMBER', 'Integer token exceeds the parser limit')
        return int(value)
    try:
        return json.loads(data.decode('utf-8'), object_pairs_hook=_pairs,
                          parse_int=integer, parse_float=bad_number, parse_constant=bad_number)
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise Invalid('INVALID_JSON', str(exc)) from exc
    except ValueError as exc:
        if isinstance(exc, Invalid):
            raise
        raise Invalid('INVALID_NUMBER', str(exc)) from exc


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'),
                       ensure_ascii=True, allow_nan=False) + '\n').encode()


def rational(value):
    q = Fraction(int(value['numerator']), int(value['denominator']))
    if (str(q.numerator), str(q.denominator)) != (value['numerator'], value['denominator']):
        raise Invalid('INVALID_RATIONAL', 'Require reduced canonical rational strings')
    return q


def wire(q):
    return {'numerator': str(q.numerator), 'denominator': str(q.denominator)}


def _unique(values, detail):
    if len(values) != len(set(values)):
        raise Invalid('DUPLICATE_ID', detail)


def validate(value):
    schema = parse(SCHEMA.read_bytes())
    error = next(Draft202012Validator(schema).iter_errors(value), None)
    if error:
        location = '/'.join(map(str, error.absolute_path))
        raise Invalid('INPUT_SCHEMA', location + ': ' + error.message[:500])
    variables = value['model']['variables']
    _unique(variables, 'model variables')
    variable_set = set(variables)

    def literals(items):
        names = [item['variable'] for item in items]
        _unique(names, 'repeated variable in a condition or clause')
        if not set(names) <= variable_set:
            raise Invalid('UNKNOWN_VARIABLE', 'Condition references an undeclared variable')

    for clause in value['model']['clauses']:
        literals(clause)
    assignment = value['model'].get('feasible_assignment')
    if assignment is not None and len(assignment) != len(variables):
        raise Invalid('ASSIGNMENT_SIZE', 'One Boolean is required for every model variable')
    if assignment is not None:
        world = dict(zip(variables, assignment))
        if not all(any(world[l['variable']] == l['value'] for l in clause)
                   for clause in value['model']['clauses']):
            raise Invalid('INVALID_MODEL_WITNESS', 'The supplied assignment violates a model clause')
    for penalty in value['loss'].values():
        if rational(penalty) < 0:
            raise Invalid('NEGATIVE_LOSS', 'Penalties and tolerance must be nonnegative')
    _unique([a['id'] for a in value['anchors']], 'cohort anchor IDs')
    weights = [rational(a['weight']) for a in value['anchors']]
    if any(w < 0 for w in weights) or sum(weights) != 1:
        raise Invalid('POPULATION_WEIGHTS', 'Nonnegative common weights must sum exactly to one')
    for anchor in value['anchors']:
        detections = []
        complete = True
        for role in ('base', 'additions'):
            output = anchor[role]
            complete &= output['state'] == 'observed'
            if output['state'] == 'observed':
                detections.extend(d['id'] for d in output['value'])
        _unique(detections, anchor['id'] + ': base/addition IDs must be distinct')
        ref = anchor['reference']
        if ref['state'] == 'open':
            continue
        objects = [o['id'] for o in ref['objects']]
        _unique(objects, anchor['id'] + ': object IDs')
        _unique([(e['detection'], e['object']) for e in ref['edges']], anchor['id'] + ': edges')
        for obj in ref['objects']:
            literals(obj['when'])
        for edge in ref['edges']:
            literals(edge['when'])
            if edge['object'] not in objects or (complete and edge['detection'] not in detections):
                raise Invalid('UNKNOWN_ENDPOINT', anchor['id'] + ': unknown edge endpoint')
    return value


def load(path, expected_sha256, limit=MAX_INPUT_BYTES, validate_input=True):
    if (type(expected_sha256) is not str or len(expected_sha256) != 64
            or any(c not in '0123456789abcdef' for c in expected_sha256)):
        raise Invalid('EXPECTED_DIGEST', 'Expected SHA-256 must be 64 lowercase hex characters')
    with Path(path).open('rb') as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise Invalid('INPUT_SIZE', 'Input exceeds the declared byte limit')
    if hashlib.sha256(data).hexdigest() != expected_sha256:
        raise Invalid('INPUT_DIGEST_MISMATCH', 'Input bytes differ from the expected identity')
    result = parse(data)
    return validate(result) if validate_input else result
