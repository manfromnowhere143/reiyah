"""Prepare common operands without losing a selected admission's joint model.

Private later-stage material: the full admission and canonical source identities
are deliberately retained. Preparing or checking it does not disclose anything.
"""
import argparse
from copy import deepcopy
import hashlib
import os
from pathlib import Path
import sys

from tools import perception_admission as admission, perception_binding as binding
from tools import perception_operands as operands
from tools.perception_decision import contract
from tools.perception_decision.cli import atomic_write
from tools.perception_inputs.source_io import require

ROOT = Path(__file__).resolve().parent.parent
GUIDES = ROOT/'research/perception-reviewed-operands/0.1.0'
VERSION = '0.1.0'
MAX_BYTES = 256 << 20
RECEIPT_LIMIT = 128 << 10


def digest(data):
    return hashlib.sha256(data).hexdigest()


def code_identities():
    paths = [Path(__file__), GUIDES/'ANALYST.md']
    return sorted(dict(operands.code_identities() + admission.code_identities() +
        [[str(p.relative_to(ROOT)), digest(p.read_bytes())] for p in paths]).items())


def equal(left, right, code, detail):
    # Canonical bytes distinguish Boolean/integer substitutions as well as values.
    require(contract.encoded(left) == contract.encoded(right), code, detail)


def project(compiled, neutral_open, mappings):
    """Rename only anchor/detection identities; world/object/edge conditions stay intact."""
    contract.validate(compiled)
    result = deepcopy(compiled)
    result['comparison_id'] = neutral_open['comparison_id']
    result['cohort_id'] = neutral_open['cohort_id']
    by_anchor = {m['original_anchor_id']: m for m in mappings}
    for anchor in result['anchors']:
        mapping = by_anchor[anchor['id']]
        nodes = {row['original']['id']: row['neutral'] for row in mapping['detections']}
        anchor['id'] = mapping['neutral_anchor_id']
        for role in ('base', 'additions'):
            if anchor[role]['state'] == 'observed':
                anchor[role]['value'] = [deepcopy(nodes[n['id']]) for n in anchor[role]['value']]
        if anchor['reference']['state'] == 'finite':
            for edge in anchor['reference']['edges']:
                edge['detection'] = nodes[edge['detection']]['id']
    check_projection(compiled, result, neutral_open, mappings)
    return result


def check_projection(compiled, neutral, neutral_open, mappings):
    """Inverse structural check, independent of matching or endpoint agreement.

    The caller supplies mappings already checked against source normalization.
    This is an integrity check; admission, parsing and source semantics are shared.
    """
    contract.validate(compiled)
    contract.validate(neutral)
    restored = deepcopy(neutral)
    by_neutral = {m['neutral_anchor_id']: m for m in mappings}
    require(len(by_neutral) == len(mappings) == len(compiled['anchors']),
            'REVIEWED_MAPPING', 'Anchor mapping must be bijective')
    equal([a['id'] for a in neutral['anchors']], [a['id'] for a in neutral_open['anchors']],
          'REVIEWED_MAPPING', 'Neutral anchor population or order changed')
    equal([neutral['comparison_id'], neutral['cohort_id']],
          [neutral_open['comparison_id'], neutral_open['cohort_id']],
          'REVIEWED_MAPPING', 'Neutral comparison identity changed')
    restored['comparison_id'] = compiled['comparison_id']
    restored['cohort_id'] = compiled['cohort_id']
    for anchor, expected_open in zip(restored['anchors'], neutral_open['anchors']):
        mapping = by_neutral[anchor['id']]
        inverse = {row['neutral']['id']: row for row in mapping['detections']}
        require(len(inverse) == len(mapping['detections']) ==
                len({row['original']['id'] for row in mapping['detections']}),
                'REVIEWED_MAPPING', 'Detection mapping must be bijective, including equal-valued rows')
        anchor['id'] = mapping['original_anchor_id']
        for role in ('base', 'additions'):
            equal(anchor[role], expected_open[role], 'REVIEWED_MAPPING',
                  'Retained detections, digests or availability changed')
            if anchor[role]['state'] == 'observed':
                anchor[role]['value'] = [deepcopy(inverse[n['id']]['original']) for n in anchor[role]['value']]
        if anchor['reference']['state'] == 'finite':
            for edge in anchor['reference']['edges']:
                require(edge['detection'] in inverse, 'REVIEWED_MAPPING', 'Unmapped edge endpoint')
                edge['detection'] = inverse[edge['detection']]['original']['id']
    equal(restored, compiled, 'REVIEWED_SEMANTICS',
          'Inverse projection differs from the complete admitted comparison')


