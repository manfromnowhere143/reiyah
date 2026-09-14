"""Open existing annotation dependencies as original records, offline.

This bounded consumer uses the existing annotation, common-operand and capture
formats. It does not discover dependencies, admit references or judge objects.
"""
import argparse
from contextlib import ExitStack
from copy import deepcopy
from fractions import Fraction
import hashlib
import io
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tools.perception_annotations import indexed_rows, digest, CATEGORY_MAP
from tools.perception_decision import checker, contract, kernel
from tools.perception_inputs.source_io import JSONStream, require, snapshot, private_output_path
from tools.perception_inputs.sensors import _table_streams

ROLES = {'case', 'source_map', 'annotation_packet', 'witness_review', 'catalog',
         'normalizations', 'operands', 'renamings', 'observation_custody'}
PACKET_FILES = {'comparison.json', 'reference.json', 'compilation.json', 'annotations.json',
                'source-custody.json', 'dispositions.json', 'decision-payload.json', 'RESULT.json'}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def fields(value, expected):
    require(type(value) is dict and set(value) == set(expected),
            'TRACE_FIELDS', 'Missing or unknown fields')


def one(rows, **keys):
    matches = [row for row in rows if all(row.get(k) == v for k, v in keys.items())]
    require(len(matches) == 1, 'TRACE_JOIN', 'Source lookup is missing or ambiguous')
    return matches[0]


def read(spec):
    fields(spec, ('path', 'byte_size', 'sha256'))
    require(Path(spec['path']).is_absolute(), 'TRACE_PATH', 'Absolute source path required')
    with snapshot(spec) as stream:
        return stream.read()


def document(spec):
    require(type(spec['byte_size']) is int and 0 <= spec['byte_size'] <= 128 << 20,
            'TRACE_SIZE', 'JSON input exceeds the bounded consumer limit')
    return contract.parse(read(spec))


def source_document(spec):
    parser = JSONStream(io.BytesIO(read(spec)))
    result, _ = parser.value(dict)
    parser.finish()
    return result


def file_spec(root, entry):
    name = entry['filename']
    require(type(name) is str and not Path(name).is_absolute() and
            '..' not in Path(name).parts and '\\' not in name,
            'TRACE_PATH', 'Unsafe source-relative path')
    return {'path': str(Path(root)/name), 'byte_size': entry['byte_size'], 'sha256': entry['sha256']}


def load(selection):
    fields(selection, ('artifact_id', 'version', 'inputs', 'targets', 'deletion_groups'))
    require(selection['artifact_id'] == 'reiyah.annotation-trace.selection' and
            selection['version'] == '0.1.0', 'TRACE_SELECTION', 'Unsupported trace selection')
    fields(selection['inputs'], ROLES)
    require(type(selection['targets']) is list and 0 < len(selection['targets']) <= 128,
            'TRACE_LIMIT', 'Select between one and 128 already reported dependencies')
    docs = {role: document(spec) for role, spec in selection['inputs'].items() if role != 'witness_review'}
    # External research reports may contain measured decimal seconds. They are
    # cited source claims, not rational-only Engine operands; retain that format.
    docs['witness_review'] = source_document(selection['inputs']['witness_review'])
    packet = docs['annotation_packet']
    base = Path(selection['inputs']['annotation_packet']['path']).parent
    require(len(packet['files']) == len(PACKET_FILES) and
            {e['path'] for e in packet['files']} == PACKET_FILES,
            'TRACE_PACKET', 'Unexpected annotation packet files')
    for e in packet['files']:
        docs[e['path']] = document({'path': str(base/e['path']),
                                   'byte_size': e['byte_size'], 'sha256': e['sha256']})
    check_case(docs)
    return docs


