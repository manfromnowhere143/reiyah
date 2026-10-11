"""Separate enumeration of recorded vote worlds and paired outcomes."""
import argparse
from collections import Counter, defaultdict
import hashlib
import itertools
import json
import math
from pathlib import Path

SOURCE = '1eb5506f328316f46fa5a036486b05689f4d504602895b80c87ee8bda0e0dd1d'
PROTOCOL = '2b084dcf491bedafd79ee9133b27823b3cd0839d31416a4333c9ecd3c62dd895'
ENGINE = '720c0285e9789fa27374108378eaf8a77d02f5925846fc52491ae63f9731a503'
ORDINARY = ('person', 'rider', 'car', 'truck', 'bus', 'train', 'motorcycle', 'bicycle')
LABELS = ORDINARY + ('cantsolve',)


def demand(ok, message):
    if not ok:
        raise ValueError(message)


def unique(pairs):
    out = {}
    for k, v in pairs:
        demand(k not in out, 'duplicate JSON key')
        out[k] = v
    return out


def invalid_constant(value):
    raise ValueError('nonfinite JSON constant: ' + value)


def parse(raw):
    return json.loads(raw, object_pairs_hook=unique, parse_constant=invalid_constant)


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def vote_result(votes):
    demand(bool(votes), 'empty vote population')
    for label in LABELS:
        if sum(x == label for x in votes) > len(votes) // 2:
            return label
    return 'no_strict_majority'


def enumerate_procedure(obj, proposed):
    if proposed:
        records = [(key, record) for key, records in obj['annotation_info'].items() for record in records]
        frequency = obj['frequencies']
    else:
        records = [(key, record) for task in obj['unbiased_annotation_info'] for key, record in task.items()]
        frequency = obj['unbiased_frequencies']
    demand(bool(records), 'empty source responses')
    ids = defaultdict(set)
    votes = []
    for reviewer, record in records:
        demand(isinstance(reviewer, str) and reviewer, 'invalid identifier')
        demand(type(record) is dict and set(record) == {'vote', 'time'}, 'invalid response shape')
        demand(record['vote'] in LABELS, 'invalid response class')
        duration = record['time']
        demand(type(duration) in (int, float) and math.isfinite(duration) and duration >= 0, 'invalid duration')
        ids[reviewer].add(record['vote'])
        votes.append(record['vote'])
    demand(all(type(v) is int and v >= 0 for v in frequency.values()), 'invalid frequencies')
    demand(set(frequency) <= set(LABELS) and Counter(votes) == Counter(frequency), 'frequency mismatch')
    nworlds = math.prod(len(v) for v in ids.values())
    demand(nworlds <= 4096, 'enumeration resource limit; result unknown')
    outcomes = set()
    for world in itertools.product(*(sorted(ids[k]) for k in sorted(ids))):
        outcomes.add(vote_result(world))
    raw = vote_result(votes)
    return {
        'entries': len(votes), 'groups': len(ids), 'raw_outcome': raw,
        'raw_winning_votes': votes.count(raw) if raw in LABELS else None,
        'attainable': sorted(outcomes),
    }, set(ids), nworlds


def reconstruct(raw):
    demand(len(raw) == 8568020 and hashlib.sha256(raw).hexdigest() == SOURCE, 'source identity mismatch')
    data = parse(raw)
    demand(data['classes'] == list(LABELS), 'class roster mismatch')
    demand(len(data['objects']) == 388, 'image roster mismatch')
    rows = []
    seen = set()
    worlds = 0
    for image in sorted(data['objects']):
        for index, obj in enumerate(data['objects'][image]):
            demand(obj['mo_id'] not in seen, 'duplicate object')
            seen.add(obj['mo_id'])
            demand(obj['proposed_class'] in ORDINARY, 'invalid proposed class')
            left, left_ids, nleft = enumerate_procedure(obj, True)
            right, right_ids, nright = enumerate_procedure(obj, False)
            worlds += nleft + nright
            pairs = list(itertools.product(left['attainable'], right['attainable']))
            equal = [a == b for a, b in pairs]
            all_normal_different = all(a in ORDINARY and b in ORDINARY and a != b for a, b in pairs)
            any_normal_different = any(a in ORDINARY and b in ORDINARY and a != b for a, b in pairs)
            raw_switch = left['raw_outcome'] != right['raw_outcome'] and left['raw_outcome'] in ORDINARY and right['raw_outcome'] in ORDINARY
            rows.append({
                'image': image, 'object_index': index, 'object_id': obj['mo_id'],
                'proposed_class': obj['proposed_class'], 'proposed': left, 'no_proposal': right,
                'shared_ID_count': len(left_ids.intersection(right_ids)),
                'raw_ordinary_switch': raw_switch,
                'raw_both_four_fifths_ordinary_switch': raw_switch and 5 * left['raw_winning_votes'] >= 4 * left['entries'] and 5 * right['raw_winning_votes'] >= 4 * right['entries'],
                'agreement': 'guaranteed_same' if all(equal) else 'ambiguous' if any(equal) else 'forced_difference',
                'forced_ordinary_switch': all_normal_different,
                'possible_ordinary_switch': any_normal_different,
                'forced_ordinary_to_unresolved': all(a in ORDINARY and b not in ORDINARY for a, b in pairs),
                'forced_unresolved_to_ordinary': all(a not in ORDINARY and b in ORDINARY for a, b in pairs),
                'forced_distinct_unresolved': all(a not in ORDINARY and b not in ORDINARY and a != b for a, b in pairs),
            })
    demand(len(rows) == 1000, 'object roster mismatch')
    return rows, worlds


