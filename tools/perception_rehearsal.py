"""Prepare private, unassigned materials for a development review rehearsal.

This packages existing interfaces for people. It performs no review, assisted
disclosure, reference admission, study selection or decision calculation.
"""
import argparse
import csv
import hashlib
import io
import os
from pathlib import Path
import sys

from tools import perception_binding as binding
from tools.perception_decision import contract as decision
from tools.perception_decision.cli import atomic_write
from tools.perception_discovery import custody, records
from tools.perception_inputs.sensors import CHANNELS
from tools.perception_inputs.source_io import require, snapshot
from tools.perception_observation import package

ROOT = Path(__file__).resolve().parent.parent
GUIDES = ROOT / 'research/perception-rehearsal/0.1.0'
TEMPLATES = ('OPERATOR.md', 'DISCOVERY_REVIEWER.md', 'ANALYST.md', 'plan.json')
MAX_KIT = 256 << 20
INDEX_COLUMNS = ('window_id', 'capture_id', 'channel', 'time_offset_us', 'evidence_state',
                 'asset_relative_path', 'sensor_to_anchor_ego_state', 'intrinsic_state')
EFFORT_COLUMNS = ('segment_id', 'participant_id', 'stage', 'role', 'work_scope', 'category',
                  'started_at_utc', 'ended_at_utc',
                  'person_seconds', 'compute_wall_seconds', 'compute_max_rss_bytes',
                  'measurement_basis', 'artifact_sha256', 'notes')


def code_identities():
    paths = [Path(__file__), *(GUIDES / name for name in TEMPLATES)]
    return sorted(binding.code_identities() +
                  [[str(p.relative_to(ROOT)), hashlib.sha256(p.read_bytes()).hexdigest()] for p in paths])


def table(columns, rows):
    out = io.StringIO(newline='')
    writer = csv.writer(out, lineterminator='\n')
    writer.writerow(columns)
    writer.writerows(rows)
    return out.getvalue().encode('utf-8')


def capture_index(manifest):
    captures = {c['id']: c for c in manifest['captures']}
    rows = []
    for window in manifest['windows']:
        for channel in CHANNELS:
            for occurrence in window['channels'][channel]['captures']:
                c = captures[occurrence['capture_id']]
                evidence = c['evidence']
                rows.append((window['id'], c['id'], channel, occurrence['time_offset_us'],
                             evidence['state'], evidence.get('asset', {}).get('filename', ''),
                             occurrence['sensor_to_anchor_ego']['state'], c['intrinsic']['state']))
    return table(INDEX_COLUMNS, rows)


def conclusion_template():
    return {'artifact_id': 'reiyah.perception-rehearsal.conclusion-draft', 'version': '0.1.0',
            'reviewer_id': None, 'stage': None, 'completed_at': {'state': 'unrecorded'},
            'status': 'not_evaluated', 'evidence_descriptors': [], 'method_and_version': None,
            'population_and_weights': None, 'loss_and_tolerance': None,
            'reference_interpretations_and_joint_constraints': None,
            'assumptions_and_unresolved_evidence': None,
            'lower': None, 'upper': None, 'preference': 'not_evaluated',
            'improvement_criterion': 'not_evaluated', 'derivation_and_artifacts': [],
            'decision_relevant_next_observation': None, 'limitations': None}


def materialize(request, rehearsal_id):
    """Build draft bytes from freshly checked sources; no filesystem writes."""
    records.neutral(rehearsal_id)
    code, runtime = code_identities(), binding.runtime()
    bound = binding.build(request)
    expected = request['package']['seal_sha256']
    manifest = custody.manifest(request['package']['path'], expected)
    files = {'operator/START_HERE.md': (GUIDES / 'OPERATOR.md').read_bytes(),
             'operator/binding-report.json': decision.encoded(bound),
             'operator/plan.json': (GUIDES / 'plan.json').read_bytes(),
             'operator/effort.csv': table(EFFORT_COLUMNS, []),
             'analysis/ANALYST.md': (GUIDES / 'ANALYST.md').read_bytes(),
             'analysis/conventional-conclusion.draft.json': decision.encoded(conclusion_template()),
             'analysis/engine-conclusion.draft.json': decision.encoded(conclusion_template())}
    # A role's record identity is reproducible for this preparation. It is not a
    # reviewer identity, source token, random cohort seed or global registry key.
    index = capture_index(manifest)
    package_identity = decision.encoded({'package_id': manifest['package_id'], 'seal_sha256': expected})
    for role in ('discovery-1', 'discovery-2'):
        record_id = hashlib.sha256(decision.encoded([rehearsal_id, expected, role])).hexdigest()[:32]
        draft = records.draft(manifest, expected, record_id)
        records.validate(draft, manifest, expected)
        record_bytes = decision.encoded(draft)
        require(len(record_bytes) <= records.MAX_RECORD, 'REHEARSAL_LIMIT', 'Draft exceeds record limit')
        files[f'{role}/START_HERE.md'] = (GUIDES / 'DISCOVERY_REVIEWER.md').read_bytes()
        files[f'{role}/package-identity.json'] = package_identity
        files[f'{role}/capture-index.csv'] = index
        files[f'{role}/discovery-record.draft.json'] = record_bytes
    roles = ('discovery-1', 'discovery-2', 'engine-analyst', 'conventional-analyst', 'adjudicator')
    files['operator/assignments.draft.json'] = decision.encoded({
        'artifact_id': 'reiyah.perception-rehearsal.assignments-draft', 'version': '0.1.0',
        'rehearsal_id': rehearsal_id, 'status': 'unassigned',
        'roles': {role: {'person_identity': None, 'competence_basis': None, 'availability': 'unconfirmed',
                        'conflicts_and_prior_exposure': 'unrecorded'} for role in roles},
        'staged_delivery_records': [], 'assistance_release': 'not_performed'})
    files['operator/binding-request.json'] = decision.encoded(request)
    # Fresh before/after checks guard preparation against ordinary input changes.
    # This is not an operating-system isolation or human blinding guarantee.
    for spec in bound['inputs'].values():
        with snapshot(spec):
            pass
    package.verify(request['package']['path'], expected)
    require(code == code_identities() and runtime == binding.runtime(),
            'REHEARSAL_CODE_CHANGED', 'Code, instructions or runtime changed during preparation')
    require(sum(map(len, files.values())) <= MAX_KIT, 'REHEARSAL_LIMIT', 'Preparation exceeds byte limit')
    return files, {'source_identities': code, 'runtime': runtime, 'summary': bound['summary'],
                   'package': bound['package']}