def check_case(docs):
    """Check the complete exported finite case, not just its aggregate delta."""
    case, core = docs['case'], docs['comparison.json']
    require(core['model']['variables'] == [] and core['model']['clauses'] == [] and
            len(case['joint_worlds']) == 1, 'TRACE_SCOPE', 'This consumer requires one fixed benchmark world')
    world = case['joint_worlds'][0]
    require([a['id'] for a in case['anchors']] == [a['id'] for a in core['anchors']],
            'TRACE_CASE', 'Exported anchors differ from Engine input')
    require(docs['source_map']['core_comparison_sha256'] == digest(core),
            'TRACE_CASE', 'Source map is bound to another comparison')
    for key in ('false_negative', 'false_positive', 'tolerance'):
        require(Fraction(case['loss'][key]) == contract.rational(core['loss'][key]),
                'TRACE_CASE', 'Exported loss differs from Engine input')
    for a, b in zip(case['anchors'], core['anchors']):
        require(a['reference_state'] == b['reference']['state'] == 'finite',
                'TRACE_SCOPE', 'Open references do not name observed-empty objects')
        require(Fraction(a['weight']) == contract.rational(b['weight']), 'TRACE_CASE', 'Anchor weight differs')
        rename = one(docs['renamings']['renamings'], neutral_anchor_id=a['id'])
        normal = one(docs['normalizations'], anchor_id=rename['original_anchor_id'])
        for exported, original in [('base_detections', 'base'), ('added_detections', 'additions')]:
            expected_detections = []
            for detection in b[original]['value']:
                translation = one(rename['detections'], neutral=detection)
                row = one(normal['qualified_records'], detection=translation['original'])['record']
                expected_detections.append({'id': detection['id'], 'class': row['class']})
            require(a[exported] == expected_detections,
                    'TRACE_CASE', 'Detection membership or class differs')
        reference_world = one(docs['reference.json']['worlds'], id=world['world_id'])
        reference_anchor = one(reference_world['anchors'], anchor_id=rename['original_anchor_id'])
        expected_objects = []
        for obj in b['reference']['objects']:
            mapping = one(docs['compilation.json']['object_mapping'], world_id=world['world_id'],
                          anchor_id=rename['original_anchor_id'], graph_id=obj['id'])
            row = one(reference_anchor['objects'], id=mapping['object_id'])
            expected_objects.append({'id': obj['id'], 'class': row['class']})
        require(a['objects'] == expected_objects, 'TRACE_CASE', 'Object membership or class differs')
        ids = [x['id'] for x in a['objects']]
        expected = world['per_anchor'][a['id']]
        require(ids == [x['id'] for x in b['reference']['objects']] == expected['objects_present'] and
                expected['edges'] == [[e['detection'], e['object']] for e in b['reference']['edges']],
                'TRACE_CASE', 'Exported objects or edges differ')
        require(all(o['when'] == [] for o in b['reference']['objects']) and
                all(e['when'] == [] for e in b['reference']['edges']), 'TRACE_SCOPE', 'Conditional graph unsupported')
    checked = checker.check(core, docs['decision-payload.json'])
    require(checked == docs['RESULT.json']['result'], 'TRACE_CASE', 'Decision report differs from checked certificate')
    return checked


def resolve(docs, target):
    fields(target, ('anchor_id', 'world_id', 'local_index', 'graph_id', 'class'))
    case_anchor = one(docs['case']['anchors'], id=target['anchor_id'])
    i = target['local_index']
    require(type(i) is int and 0 <= i < len(case_anchor['objects']), 'TRACE_INDEX', 'Invalid local object index')
    obj = case_anchor['objects'][i]
    require(obj == {'id': target['graph_id'], 'class': target['class']},
            'TRACE_INDEX', 'Local index, graph identity and class disagree')
    one(docs['case']['joint_worlds'], world_id=target['world_id'])
    mapping = one(docs['source_map']['mappings'], neutral_anchor_id=target['anchor_id'],
                  world_id=target['world_id'], graph_id=target['graph_id'])
    compiler = one(docs['compilation.json']['object_mapping'], world_id=target['world_id'],
                   anchor_id=mapping['anchor_id'], graph_id=target['graph_id'])
    require(all(mapping[k] == v for k, v in compiler.items()), 'TRACE_MAPPING', 'Source map differs from compiler')
    world = one(docs['reference.json']['worlds'], id=target['world_id'])
    anchor = one(world['anchors'], anchor_id=mapping['anchor_id'])
    reference = one(anchor['objects'], id=mapping['object_id'])
    require(reference == mapping['reference_object'] and reference['class'] == target['class'] and
            reference['members'] == [reference['id']], 'TRACE_MAPPING', 'Expected one original benchmark annotation')
    row = one(docs['annotations.json'], annotation_token=reference['id'])
    require(digest(row) == reference['record_sha256'] == mapping['record_sha256'] and
            row['translation'][:2] == reference['xy'] and
            row['sample']['record']['timestamp'] == reference['timestamp_us'] and
            CATEGORY_MAP.get(row['category']['record']['name']) == reference['class'],
            'TRACE_RECORD', 'Reference and source record disagree')
    clock = one(docs['catalog']['anchors'], sample_token=row['sample_token'])
    rename = one(docs['renamings']['renamings'], neutral_anchor_id=target['anchor_id'])
    require(rename['original_anchor_id'] == mapping['anchor_id'] and rename['sample_token'] == row['sample_token'] and
            clock['scene_token'] == row['sample']['record']['scene_token'] and
            clock['anchor_timestamp_us'] == reference['timestamp_us'], 'TRACE_ANCHOR', 'Wrong source anchor')
    return {'target': target, 'mapping': mapping, 'annotation': row, 'clock': clock,
            'renaming': rename}


