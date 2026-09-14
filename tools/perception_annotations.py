"""Replay a fixed comparison against source-bound benchmark annotations, offline.

This adapter constructs an explicit conditional reference model. It never calls
human admission, creates reviewer records, or modifies the original comparison.
The existing reference compiler, neutral projection and certificate checker are
shared trusted code, not independent validation of the benchmark labels.
"""
import argparse
from contextlib import ExitStack
import hashlib
import os
from pathlib import Path
import sys

from tools import perception_reference as reference
from tools.perception_reviewed_operands import project
from tools.perception_decision import contract, kernel, checker
from tools.perception_decision.cli import atomic_write
from tools.perception_decision.nuscenes import _number
from tools.perception_inputs.clock import identity, timestamp
from tools.perception_inputs.sensors import _table_streams
from tools.perception_inputs.source_io import JSONStream, require, snapshot, private_output_path

ROOT = Path(__file__).resolve().parents[1]
VERSION = '0.1.0'
POLICY = 'reiyah.annotation-conditional-fixed-comparison.0.1.0'
ROLES = ('comparison', 'normalizations', 'catalog', 'common_comparison', 'renamings', 'metadata')
TABLES = ('sample.json', 'sample_annotation.json', 'instance.json', 'category.json')
# Category names are data vocabulary. Policy/source basis is recorded in the README.
CATEGORY_MAP = {
    'movable_object.barrier': 'barrier', 'vehicle.bicycle': 'bicycle',
    'vehicle.bus.bendy': 'bus', 'vehicle.bus.rigid': 'bus', 'vehicle.car': 'car',
    'vehicle.construction': 'construction_vehicle', 'vehicle.motorcycle': 'motorcycle',
    'human.pedestrian.adult': 'pedestrian', 'human.pedestrian.child': 'pedestrian',
    'human.pedestrian.construction_worker': 'pedestrian',
    'human.pedestrian.police_officer': 'pedestrian',
    'movable_object.trafficcone': 'traffic_cone', 'vehicle.trailer': 'trailer', 'vehicle.truck': 'truck',
}


def digest(value):
    return hashlib.sha256(contract.encoded(value)).hexdigest()


def code_identities():
    paths = sorted((ROOT/'tools').glob('perception_*.py'))
    for directory in sorted((ROOT/'tools').glob('perception_*')):
        if directory.is_dir():
            paths.extend(sorted(directory.glob('*.py')))
    paths.append(contract.SCHEMA)
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def fields(value, names):
    require(type(value) is dict and set(value) == set(names.split()),
            'ANNOTATION_FIELDS', 'Missing or unknown fields')


def request_contract(request):
    fields(request, 'artifact_id version policy inputs')
    require(request['artifact_id'] == 'reiyah.perception-annotations.request'
            and request['version'] == VERSION and request['policy'] == POLICY,
            'ANNOTATION_POLICY', 'Unsupported annotation experiment or policy')
    fields(request['inputs'], ' '.join(ROLES))
    for spec in request['inputs'].values():
        fields(spec, 'path byte_size sha256')
        require(type(spec['path']) is str and Path(spec['path']).is_absolute(),
                'ANNOTATION_PATH', 'Require absolute source paths')


def bound_document(spec):
    require(type(spec['byte_size']) is int and 0 <= spec['byte_size'] <= 128 << 20,
            'ANNOTATION_SIZE', 'Bounded JSON input required')
    with snapshot(spec) as stream:
        return contract.parse(stream.read())


def indexed_rows(stream, limit):
    """Retain literal UTF-8 row offsets, size and hash using the source parser."""
    reader = JSONStream(stream)
    reader.expect('[')
    seen, index = set(), 0
    if reader.peek() != ']':
        while True:
            require(index < limit, 'ANNOTATION_LIMIT', 'Source table exceeds row limit')
            row, binding = reader.value(dict)
            token = identity(row.get('token'))
            require(token not in seen, 'ANNOTATION_DUPLICATE', 'Duplicate source table token')
            seen.add(token)
            yield row, {'row_index': index, **binding}
            index += 1
            if reader.peek() == ']':
                break
            reader.expect(',')
    reader.expect(']')
    reader.finish()


