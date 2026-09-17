"""Exact weak-duality bounds for a shared uncertain matching graph.

No optimizer is imported. Every admitted graph supplies a feasible matching/cover
assignment to the reconstructed relaxation; integer gain is at least ceil(bound).
Detection and reference identities occupy different variable namespaces.
"""
from fractions import Fraction
import hashlib

from tools.perception_decision.checker import _keys, _require
from .contract import DIRECTORY, MAX_INPUT_BYTES, MAX_WORK, encoded, rational

VERSION = '0.1.0'
PROGRAM = 'shared_matching_box_lp.0.1.0'
SCHEMA = DIRECTORY / 'linear-certificate.schema.json'
MAX_MULTIPLIER_BITS = 256
MAX_ACCUMULATOR_BITS = 4096


def program(row, direction):
    """Return sparse integer constraints Ax >= b with every variable in [0,1]."""
    _require(direction in ('b_minus_a', 'a_minus_b'), 'Unknown linear-bound direction')
    match, cover = (row['a'], row['b']) if direction == 'b_minus_a' else (row['b'], row['a'])
    possible, guaranteed = row['possible'], row['guaranteed']
    uncertain = sorted(possible - guaranteed)
    objects = sorted({o for _, o in possible})
    matched_edges = sorted((d, o) for d, o in possible if d in match)
    variables = ([['presence', d, o] for d, o in uncertain]
                 + [['cover_detection', d] for d in sorted(cover)]
                 + [['cover_reference', o] for o in objects]
                 + [['matching', d, o] for d, o in matched_edges])
    index = {tuple(v): i for i, v in enumerate(variables)}
    costs = [1 if v[0].startswith('cover_') else -1 if v[0] == 'matching' else 0 for v in variables]
    rows = []

    def add(key, terms, lower):
        rows.append({'id': key, 'terms': sorted([[index[tuple(v)], c] for v, c in terms]), 'lower': lower})

    for d, o in sorted(possible):
        if d in cover:
            terms = [(['cover_detection', d], 1), (['cover_reference', o], 1)]
            if (d, o) not in guaranteed:
                terms.append((['presence', d, o], -1))
            add(['cover', d, o], terms, int((d, o) in guaranteed))
    by_detection = {d: [] for d in match}
    by_object = {o: [] for o in objects}
    for d, o in matched_edges:
        terms = [(['matching', d, o], -1)]
        if (d, o) not in guaranteed:
            terms.append((['presence', d, o], 1))
        add(['available', d, o], terms, -int((d, o) in guaranteed))
        by_detection[d].append((['matching', d, o], -1))
        by_object[o].append((['matching', d, o], -1))
    for d in sorted(match):
        add(['detection_capacity', d], by_detection[d], -1)
    for o in objects:
        add(['reference_capacity', o], by_object[o], -1)
    return {'version': PROGRAM, 'direction': direction, 'variables': variables, 'costs': costs, 'rows': rows}


def digest(prog):
    return hashlib.sha256(encoded(prog)).hexdigest()


def bounded(value):
    _require(max(abs(value.numerator).bit_length(), value.denominator.bit_length()) <= MAX_ACCUMULATOR_BITS,
             'Linear arithmetic exceeds the accumulator limit')
    return value


def multiplier(value):
    _keys(value, ('numerator', 'denominator'))
    _require(all(type(value[k]) is str and 1 <= len(value[k]) <= 79 for k in value),
             'Malformed or oversized linear multiplier')
    try:
        result = rational(value)
    except (ValueError, ZeroDivisionError):
        _require(False, 'Malformed linear multiplier')
    _require(result >= 0 and max(result.numerator.bit_length(), result.denominator.bit_length()) <= MAX_MULTIPLIER_BITS,
             'Linear multipliers must be nonnegative and bounded')
    return result


def lower_bound(prog, supplied):
    """b.y + sum min(0, c-A^T.y); all arithmetic is exact."""
    _require(type(supplied) is list and len(supplied) == len(prog['rows']), 'Wrong linear multiplier count')
    residual = [Fraction(c) for c in prog['costs']]
    bound = Fraction(0)
    for row, value in zip(prog['rows'], supplied):
        y = multiplier(value)
        bound = bounded(bound + row['lower'] * y)
        for j, coefficient in row['terms']:
            residual[j] = bounded(residual[j] - coefficient * y)
    for value in residual:
        bound = bounded(bound + min(0, value))
    return bound


def check(prepared, certificate):
    """Validate partial proposals; missing directions retain output-count bounds."""
    _require(type(certificate) is dict and len(encoded(certificate)) <= MAX_INPUT_BYTES,
             'Linear certificate exceeds its input limit')
    _keys(certificate, ('artifact_id', 'version', 'entries'))
    _require(certificate['artifact_id'] == 'reiyah.perception-revision.linear-certificate'
             and certificate['version'] == VERSION, 'Unknown linear certificate version')
    known = {r['anchor']['id']: r for r in prepared['rows']}
    entries = certificate['entries']
    _require(type(entries) is list and len(entries) <= 2 * len(known), 'Invalid linear entries')
    result = {}
    work = prepared['geometry_work']
    for entry in entries:
        _keys(entry, ('anchor', 'direction', 'program_sha256', 'multipliers'))
        aid, direction = entry['anchor'], entry['direction']
        _require(type(aid) is str and aid in known and type(direction) is str
                 and direction in ('b_minus_a', 'a_minus_b'), 'Unknown linear-bound subject')
        key = aid, direction
        _require(key not in result, 'Repeated linear-bound subject')
        row = known[aid]
        # Charge before constructing the program, including every sparse term.
        estimate = 40 * (len(row['possible']) + len(row['a']) + len(row['b']) + len(row['references']) + 1)
        work += estimate
        _require(work <= MAX_WORK, 'Linear certificate exceeds the work limit')
        prog = program(row, direction)
        _require(sum(len(r['terms']) for r in prog['rows']) + len(prog['rows']) + len(prog['variables']) <= estimate,
                 'Linear program exceeded its charged estimate')
        _require(entry['program_sha256'] == digest(prog), 'Linear program binding differs')
        bound = lower_bound(prog, entry['multipliers'])
        result[key] = -(-bound.numerator // bound.denominator)
    return result