def evaluate_groups(docs, targets, groups):
    require(type(groups) is list and 0 < len(groups) <= 128, 'TRACE_LIMIT', 'One to 128 explicit deletion groups required')
    results, used = [], set()
    for group in groups:
        fields(group, ('target_indices', 'expected_delta', 'expected_criterion', 'expected_preference'))
        indices = group['target_indices']
        require(type(indices) is list and 0 < len(indices) <= len(targets) and
                all(type(i) is int and 0 <= i < len(targets) for i in indices) and len(set(indices)) == len(indices),
                'TRACE_INDEX', 'Invalid or repeated joint-deletion target')
        used.update(indices)
        changed = deepcopy(docs['comparison.json'])
        for i in indices:
            target = targets[i]
            edited = one(changed['anchors'], id=target['anchor_id'])['reference']
            edited['objects'] = [o for o in edited['objects'] if o['id'] != target['graph_id']]
            edited['edges'] = [e for e in edited['edges'] if e['object'] != target['graph_id']]
        proof = kernel.produce(contract.validate(changed))
        result = checker.check(changed, proof)
        require(all(contract.rational(result['bounds'][side]) == Fraction(group['expected_delta']) for side in ('lower', 'upper')) and
                result['decision']['improvement_criterion'] == group['expected_criterion'] and
                result['decision']['preference'] == group['expected_preference'],
                'TRACE_WITNESS', 'Supplied joint deletion result does not reproduce')
        results.append({'selection': group, 'result': result, 'certificate': proof})
    require(used == set(range(len(targets))), 'TRACE_SELECTION', 'An extracted target has no declared deletion group')
    return results


def original_annotations(docs, traces, output):
    custody = docs['source-custody.json']
    wanted = {name: {} for name in ('sample_annotation.json', 'sample.json', 'instance.json', 'category.json')}
    for t in traces:
        row = t['annotation']
        wanted['sample_annotation.json'][row['annotation_token']] = row['annotation_source']
        for name, key in [('sample.json', 'sample'), ('instance.json', 'instance'), ('category.json', 'category')]:
            wanted[name][row[key]['record']['token']] = row[key]['source']
    retained = {}
    with snapshot(custody['archive']) as stream, ExitStack() as stack:
        tables = _table_streams(stream, stack, tuple(wanted))
        for name, f in tables.items():
            h, size = hashlib.sha256(), 0
            while raw := f.read(1 << 20):
                h.update(raw); size += len(raw)
            require(custody['tables'][name] == {'member': 'v1.0-trainval/'+name,
                    'byte_size': size, 'sha256': h.hexdigest()}, 'TRACE_TABLE', 'Original table identity differs')
            f.seek(0)
            found = {}
            for row, binding in indexed_rows(f, 2_000_000):
                if row['token'] in wanted[name]:
                    require(binding == wanted[name][row['token']], 'TRACE_ROW', 'Original row index or bytes differ')
                    found[row['token']] = (row, binding)
            require(set(found) == set(wanted[name]), 'TRACE_ROW', 'Original row is missing')
            for token, (row, binding) in found.items():
                f.seek(binding['byte_offset']); raw = f.read(binding['byte_size'])
                require(sha(raw) == binding['sha256'], 'TRACE_ROW', 'Record bytes changed')
                path = output/'records'/f'{name[:-5]}-{binding["row_index"]}.json'
                path.write_bytes(raw)
                retained[name, token] = {'record': row, 'binding': binding,
                                         'extracted_path': str(path), 'table': custody['tables'][name]}
    for t in traces:
        row = t['annotation']; original = retained['sample_annotation.json', row['annotation_token']]['record']
        require(original['sample_token'] == row['sample_token'] and
                original['instance_token'] == row['instance']['record']['token'] and
                [Fraction(v) for v in original['translation']] == [contract.rational(v) for v in row['translation']],
                'TRACE_ROW', 'Original annotation meaning differs')
        require(all(original[k] == row[k] for k in ('num_lidar_pts', 'num_radar_pts')),
                'TRACE_ROW', 'Source support counts differ')
        require(row['category']['record']['token'] == row['instance']['record']['category_token'],
                'TRACE_ROW', 'Category join differs')
        t['original_records'] = {'annotation': retained['sample_annotation.json', row['annotation_token']]}
        for name, key in [('sample.json', 'sample'), ('instance.json', 'instance'), ('category.json', 'category')]:
            entry = retained[name, row[key]['record']['token']]
            require(entry['record'] == row[key]['record'], 'TRACE_ROW', 'Joined source record differs')
            t['original_records'][key] = entry
    for t in traces:
        t['original_records'] = {key: {k: v for k, v in entry.items() if k != 'record'}
                                 for key, entry in t['original_records'].items()}