def summarize_separately(rows):
    totals = {'objects': 0, 'image_groups': 0,
              'agreement': {'guaranteed_same': 0, 'forced_difference': 0, 'ambiguous': 0},
              'comparisons': {key: 0 for key in ('forced_ordinary_switch', 'possible_ordinary_switch', 'forced_ordinary_to_unresolved', 'forced_unresolved_to_ordinary', 'forced_distinct_unresolved', 'raw_ordinary_switch', 'raw_both_four_fifths_ordinary_switch')},
              'raw_equal': 0,
              'procedures': {p: {'entries': 0, 'ID_object_pairs': 0, 'raw_outcomes': {}} for p in ('proposed', 'no_proposal')},
              'forced_difference_image_groups': 0,
              'objects_with_cross_procedure_ID_overlap': 0,
              'forced_difference_with_ID_overlap': 0,
              'by_proposed_class': {label: {'objects': 0, 'forced_difference': 0, 'forced_ordinary_switch': 0} for label in ORDINARY}}
    images, different_images = set(), set()
    transitions = {}
    for row in rows:
        totals['objects'] += 1
        images.add(row['image'])
        state = row['agreement']
        totals['agreement'][state] += 1
        for key in totals['comparisons']:
            if row[key]:
                totals['comparisons'][key] += 1
        a, b = row['proposed']['raw_outcome'], row['no_proposal']['raw_outcome']
        transitions[a, b] = transitions.get((a, b), 0) + 1
        if a == b:
            totals['raw_equal'] += 1
        for p in totals['procedures']:
            agg, entry = totals['procedures'][p], row[p]
            agg['entries'] += entry['entries']
            agg['ID_object_pairs'] += entry['groups']
            c = entry['raw_outcome']
            agg['raw_outcomes'][c] = agg['raw_outcomes'].get(c, 0) + 1
        if row['shared_ID_count']:
            totals['objects_with_cross_procedure_ID_overlap'] += 1
            if state == 'forced_difference':
                totals['forced_difference_with_ID_overlap'] += 1
        group = totals['by_proposed_class'][row['proposed_class']]
        group['objects'] += 1
        if state == 'forced_difference':
            group['forced_difference'] += 1
            different_images.add(row['image'])
        if row['forced_ordinary_switch']:
            group['forced_ordinary_switch'] += 1
    totals['image_groups'] = len(images)
    totals['forced_difference_image_groups'] = len(different_images)
    totals['raw_transitions'] = [{'proposed': a, 'no_proposal': b, 'objects': transitions[a, b]} for a, b in sorted(transitions)]
    return totals


def verify(raw, supplied_rows, supplied_result):
    rows, worlds = reconstruct(raw)
    demand(encoded(supplied_rows) == encoded(rows), 'paired rows mismatch')
    proto = Path(__file__).with_name('protocol.json').read_bytes()
    demand(hashlib.sha256(proto).hexdigest() == PROTOCOL, 'protocol changed')
    expected = {
        'artifact_id': 'reiyah.review-procedure-sensitivity.result',
        'version': '0.1.0', 'lifecycle_status': 'exploratory',
        'source_sha256': SOURCE, 'protocol_sha256': PROTOCOL,
        'identity_engine_sha256': ENGINE,
        'summary': summarize_separately(rows),
        'scope': 'Finite recorded-object decision sensitivity; not physical truth, causality, future-review reliability, detector performance or work saving.',
    }
    demand(encoded(supplied_result) == encoded(expected), 'aggregate result mismatch')
    return {'paired_objects_verified': len(rows), 'procedure_object_worlds_enumerated': worlds,
            'source_sha256': SOURCE, 'result': 'pass',
            'scope': 'Separate implementation, same investigator; not independent scientific review.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, required=True)
    parser.add_argument('--rows', type=Path, required=True)
    parser.add_argument('--result', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.data.read_bytes(), parse(args.rows.read_bytes()), parse(args.result.read_bytes())), indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
