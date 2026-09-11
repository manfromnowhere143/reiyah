"""Prepare equal, private analysis operands from expected source assistance.

This pre-review stage preserves open references. It never interprets annotations,
admits reference constraints, releases assistance or evaluates a detector decision.
"""
import argparse
from copy import deepcopy
from decimal import Decimal, InvalidOperation
import hashlib
import os
from pathlib import Path
import stat
import sys

from tools import perception_assistance as assistance, perception_binding as binding
from tools.perception_decision import contract as decision
from tools.perception_decision.cli import atomic_write
from tools.perception_discovery import custody
from tools.perception_geometry.bind import read
from tools.perception_inputs.source_io import digest_value, require, snapshot
from tools.perception_observation import contract

ROOT = Path(__file__).resolve().parent.parent
GUIDES = ROOT/'research/perception-operands/0.1.0'
MAX_BYTES = 128 << 20
INPUT_FILES = frozenset(('common/assistance.json', 'common/READER.md',
    'operator/comparison.json', 'operator/normalizations.json',
    'operator/source-custody.json', 'operator/binding-report.json'))


def code_identities():
    paths = [Path(__file__), GUIDES/'ANALYST.md', GUIDES/'rules.json']
    return sorted(dict(assistance.code_identities() +
        [[str(p.relative_to(ROOT)), hashlib.sha256(p.read_bytes()).hexdigest()] for p in paths]).items())


def checked_bytes(path, expected, limit, size=None):
    require(digest_value(expected), 'OPERANDS_DIGEST', 'Require an expected SHA-256')
    fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
    with os.fdopen(fd, 'rb') as stream:
        require(stat.S_ISREG(os.fstat(stream.fileno()).st_mode), 'OPERANDS_SOURCE', 'Require a regular file')
        data = stream.read(limit+1)
    require(len(data) <= limit and (size is None or len(data) == size),
            'OPERANDS_SIZE', 'Input differs from its bounded byte size')
    require(hashlib.sha256(data).hexdigest() == expected, 'OPERANDS_DIGEST', 'Input differs from its expected bytes')
    return data


def load_assistance(path, expected, request_digest):
    path = Path(path)
    require(path.is_absolute() and path.is_dir() and not path.is_symlink(),
            'OPERANDS_SOURCE', 'Require an absolute assistance directory')
    receipt = decision.parse(checked_bytes(path/'PREPARATION.json', expected, 64 << 10))
    require(receipt.get('artifact_id') == 'reiyah.perception-assistance.preparation'
            and receipt.get('version') == '0.1.0' and receipt.get('status') == 'prepared_not_disclosed'
            and receipt.get('request_file_sha256') == request_digest,
            'OPERANDS_ASSISTANCE', 'Wrong assistance stage, version or comparison request')
    rows = receipt.get('files')
    require(type(rows) is list and len(rows) == len(INPUT_FILES), 'OPERANDS_ASSISTANCE', 'Incomplete assistance inventory')
    files, total = {}, 0
    for row in rows:
        contract.closed(row, ('path', 'byte_size', 'sha256'), 'OPERANDS_ASSISTANCE')
        name = row['path']
        require(type(name) is str and name in INPUT_FILES and name not in files,
                'OPERANDS_ASSISTANCE', 'Unexpected or repeated assistance entry')
        contract.integer(row['byte_size'], 0, MAX_BYTES, 'OPERANDS_SIZE')
        size = row['byte_size']
        total += size
        require(total <= MAX_BYTES, 'OPERANDS_SIZE', 'Assistance exceeds total input limit')
        parent = (path/name).parent
        require(parent.is_dir() and not parent.is_symlink(), 'OPERANDS_SOURCE', 'Require regular role directories')
        files[name] = checked_bytes(path/name, row['sha256'], size, size)
    require({p.name for p in path.iterdir()} == {'PREPARATION.json', 'common', 'operator'},
            'OPERANDS_ASSISTANCE', 'Unexpected assistance root entry')
    for role in ('common', 'operator'):
        require({p.name for p in (path/role).iterdir()} == {Path(n).name for n in INPUT_FILES if n.startswith(role+'/')},
                'OPERANDS_ASSISTANCE', 'Unexpected assistance role entry')
    return files, receipt


def restore_source(value):
    """Inverse of the pinned assistance custody's explicit decimal encoding."""
    if type(value) is dict:
        if set(value) == {'source_decimal'}:
            text = value['source_decimal']
            require(type(text) is str and 0 < len(text) <= 128, 'OPERANDS_SOURCE', 'Invalid source decimal')
            try:
                return Decimal(text)
            except InvalidOperation as exc:
                raise decision.Invalid('OPERANDS_SOURCE', 'Invalid source decimal') from exc
        return {k: restore_source(v) for k, v in value.items()}
    if type(value) is list:
        return [restore_source(v) for v in value]
    return value