def run(request_path, expected, rehearsal_id, output):
    output = Path(output)
    require(output.is_absolute(), 'REHEARSAL_OUTPUT', 'Require an absolute private output directory')
    require(not os.path.lexists(output), 'OUTPUT_EXISTS', 'Preparation identity already exists')
    request = decision.load(request_path, expected, binding.REQUEST_LIMIT, validate_input=False)
    binding.request_contract(request)
    for forbidden in (ROOT, Path(request['package']['path']).resolve()):
        require(not output.resolve().is_relative_to(forbidden), 'REHEARSAL_OUTPUT',
                'Preparation must be outside the source tree and observation package')
    require(output.parent.is_dir(), 'REHEARSAL_OUTPUT', 'Output parent must already exist')
    files, context = materialize(request, rehearsal_id)
    decision.load(request_path, expected, binding.REQUEST_LIMIT, validate_input=False)
    receipt = {'artifact_id': 'reiyah.perception-rehearsal.preparation', 'version': '0.1.0',
               'rehearsal_id': rehearsal_id, 'status': 'unassigned_preparation',
               'request_file_sha256': expected, **context,
               'files': [{'path': path, 'byte_size': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
                         for path, data in sorted(files.items())],
               'human_review_performed': False, 'assisted_evidence_released': False,
               'study_selection_performed': False, 'decision_evaluated': False,
               'reviewer_independence': 'not_established', 'physical_reference_coverage': 'not_established',
               'prior_exposure_history': 'coordinator_premise_not_verified_by_preparation',
               'completion_scope': 'draft_file_preparation_only'}
    # A fresh directory and completion record written last preserve interruption
    # as a partial preparation. No existing folder is overwritten or cleaned up.
    output.mkdir(mode=0o700)
    for role in ('operator', 'analysis', 'discovery-1', 'discovery-2'):
        (output / role).mkdir(mode=0o700)
    for name, data in sorted(files.items()):
        atomic_write(output / name, data)
    roles = {'operator', 'analysis', 'discovery-1', 'discovery-2'}
    require({p.name for p in output.iterdir()} == roles, 'REHEARSAL_OUTPUT_CHANGED',
            'Unexpected entry in the preparation directory')
    for role in roles:
        directory = output / role
        expected_names = {Path(name).name for name in files if name.startswith(role + '/')}
        require(not directory.is_symlink() and directory.is_dir()
                and {p.name for p in directory.iterdir()} == expected_names,
                'REHEARSAL_OUTPUT_CHANGED', 'Unexpected entry in a role directory')
    for spec in receipt['files']:
        path = output / spec['path']
        require(not path.is_symlink() and path.is_file(), 'REHEARSAL_OUTPUT_CHANGED',
                'A draft path is not a regular file')
        data = path.read_bytes()
        require(len(data) == spec['byte_size'] and hashlib.sha256(data).hexdigest() == spec['sha256'],
                'REHEARSAL_OUTPUT_CHANGED', 'A written draft changed before completion')
    encoded = decision.encoded(receipt)
    atomic_write(output / 'PREPARATION.json', encoded)
    return {'status': receipt['status'], 'preparation_sha256': hashlib.sha256(encoded).hexdigest(),
            'files': len(files), 'summary': context['summary'], 'human_review_performed': False,
            'assisted_evidence_released': False, 'decision_evaluated': False}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--binding-request', type=Path, required=True)
    p.add_argument('--binding-request-sha256', required=True)
    p.add_argument('--rehearsal-id', required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args(argv)
    try:
        sys.stdout.buffer.write(decision.encoded(run(args.binding_request, args.binding_request_sha256,
                                                   args.rehearsal_id, args.output)))
        return 0
    except decision.Invalid as exc:
        diagnostic = exc.diagnostic()
    except OSError as exc:
        diagnostic = {'code': 'IO_ERROR', 'detail': str(exc)}
    sys.stderr.buffer.write(decision.encoded({'status': 'invalid', 'decision_evaluated': False, **diagnostic}))
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