def capture_context(docs, clock):
    custody = docs['observation_custody']; package = Path(custody['output'])
    seal_spec = {'path': str(package/'SEAL.json'), 'byte_size': (package/'SEAL.json').stat().st_size,
                 'sha256': custody['expected_seal_sha256']}
    seal = document(seal_spec)
    manifest = document(file_spec(package, seal['manifest']))
    require(manifest['package_id'] == seal['package_id'], 'TRACE_CAPTURE', 'Package identity differs')
    result = []
    for channel, meta in clock['keyframe_metadata'].items():
        if meta['metadata_state'] == 'missing':
            result.append({'channel': channel, 'state': 'missing_metadata'}); continue
        matches = [c for c in custody['captures'] if c['sample_data_token'] == meta['sample_data_token']]
        if not matches:
            result.append({'channel': channel, 'state': 'capture_not_in_supplied_package', 'metadata': meta}); continue
        require(len(matches) == 1, 'TRACE_CAPTURE', 'Ambiguous original capture')
        c = matches[0]; source = c['source']
        require(source['sample_token'] == clock['sample_token'] and source['channel'] == channel and
                all(source[k] == meta[k] for k in ('filename', 'capture_timestamp_us', 'ego_pose_token', 'calibrated_sensor_token')) and
                meta['capture_delta_us'] == source['capture_timestamp_us']-clock['anchor_timestamp_us'],
                'TRACE_CAPTURE', 'Capture identity or nominal time differs')
        delivered = one(manifest['captures'], id=c['capture_id'])
        require(delivered['evidence'] == c['disclosed_evidence'] and delivered['channel'] == channel,
                'TRACE_CAPTURE', 'Delivered capture differs from custody')
        if c['raw_identity']['state'] != 'retained' or c['disclosed_evidence']['state'] != 'delivered':
            result.append({'channel': channel, 'state': 'capture_bytes_unavailable', 'custody': c}); continue
        raw_spec = file_spec(custody['request']['raw_root'], c['raw_identity'])
        asset_spec = file_spec(package, c['disclosed_evidence']['asset'])
        raw, asset = read(raw_spec), read(asset_spec)
        if channel == 'LIDAR_TOP':
            marker = b'end_header\n'; start = asset.find(marker)+len(marker)
            require(start >= len(marker) and asset[start:] == raw, 'TRACE_CAPTURE', 'Point records differ from original')
        else:
            require(raw == asset, 'TRACE_CAPTURE', 'Image bytes differ from original')
        result.append({'channel': channel, 'state': 'original_and_delivered_bytes_verified',
                       'capture_id': c['capture_id'], 'sample_data_token': c['sample_data_token'],
                       'nominal_delta_us': meta['capture_delta_us'], 'original': raw_spec, 'delivered': asset_spec,
                       'object_point_or_pixel_locator': 'not_established'})
    return result