def source_projection(common, source, catalog, bound, manifest):
    labels = source['configuration_roles']
    require(set(labels) == {'base', 'camera'} and set(labels.values()) == set(assistance.LABELS),
            'OPERANDS_ROLES', 'Require two distinct declared configuration labels')
    selected, occurrences = assistance.sources.selected_frames(catalog, bound['windows'], manifest)
    require([f['id'] for f in common['frames']] == [f['frame_id'] for f in selected.values()]
            == [f['frame_id'] for f in source['frames']],
            'OPERANDS_POPULATION', 'Assistance frame population or order differs')
    require(len(common['windows']) == len(occurrences), 'OPERANDS_POPULATION', 'Assistance window population differs')
    for mapping, expected, window in zip(bound['windows'], occurrences, common['windows']):
        require(all(decision.encoded(window[k]) == decision.encoded(v) for k, v in expected.items())
                and window['comparison_frame_id'] == selected[mapping['sample_token']]['frame_id'],
                'OPERANDS_POPULATION', 'Assistance window, clock or comparison frame differs')
    outputs = {}
    for (sample, expected), public, private in zip(selected.items(), common['frames'], source['frames']):
        require(private['sample_token'] == sample and private['scene_token'] == expected['scene_token']
                and type(private['timestamp_us']) is int and private['timestamp_us'] == expected['anchor_timestamp_us'],
                'OPERANDS_POPULATION', 'Assistance source clock or membership differs')
        outputs[sample] = {}
        require(set(public['predictions']) == set(assistance.LABELS), 'OPERANDS_ROLES', 'Unexpected prediction configuration')
        for role, label in labels.items():
            stored = private['predictions'][role]
            require(decision.encoded(stored['descriptor']) == decision.encoded(expected[role]),
                    'OPERANDS_SOURCE', 'Prediction descriptor differs from bound catalog')
            output = restore_source(stored['full_rows'])
            require(type(output) is dict and output.get('state') == expected[role]['state'],
                    'OPERANDS_SOURCE', 'Restored prediction availability contradicts its source descriptor')
            if output['state'] == 'observed':
                contract.closed(output, ('state', 'value'), 'OPERANDS_SOURCE')
                count = expected[role]['row_count']
                require(type(count) is int and type(output['value']) is list and len(output['value']) == count,
                        'OPERANDS_SOURCE', 'Restored prediction count contradicts its source descriptor')
                assistance.sources.inventory.validate_predictions(output['value'], sample)
                for row in output['value']:
                    contract.closed(row, assistance.sources.PREDICTION_FIELDS, 'OPERANDS_SOURCE')
            else:
                contract.closed(output, ('state', 'reason'), 'OPERANDS_SOURCE')
                require(output['reason'] == expected[role]['reason'],
                        'OPERANDS_SOURCE', 'Unavailable source reason differs from its descriptor')
            projected = assistance.sources.prediction_rows(output, public['id']+'-'+label)
            require(decision.encoded(projected) == decision.encoded(public['predictions'][label]),
                    'OPERANDS_ROWS', 'Common prediction rows differ from pinned source rows')
            outputs[sample][role] = output
    return labels, selected, outputs


def open_stage(case):
    decision.validate(case)
    require(not case['model']['variables'] and not case['model']['clauses']
            and all(a['reference']['state'] == 'open' for a in case['anchors']),
            'OPERANDS_REFERENCE_STAGE', 'This stage requires an open reference and no admitted joint model')


