"""Typed observation proposals and complete, explicit inspection accounting."""
from collections import Counter
from datetime import datetime
import re

from tools.perception_decision.contract import Invalid
from tools.perception_inputs.sensors import CHANNELS
from tools.perception_inputs.source_io import digest_value, require
from tools.perception_observation.contract import closed, integer

MAX_RECORD = 16 << 20
MAX_PROPOSALS = 5_000
REVIEW_STATES = ('inspected', 'partly_inspected', 'unviewable', 'not_inspected')
EXPOSURES = ('annotations', 'predictions', 'configuration_identities', 'other_reviewer_records', 'prior_candidate_rankings')
CLASSES = ('car', 'truck', 'bus', 'trailer', 'construction_vehicle', 'pedestrian',
           'motorcycle', 'bicycle', 'traffic_cone', 'barrier', 'outside_target')


def text(value, minimum=1, maximum=4096):
    require(type(value) is str and minimum <= len(value) <= maximum and '\0' not in value,
            'DISCOVERY_TEXT', 'Invalid bounded text')
    return value


def neutral(value):
    require(type(value) is str and re.fullmatch('[0-9a-f]{32}', value) is not None,
            'DISCOVERY_ID', 'Require a neutral 32-hex identity')
    return value


def reported_time(value):
    require(type(value) is dict and value.get('state') in ('reported', 'unrecorded'),
            'DISCOVERY_TIME', 'Missing explicit completion-time state')
    if value['state'] == 'unrecorded':
        closed(value, ('state',), 'DISCOVERY_TIME')
        return
    closed(value, ('state', 'utc'), 'DISCOVERY_TIME')
    require(type(value['utc']) is str and re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z', value['utc']) is not None,
            'DISCOVERY_TIME', 'Require a whole-second reported UTC timestamp')
    try:
        datetime.strptime(value['utc'], '%Y-%m-%dT%H:%M:%SZ')
    except ValueError as exc:
        raise Invalid('DISCOVERY_TIME', 'Invalid calendar timestamp') from exc


def population(manifest):
    return [(w['id'], r['capture_id']) for w in manifest['windows'] for channel in CHANNELS
            for r in w['channels'][channel]['captures']]


def draft(manifest, seal_sha256, record_id):
    neutral(record_id)
    require(digest_value(seal_sha256), 'DISCOVERY_BINDING', 'Expected package seal is required')
    return {'artifact_id': 'reiyah.perception-discovery.record', 'version': '0.1.0',
            'record_id': record_id, 'package_id': manifest['package_id'], 'package_seal_sha256': seal_sha256,
            'phase': 'unassisted_discovery', 'reviewer_id': None, 'completed_at': {'state': 'unrecorded'},
            'reported_exposure': {name:'unknown' for name in EXPOSURES},
            'capture_reviews': [{'window_id':w, 'capture_id':c, 'state':'not_inspected', 'limitations':'Not yet reviewed'}
                                for w,c in population(manifest)], 'proposals': []}


def locator(value, capture):
    require(type(value) is dict and type(value.get('kind')) is str,
            'DISCOVERY_LOCATOR', 'Missing evidence locator')
    kind = value['kind']
    if kind == 'capture':
        closed(value, ('kind',), 'DISCOVERY_LOCATOR')
    elif kind == 'image_region':
        closed(value, ('kind', 'xyxy'), 'DISCOVERY_LOCATOR')
        require(capture['channel'] != 'LIDAR_TOP', 'DISCOVERY_LOCATOR', 'Image region cannot refer to lidar')
        xy = value['xyxy']; width, height = capture['image_shape']
        require(type(xy) is list and len(xy) == 4 and all(type(v) is int for v in xy)
                and 0 <= xy[0] < xy[2] <= width and 0 <= xy[1] < xy[3] <= height,
                'DISCOVERY_LOCATOR', 'Require a nonempty half-open pixel rectangle inside the image')
    elif kind == 'point_indices':
        closed(value, ('kind', 'indices'), 'DISCOVERY_LOCATOR')
        require(capture['channel'] == 'LIDAR_TOP' and capture['evidence']['state'] == 'delivered',
                'DISCOVERY_LOCATOR', 'Point indices require delivered lidar evidence')
        indices = value['indices']; n = capture['evidence']['point_count']
        require(type(indices) is list and 0 < len(indices) <= 4096
                and all(type(i) is int and 0 <= i < n for i in indices)
                and indices == sorted(set(indices)), 'DISCOVERY_LOCATOR', 'Invalid, duplicate or unordered raw point index')
    else:
        raise Invalid('DISCOVERY_LOCATOR', 'Unsupported evidence locator')


