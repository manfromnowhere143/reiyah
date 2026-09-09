"""Compile explicit joint point-reference alternatives into checked-core operands.

The finite envelope is an input assumption, never a physical-coverage certificate.
Unknown coverage, geometry or timing keeps the affected anchor open. Joint worlds
share one choice across the whole cohort; no independent per-anchor choices are added.
"""
from copy import deepcopy
import hashlib
from pathlib import Path
import re

from .perception_decision import contract
from .perception_decision.nuscenes import CLASSES, POLICY
from .perception_inputs.clock import identity, timestamp
from .perception_inputs.source_io import digest_value, require

VERSION = '0.1.0'
MAX_JOINT_WORLDS = 64
MAX_GEOMETRY_COMPARISONS = 2_000_000


def _fields(value, names):
    require(type(value) is dict and set(value) == set(names.split()),
            'REFERENCE_FIELDS', 'Missing or unknown reference fields')


def _list(value, maximum, minimum=0):
    require(type(value) is list and minimum <= len(value) <= maximum,
            'REFERENCE_SIZE', 'Invalid or oversized reference collection')
    return value


def _text(value):
    require(type(value) is str and 0 < len(value) <= 1024,
            'REFERENCE_FIELDS', 'An explicit bounded explanation is required')


def _digest(value):
    require(digest_value(value), 'REFERENCE_BINDING', 'Require an exact SHA-256 identity')
    return value


def _hash(value):
    return hashlib.sha256(contract.encoded(value)).hexdigest()


def _point(value):
    _list(value, 2, 2)
    result = []
    for q in value:
        _fields(q, 'numerator denominator')
        require(type(q['numerator']) is str and re.fullmatch(r'0|-?[1-9][0-9]{0,31}', q['numerator']) is not None and
                type(q['denominator']) is str and re.fullmatch(r'[1-9][0-9]{0,31}', q['denominator']) is not None,
                'REFERENCE_NUMBER', 'Coordinates require bounded canonical rational strings')
        number = contract.rational(q)
        require(abs(number) <= 10**12, 'REFERENCE_NUMBER', 'Coordinate exceeds the declared numerical scope')
        result.append(number)
    return tuple(result)


def _distance2(a, b):
    return sum((x-y)**2 for x, y in zip(a, b))


def _coverage(value, admitted_state):
    require(type(value) is dict, 'REFERENCE_FIELDS', 'Explicit coverage state is required')
    if value.get('state') == 'unknown':
        _fields(value, 'state reason')
        _text(value['reason'])
        return False
    _fields(value, 'state statement basis_sha256')
    require(value['state'] == admitted_state, 'REFERENCE_COVERAGE', 'No physical coverage or acceptance state is admitted')
    _text(value['statement'])
    _digest(value['basis_sha256'])
    return True


def _header(spec):
    _fields(spec, 'artifact_id version coordinate_frame inputs joint_coverage worlds')
    require(spec['artifact_id'] == 'reiyah.perception-reference.input' and spec['version'] == VERSION and
            spec['coordinate_frame'] == 'nominal_global_xy', 'REFERENCE_VERSION', 'Unsupported reference contract')
    _fields(spec['inputs'], 'comparison_sha256 normalizations_sha256 catalog_sha256')
    for digest in spec['inputs'].values():
        _digest(digest)
    _coverage(spec['joint_coverage'], 'assumed_complete')
    _list(spec['worlds'], MAX_JOINT_WORLDS, 1)