def project(case, normalizations, mappings, selected, labels):
    open_stage(case)
    by_anchor = {m['anchor_id']: m for m in mappings}
    normals = {n['anchor_id']: n for n in normalizations}
    result = deepcopy(case)
    result.update(comparison_id='reiyah.prepared-analysis', cohort_id='bound-comparison-anchors')
    anchors, private_maps = [], []
    for original, anchor in zip(case['anchors'], result['anchors']):
        mapping, normal = by_anchor[original['id']], normals[original['id']]
        frame = selected[mapping['sample_token']]['frame_id']
        anchor['id'] = mapping['window_id']
        nodes, normalized, translations = {}, [], []

        def row_id(role, index):
            return f'{frame}-{labels[role]}-row-{index+1:04d}'

        for entry in normal['qualified_records']:
            record, old = entry['record'], entry['detection']
            identifier = row_id(record['source'], record['source_index'])
            neutral = {'policy': normal['policy'], 'frame_id': frame,
                       'configuration_id': labels[record['source']], 'row_id': identifier,
                       **{key: record[key] for key in ('class', 'xy', 'score')}}
            node = {'id': identifier, 'record_sha256': hashlib.sha256(decision.encoded(neutral)).hexdigest()}
            nodes[old['id']] = node
            normalized.append({'detection': node, 'record': neutral})
            translations.append({'original': old, 'neutral': node})
        for role in ('base', 'additions'):
            if anchor[role]['state'] == 'observed':
                anchor[role]['value'] = [nodes[n['id']] for n in original[role]['value']]
        trace = [{'row_id': row_id(t['source'], t['source_index']), 'configuration_id': labels[t['source']],
                  **{key: t[key] for key in ('score_eligible', 'range_eligible', 'retention')},
                  'blocked_by': None if t['blocked_by'] is None else nodes[t['blocked_by']]['id']}
                 for t in normal['trace']]
        anchors.append({'anchor_id': anchor['id'], 'frame_id': frame, 'time_offset_us': 0,
                        'nominal_global_ego_xy': normal['ego_xy'],
                        'source_availability': {labels[r]: s for r, s in normal['source_availability'].items()},
                        'input_counts': {labels[r]: n for r, n in normal['input_counts'].items()},
                        'qualified_records': normalized, 'trace': trace,
                        'unused_prediction_fields': normal['unused_prediction_fields']})
        private_maps.append({'original_anchor_id': original['id'], 'neutral_anchor_id': anchor['id'],
                             'frame_id': frame, 'sample_token': mapping['sample_token'], 'detections': translations})
    decision.validate(result)
    return result, anchors, private_maps


def retained_summary(case, role):
    observed = [a for a in case['anchors'] if a[role]['state'] == 'observed']
    count = sum(len(a[role]['value']) for a in observed)
    if len(observed) == len(case['anchors']):
        return {'state': 'observed', 'value': count}
    return {'state': 'unavailable', 'observed_partial_count': count,
            'unavailable_anchors': len(case['anchors'])-len(observed)}


def materialize(request, files, receipt):
    code, runtime = code_identities(), binding.runtime()
    open_stage(decision.parse(files['operator/comparison.json']))
    bound = binding.build(request)
    require(decision.encoded(bound) == files['operator/binding-report.json'],
            'OPERANDS_BINDING', 'Fresh population/asset binding differs from expected assistance')
    require(receipt['binding_inputs'] == bound['inputs'], 'OPERANDS_BINDING', 'Assistance inputs differ')
    case = read(request['comparison'], binding.LIMITS['comparison'])
    normals = read(request['normalizations'], binding.LIMITS['normalizations'])
    require(decision.encoded(case) == files['operator/comparison.json']
            and decision.encoded(normals) == files['operator/normalizations.json'],
            'OPERANDS_BINDING', 'Comparison or normalization bytes differ')
    common = decision.parse(files['common/assistance.json'])
    source = decision.parse(files['operator/source-custody.json'])
    catalog = read(request['catalog'], binding.LIMITS['catalog'])
    manifest = custody.manifest(request['package']['path'], request['package']['seal_sha256'])
    require(common['observation_package'] == receipt['observation_package']
            == {'package_id': manifest['package_id'], 'seal_sha256': request['package']['seal_sha256']},
            'OPERANDS_BINDING', 'Assistance observation package differs')
    labels, selected, outputs = source_projection(common, source, catalog, bound, manifest)
    assistance.normalize_check(case, normals, catalog, outputs, bound['windows'])
    neutral, anchors, mapping = project(case, normals, bound['windows'], selected, labels)
    comparison_bytes = decision.encoded(neutral)
    rules = (GUIDES/'rules.json').read_bytes()
    operands = {'artifact_id': 'reiyah.perception-operands.common', 'version': '0.1.0',
        'status': 'prepared_not_disclosed', 'comparison_sha256': hashlib.sha256(comparison_bytes).hexdigest(),
        'assistance_sha256': hashlib.sha256(files['common/assistance.json']).hexdigest(),
        'rules_sha256': hashlib.sha256(rules).hexdigest(),
        'configuration_roles': {'existing': labels['base'], 'candidate': labels['camera'],
                                'augmented': 'all_existing_retained_plus_retained_candidate'},
        'reference_stage': 'open_before_review_no_source_annotations_admitted', 'anchors': anchors}
    prepared = {'common/comparison.json': comparison_bytes, 'common/operands.json': decision.encoded(operands),
                'common/rules.json': rules, 'common/ANALYST.md': (GUIDES/'ANALYST.md').read_bytes(),
                'common/assistance.json': files['common/assistance.json'],
                'common/SOURCE_READER.md': files['common/READER.md'],
                'operator/custody.json': decision.encoded({'artifact_id': 'reiyah.perception-operands.custody',
                    'version': '0.1.0', 'configuration_roles': labels, 'renamings': mapping,
                    'original_comparison_sha256': request['comparison']['sha256'],
                    'bound_inputs': bound['inputs']})}
    require(sum(map(len, prepared.values())) <= MAX_BYTES, 'OPERANDS_SIZE', 'Prepared output exceeds limit')
    for spec in bound['inputs'].values():
        with snapshot(spec):
            pass
    require(code == code_identities() and runtime == binding.runtime(),
            'OPERANDS_CODE_CHANGED', 'Implementation, rules or runtime changed')
    summary = {'comparison_anchors': len(anchors), 'context_keyframes': len(selected),
               'mapped_rows': sum(len(a['trace']) for a in anchors),
               'qualified_records': sum(len(a['qualified_records']) for a in anchors),
               'retained': {role: retained_summary(neutral, role) for role in ('base', 'additions')}}
    return prepared, {'source_identities': code, 'runtime': runtime, 'summary': summary}