def predictions(docs, traces, output):
    """Retrieve incident detections by retained source_index, never an ID suffix."""
    cache = {}
    for t in traces:
        target = t['target']; core = one(docs['comparison.json']['anchors'], id=target['anchor_id'])
        ids = sorted({e['detection'] for e in core['reference']['edges'] if e['object'] == target['graph_id']})
        normal = one(docs['normalizations'], anchor_id=t['mapping']['anchor_id'])
        operands = one(docs['operands']['anchors'], anchor_id=target['anchor_id'])
        rows = []
        for name in ids:
            translation = one(t['renaming']['detections'], neutral=one(operands['qualified_records'],
                              detection=one(core['base']['value']+core['additions']['value'], id=name))['detection'])
            old = one(normal['qualified_records'], detection=translation['original'])['record']
            neutral = one(operands['qualified_records'], detection=translation['neutral'])['record']
            require(digest(old) == translation['original']['record_sha256'] and
                    digest(neutral) == translation['neutral']['record_sha256'] and
                    all(old[k] == neutral[k] for k in ('xy', 'class', 'score')),
                    'TRACE_PREDICTION', 'Normalized detection identity differs')
            role = old['source']; frame_key = (role, t['clock']['sample_token'])
            source = docs['catalog']['sources'][role]
            require(old['sample_token'] == frame_key[1] and old['source_sha256'] == source['sha256'],
                    'TRACE_PREDICTION', 'Prediction source or sample differs')
            if frame_key not in cache:
                frame = t['clock'][role]
                with snapshot(source) as stream:
                    stream.seek(frame['byte_offset']); raw = stream.read(frame['byte_size'])
                require(sha(raw) == frame['sha256'], 'TRACE_PREDICTION', 'Original sample array differs')
                parser = JSONStream(io.BytesIO(raw)); parser.expect('['); records = []
                if parser.peek() != ']':
                    while True:
                        row, binding = parser.value(dict); records.append((row, binding, raw))
                        if parser.peek() == ']': break
                        parser.expect(',')
                parser.expect(']'); parser.finish()
                require(len(records) == frame['row_count'], 'TRACE_PREDICTION', 'Prediction row count differs')
                cache[frame_key] = records
            index = old['source_index']
            require(type(index) is int and 0 <= index < len(cache[frame_key]), 'TRACE_INDEX', 'Invalid original prediction index')
            row, binding, frame_raw = cache[frame_key][index]
            require(row['detection_name'] == old['class'] and
                    [Fraction(v) for v in row['translation'][:2]] == [contract.rational(v) for v in old['xy']] and
                    Fraction(row['detection_score']) == contract.rational(old['score']),
                    'TRACE_PREDICTION', 'Original detection record differs')
            raw = frame_raw[binding['byte_offset']:binding['byte_offset']+binding['byte_size']]
            # Use a content name because the same source frame can be revisited.
            p = output/'records'/('prediction-'+sha(raw)+'.json'); p.write_bytes(raw)
            rows.append({'neutral_id': name, 'original_index': index, 'source': source,
                         'sample_token': frame_key[1], 'array': t['clock'][role],
                         'record': {**binding, 'absolute_byte_offset': t['clock'][role]['byte_offset']+binding['byte_offset']},
                         'extracted_path': str(p), 'normalization': old})
        t['incident_predictions'] = rows


def render(traces, groups, output):
    lines = ['# Decision dependencies and original evidence', '',
             'Selected conditional-decision dependencies; no judgment that labels are wrong.', '',
             'Original camera images and point captures provide context. No object-to-pixel or point association is established.', '',
             '| Anchor | Local label | Class | Deletion groups | Original sensor-count metadata | Evidence |',
             '|---|---:|---|---|---|---|']
    for n, t in enumerate(traces, 1):
        target, row = t['target'], t['annotation']; page = f'dependency-{n:03}.md'
        memberships = [str(g+1) for g, group in enumerate(groups) if n-1 in group['selection']['target_indices']]
        lines.append(f'| {target["anchor_id"]} | {target["local_index"]} | {target["class"]} | {", ".join(memberships)} | '
                     f'{row["num_lidar_pts"]} lidar / {row["num_radar_pts"]} radar | [Open]({page}) |')
        text = [f'# {target["anchor_id"]}: label {target["local_index"]}', '',
                f'This label participates in deletion group(s) {", ".join(memberships)}. '
                'The group changes all its listed labels together; it is not a claim that each label alone changes the decision.', '',
                '## Original records', '']
        for role, entry in t['original_records'].items():
            text.append(f'- [{role}]({Path(entry["extracted_path"]).relative_to(output)}): '
                        f'original row {entry["binding"]["row_index"]}, byte offset {entry["binding"]["byte_offset"]}.')
        text.extend(['', '## Detector records that could match this label', ''])
        for pred in t['incident_predictions']:
            text.append(f'- [{pred["neutral_id"]}]({Path(pred["extracted_path"]).relative_to(output)}): '
                        f'original row {pred["original_index"]}.')
        text.extend(['', '## Capture context', '', 'These captures have the declared sample association; physical synchronization and object correspondence remain unestablished.', ''])
        for capture in t['captures']:
            if capture['state'] == 'original_and_delivered_bytes_verified':
                text.append(f'- [{capture["channel"]}](<{capture["delivered"]["path"]}>): '
                            f'nominal timestamp offset {capture["nominal_delta_us"]} microseconds.')
            else: text.append(f'- {capture["channel"]}: {capture["state"]}.')
        (output/page).write_text('\n'.join(text)+'\n')
    lines.extend(['', '## Checked joint deletions', '',
                  'A group is one counterfactual comparison using the same configurations, weights and tolerance.', ''])
    for g, group in enumerate(groups, 1):
        refs = ', '.join(f'[label {i+1}](dependency-{i+1:03}.md)' for i in group['selection']['target_indices'])
        result = group['result']; delta = str(contract.rational(result['bounds']['lower']))
        lines.append(f'- Group {g}: {refs} → delta {delta}, {result["decision"]["improvement_criterion"]}.')
    (output/'OPEN_EVIDENCE.md').write_text('\n'.join(lines)+'\n')