def materialize(*, binding_request, binding_request_sha256, admission_request,
                admission_request_sha256, admission_report, admission_report_sha256,
                assistance, preparation_sha256):
    """Recheck separately selected sources before producing any output bytes."""
    code, runtime = code_identities(), binding.runtime()
    selected = [(binding_request, binding_request_sha256, binding.REQUEST_LIMIT),
                (admission_request, admission_request_sha256, admission.REQUEST_LIMIT),
                (admission_report, admission_report_sha256, admission.REPORT_LIMIT)]
    for path, _, _ in selected:
        binding.absolute_path(str(path))
    raw_binding, raw_request, raw_report = [operands.checked_bytes(*row) for row in selected]
    request, review_request = contract.parse(raw_binding), contract.parse(raw_request)
    binding.request_contract(request)
    admission.request_contract(review_request)
    equal(review_request['binding_request'],
          {'path': str(binding_request), 'byte_size': len(raw_binding), 'sha256': binding_request_sha256},
          'REVIEWED_BINDING', 'Admission selects a different binding request')
    expected_report = admission.build(review_request)
    expected_report['request_file_sha256'] = admission_request_sha256
    require(contract.encoded(expected_report) == raw_report, 'REVIEWED_ADMISSION',
            'Selected admission differs from fresh contents-checked reconstruction')
    original, receipt = operands.load_assistance(assistance, preparation_sha256, binding_request_sha256)
    prepared, context = operands.materialize(request, original, receipt)
    equal(expected_report['binding'], contract.parse(original['operator/binding-report.json']),
          'REVIEWED_BINDING', 'Admission and assistance have different population, clock or assets')
    open_case = contract.parse(prepared['common/comparison.json'])
    custody = contract.parse(prepared['operator/custody.json'])
    mappings = custody['renamings']
    compiled = expected_report['compiled_input']
    neutral = project(compiled, open_case, mappings)
    neutral_bytes = contract.encoded(neutral)
    require(len(neutral_bytes) <= contract.MAX_INPUT_BYTES, 'REVIEWED_SIZE',
            'Renamed comparison exceeds the existing core input limit')
    renamings = contract.encoded({'artifact_id': 'reiyah.perception-reviewed-operands.renamings',
        'version': VERSION, 'admission_report_sha256': admission_report_sha256,
        'original_compiled_sha256': digest(contract.encoded(compiled)),
        'neutral_comparison_sha256': digest(neutral_bytes), 'anchors': mappings,
        'unchanged_identities': ['model_variables', 'world_ids', 'graph_object_ids', 'proposal_members'],
        'world_encodings': expected_report['compilation']['world_encodings'],
        'object_mapping': expected_report['compilation']['object_mapping'],
        'object_mapping_scope': expected_report['compilation']['mapping_scope']})
    common = contract.parse(prepared['common/operands.json'])
    rules = contract.parse(prepared['common/rules.json'])
    rules.update(artifact_id='reiyah.perception-reviewed-operands.rules',
        reference_stage='contents_checked_conditional_review',
        inherited_open_rules_sha256=digest(prepared['common/rules.json']))
    prepared['common/rules.json'] = contract.encoded(rules)
    common.update(artifact_id='reiyah.perception-reviewed-operands.common', version=VERSION,
        comparison_sha256=digest(neutral_bytes), admission_report_sha256=admission_report_sha256,
        rules_sha256=digest(prepared['common/rules.json']),
        renamings_sha256=digest(renamings), reference_stage='contents_checked_conditional_review',
        physical_reference_coverage='not_established')
    prepared.update({'common/comparison.json': neutral_bytes,
        'common/operands.json': contract.encoded(common), 'common/admission.json': raw_report,
        'common/renamings.json': renamings, 'common/ANALYST.md': (GUIDES/'ANALYST.md').read_bytes()})
    require(sum(map(len, prepared.values())) <= MAX_BYTES, 'REVIEWED_SIZE', 'Complete output exceeds its byte limit')
    for row, before in zip(selected, (raw_binding, raw_request, raw_report)):
        require(operands.checked_bytes(*row) == before, 'REVIEWED_CHANGED', 'Selected source changed')
    again, _ = operands.load_assistance(assistance, preparation_sha256, binding_request_sha256)
    require(again == original, 'REVIEWED_CHANGED', 'Assistance changed during preparation')
    require(code == code_identities() and runtime == binding.runtime(),
            'REVIEWED_CODE_CHANGED', 'Implementation or runtime changed')
    record = {'artifact_id': 'reiyah.perception-reviewed-operands.preparation', 'version': VERSION,
        'status': 'prepared_not_disclosed', 'binding_request_sha256': binding_request_sha256,
        'admission_request_sha256': admission_request_sha256, 'admission_report_sha256': admission_report_sha256,
        'assistance_preparation_sha256': preparation_sha256, 'source_identities': code, 'runtime': runtime,
        'summary': context['summary'] | {'joint_worlds': expected_report['compilation']['joint_world_count'],
            'reference_states': {a['id']: a['reference']['state'] for a in neutral['anchors']}},
        'files': [{'path': n, 'byte_size': len(b), 'sha256': digest(b)} for n, b in sorted(prepared.items())],
        'decision_evaluated': False, 'human_review_performed': False, 'assisted_evidence_released': False,
        'study_selection_performed': False, 'physical_reference_coverage': 'not_established',
        'identity_and_blinding': 'not_established_full_private_admission_and_custody_retained'}
    require(len(contract.encoded(record)) <= RECEIPT_LIMIT, 'REVIEWED_SIZE', 'Receipt exceeds its byte limit')
    return prepared, record