def run(request_path, expected, assistance_path, preparation_digest, output):
    output = Path(output)
    require(output.is_absolute() and output.parent.is_dir(), 'OPERANDS_OUTPUT', 'Require a private absolute output')
    require(not os.path.lexists(output), 'OUTPUT_EXISTS', 'Refuse an existing preparation identity')
    request = decision.load(request_path, expected, binding.REQUEST_LIMIT, validate_input=False)
    binding.request_contract(request)
    for forbidden in (ROOT, Path(assistance_path).resolve(), Path(request['package']['path']).resolve()):
        require(not output.resolve().is_relative_to(forbidden), 'OPERANDS_OUTPUT', 'Output overlaps code or source inputs')
    try:
        original, receipt = load_assistance(assistance_path, preparation_digest, expected)
        files, context = materialize(request, original, receipt)
        again, _ = load_assistance(assistance_path, preparation_digest, expected)
        require(again == original, 'OPERANDS_CHANGED', 'Assistance changed during preparation')
    except (KeyError, TypeError, AttributeError, IndexError, RecursionError) as exc:
        raise decision.Invalid('OPERANDS_INPUT', 'Malformed required assistance structure') from exc
    decision.load(request_path, expected, binding.REQUEST_LIMIT, validate_input=False)
    record = {'artifact_id': 'reiyah.perception-operands.preparation', 'version': '0.1.0',
        'status': 'prepared_not_disclosed', 'request_file_sha256': expected,
        'assistance_preparation_sha256': preparation_digest, **context,
        'files': [{'path': n, 'byte_size': len(b), 'sha256': hashlib.sha256(b).hexdigest()} for n, b in sorted(files.items())],
        'human_review_performed': False, 'assisted_evidence_released': False, 'decision_evaluated': False,
        'reference_constraints_admitted': False, 'study_selection_performed': False,
        'physical_reference_coverage': 'not_established', 'blinding': 'not_guaranteed_free_text_retained'}
    output.mkdir(mode=0o700)
    for role in ('common', 'operator'):
        (output/role).mkdir(mode=0o700)
    for name, data in sorted(files.items()):
        atomic_write(output/name, data)
    assistance.verify_files(output, files)
    data = decision.encoded(record)
    atomic_write(output/'PREPARATION.json', data)
    return {'status': record['status'], 'preparation_sha256': hashlib.sha256(data).hexdigest(),
            'summary': context['summary'], 'decision_evaluated': False, 'assisted_evidence_released': False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binding-request', type=Path, required=True)
    parser.add_argument('--binding-request-sha256', required=True)
    parser.add_argument('--assistance', type=Path, required=True)
    parser.add_argument('--preparation-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = run(args.binding_request, args.binding_request_sha256, args.assistance, args.preparation_sha256, args.output)
        sys.stdout.buffer.write(decision.encoded(result))
        return 0
    except decision.Invalid as exc:
        diagnostic = exc.diagnostic()
    except OSError as exc:
        diagnostic = {'code': 'IO_ERROR', 'detail': str(exc)}
    sys.stderr.buffer.write(decision.encoded({'status': 'invalid', 'decision_evaluated': False, **diagnostic}))
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