def run(path, expected, output):
    raw = path.read_bytes()
    require(sha(raw) == expected, 'TRACE_SELECTION', 'Selection bytes differ')
    selection = contract.parse(raw)
    docs = load(selection)
    output = private_output_path(output, [ROOT, path.parent] +
             [Path(s['path']).parent for s in selection['inputs'].values()],
             'TRACE_OUTPUT', 'A fresh private output outside source directories is required')
    require(not output.exists(), 'TRACE_OUTPUT', 'Refuse a consumed output identity')
    traces = [resolve(docs, target) for target in selection['targets']]
    require(len({(t['target']['world_id'], t['target']['anchor_id'], t['target']['graph_id']) for t in traces}) == len(traces),
            'TRACE_SELECTION', 'Repeated trace target')
    groups = evaluate_groups(docs, selection['targets'], selection['deletion_groups'])
    output.mkdir(); (output/'records').mkdir()
    original_annotations(docs, traces, output)
    predictions(docs, traces, output)
    captures = {}
    for t in traces:
        key = t['clock']['sample_token']
        if key not in captures: captures[key] = capture_context(docs, t['clock'])
        t['captures'] = captures[key]
        del t['renaming']; del t['clock']
    render(traces, groups, output)
    result = {'artifact_id': 'reiyah.annotation-trace.result', 'version': '0.1.0',
              'selection_sha256': expected, 'inputs': selection['inputs'], 'traces': traces, 'deletion_groups': groups,
              'implementation_sha256': {str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in
                  [Path(__file__).resolve(), ROOT/'tools/perception_annotations.py',
                   ROOT/'tools/perception_inputs/source_io.py', ROOT/'tools/perception_inputs/sensors.py',
                   ROOT/'tools/perception_decision/kernel.py', ROOT/'tools/perception_decision/checker.py',
                   ROOT/'tools/perception_decision/contract.py', contract.SCHEMA]},
              'evidence_kind': 'benchmark_annotation_conditional', 'physical_reference_validity': 'not_established',
              'human_observation': 'not_performed', 'human_effort': 'unmeasured',
              'shared_trusted_code': ['Engine source snapshot, JSON/archive readers, category map, matching producer and certificate checker'],
              'scope': 'Selected witnesses and source joins; no completeness check of the deletion family, new dependency search, or physical object judgment.'}
    (output/'TRACE.json').write_bytes(contract.encoded(result))
    files = [{'path': str(p.relative_to(output)), 'byte_size': p.stat().st_size, 'sha256': sha(p.read_bytes())}
             for p in sorted(output.rglob('*')) if p.is_file()]
    (output/'PACKET.json').write_bytes(contract.encoded({'artifact_id': 'reiyah.annotation-trace.packet',
        'version': '0.1.0', 'selection_sha256': expected, 'files': files}))
    return {'trace_count': len(traces), 'capture_count': sum(len(v) for v in captures.values()),
            'output': str(output), 'packet_sha256': sha((output/'PACKET.json').read_bytes())}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--selection', type=Path, required=True)
    parser.add_argument('--selection-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(run(args.selection, args.selection_sha256, args.output), sort_keys=True))
    except contract.Invalid as exc:
        print(json.dumps({'state': 'invalid', 'code': exc.code, 'detail': str(exc)}), file=sys.stderr)
        raise SystemExit(2)
