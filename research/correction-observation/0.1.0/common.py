"""Offline development arithmetic. No oracle files, network, or product behavior."""
from collections import deque
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tools.perception_revision import boxes, checker, contract, kernel

VERSION = '0.1.0'
FAMILIES = ('exact_publisher', 'one_edit_per_image', 'one_edit_global')
ARMS = {'A': ('width', 'conventional'), 'B': ('width', 'native'),
        'C': ('prior_margin', 'native'), 'D': ('prior_margin', 'conventional')}
ROLES = ('output_a', 'output_b')


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':')) + '\n').encode()


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def file_digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def put(path, value):
    with Path(path).open('xb') as output:
        output.write(encoded(value))


def utc():
    return datetime.now(timezone.utc).isoformat()


def q(value):
    return contract.rational(value)


def w(value):
    return contract.wire(Fraction(value))


def need(condition, message):
    if not condition:
        raise ValueError(message)


def subject(image):
    # Only visible operands enter this digest; no corrected count/hash/alternative.
    return digest(image)


def linked(image):
    return all(image[role]['state'] == 'observed' for role in ROLES)


def validate_rows(rows):
    need(type(rows) is list and len(rows) <= 128, 'Reference/operand size limit')
    need(len({r['id'] for r in rows}) == len(rows), 'Repeated record')
    for row in rows:
        need(set(row) == {'id', 'record_sha256', 'xyxy'}, 'Unknown rectangle property')
        need(type(row['id']) is str and row['id'], 'Invalid record id')
        need(type(row['record_sha256']) is str and len(row['record_sha256']) == 64
             and all(c in '0123456789abcdef' for c in row['record_sha256']), 'Invalid record digest')
        need(len(row['xyxy']) == 4, 'Four coordinates required')
        geometry = boxes.rectangle(row)
        need(geometry[3] - geometry[1] >= 25, 'Rectangle outside fixed height policy')


def open_interval(image):
    need(linked(image), 'Unavailable output is not an empty output')
    shared = {}
    for role in ROLES:
        for row in image[role]['value']:
            need(row['id'] not in shared or shared[row['id']] == row, 'Inconsistent common output')
            shared[row['id']] = row
    aa, bb = ({r['id'] for r in image[role]['value']} for role in ROLES)
    size = len(aa - bb) + len(bb - aa)
    return Fraction(-size), Fraction(size)


def iou(a, b):
    """Separate rational implementation from the native rectangle compiler."""
    ax, ay, az, at = [q(x) for x in a['xyxy']]
    bx, by, bz, bt = [q(x) for x in b['xyxy']]
    width, height = min(az, bz) - max(ax, bx), min(at, bt) - max(ay, by)
    intersection = max(0, width) * max(0, height)
    return intersection / ((az - ax) * (at - ay) + (bz - bx) * (bt - by) - intersection)


def flow_rank(left, right, edges):
    """Conventional unit-capacity max flow, independent of Engine matcher."""
    source, sink = ('source',), ('sink',)
    residual = {}
    def add(a, b):
        residual.setdefault(a, {})[b] = 1
        residual.setdefault(b, {})[a] = 0
    for d in sorted(left):
        add(source, ('d', d))
    for o in sorted(right):
        add(('o', o), sink)
    for d, o in sorted(edges):
        add(('d', d), ('o', o))
    count = 0
    while True:
        previous = {source: None}
        queue = deque([source])
        while queue and sink not in previous:
            node = queue.popleft()
            for nxt, capacity in residual.get(node, {}).items():
                if capacity and nxt not in previous:
                    previous[nxt] = node
                    queue.append(nxt)
        if sink not in previous:
            return count
        node = sink
        while previous[node] is not None:
            parent = previous[node]
            residual[parent][node] = 0
            residual[node][parent] = 1
            node = parent
        count += 1


def conventional_measure(image, references):
    need(linked(image), 'Unavailable output')
    validate_rows(references)
    ranks = []
    for role in ROLES:
        rows = image[role]['value']
        edges = {(d['id'], r['id']) for d in rows for r in references if iou(d, r) >= Fraction(1, 2)}
        ranks.append(flow_rank({d['id'] for d in rows}, {r['id'] for r in references}, edges))
    delta = 2 * (ranks[1] - ranks[0]) - (len(image['output_b']['value']) - len(image['output_a']['value']))
    return {'ranks': ranks, 'delta': w(delta)}


