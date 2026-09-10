"""Prepare a private common packet for later assisted inspection, without releasing it."""
import argparse
from decimal import Decimal, localcontext
import hashlib
import os
from pathlib import Path
import sys

from tools import perception_assistance_sources as sources, perception_binding as binding
from tools.perception_decision import contract as decision, nuscenes
from tools.perception_decision.cli import atomic_write
from tools.perception_discovery import custody
from tools.perception_geometry.bind import read
from tools.perception_inputs.source_io import require, snapshot
from tools.perception_observation import package

ROOT = Path(__file__).resolve().parent.parent
GUIDE = ROOT / 'research/perception-assistance/0.1.0/READER.md'
MAX_PACKET = 128 << 20
LABELS = ('configuration-1', 'configuration-2')


def code_identities():
    extra = [Path(__file__), Path(sources.__file__), GUIDE, Path(nuscenes.__file__)]
    extra += sorted((ROOT/'tools/perception_inputs').glob('*.py'))
    return sorted(dict(binding.code_identities() +
                       [[str(p.relative_to(ROOT)), hashlib.sha256(p.read_bytes()).hexdigest()] for p in extra]).items())


def exact_decimal(wire):
    q = decision.rational(wire)
    with localcontext() as context:
        context.prec = 128
        d = Decimal(q.numerator) / Decimal(q.denominator)
    require(nuscenes._number(d) == q, 'ASSISTANCE_NORMALIZATION', 'Ego position has no supported exact source decimal')
    return d


def normalize_check(case, normalizations, catalog, outputs, mappings):
    by_sample = {a['sample_token']: a for a in catalog['anchors']}
    by_anchor = {a['id']: a for a in case['anchors']}
    receipts = {r['anchor_id']: r for r in normalizations}
    for m in mappings:
        original = by_anchor[m['anchor_id']]
        sample = m['sample_token']
        anchor, receipt = nuscenes.normalize_frame(
            sample_token=sample, anchor_id=original['id'], weight=decision.rational(original['weight']),
            ego_xy=[exact_decimal(v) for v in by_sample[sample]['nominal_ego_xy']['value']],
            **outputs[sample], source_sha256={role: catalog['sources'][role].get('sha256') for role in ('base', 'camera')}
            | {'clock': catalog['sources']['metadata']['sha256']})
        for field in ('id', 'weight', 'base', 'additions'):
            require(decision.encoded(anchor[field]) == decision.encoded(original[field]),
                    'ASSISTANCE_NORMALIZATION', 'Recomputed comparison detections or weights differ')
        require(decision.encoded(receipt) == decision.encoded(receipts[original['id']]),
                'ASSISTANCE_NORMALIZATION', 'Recomputed normalization receipt differs')


def materialize(request, base_label):
    require(base_label in LABELS, 'ASSISTANCE_LABEL', 'Choose a declared neutral base label')
    labels = {'base': base_label, 'camera': next(l for l in LABELS if l != base_label)}
    code, runtime = code_identities(), binding.runtime()
    bound = binding.build(request)
    manifest = custody.manifest(request['package']['path'], request['package']['seal_sha256'])
    catalog = read(request['catalog'], binding.LIMITS['catalog'])
    case = read(request['comparison'], binding.LIMITS['comparison'])
    normalizations = read(request['normalizations'], binding.LIMITS['normalizations'])
    geometry = read(bound['inputs']['geometry_report'], 128 << 20)
    selected, occurrences = sources.selected_frames(catalog, bound['windows'], manifest)
    transforms = {w['anchor_id']: package.projected_transform(w.get('nominal_anchor_ego_to_global'))
                  for w in geometry['windows']}
    for m, occurrence in zip(bound['windows'], occurrences):
        occurrence['nominal_anchor_ego_to_global'] = transforms[m['anchor_id']]
        occurrence['comparison_frame_id'] = selected[m['sample_token']]['frame_id']
    annotations, instances, lookups, all_tokens, table_ids = sources.metadata(
        catalog['sources']['metadata'], selected, bound['windows'], occurrences)
    annotation_rows, annotation_custody = sources.annotation_rows(selected, annotations, instances, lookups, all_tokens)
    del all_tokens
    outputs = sources.predictions(catalog, selected)
    normalize_check(case, normalizations, catalog, outputs, bound['windows'])
    frames, private_frames = [], []
    for sample, row in selected.items():
        frame = {'id': row['frame_id'], 'annotations': {'state': 'source_rows', 'value': annotation_rows[sample]},
                 'predictions': {label: sources.prediction_rows(outputs[sample][role], row['frame_id']+'-'+label)
                                 for role, label in sorted(labels.items(), key=lambda item: item[1])}}
        frames.append(frame)
        private_frames.append({'frame_id': row['frame_id'], 'sample_token': sample, 'scene_token': row['scene_token'],
                               'timestamp_us': row['anchor_timestamp_us'],
                               'predictions': {role: {'descriptor': row[role],
                                                    'full_rows': sources._source_wire(outputs[sample][role])}
                                               for role in ('base', 'camera')}})
    summary = {'windows': len(occurrences), 'distinct_keyframes': len(frames),
               'keyframe_occurrences': sum(len(w['keyframes']) for w in occurrences),
               'comparison_anchors': len(bound['windows']), 'annotations': len(annotations),
               'prediction_rows': {labels[role]: sum(len(v[role]['value']) for v in outputs.values()
                                                      if v[role]['state'] == 'observed') for role in labels},
               'prediction_states': {labels[role]: {state: sum(v[role]['state'] == state for v in outputs.values())
                                        for state in sorted({v[role]['state'] for v in outputs.values()})} for role in labels}}
    common = {'artifact_id': 'reiyah.perception-assistance.common', 'version': '0.1.0',
              'status': 'prepared_not_disclosed',
              'observation_package': {'package_id': manifest['package_id'], 'seal_sha256': request['package']['seal_sha256']},
              'population_rule': 'all_source_keyframes_in_each_bound_closed_window',
              'coordinate_frame': 'source_global', 'geometry_authority': 'nominal_source_values_not_physical_accuracy',
              'number_encoding': 'exact_decimal_text_or_explicit_nonfinite_source_value; matrices_use_rational_objects',
              'box_time': 'keyframe_time_only_no_interpolation_or_object_motion_compensation',
              'reference_authority': 'source_suggestions_only_no_human_judgments',
              'windows': occurrences, 'frames': frames, 'summary': summary}
    files = {'common/assistance.json': decision.encoded(common), 'common/READER.md': GUIDE.read_bytes(),
             'operator/binding-report.json': decision.encoded(bound),
             'operator/source-custody.json': decision.encoded({
                 'artifact_id': 'reiyah.perception-assistance.custody', 'version': '0.1.0',
                 'configuration_roles': labels, 'tables': table_ids, 'sources': catalog['sources'],
                 'frames': private_frames, 'annotations': annotation_custody}),
             'operator/normalizations.json': decision.encoded(normalizations),
             'operator/comparison.json': decision.encoded(case)}
    require(sum(map(len, files.values())) <= MAX_PACKET, 'ASSISTANCE_LIMIT', 'Prepared packet exceeds byte limit')
    # Complete parent identities, package assets and code rechecked before returning.
    for spec in bound['inputs'].values():
        with snapshot(spec):
            pass
    for role in ('metadata', 'base', 'camera'):
        spec = catalog['sources'][role]
        if role == 'metadata' or spec['state'] == 'observed':
            with snapshot(spec):
                pass
    package.verify(request['package']['path'], request['package']['seal_sha256'])
    require(code == code_identities() and runtime == binding.runtime(),
            'ASSISTANCE_CODE_CHANGED', 'Code, reader instructions or runtime changed')
    return files, {'source_identities': code, 'runtime': runtime, 'summary': summary,
                   'source_inputs': {role: catalog['sources'][role] for role in ('metadata', 'base', 'camera')},
                   'binding_inputs': bound['inputs'], 'observation_package': common['observation_package']}