def validate(record, manifest, expected_seal, submission=False):
    closed(record, ('artifact_id', 'version', 'record_id', 'package_id', 'package_seal_sha256', 'phase',
                   'reviewer_id', 'completed_at', 'reported_exposure', 'capture_reviews', 'proposals'), 'DISCOVERY_SCHEMA')
    require(record['artifact_id'] == 'reiyah.perception-discovery.record' and record['version'] == '0.1.0'
            and record['phase'] == 'unassisted_discovery', 'DISCOVERY_SCHEMA', 'Unsupported record identity or phase')
    neutral(record['record_id'])
    require(digest_value(expected_seal) and record['package_id'] == manifest['package_id']
            and record['package_seal_sha256'] == expected_seal, 'DISCOVERY_BINDING', 'Record refers to different evidence')
    reviewer = record['reviewer_id']
    if reviewer is not None:
        text(reviewer, maximum=128)
        require(reviewer == reviewer.strip(), 'DISCOVERY_ID', 'Reviewer handle must not hide surrounding whitespace')
    require(not submission or reviewer is not None, 'DISCOVERY_REVIEWER', 'An unassigned draft cannot be sealed as a submitted record')
    reported_time(record['completed_at'])
    closed(record['reported_exposure'], EXPOSURES, 'DISCOVERY_EXPOSURE')
    require(all(type(v) is str and v in ('reported_not_exposed', 'reported_exposed', 'unknown')
                for v in record['reported_exposure'].values()), 'DISCOVERY_EXPOSURE', 'Exposure must remain an explicit reported state')
    expected = population(manifest); rows = record['capture_reviews']; captures = {c['id']:c for c in manifest['captures']}
    require(type(rows) is list and len(rows) == len(expected), 'DISCOVERY_POPULATION', 'Every window/capture occurrence needs a review state')
    reviewed = {}
    for row, (w,c) in zip(rows, expected):
        closed(row, ('window_id', 'capture_id', 'state', 'limitations'), 'DISCOVERY_SCHEMA')
        require(row['window_id'] == w and row['capture_id'] == c, 'DISCOVERY_POPULATION', 'Missing, reordered or substituted review occurrence')
        state = row['state']
        require(type(state) is str and state in REVIEW_STATES, 'DISCOVERY_STATE', 'Unknown inspection state')
        text(row['limitations'], minimum=0 if state == 'inspected' else 1)
        require(state not in ('inspected', 'partly_inspected') or captures[c]['evidence']['state'] == 'delivered',
                'DISCOVERY_UNAVAILABLE', 'Undelivered evidence cannot be reported as inspected within this package')
        reviewed[w,c] = state
    proposals = record['proposals']
    require(type(proposals) is list and len(proposals) <= MAX_PROPOSALS, 'DISCOVERY_LIMIT', 'Too many observation proposals')
    for i, proposal in enumerate(proposals, 1):
        closed(proposal, ('id', 'window_id', 'description', 'class_hypotheses', 'evidence'), 'DISCOVERY_SCHEMA')
        require(proposal['id'] == f'proposal-{i:05d}' and type(proposal['window_id']) is str,
                'DISCOVERY_ID', 'Noncanonical proposal or invalid window identifier')
        text(proposal['description'])
        classes = proposal['class_hypotheses']
        require(type(classes) is dict and classes.get('state') in ('proposed', 'unresolved'),
                'DISCOVERY_CLASS', 'Unknown class is an explicit unresolved proposal')
        if classes['state'] == 'unresolved':
            closed(classes, ('state',), 'DISCOVERY_CLASS')
        else:
            closed(classes, ('state', 'values'), 'DISCOVERY_CLASS')
            vs = classes['values']
            require(type(vs) is list and 0 < len(vs) <= len(CLASSES) and
                    all(type(v) is str and v in CLASSES for v in vs) and len(vs) == len(set(vs)),
                    'DISCOVERY_CLASS', 'Invalid or duplicated proposed class alternative')
        basis = proposal['evidence']
        require(type(basis) is list and 0 < len(basis) <= 128, 'DISCOVERY_EVIDENCE', 'Proposal needs bounded observable support')
        seen = set()
        for evidence in basis:
            closed(evidence, ('capture_id', 'locator'), 'DISCOVERY_SCHEMA')
            cid = evidence['capture_id']; window = proposal['window_id']
            require(type(cid) is str and (window,cid) in reviewed and cid not in seen,
                    'DISCOVERY_EVIDENCE', 'Unknown, repeated or out-of-window evidence')
            require(reviewed[window,cid] in ('inspected', 'partly_inspected'),
                    'DISCOVERY_EVIDENCE', 'Uninspected evidence cannot support a discovery proposal')
            locator(evidence['locator'], captures[cid]); seen.add(cid)
    counts = dict(sorted(Counter(r['state'] for r in rows).items()))
    exposure = record['reported_exposure'].values()
    blinding = ('contested' if 'reported_exposed' in exposure else 'unknown' if 'unknown' in exposure else 'reported_clear')
    return {'capture_occurrences': len(rows), 'inspection_states': counts, 'proposals': len(proposals),
            'recorded_capture_inspection': 'reported_complete' if counts == {'inspected':len(rows)} else 'incomplete',
            'blinding': blinding, 'reviewer_identity': 'unassigned' if reviewer is None else 'unverified_handle',
            'human_independence': 'not_established', 'physical_reference_coverage': 'not_established',
            'physical_absence_from_zero_proposals': 'not_established', 'completion_clock_accuracy': 'not_established'}