def native_graph(image, references):
    need(linked(image), 'Unavailable output')
    open_interval(image)
    validate_rows(references)
    geometry = {d['id']: boxes.rectangle(d) for role in ROLES for d in image[role]['value']}
    need(len(geometry) * len(references) <= contract.MAX_WORK, 'Rectangle work limit')
    anchor = {'id': image['id'], 'weight': w(1)}
    for role in ROLES:
        anchor[role] = {'state': 'observed', 'value': [
            {k: d[k] for k in ('id', 'record_sha256')} for d in image[role]['value']]}
    anchor['reference'] = {'state': 'finite',
        'objects': [{'id': r['id'], 'when': []} for r in references],
        'edges': [{'detection': did, 'object': r['id'], 'when': []}
                  for r in references for did, box in sorted(geometry.items())
                  if boxes.overlap(box, boxes.rectangle(r), Fraction(1, 2))]}
    case = {'artifact_id': 'reiyah.perception-revision.input', 'version': VERSION,
        'comparison_id': 'correction-observation:' + image['id'],
        'cohort_id': 'correction-observation:' + subject(image),
        'evidence_kind': 'conditional_reference_graph', 'input_scope': 'normalized_research_graphs',
        'reference_context_sha256': digest({'visible_subject': subject(image), 'references': references}),
        'assumptions': ['Fixed published development operands; observed reference is a supplied premise.',
                        'Exact nominal matching only; residual edits are bounded separately.'],
        'loss': {'false_negative': w(1), 'false_positive': w(1), 'tolerance': w(0)},
        'model': {'variables': [], 'clauses': []}, 'anchors': [anchor]}
    return contract.validate(case)


def native_measure(image, references):
    start = time.perf_counter()
    graph = native_graph(image, references)
    compiled = time.perf_counter()
    payload = kernel.produce(graph)
    proposed = time.perf_counter()
    checker.check(graph, payload)
    checked = time.perf_counter()
    need(payload['result']['enclosure_kind'] == 'exact_for_finite_model', 'Native work limit or unavailable result')
    row = payload['proof']['worlds'][0]['anchors'][0]
    return {'ranks': [len(row[role]['matching']) for role in ROLES],
            'delta': payload['result']['bounds']['lower'], 'graph_sha256': digest(graph), 'payload': payload,
            'timing': {'compile_seconds': compiled - start, 'proposal_seconds': proposed - compiled,
                       'check_seconds': checked - proposed}}


def edit_interval(image, measured):
    """One arbitrary insertion/deletion/replacement, exact rank clipping."""
    aa, bb = (len(image[role]['value']) for role in ROLES)
    ma, mb = measured['ranks']
    need(0 <= ma <= aa and 0 <= mb <= bb, 'Invalid matching ranks')
    need(q(measured['delta']) == 2 * (mb - ma) - (bb - aa), 'Rank/delta mismatch')
    lo = 2 * (max(0, mb - 1) - min(aa, ma + 1)) - (bb - aa)
    hi = 2 * (min(bb, mb + 1) - max(0, ma - 1)) - (bb - aa)
    low, high = open_interval(image)
    return max(low, lo), min(high, hi)


def interval(images, measurements, family):
    need(family in FAMILIES, 'Unknown uncertainty family')
    if not all(linked(image) for image in images):
        return None
    lower = upper = Fraction(0)
    downward, upward = [], []
    for image in images:
        if image['id'] not in measurements:
            lo, hi = open_interval(image)
        else:
            measured = measurements[image['id']]
            nominal = q(measured['delta'])
            lo = hi = nominal
            if family != 'exact_publisher':
                edit_lo, edit_hi = edit_interval(image, measured)
                if family == 'one_edit_per_image':
                    lo, hi = edit_lo, edit_hi
                else:
                    downward.append(nominal - edit_lo)
                    upward.append(edit_hi - nominal)
        lower += lo
        upper += hi
    if family == 'one_edit_global':
        lower -= max(downward, default=0)
        upper += max(upward, default=0)
    return lower / len(images), upper / len(images)


def decision(bounds):
    if bounds is None:
        return 'input_blocked'
    return 'supported' if bounds[0] > 0 else 'excluded' if bounds[1] <= 0 else 'unresolved'


def wire_interval(bounds):
    return None if bounds is None else [w(x) for x in bounds]


def ranking(images, policy):
    need(policy in ('width', 'prior_margin'), 'Unknown selector')
    if not all(linked(image) for image in images):
        return []
    # Hints are optional overhead; width does not compute unused old-reference matches.
    hints = ({im['id']: q(conventional_measure(im, im['original_reference'])['delta']) for im in images}
             if policy == 'prior_margin' else {im['id']: Fraction(0) for im in images})
    target = 1 if sum(hints.values()) > 0 else -1
    eligible = [im for im in images if open_interval(im)[0] != open_interval(im)[1]]
    def score(im):
        radius = open_interval(im)[1]
        return (-(radius + (target * hints[im['id']] if policy == 'prior_margin' else 0)),
                -radius, im['ordinal'])
    return [im['id'] for im in sorted(eligible, key=score)]


def validate_event(event, request):
    need(set(event) == {'request', 'answer', 'source_sha256', 'basis', 'residual',
                       'requested_utc', 'returned_utc', 'cost', 'evidence_sha256'}, 'Unknown event property')
    need(event['request'] == request, 'Observation subject, context, family or sequence mismatch')
    need(event['basis'] == 'published_correction_replay', 'Unknown observation basis')
    need(event['residual'] == request['family'], 'Residual error silently changed')
    need(event['evidence_sha256'] == digest({k: v for k, v in event.items() if k != 'evidence_sha256'}),
         'Observation bytes changed')
    need(event['cost']['observation_units'] == 1 and event['cost']['human_seconds'] is None,
         'Invalid or fabricated observation cost')
    validate_rows(event['answer'])
    return event['answer']