def verify_files(output, files):
    require({p.name for p in output.iterdir()} == {'common', 'operator'},
            'ASSISTANCE_OUTPUT_CHANGED', 'Unexpected output entry')
    for role in ('common', 'operator'):
        directory = output/role
        names = {Path(name).name for name in files if name.startswith(role+'/')}
        require(not directory.is_symlink() and directory.is_dir() and {p.name for p in directory.iterdir()} == names,
                'ASSISTANCE_OUTPUT_CHANGED', 'Unexpected role entry')
    for name, expected in files.items():
        p = output/name
        require(not p.is_symlink() and p.is_file() and p.stat().st_size == len(expected),
                'ASSISTANCE_OUTPUT_CHANGED', 'Prepared file type or size differs')
        with p.open('rb') as f:
            require(f.read(len(expected)+1) == expected, 'ASSISTANCE_OUTPUT_CHANGED', 'Prepared bytes differ')


def run(request_path, expected, base_label, output):
    output = Path(output)
    require(output.is_absolute() and output.parent.is_dir(), 'ASSISTANCE_OUTPUT', 'Require a private absolute output with existing parent')
    require(not os.path.lexists(output), 'OUTPUT_EXISTS', 'Refuse an existing preparation identity')
    request = decision.load(request_path, expected, binding.REQUEST_LIMIT, validate_input=False)
    binding.request_contract(request)
    for forbidden in (ROOT, Path(request['package']['path']).resolve()):
        require(not output.resolve().is_relative_to(forbidden), 'ASSISTANCE_OUTPUT', 'Output must be outside code and source package')
    files, context = materialize(request, base_label)
    decision.load(request_path, expected, binding.REQUEST_LIMIT, validate_input=False)
    receipt = {'artifact_id': 'reiyah.perception-assistance.preparation', 'version': '0.1.0',
               'status': 'prepared_not_disclosed', 'request_file_sha256': expected, **context,
               'files': [{'path': name, 'byte_size': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
                         for name, data in sorted(files.items())],
               'human_review_performed': False, 'assisted_evidence_released': False,
               'reference_constraints_admitted': False, 'decision_evaluated': False,
               'study_selection_performed': False, 'physical_reference_coverage': 'not_established',
               'reviewer_independence': 'not_established', 'blinding': 'identifier_masking_only_not_guaranteed'}
    output.mkdir(mode=0o700)
    for role in ('common', 'operator'):
        (output/role).mkdir(mode=0o700)
    for name, data in sorted(files.items()):
        atomic_write(output/name, data)
    verify_files(output, files)
    # Completion is recorded last. Interrupted preparations retain their partial files.
    data = decision.encoded(receipt)
    atomic_write(output/'PREPARATION.json', data)
    return {'status': receipt['status'], 'preparation_sha256': hashlib.sha256(data).hexdigest(),
            'summary': context['summary'], 'assisted_evidence_released': False, 'decision_evaluated': False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binding-request', type=Path, required=True)
    parser.add_argument('--binding-request-sha256', required=True)
    parser.add_argument('--base-label', choices=LABELS, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = run(args.binding_request, args.binding_request_sha256, args.base_label, args.output)
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