def read_annotations(metadata, wanted):
    """Scan complete tables; select every annotation for the exact anchor tokens."""
    with snapshot(metadata) as stream, ExitStack() as stack:
        tables = _table_streams(stream, stack, TABLES)
        table_bindings = {}
        for name, table in tables.items():
            h, size = hashlib.sha256(), 0
            while chunk := table.read(1 << 20):
                h.update(chunk)
                size += len(chunk)
            table.seek(0)
            table_bindings[name] = {'member': 'v1.0-trainval/' + name,
                                    'byte_size': size, 'sha256': h.hexdigest()}
        samples, selected_samples = set(), {}
        for row, binding in indexed_rows(tables['sample.json'], 50000):
            fields(row, 'token scene_token timestamp prev next')
            samples.add(row['token'])
            if row['token'] in wanted:
                require(timestamp(row['timestamp']) == wanted[row['token']]['time'],
                        'ANNOTATION_TIME', 'Annotation sample time differs from bound anchor')
                require(identity(row['scene_token']) == wanted[row['token']]['scene'],
                        'ANNOTATION_SAMPLE', 'Annotation sample belongs to another scene')
                selected_samples[row['token']] = {'record': row, 'source': binding}
        require(set(selected_samples) == set(wanted), 'ANNOTATION_SAMPLE', 'A requested sample is absent')
        annotations, scanned = [], 0
        for row, binding in indexed_rows(tables['sample_annotation.json'], 2_000_000):
            fields(row, 'token sample_token instance_token attribute_tokens visibility_token '
                        'translation size rotation prev next num_lidar_pts num_radar_pts')
            require(identity(row['sample_token']) in samples, 'ANNOTATION_SAMPLE', 'Dangling annotation sample')
            scanned += 1
            if row['sample_token'] in wanted:
                require(len(annotations) < 16384, 'ANNOTATION_LIMIT', 'Selected annotations exceed limit')
                annotations.append((row, binding))
        instance_tokens = {identity(row['instance_token']) for row, _ in annotations}
        instances = {}
        for row, binding in indexed_rows(tables['instance.json'], 1_000_000):
            fields(row, 'token category_token first_annotation_token last_annotation_token nbr_annotations')
            if row['token'] in instance_tokens:
                instances[row['token']] = {'record': row, 'source': binding}
        require(set(instances) == instance_tokens, 'ANNOTATION_INSTANCE', 'An annotation instance is absent')
        categories = {}
        for row, binding in indexed_rows(tables['category.json'], 10000):
            fields(row, 'token name description')
            require(type(row['name']) is str and 0 < len(row['name']) <= 256,
                    'ANNOTATION_CATEGORY', 'Missing category name')
            categories[row['token']] = {'record': row, 'source': binding}
        rows = []
        for row, binding in annotations:
            inst = instances[row['instance_token']]
            category = inst['record']['category_token']
            require(category in categories, 'ANNOTATION_CATEGORY', 'An instance category is absent')
            center = row['translation']
            require(type(center) is list and len(center) == 3, 'ANNOTATION_POSITION', 'Require source XYZ')
            point = [contract.wire(_number(q)) for q in center]
            for key in ('num_lidar_pts', 'num_radar_pts'):
                require(type(row[key]) is int and 0 <= row[key] <= 10**9,
                        'ANNOTATION_POINTS', 'Invalid source point count')
            rows.append({'annotation_token': row['token'], 'sample_token': row['sample_token'],
                         'translation': point, 'annotation_source': binding,
                         'sample': selected_samples[row['sample_token']],
                         'instance': inst, 'category': categories[category],
                         'num_lidar_pts': row['num_lidar_pts'], 'num_radar_pts': row['num_radar_pts']})
    return rows, {'archive': metadata, 'tables': table_bindings,
                  'annotation_rows_scanned': scanned, 'selected_samples': selected_samples}