def pair_report(first, second):
    """Report structural prerequisites only; no assisted-data release or authority."""
    a,b = first['record'], second['record']
    require(a['record_id'] != b['record_id'], 'DISCOVERY_PAIR', 'Two copies of one record are not two submissions')
    require(a['package_id'] == b['package_id'] and a['package_seal_sha256'] == b['package_seal_sha256'],
            'DISCOVERY_PAIR', 'Reviewer records cover different evidence packages')
    handles = 'distinct_handles' if a['reviewer_id'] != b['reviewer_id'] else 'same_handle'
    reasons = []
    if handles != 'distinct_handles':
        reasons.append('reviewer_handles_not_distinct')
    for i,item in enumerate((first,second),1):
        if item['summary']['recorded_capture_inspection'] != 'reported_complete':
            reasons.append(f'record_{i}_inspection_incomplete')
        if item['summary']['blinding'] != 'reported_clear':
            reasons.append(f'record_{i}_blinding_'+item['summary']['blinding'])
        if item['record']['completed_at']['state'] != 'reported':
            reasons.append(f'record_{i}_completion_time_unrecorded')
    return {'package_id': a['package_id'], 'package_seal_sha256': a['package_seal_sha256'],
            'structural_review': 'eligible_for_external_review' if not reasons else 'needs_resolution',
            'reasons': reasons, 'reviewer_handles': handles, 'human_independence': 'not_established',
            'reported_blinding_independently_verified': 'not_established',
            'sealing_before_assisted_exposure': 'not_established',
            'phase_2_release': 'not_authorized_by_this_tool', 'physical_reference_coverage': 'not_established'}
