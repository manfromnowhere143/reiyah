"""Bounded position observations, applicability and conservative conditioning."""
import copy
import hashlib

from . import localization_contract as geometry
from .contract import (DIRECTORY, MAX_INPUT_BYTES, MAX_WORK, ROLES, encoded,
                       rational, require, schema_check, unique, validate)

SCHEMA = DIRECTORY / 'position-observations.schema.json'
VERSION = '0.1.0'
FAMILY = 'independent_intersections_of_prior_and_observed_closed_balls'


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def subject_digest(case, request, anchor_id, reference):
    """Declared source/coordinate identity, independent of detectors and radii.

    The reference context must bind frame, time and interpretation upstream.
    This fingerprint checks agreement of premises, not their physical validity.
    """
    return digest({'cohort_id': case['cohort_id'],
                   'reference_context_sha256': case['reference_context_sha256'],
                   'coordinate_system': request['coordinate_system'], 'anchor': anchor_id,
                   'reference': {k: reference[k] for k in ('id', 'record_sha256', 'class', 'xy')}})


def validate_observations(case, request, observations):
    require(len(encoded(observations)) <= MAX_INPUT_BYTES,
            'INPUT_SIZE', 'Position observations exceed byte limit')
    schema_check(observations, SCHEMA)
    require(observations['cohort_id'] == case['cohort_id']
            and observations['reference_context_sha256'] == case['reference_context_sha256'],
            'POSITION_CONTEXT', 'Position observations require a new applicability assessment')
    unique([(o['anchor'], o['object']) for o in observations['observations']],
           'Only one position answer per reference is admitted; repeated measurements need a new contract')
    known = {(a['id'], o['id']): o for a in request['anchors'] for o in a['references']}
    for answer in observations['observations']:
        key = answer['anchor'], answer['object']
        require(key in known, 'POSITION_SUBJECT', 'Unknown position-observation subject')
        require(answer['subject_sha256'] == subject_digest(case, request, key[0], known[key]),
                'POSITION_SUBJECT', 'Reference record, class, nominal center or coordinate context changed')
        geometry.point(answer['xy'])
        require(0 <= rational(answer['radius']) <= geometry.MAX_COORDINATE,
                'POSITION_RADIUS', 'Observation residual radius must be nonnegative and bounded')
    return observations


def ball_relation(prior, answer):
    """Exact nonemptiness and containment; a partial intersection stays outer-bounded."""
    r, s = rational(prior['radius']), rational(answer['radius'])
    distance = geometry.squared_distance(geometry.point(prior['xy']), geometry.point(answer['xy']))
    if distance > (r + s) ** 2:
        return 'disjoint', None
    if r == s and distance == 0:
        return 'equal', 'prior'
    if s <= r and distance <= (r - s) ** 2:
        return 'observation_contained', 'observation'
    if r <= s and distance <= (s - r) ** 2:
        return 'prior_contained', 'prior'
    # Includes external tangency. The intersection is nonempty but neither
    # entire ball need be contained in the other. No exact lens claim is made.
    return 'partial_overlap', 'observation' if s < r else 'prior'


def condition(case, request, observations):
    """Return checked conditioning metadata and, when available, derived operands.

    For each reference the feasible set is P intersect M. Its smaller containing
    ball is an outer enclosure, not a replacement assertion about measured truth.
    Detector outputs, classes, weights and loss are kept. A fresh nominal graph is
    computed at the enclosure center. No old matching or decision is reused here.
    """
    require(len(encoded(case)) <= MAX_INPUT_BYTES, 'INPUT_SIZE', 'Comparison exceeds byte limit')
    validate(case)
    geometry.validate_request(case, request)
    validate_observations(case, request, observations)
    report = {'status': 'available', 'reason': None, 'records': [],
              'derived_input_sha256': None, 'derived_request_sha256': None}

    def unavailable(reason):
        report.update(status='unavailable', reason=reason)
        return report, None

    if any(a[r]['state'] != 'observed' for a in case['anchors'] for r in ROLES):
        return unavailable('unavailable_outputs')
    if any(a['reference']['state'] != 'finite' for a in case['anchors']):
        return unavailable('open_references')
    if case['model']['variables'] or case['model']['clauses']:
        return unavailable('conditional_reference_model')
    pairs = sum(len(a['detections']) * len(a['references']) for a in request['anchors'])
    derived_case, derived_request = copy.deepcopy(case), copy.deepcopy(request)
    observed = {(o['anchor'], o['object']): o for o in observations['observations']}
    original = {a['id']: a for a in request['anchors']}
    derived = {a['id']: a for a in derived_request['anchors']}
    changed = set()
    for anchor in derived_case['anchors']:
        for ref in derived[anchor['id']]['references']:
            answer = observed.get((anchor['id'], ref['id']))
            if answer is not None:
                relation, selected = ball_relation(ref, answer)
                report['records'].append({'anchor': anchor['id'], 'object': ref['id'],
                                          'relation': relation, 'enclosure': selected})
                if selected == 'observation':
                    if geometry.point(ref['xy']) != geometry.point(answer['xy']):
                        changed.add(anchor['id'])
                    ref['xy'], ref['radius'] = copy.deepcopy(answer['xy']), copy.deepcopy(answer['radius'])
    if any(r['relation'] == 'disjoint' for r in report['records']):
        report.update(status='inconsistent_premises', reason='disjoint_position_balls')
        return report, None
    changed_pairs = sum(len(a['detections']) * len(a['references']) for a in request['anchors'] if a['id'] in changed)
    # With unchanged centers the existing geometry route also checks the original
    # nominal graph. Changed anchors need two additional full nominal passes.
    overhead = 2 * changed_pairs + len(observations['observations'])
    if 3 * pairs + overhead > MAX_WORK:
        return unavailable('conditioning_work_limit')
    for anchor in derived_case['anchors']:
        if anchor['id'] not in changed:
            continue
        old, new = original[anchor['id']], derived[anchor['id']]
        threshold = rational(request['threshold'])
        graphs = []
        for row in (old, new):
            detections = [(d['id'], d['class'], geometry.point(d['xy'])) for d in row['detections']]
            references = [(o['id'], o['class'], geometry.point(o['xy'])) for o in row['references']]
            graphs.append({(did, oid) for did, dc, xy in detections for oid, oc, uv in references
                           if dc == oc and geometry.squared_distance(xy, uv) < threshold ** 2})
        require(graphs[0] == {(e['detection'], e['object']) for e in anchor['reference']['edges']},
                'LOCALIZATION_NOMINAL_GRAPH', 'Original geometry differs from the bound comparison graph')
        anchor['reference']['edges'] = [{'detection': d, 'object': o, 'when': []} for d, o in sorted(graphs[1])]
    if len(encoded(derived_case)) > MAX_INPUT_BYTES or len(encoded(derived_request)) > MAX_INPUT_BYTES:
        return unavailable('conditioned_input_limit')
    # The strict input graph bound still applies to the new center.
    if any(len(a['reference']['edges']) > geometry.MAX_EDGES for a in derived_case['anchors']):
        return unavailable('possible_edge_limit')
    validate(derived_case)
    reason, prepared = geometry.prepare(derived_case, derived_request)
    if reason is not None:
        return unavailable(reason)
    if overhead + geometry.matching_work(prepared) > MAX_WORK:
        return unavailable('conditioning_work_limit')
    report['derived_input_sha256'], report['derived_request_sha256'] = digest(derived_case), digest(derived_request)
    return report, (derived_case, derived_request)