def model_from_annotations(rows, wanted, input_hashes, basis):
    """One benchmark world; each exclusion and source identity remains explicit."""
    anchors = {row['anchor_id']: {'anchor_id': row['anchor_id'], 'objects': [],
                'unlisted_objects': {'state': 'excluded_by_assumption', 'basis_sha256': basis,
                'statement': 'Target is exactly the mapped benchmark labels within nominal 50 m; physical completeness is not asserted.'}}
               for row in wanted.values()}
    dispositions, seen = [], set()
    for row in rows:
        name = identity(row['annotation_token'])
        require(name not in seen, 'ANNOTATION_DUPLICATE', 'Repeated selected annotation identity')
        seen.add(name)
        require(row['sample_token'] in wanted, 'ANNOTATION_SAMPLE', 'Unexpected selected sample')
        anchor = wanted[row['sample_token']]
        xy = row['translation'][:2]
        point = reference._point(xy)
        distance2 = sum((x-y)**2 for x, y in zip(point, anchor['ego']))
        category = row['category']['record']['name']
        label = CATEGORY_MAP.get(category)
        reason = ('unmapped_category' if label is None else
                  'outside_nominal_50m' if distance2 > 2500 else 'included')
        dispositions.append({'annotation_token': name, 'anchor_id': anchor['anchor_id'],
                             'source_row_sha256': row['annotation_source']['sha256'],
                             'category': category, 'detection_class': label,
                             'distance_squared': contract.wire(distance2), 'disposition': reason})
        if reason != 'included':
            continue
        objects = anchors[anchor['anchor_id']]['objects']
        require(len(objects) < 128, 'ANNOTATION_LIMIT', 'Too many eligible objects; no clipping is permitted')
        objects.append({'id': name, 'members': [name], 'record_sha256': digest(row),
                        'state': 'point', 'class': label, 'xy': xy, 'timestamp_us': anchor['time']})
    spec = {'artifact_id': 'reiyah.perception-reference.input', 'version': VERSION,
            'coordinate_frame': 'nominal_global_xy', 'inputs': input_hashes,
            'joint_coverage': {'state': 'assumed_complete', 'basis_sha256': basis,
                              'statement': 'One complete interpretation of the selected benchmark labels, conditional on this target definition.'},
            'worlds': [{'id': 'benchmark-labels', 'basis_sha256': basis, 'anchors': list(anchors.values())}]}
    return spec, dispositions