def _joined_detections(case, normalizations, catalog):
    """Validate consumed lineage and geometry; upstream normalization remains trusted."""
    require(type(catalog) is dict and catalog.get('artifact_id') == 'reiyah.perception-inputs.catalog' and
            catalog.get('version') == VERSION and type(catalog.get('sources')) is dict,
            'REFERENCE_BINDING', 'Require the expected upstream catalog contract')
    clock = {}
    for row in _list(catalog.get('anchors'), 50000, 1):
        require(type(row) is dict, 'REFERENCE_BINDING', 'Malformed catalog anchor')
        token = identity(row.get('sample_token'))
        require(token not in clock, 'REFERENCE_BINDING', 'Duplicate catalog sample identity')
        clock[token] = row
    receipts = {}
    for row in _list(normalizations, 128, 1):
        require(type(row) is dict and row.get('artifact_id') == 'reiyah.perception-decision.normalization' and
                row.get('version') == VERSION and row.get('policy') == POLICY,
                'REFERENCE_BINDING', 'Unsupported normalization receipt')
        name = identity(row.get('anchor_id'))
        require(name not in receipts, 'REFERENCE_BINDING', 'Duplicate normalization anchor')
        receipts[name] = row
    require(set(receipts) == {a['id'] for a in case['anchors']},
            'REFERENCE_POPULATION', 'Normalization and comparison populations differ')
    joined, seen_samples = {}, set()
    for anchor in case['anchors']:
        receipt = receipts[anchor['id']]
        sample = identity(receipt.get('sample_token'))
        require(sample in clock and sample not in seen_samples, 'REFERENCE_POPULATION', 'Missing or repeated comparison sample')
        seen_samples.add(sample)
        require(receipt.get('normalized_anchor_sha256') == _hash(anchor),
                'REFERENCE_BINDING', 'Normalization is bound to different anchor bytes')
        row = clock[sample]
        time = timestamp(row.get('anchor_timestamp_us'))
        _fields(receipt.get('source_sha256'), 'base camera clock')
        for role in ('base', 'camera', 'clock'):
            source = catalog['sources'].get('metadata' if role == 'clock' else role)
            require(type(source) is dict, 'REFERENCE_BINDING', 'Catalog source role is absent')
            require(receipt['source_sha256'][role] == source.get('sha256'),
                    'REFERENCE_BINDING', 'Normalization and catalog source identities differ')
            if role == 'clock':
                _digest(source.get('sha256'))
        pose = row.get('nominal_ego_xy')
        require(type(pose) is dict and pose.get('state') == 'observed' and pose.get('timestamp_us') == time,
                'REFERENCE_POSE', 'No observed nominal ego pose at the comparison anchor time')
        ego = _point(pose.get('value'))
        require(_point(receipt.get('ego_xy')) == ego, 'REFERENCE_POSE', 'Normalization and catalog ego positions differ')
        records = {}
        for entry in _list(receipt.get('qualified_records'), 1024):
            _fields(entry, 'detection record')
            _fields(entry['detection'], 'id record_sha256')
            node, record = entry['detection'], entry['record']
            _fields(record, 'policy sample_token source source_sha256 source_index class xy score')
            require(record['policy'] == POLICY and record['sample_token'] == sample and
                    record['source'] in ('base', 'camera') and type(record['source_index']) is int and
                    0 <= record['source_index'] < 512, 'REFERENCE_BINDING', 'Malformed normalized detection lineage')
            require(record['source_sha256'] == receipt['source_sha256'][record['source']] and
                    node['id'] == record['source'] + ':' + str(record['source_index']) and
                    node['record_sha256'] == _hash(record), 'REFERENCE_BINDING', 'Detection identity or record bytes differ')
            require(node['id'] not in records and type(record['class']) is str and record['class'] in CLASSES,
                    'REFERENCE_BINDING', 'Duplicate detection or unknown normalized class')
            records[node['id']] = (node, record['class'], _point(record['xy']), record['source'])
        selected = []
        for role, source_role in [('base', 'base'), ('additions', 'camera')]:
            if anchor[role]['state'] != 'observed':
                continue
            for node in anchor[role]['value']:
                require(node['id'] in records and records[node['id']][0] == node and records[node['id']][3] == source_role,
                        'REFERENCE_BINDING', 'Retained detection lacks its exact role-bound geometric record')
                selected.append((node['id'], records[node['id']][1], records[node['id']][2]))
        joined[anchor['id']] = {'time': time, 'ego': ego, 'detections': selected}
    return joined


