"""Paired recorded-procedure sensitivity; no causal or physical-truth inference."""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import time

SOURCE = '1eb5506f328316f46fa5a036486b05689f4d504602895b80c87ee8bda0e0dd1d'
ENGINE_SHA = '720c0285e9789fa27374108378eaf8a77d02f5925846fc52491ae63f9731a503'
CLASSES = ('person', 'rider', 'car', 'truck', 'bus', 'train', 'motorcycle', 'bicycle')
UNRESOLVED = {'cantsolve', 'no_strict_majority'}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n'


def load_engine():
    path = Path(__file__).resolve().parents[2] / 'reviewer-identity-sensitivity/0.1.0/reproduce.py'
    require(hashlib.sha256(path.read_bytes()).hexdigest() == ENGINE_SHA, 'changed identity engine')
    spec = importlib.util.spec_from_file_location('identity_engine', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def classify(left, right):
    ordinary = set(CLASSES)
    require(bool(left) and bool(right), 'empty outcome support')
    require(left <= ordinary | UNRESOLVED and right <= ordinary | UNRESOLVED,
            'undeclared outcome')
    same = len(left) == len(right) == 1 and left == right
    different = left.isdisjoint(right)
    return {
        'agreement': 'guaranteed_same' if same else 'forced_difference' if different else 'ambiguous',
        'forced_ordinary_switch': different and left <= ordinary and right <= ordinary,
        'possible_ordinary_switch': any(a != b for a in left & ordinary for b in right & ordinary),
        'forced_ordinary_to_unresolved': left <= ordinary and right <= UNRESOLVED,
        'forced_unresolved_to_ordinary': left <= UNRESOLVED and right <= ordinary,
        'forced_distinct_unresolved': different and left <= UNRESOLVED and right <= UNRESOLVED,
    }


def paired_rows(data, engine):
    characterized = engine.analyze_source(data)
    indexed = {(r['image_name'], r['object_index'], r['procedure']): r for r in characterized}
    require(len(indexed) == 2000, 'identity row membership mismatch')
    rows = []
    for image, objects in sorted(data['objects'].items()):
        for index, obj in enumerate(objects):
            require(obj['proposed_class'] in CLASSES, 'invalid proposed class')
            summaries = {}
            id_sets = {}
            for procedure in ('proposed', 'no_proposal'):
                row = indexed[image, index, procedure]
                require(row['object_id'] == obj['mo_id'], 'object join mismatch')
                entries = engine.procedure_entries(obj, procedure)
                counts = Counter(response['vote'] for _, response in entries)
                raw = row['raw_outcome']
                summaries[procedure] = {
                    'entries': len(entries), 'groups': row['group_count'],
                    'raw_outcome': raw,
                    'raw_winning_votes': counts[raw] if raw != 'no_strict_majority' else None,
                    'attainable': row['possible_outcomes'],
                }
                id_sets[procedure] = set(row['reviewer_ids'])
            a, b = summaries['proposed'], summaries['no_proposal']
            raw_switch = a['raw_outcome'] in CLASSES and b['raw_outcome'] in CLASSES and a['raw_outcome'] != b['raw_outcome']
            rows.append({
                'image': image, 'object_index': index, 'object_id': obj['mo_id'],
                'proposed_class': obj['proposed_class'], **summaries,
                'shared_ID_count': len(id_sets['proposed'] & id_sets['no_proposal']),
                'raw_ordinary_switch': raw_switch,
                'raw_both_four_fifths_ordinary_switch': raw_switch and all(
                    5 * p['raw_winning_votes'] >= 4 * p['entries'] for p in (a, b)),
                **classify(set(a['attainable']), set(b['attainable'])),
            })
    require(len(rows) == 1000, 'paired roster mismatch')
    return rows


def summarize(rows):
    fields = ('forced_ordinary_switch', 'possible_ordinary_switch',
              'forced_ordinary_to_unresolved', 'forced_unresolved_to_ordinary',
              'forced_distinct_unresolved', 'raw_ordinary_switch',
              'raw_both_four_fifths_ordinary_switch')
    transitions = Counter((r['proposed']['raw_outcome'], r['no_proposal']['raw_outcome']) for r in rows)
    return {
        'objects': len(rows), 'image_groups': len({r['image'] for r in rows}),
        'agreement': {key: sum(r['agreement'] == key for r in rows) for key in
                      ('guaranteed_same', 'forced_difference', 'ambiguous')},
        'comparisons': {key: sum(r[key] for r in rows) for key in fields},
        'raw_equal': sum(r['proposed']['raw_outcome'] == r['no_proposal']['raw_outcome'] for r in rows),
        'raw_transitions': [{'proposed': a, 'no_proposal': b, 'objects': n} for (a, b), n in sorted(transitions.items())],
        'procedures': {p: {
            'entries': sum(r[p]['entries'] for r in rows),
            'ID_object_pairs': sum(r[p]['groups'] for r in rows),
            'raw_outcomes': dict(sorted(Counter(r[p]['raw_outcome'] for r in rows).items())),
        } for p in ('proposed', 'no_proposal')},
        'forced_difference_image_groups': len({r['image'] for r in rows if r['agreement'] == 'forced_difference'}),
        'objects_with_cross_procedure_ID_overlap': sum(r['shared_ID_count'] > 0 for r in rows),
        'forced_difference_with_ID_overlap': sum(r['shared_ID_count'] > 0 and r['agreement'] == 'forced_difference' for r in rows),
        'by_proposed_class': {label: {
            'objects': sum(r['proposed_class'] == label for r in rows),
            'forced_difference': sum(r['proposed_class'] == label and r['agreement'] == 'forced_difference' for r in rows),
            'forced_ordinary_switch': sum(r['proposed_class'] == label and r['forced_ordinary_switch'] for r in rows),
        } for label in CLASSES},
    }


def analyze(raw):
    require(len(raw) == 8568020 and hashlib.sha256(raw).hexdigest() == SOURCE, 'frozen source mismatch')
    engine = load_engine()
    data = engine.load_json(raw)
    rows = paired_rows(data, engine)
    proto_bytes = Path(__file__).with_name('protocol.json').read_bytes()
    require(hashlib.sha256(proto_bytes).hexdigest() == '2b084dcf491bedafd79ee9133b27823b3cd0839d31416a4333c9ecd3c62dd895', 'protocol changed')
    result = {
        'artifact_id': 'reiyah.review-procedure-sensitivity.result',
        'version': '0.1.0', 'lifecycle_status': 'exploratory',
        'source_sha256': SOURCE, 'protocol_sha256': hashlib.sha256(proto_bytes).hexdigest(),
        'identity_engine_sha256': ENGINE_SHA,
        'summary': summarize(rows),
        'scope': 'Finite recorded-object decision sensitivity; not physical truth, causality, future-review reliability, detector performance or work saving.',
    }
    return rows, result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--expected', type=Path)
    args = parser.parse_args()
    started = time.perf_counter()
    require(not args.output.exists(), 'output must be fresh')
    rows, result = analyze(args.data.read_bytes())
    if args.expected:
        require(canonical(result) == canonical(load_engine().load_json(args.expected.read_bytes())), 'retained result mismatch')
    args.output.mkdir(parents=True)
    for name, value in [('private_rows.json', rows), ('result.json', result)]:
        (args.output / name).write_text(canonical(value))
    (args.output / 'execution.json').write_text(canonical({
        'python': platform.python_version(), 'platform': platform.platform(),
        'wall_seconds': time.perf_counter() - started,
        'scope': 'Local process wall time excluding imports; not human effort or review cost.',
    }))
    print(canonical(result))


if __name__ == '__main__':
    main()