def destination(output, inputs):
    output = Path(output)
    require(output.is_absolute() and output.parent.is_dir(), 'REVIEWED_OUTPUT', 'Require an absolute private output')
    require(not os.path.lexists(output), 'OUTPUT_EXISTS', 'Refuse an existing preparation identity')
    request = contract.parse(operands.checked_bytes(inputs['binding_request'],
        inputs['binding_request_sha256'], binding.REQUEST_LIMIT))
    binding.request_contract(request)
    for forbidden in (ROOT, Path(inputs['assistance']).resolve(), Path(request['package']['path']).resolve()):
        require(not output.resolve().is_relative_to(forbidden), 'REVIEWED_OUTPUT', 'Output overlaps code or source inputs')
    return output


def run(output, **inputs):
    output = destination(output, inputs)
    files, record = materialize(**inputs)
    output.mkdir(mode=0o700)
    for role in ('common', 'operator'):
        (output/role).mkdir(mode=0o700)
    for name, data in sorted(files.items()):
        atomic_write(output/name, data)
    operands.assistance.verify_files(output, files)
    atomic_write(output/'PREPARATION.json', contract.encoded(record))
    return {'status': record['status'], 'preparation_sha256': digest(contract.encoded(record)),
            'summary': record['summary'], 'decision_evaluated': False, 'assisted_evidence_released': False}


def check(packet, packet_sha256, **inputs):
    """Check a selected packet against freshly reconstructed, separately selected sources."""
    packet = Path(packet)
    require(packet.is_absolute() and packet.is_dir() and not packet.is_symlink(),
            'REVIEWED_PACKET', 'Require an absolute regular packet directory')
    raw = operands.checked_bytes(packet/'PREPARATION.json', packet_sha256, RECEIPT_LIMIT)
    files, expected = materialize(**inputs)
    require(raw == contract.encoded(expected), 'REVIEWED_PACKET', 'Receipt differs from the selected source preparation')
    require({p.name for p in packet.iterdir()} == {'PREPARATION.json', 'common', 'operator'},
            'REVIEWED_PACKET', 'Unexpected packet entries')
    for role in ('common', 'operator'):
        parent = packet/role
        require(parent.is_dir() and not parent.is_symlink(), 'REVIEWED_PACKET', 'Require regular role directories')
        require({p.name for p in parent.iterdir()} == {Path(n).name for n in files if n.startswith(role+'/')},
                'REVIEWED_PACKET', 'Unexpected role entries')
    for name, data in files.items():
        operands.checked_bytes(packet/name, digest(data), len(data), len(data))
    operands.checked_bytes(packet/'PREPARATION.json', packet_sha256, RECEIPT_LIMIT)
    return {'status': 'checked_against_selected_sources', 'preparation_sha256': packet_sha256,
            'decision_evaluated': False, 'physical_reference_coverage': 'not_established'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    for action in ('prepare', 'check'):
        command = sub.add_parser(action)
        for name in ('binding-request', 'admission-request', 'admission-report'):
            command.add_argument('--'+name, type=Path, required=True)
            command.add_argument('--'+name+'-sha256', required=True)
        command.add_argument('--assistance', type=Path, required=True)
        command.add_argument('--preparation-sha256', required=True)
        if action == 'prepare':
            command.add_argument('--output', type=Path, required=True)
        else:
            command.add_argument('--packet', type=Path, required=True)
            command.add_argument('--packet-sha256', required=True)
    args = vars(parser.parse_args(argv))
    action = args.pop('action')
    try:
        result = run(**args) if action == 'prepare' else check(**args)
        sys.stdout.buffer.write(contract.encoded(result))
        return 0
    except contract.Invalid as exc:
        diagnostic = exc.diagnostic()
    except (KeyError, TypeError, AttributeError, IndexError, RecursionError) as exc:
        diagnostic = {'code': 'REVIEWED_INPUT', 'detail': 'Malformed required structure: '+type(exc).__name__}
    except OSError as exc:
        diagnostic = {'code': 'IO_ERROR', 'detail': str(exc)}
    sys.stderr.buffer.write(contract.encoded({'status': 'invalid', 'decision_evaluated': False, **diagnostic}))
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