def compile_model(spec, case, normalizations, catalog):
    """Pure compilation of already hash-bound inputs; prefer compile_files at a boundary."""
    _header(spec)
    contract.validate(case)
    require(case['model'] == {'variables': [], 'clauses': []} and
            all(a['reference']['state'] == 'open' for a in case['anchors']),
            'REFERENCE_PRECONDITION', 'Compile only the unmodified open normalized comparison')
    geometry = _joined_detections(case, normalizations, catalog)
    result = deepcopy(case)
    anchors = {a['id']: a for a in result['anchors']}
    worlds = spec['worlds']
    bits = (len(worlds)-1).bit_length()
    variables = ['reference-choice-' + str(i) for i in range(bits)]

    def condition(index):
        return [{'variable': name, 'value': bool(index & (1 << i))} for i, name in enumerate(variables)]

    # Exclude unused encodings without turning a joint choice into independent anchors.
    result['model'] = {'variables': variables,
                       'clauses': [[dict(l, value=not l['value']) for l in condition(i)]
                                   for i in range(len(worlds), 1 << bits)],
                       'feasible_assignment': [False] * bits}
    refs = {name: {'state': 'finite', 'objects': [], 'edges': []} for name in anchors}
    reasons = {name: set() for name in anchors}
    if not _coverage(spec['joint_coverage'], 'assumed_complete'):
        for entries in reasons.values():
            entries.add('joint_interpretation_coverage_unknown')
    world_ids, mappings, geometry_work = set(), [], 0
    for wi, world in enumerate(worlds):
        _fields(world, 'id basis_sha256 anchors')
        wid = identity(world['id'])
        require(wid not in world_ids, 'REFERENCE_IDENTITY', 'Duplicate joint-world identity')
        world_ids.add(wid)
        _digest(world['basis_sha256'])
        entries = _list(world['anchors'], 128, 1)
        names = []
        for entry in entries:
            _fields(entry, 'anchor_id unlisted_objects objects')
            names.append(identity(entry['anchor_id']))
        require(len(names) == len(set(names)) and set(names) == set(anchors),
                'REFERENCE_POPULATION', 'Every joint world must cover exactly the common anchor population')
        for entry in entries:
            name = entry['anchor_id']
            if not _coverage(entry['unlisted_objects'], 'excluded_by_assumption'):
                reasons[name].add('unlisted_matchable_objects_not_bounded')
            ids, members = set(), set()
            for oi, obj in enumerate(_list(entry['objects'], 128)):
                require(type(obj) is dict and obj.get('state') in ('point', 'unresolved'),
                        'REFERENCE_FIELDS', 'Explicit point or unresolved object state is required')
                _fields(obj, 'id members record_sha256 state ' + ('class xy timestamp_us' if obj['state'] == 'point' else 'reason'))
                oid = identity(obj['id'])
                require(oid not in ids, 'REFERENCE_IDENTITY', 'Repeated object identity within an interpretation')
                ids.add(oid)
                aliases = [identity(m) for m in _list(obj['members'], 32, 1)]
                require(len(aliases) == len(set(aliases)) and not members.intersection(aliases),
                        'REFERENCE_ALIAS', 'One observation proposal cannot represent two objects in one interpretation')
                members.update(aliases)
                _digest(obj['record_sha256'])
                if obj['state'] == 'unresolved':
                    _text(obj['reason'])
                    reasons[name].add('object_class_geometry_or_time_unresolved')
                    continue
                require(type(obj['class']) is str and obj['class'] in CLASSES | {'outside_target'},
                        'REFERENCE_CLASS', 'Unknown class is not silently treated as outside the target')
                point = _point(obj['xy'])
                time = timestamp(obj['timestamp_us'])
                if time != geometry[name]['time']:
                    reasons[name].add('object_time_differs_no_reconstruction_policy')
                    continue
                if obj['class'] == 'outside_target' or _distance2(point, geometry[name]['ego']) > 2500:
                    continue
                graph_id = 'w' + str(wi) + ':o' + str(oi)
                mappings.append({'anchor_id': name, 'world_id': wid, 'object_id': oid, 'graph_id': graph_id,
                                 'record_sha256': obj['record_sha256'], 'members': aliases})
                # Validate all remaining input objects, but stop materializing a graph
                # once its anchor must remain open. No partial finite graph is emitted.
                if reasons[name]:
                    continue
                if len(refs[name]['objects']) == 128:
                    reasons[name].add('compiled_graph_exceeds_core_resource_scope')
                    continue
                if geometry_work + len(geometry[name]['detections']) > MAX_GEOMETRY_COMPARISONS:
                    reasons[name].add('reference_geometry_work_limit')
                    continue
                geometry_work += len(geometry[name]['detections'])
                refs[name]['objects'].append({'id': graph_id, 'when': condition(wi)})
                for did, label, center in geometry[name]['detections']:
                    if label == obj['class'] and _distance2(center, point) < 4:
                        if len(refs[name]['edges']) == 2048:
                            reasons[name].add('compiled_graph_exceeds_core_resource_scope')
                            break
                        refs[name]['edges'].append({'detection': did, 'object': graph_id, 'when': []})
    for name, anchor in anchors.items():
        if any(anchor[role]['state'] != 'observed' for role in ('base', 'additions')):
            reasons[name].add('required_predictions_unavailable')
        anchor['reference'] = ({'state': 'open', 'reason': '; '.join(sorted(reasons[name]))}
                               if reasons[name] else refs[name])
    require(len(result['assumptions']) <= 30, 'REFERENCE_SIZE', 'No room to retain reference assumptions without dropping existing ones')
    result['assumptions'] += [
        'Finite point interpretations share one cohort-wide choice. Coverage is assumed, not independently established; continuous uncertainty requires an open reference.',
        'Reference input canonical SHA-256: ' + _hash(spec) + '. Nominal ego pose and strict 2 m matching; 50 m common object range.']
    contract.validate(result)
    require(len(contract.encoded(result)) <= contract.MAX_INPUT_BYTES,
            'REFERENCE_SIZE', 'Compiled input exceeds the core byte limit; no anchors or alternatives are clipped')
    receipt = {'artifact_id': 'reiyah.perception-reference.compilation', 'version': VERSION,
               'lifecycle_status': 'exploratory', 'compiled_input_sha256': _hash(result),
               'reference_semantic_sha256': _hash(spec), 'joint_world_count': len(worlds),
               'choice_variables': variables, 'world_encodings': [{'world_id': w['id'], 'when': condition(i)} for i, w in enumerate(worlds)],
               'anchor_reference_states': {name: a['reference']['state'] for name, a in anchors.items()},
               'open_reasons': {name: sorted(values) for name, values in reasons.items() if values},
               'geometry_comparisons_budgeted': geometry_work,
               'object_mapping': mappings, 'mapping_scope': 'proposed_graph_nodes_before_any_open_reference_fallback',
               'upstream_normalization': 'identified_trusted_input_not_recomputed_here',
               'physical_coverage': 'not_established', 'statistical_confidence_level': None,
               'authority_state': 'offline_research_only'}
    return result, receipt


def compile_files(*, reference_path, reference_sha256, comparison_path, normalizations_path, catalog_path):
    """Verify all four exact input identities before constructing model-relative graphs."""
    code = Path(__file__).read_bytes()
    spec = contract.load(reference_path, reference_sha256, validate_input=False)
    _header(spec)
    bindings = spec['inputs']
    case = contract.load(comparison_path, bindings['comparison_sha256'])
    normalizations = contract.load(normalizations_path, bindings['normalizations_sha256'],
                                   limit=16 << 20, validate_input=False)
    catalog = contract.load(catalog_path, bindings['catalog_sha256'], limit=128 << 20, validate_input=False)
    result, receipt = compile_model(spec, case, normalizations, catalog)
    require(Path(__file__).read_bytes() == code, 'REFERENCE_SOURCE_CHANGED', 'Compiler source changed during compilation')
    receipt['input_file_sha256'] = {'reference': reference_sha256, **bindings}
    receipt['compiler_source_sha256'] = hashlib.sha256(code).hexdigest()
    return result, receipt