def build(request):
    request_contract(request)
    inputs = request['inputs']
    docs = {role: bound_document(inputs[role]) for role in ROLES if role != 'metadata'}
    case, normals, catalog = (docs[k] for k in ('comparison', 'normalizations', 'catalog'))
    contract.validate(case)
    geometry = reference._joined_detections(case, normals, catalog)
    require(all(a['reference']['state'] == 'open' for a in case['anchors'])
            and case['model'] == {'variables': [], 'clauses': []},
            'ANNOTATION_STAGE', 'Require the original open comparison')
    require(all(a[r]['state'] == 'observed' for a in case['anchors'] for r in ('base', 'additions')),
            'ANNOTATION_PREDICTIONS', 'Both fixed prediction outputs must be observed')
    require(all(catalog['sources']['metadata'][k] == inputs['metadata'][k]
                for k in ('path', 'byte_size', 'sha256')),
            'ANNOTATION_BINDING', 'Separately expected metadata differs from catalog')
    mappings = docs['renamings']['renamings']
    require(digest(project(case, docs['common_comparison'], mappings)) == digest(docs['common_comparison']),
            'ANNOTATION_BINDING', 'Common comparison is not the exact original prediction projection')
    clocks = {r['sample_token']: r for r in catalog['anchors']}
    wanted = {n['sample_token']: {'anchor_id': n['anchor_id'], **geometry[n['anchor_id']],
              'scene': clocks[n['sample_token']]['scene_token']} for n in normals}
    rows, custody = read_annotations(inputs['metadata'], wanted)
    basis = digest({'policy': POLICY, 'request_sha256': digest(request), 'custody': custody})
    spec, dispositions = model_from_annotations(rows, wanted,
        {role+'_sha256': inputs[role]['sha256'] for role in ('comparison', 'normalizations', 'catalog')}, basis)
    compiled, compilation = reference.compile_model(spec, case, normals, catalog)
    comparison = project(compiled, docs['common_comparison'], mappings)
    comparison['comparison_id'] = 'reiyah.annotation-conditional-fixed-comparison'
    # Preserve inherited assumptions as historical scope, then state this distinct target.
    comparison['assumptions'].append('Separate retrospective benchmark-label calculation under '+POLICY+
        '; the original physical-reference comparison remains open. No human reference admission.')
    contract.validate(comparison)
    payload = kernel.produce(comparison)
    checker.check(comparison, payload)
    anchors = []
    for old, new in zip(case['anchors'], comparison['anchors']):
        anchors.append({'anchor_id': new['id'], 'original_anchor_id': old['id'],
                        'base_count': len(new['base']['value']), 'addition_count': len(new['additions']['value']),
                        'reference_state': new['reference']['state'],
                        'included_annotations': sum(d['anchor_id'] == old['id'] and d['disposition'] == 'included' for d in dispositions)})
    report = {'artifact_id': 'reiyah.perception-annotations.result', 'version': VERSION,
              'policy': POLICY, 'request_sha256': digest(request),
              'evidence_kind': 'benchmark_annotation_conditional',
              'original_common_comparison_sha256': inputs['common_comparison']['sha256'],
              'comparison_sha256': digest(comparison), 'reference_sha256': digest(spec),
              'anchors': anchors, 'result': payload['result'],
              'source_annotation_count': len(rows), 'annotation_rows_scanned': custody['annotation_rows_scanned'],
              'excluded_annotations': sum(d['disposition'] != 'included' for d in dispositions),
              'admitted_human_readings': 0, 'original_reference_changed': False,
              'human_effort': 'unmeasured', 'independent_label_accuracy': 'not_established',
              'official_nuscenes_score': False, 'physical_safety_claim': False,
              'shared_trusted_code': ['source JSON/archives', 'normalization lineage', 'reference compiler',
                                      'neutral projection', 'core contract and witness checker'],
              'upstream_prediction_qualification': 'inherited separately bound source qualification; not model inference reproduction'}
    return {'comparison.json': comparison, 'reference.json': spec, 'compilation.json': compilation,
            'annotations.json': rows, 'source-custody.json': custody, 'dispositions.json': dispositions,
            'decision-payload.json': payload, 'RESULT.json': report}


def run(request_path, expected, output):
    request = contract.load(request_path, expected, 1 << 20, validate_input=False)
    request_contract(request)
    output = Path(output)
    require(output.is_absolute() and output.parent.is_dir() and not os.path.lexists(output),
            'ANNOTATION_OUTPUT', 'Require a fresh absolute output with existing parent')
    output = private_output_path(output, [ROOT, *[Path(s['path']).parent for s in request['inputs'].values()]],
                                 'ANNOTATION_OUTPUT', 'Output must be outside code and input directories')
    code = code_identities()
    files = build(request)
    require(code_identities() == code, 'ANNOTATION_CODE_CHANGED', 'Source changed during replay')
    contract.load(request_path, expected, 1 << 20, validate_input=False)
    output.mkdir(mode=0o700)
    for name, document in files.items():
        atomic_write(output/name, contract.encoded(document))
    manifest = {'artifact_id': 'reiyah.perception-annotations.packet', 'version': VERSION,
                'request_file_sha256': expected, 'source_identities': code, 'files': [
                    {'path': name, 'byte_size': len(contract.encoded(doc)), 'sha256': digest(doc)}
                    for name, doc in sorted(files.items())]}
    atomic_write(output/'PACKET.json', contract.encoded(manifest))
    return files['RESULT.json']


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--request-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = run(args.request, args.request_sha256, args.output)
    except contract.Invalid as exc:
        sys.stderr.buffer.write(contract.encoded({'status': 'invalid', **exc.diagnostic()}))
        return 2
    except (OSError, KeyError, TypeError, ValueError) as exc:
        sys.stderr.buffer.write(contract.encoded({'status': 'invalid', 'code': 'ANNOTATION_INPUT', 'detail': str(exc)}))
        return 2
    sys.stdout.buffer.write(contract.encoded(result))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
