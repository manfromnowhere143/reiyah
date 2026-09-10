"""Read bound review contents and compile explicitly conditional joint references."""
import argparse
from copy import deepcopy
import hashlib
import os
from pathlib import Path
import sys

from tools import perception_binding as binding, perception_reference as reference
from tools.perception_decision import contract
from tools.perception_decision.cli import atomic_write
from tools.perception_discovery import custody, records
from tools.perception_geometry.bind import read, source
from tools.perception_inputs.clock import identity
from tools.perception_inputs.source_io import digest_value, require, snapshot
from tools.perception_observation.contract import closed

VERSION = '0.1.0'
REQUEST_LIMIT = 32 << 10
ADJUDICATION_LIMIT = 32 << 20
REPORT_LIMIT = 128 << 20
MAX_DISPOSITIONS = 200_000


def digest(value):
    return hashlib.sha256(contract.encoded(value)).hexdigest()


def fields(value, names):
    closed(value, names.split(), 'ADMISSION_FIELDS')


def items(value, maximum, minimum=0):
    require(type(value) is list and minimum <= len(value) <= maximum,
            'ADMISSION_LIMIT', 'Missing or oversized admission collection')
    return value


def descriptor(value, limit):
    source(value, limit)
    binding.absolute_path(value['path'])
    require(digest_value(value['sha256']), 'ADMISSION_SOURCE', 'Require an expected source digest')


def request_contract(request):
    fields(request, 'artifact_id version binding_request discoveries assisted adjudication')
    require(request['artifact_id'] == 'reiyah.perception-admission.request' and request['version'] == VERSION,
            'ADMISSION_VERSION', 'Unsupported admission request')
    descriptor(request['binding_request'], binding.REQUEST_LIMIT)
    for spec in items(request['discoveries'], 2, 2):
        descriptor(spec, records.MAX_RECORD)
    require(len({s['sha256'] for s in request['discoveries']}) == 2,
            'ADMISSION_RECORD', 'Two copies of one sealed file are not two records')
    descriptor(request['assisted'], records.MAX_RECORD)
    descriptor(request['adjudication'], ADJUDICATION_LIMIT)


def code_identities():
    return sorted(binding.code_identities() + [['tools/perception_admission.py',
                   hashlib.sha256(Path(__file__).read_bytes()).hexdigest()]])


def assisted_record(value, manifest, seal, expected):
    # Validate exactly the shared proposal/inspection content, without changing
    # the retained assisted phase or treating its exposure as discovery blinding.
    fields(value, 'artifact_id version record_id package_id package_seal_sha256 phase reviewer_id '
                 'completed_at reported_exposure capture_reviews proposals inputs')
    require(value['artifact_id'] == 'reiyah.perception-admission.assisted' and value['version'] == VERSION
            and value['phase'] == 'proposal_assisted', 'ADMISSION_PHASE', 'Unsupported assisted record')
    require(contract.encoded(value['inputs']) == contract.encoded(expected),
            'ADMISSION_PREDECESSOR', 'Assisted record is bound to different discovery or comparison inputs')
    projected = {k: v for k, v in value.items() if k != 'inputs'}
    projected.update(artifact_id='reiyah.perception-discovery.record', phase='unassisted_discovery')
    return records.validate(projected, manifest, seal, submission=True)


def coverage(value, state, basis):
    require(type(value) is dict, 'ADMISSION_COVERAGE', 'Coverage must remain explicit')
    if value.get('state') == 'unknown':
        fields(value, 'state reason')
        records.text(value['reason'], maximum=1024)
        return deepcopy(value)
    fields(value, 'state statement')
    require(value['state'] == state, 'ADMISSION_COVERAGE', 'No physical verification or acceptance is admitted')
    records.text(value['statement'], maximum=1024)
    return dict(value, basis_sha256=basis)


def chronology(discoveries, assisted, adjudication):
    reasons = []
    assisted_time = assisted['completed_at']
    end = adjudication['completed_at']
    for entry in discoveries:
        completed = entry['record']['completed_at']
        seal = entry['sealed_at_utc']
        if completed['state'] == 'unrecorded':
            reasons.append('discovery_completion_time_unrecorded')
        else:
            require(completed['utc'] <= seal, 'ADMISSION_CHRONOLOGY', 'Discovery completion is reported after its seal')
        if assisted_time['state'] == 'reported':
            require(seal <= assisted_time['utc'], 'ADMISSION_CHRONOLOGY', 'Assisted completion precedes a discovery seal')
        if end['state'] == 'reported':
            require(seal <= end['utc'], 'ADMISSION_CHRONOLOGY', 'Adjudication completion precedes a discovery seal')
    if assisted_time['state'] == 'unrecorded':
        reasons.append('assisted_completion_time_unrecorded')
    if end['state'] == 'unrecorded':
        reasons.append('adjudication_completion_time_unrecorded')
    elif assisted_time['state'] == 'reported':
        require(assisted_time['utc'] <= end['utc'], 'ADMISSION_CHRONOLOGY', 'Adjudication completion precedes assistance')
    return reasons


def registry_and_guards(discoveries, assisted, windows):
    registry, seen_records = {}, set()
    guards = {w['window_id']: set() for w in windows}
    all_records = [(v['record'], 'unassisted_discovery') for v in discoveries] + [(assisted, 'proposal_assisted')]
    for record, phase in all_records:
        require(record['record_id'] not in seen_records, 'ADMISSION_RECORD', 'Record identity reused across stages')
        seen_records.add(record['record_id'])
        canonical = digest(record)
        inspected_windows = set()
        for row in record['capture_reviews']:
            inspected_windows.add(row['window_id'])
            if row['state'] != 'inspected':
                guards[row['window_id']].add('incomplete_recorded_capture_inspection')
        for window in set(guards) - inspected_windows:
            guards[window].add('no_recorded_capture_occurrences')
        for proposal in record['proposals']:
            member = canonical + ':' + proposal['id']
            require(member not in registry, 'ADMISSION_RECORD', 'Repeated qualified proposal identity')
            registry[member] = {'phase': phase, 'canonical_record_sha256': canonical,
                                'proposal_sha256': digest(proposal), 'proposal': proposal}
    return registry, guards, seen_records


def compile_ledger(adjudication, registry, windows, global_guards, window_guards, sources):
    mappings = {w['window_id']: w for w in windows}
    proposal_sets = {w: {key for key, row in registry.items() if row['proposal']['window_id'] == w} for w in mappings}
    worlds = items(adjudication['worlds'], reference.MAX_JOINT_WORLDS, 1)
    require(len(registry) * len(worlds) <= MAX_DISPOSITIONS,
            'ADMISSION_LIMIT', 'Proposal/world accounting exceeds the declared work budget')
    adjudication_digest = digest(adjudication)
    spec = {'artifact_id': 'reiyah.perception-reference.input', 'version': VERSION,
            'coordinate_frame': 'nominal_global_xy',
            'inputs': {role+'_sha256': sources[role]['sha256'] for role in ('comparison', 'normalizations', 'catalog')},
            'joint_coverage': coverage(adjudication['joint_coverage'], 'assumed_complete', adjudication_digest),
            'worlds': []}
    if global_guards:
        spec['joint_coverage'] = {'state': 'unknown', 'reason': '; '.join(sorted(set(global_guards)))}
    world_ids = set()
    accounting = []
    for world in worlds:
        fields(world, 'id rationale windows')
        wid = identity(world['id'])
        require(wid not in world_ids, 'ADMISSION_WORLD', 'Repeated joint-world identity')
        world_ids.add(wid)
        records.text(world['rationale'], maximum=1024)
        entries = items(world['windows'], 128, 1)
        require(all(type(row) is dict and type(row.get('window_id')) is str for row in entries),
                'ADMISSION_POPULATION', 'Malformed world window identity')
        names = [row['window_id'] for row in entries]
        require(len(names) == len(set(names)) and set(names) == set(mappings),
                'ADMISSION_POPULATION', 'Every joint world must cover exactly the bound windows')
        compiled_world = {'id': wid, 'basis_sha256': digest({'adjudication': adjudication_digest, 'world': world}), 'anchors': []}
        for entry in entries:
            fields(entry, 'window_id unlisted_objects objects unrepresented')
            window = entry['window_id']
            anchor = {'anchor_id': mappings[window]['anchor_id'], 'unlisted_objects': coverage(
                entry['unlisted_objects'], 'excluded_by_assumption', digest({'world': compiled_world['basis_sha256'], 'window': entry})),
                'objects': []}
            seen, objects = set(), set()
            local_guards = set(window_guards[window])
            represented = 0
            for obj in items(entry['objects'], 128):
                require(type(obj) is dict and obj.get('state') in ('point', 'unresolved'),
                        'ADMISSION_OBJECT', 'Require an explicit point or unresolved object')
                fields(obj, 'id members rationale state ' + ('class xy timestamp_us' if obj['state'] == 'point' else 'reason'))
                oid = identity(obj['id'])
                require(oid not in objects, 'ADMISSION_OBJECT', 'Duplicate object in one interpretation')
                objects.add(oid)
                records.text(obj['rationale'], maximum=1024)
                members = [identity(m) for m in items(obj['members'], 32, 1)]
                require(len(members) == len(set(members)) and set(members) <= proposal_sets[window]
                        and not seen.intersection(members), 'ADMISSION_MEMBERS', 'Repeated, foreign or fabricated proposal member')
                seen.update(members)
                represented += len(members)
                body = {key: value for key, value in obj.items() if key != 'rationale'}
                # Full source contents are retained once in the registry. Fixed-size
                # source digests preserve transitive binding without serializing a
                # large point-index list again for each world that uses the proposal.
                links = {m: {key: registry[m][key] for key in ('phase', 'canonical_record_sha256', 'proposal_sha256')}
                         for m in members}
                body['record_sha256'] = digest({'world_basis': compiled_world['basis_sha256'],
                    'window_id': window, 'object': obj, 'sources': links})
                anchor['objects'].append(body)
            counts = {'represented': represented, 'excluded_by_assumption': 0, 'unresolved': 0}
            for row in items(entry['unrepresented'], records.MAX_PROPOSALS * 3):
                fields(row, 'member state reason')
                member = identity(row['member'])
                require(member in proposal_sets[window] and member not in seen,
                        'ADMISSION_MEMBERS', 'Repeated, foreign or fabricated unrepresented proposal')
                require(type(row['state']) is str and row['state'] in ('excluded_by_assumption', 'unresolved'),
                        'ADMISSION_DISPOSITION', 'Unrepresented proposals require exclusion or unresolved status')
                records.text(row['reason'], maximum=1024)
                counts[row['state']] += 1
                seen.add(member)
                if row['state'] == 'unresolved':
                    local_guards.add('unresolved_proposal_disposition')
            require(seen == proposal_sets[window], 'ADMISSION_ACCOUNTING', 'A source proposal has no disposition in this world')
            if local_guards:
                anchor['unlisted_objects'] = {'state': 'unknown', 'reason': '; '.join(sorted(local_guards))}
            compiled_world['anchors'].append(anchor)
            accounting.append({'world_id': wid, 'window_id': window, 'anchor_id': anchor['anchor_id'],
                               'dispositions': counts, 'guards': sorted(local_guards)})
        spec['worlds'].append(compiled_world)
    return spec, accounting


def _build(request):
    request_contract(request)
    code, environment = code_identities(), binding.runtime()
    binding_request = read(request['binding_request'], binding.REQUEST_LIMIT)
    bound = binding.build(binding_request)
    package = binding_request['package']
    manifest = custody.manifest(package['path'], package['seal_sha256'])
    discoveries = []
    for descriptor_ in request['discoveries']:
        # Also verify the declared byte size; the existing seal verifier binds its
        # canonical embedded record independently of the source-file assertion.
        with snapshot(descriptor_):
            pass
        discoveries.append(custody.verified_record(descriptor_['path'], descriptor_['sha256'], manifest, package['seal_sha256']))
    predecessors = {'binding_request_sha256': request['binding_request']['sha256'],
                    'discovery_sha256': [s['sha256'] for s in request['discoveries']]}
    assisted = read(request['assisted'], records.MAX_RECORD)
    assisted_summary = assisted_record(assisted, manifest, package['seal_sha256'], predecessors)
    adjudication = read(request['adjudication'], ADJUDICATION_LIMIT)
    fields(adjudication, 'artifact_id version record_id reviewer_id completed_at inputs joint_coverage worlds')
    require(adjudication['artifact_id'] == 'reiyah.perception-admission.adjudication' and adjudication['version'] == VERSION,
            'ADMISSION_PHASE', 'Unsupported adjudication record')
    records.neutral(adjudication['record_id'])
    records.text(adjudication['reviewer_id'], maximum=128)
    require(adjudication['reviewer_id'] == adjudication['reviewer_id'].strip(),
            'ADMISSION_RECORD', 'Adjudicator handle contains surrounding whitespace')
    records.reported_time(adjudication['completed_at'])
    require(contract.encoded(adjudication['inputs']) == contract.encoded(predecessors | {'assisted_sha256': request['assisted']['sha256']}),
            'ADMISSION_PREDECESSOR', 'Adjudication is bound to different selected records')
    pair = records.pair_report(*discoveries)
    global_guards = [reason for reason in pair['reasons'] if 'inspection_incomplete' not in reason]
    global_guards += chronology(discoveries, assisted, adjudication)
    registry, window_guards, record_ids = registry_and_guards(discoveries, assisted, bound['windows'])
    require(adjudication['record_id'] not in record_ids, 'ADMISSION_RECORD', 'Adjudication reuses a source record identity')
    spec, accounting = compile_ledger(adjudication, registry, bound['windows'], global_guards, window_guards, binding_request)
    operands = {role: read(binding_request[role], limit) for role, limit in binding.LIMITS.items() if role != 'observation_custody'}
    compiled, compilation = reference.compile_model(spec, operands['comparison'], operands['normalizations'], operands['catalog'])
    # Embed an admission identity in the model assumptions, so a compiled input
    # cannot lose the fact that it came through this source-admission request.
    require(len(compiled['assumptions']) < 32, 'ADMISSION_LIMIT', 'No room for admission provenance without dropping assumptions')
    compiled['assumptions'].append('Reviewed-source admission request canonical SHA-256: '+digest(request)+'. Physical review validity remains unestablished.')
    contract.validate(compiled)
    require(len(contract.encoded(compiled)) <= contract.MAX_INPUT_BYTES,
            'ADMISSION_LIMIT', 'Compiled input exceeds its byte limit after admission provenance')
    compilation['compiled_input_sha256'] = digest(compiled)
    compilation['admission_provenance_appended'] = True
    sources = [request['binding_request'], *request['discoveries'], request['assisted'], request['adjudication'], *bound['inputs'].values()]
    for descriptor_ in sources:
        with snapshot(descriptor_):
            pass
    custody.manifest(package['path'], package['seal_sha256'])
    require(code == code_identities() and environment == binding.runtime(),
            'ADMISSION_CODE_CHANGED', 'Code or runtime changed during admission')
    return {'artifact_id': 'reiyah.perception-admission.report', 'version': VERSION, 'lifecycle_status': 'exploratory',
            'status': 'compiled_conditional_model', 'request_sha256': digest(request), 'inputs': request,
            'binding': bound, 'discovery_records': discoveries, 'discovery_pair': pair,
            'assisted_record': assisted, 'assisted_summary': assisted_summary, 'adjudication': adjudication,
            'proposal_registry': registry, 'global_guards': sorted(set(global_guards)), 'world_accounting': accounting,
            'reference': spec, 'compiled_input': compiled, 'compilation': compilation,
            'source_identities': code, 'runtime': environment,
            'reference_contents_checked': True, 'decision_evaluated': False, 'study_selection_performed': False,
            'physical_reference_coverage': 'not_established', 'human_identity_and_independence': 'not_established',
            'sealing_before_assisted_exposure': 'not_established', 'phase_2_release': 'not_authorized_by_this_tool',
            'authority': 'conditional_model_contents_and_integrity_only_not_physical_truth_or_operator_acceptance',
            'trusted': bound['trusted'] + ['selected_expected_review_record_identities', 'reported_review_facts_and_explicit_coverage_assumptions',
                                         'shared_discovery_content_validation_and_reference_compiler']}


def build(request):
    """Composition interface; run() binds the outer request file and output boundary."""
    try:
        return _build(request)
    except (KeyError, TypeError, AttributeError, IndexError) as exc:
        raise contract.Invalid('ADMISSION_INPUT', 'Malformed required admission input structure') from exc


def run(request_path, expected, output):
    require(not os.path.lexists(output), 'OUTPUT_EXISTS', 'Admission report identity already exists')
    request = contract.load(request_path, expected, REQUEST_LIMIT, validate_input=False)
    request_contract(request)
    binding_request = read(request['binding_request'], binding.REQUEST_LIMIT)
    binding.request_contract(binding_request)
    require(not Path(output).resolve().is_relative_to(Path(binding_request['package']['path']).resolve()),
            'ADMISSION_PRIVATE_OUTPUT', 'Review contents must remain outside the observation package')
    report = build(request)
    contract.load(request_path, expected, REQUEST_LIMIT, validate_input=False)
    report['request_file_sha256'] = expected
    data = contract.encoded(report)
    require(len(data) <= REPORT_LIMIT, 'ADMISSION_LIMIT', 'Admission report exceeds its byte limit')
    atomic_write(output, data)
    return {'status': report['status'], 'report_sha256': hashlib.sha256(data).hexdigest(),
            'anchor_reference_states': report['compilation']['anchor_reference_states'],
            'decision_evaluated': False, 'physical_reference_coverage': 'not_established'}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--request-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        sys.stdout.buffer.write(contract.encoded(run(args.request, args.request_sha256, args.output)))
        return 0
    except contract.Invalid as exc:
        diagnostic = exc.diagnostic()
    except OSError as exc:
        diagnostic = {'code': 'IO_ERROR', 'detail': str(exc)}
    sys.stderr.buffer.write(contract.encoded({'status': 'invalid', 'decision_evaluated': False, **diagnostic}))
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
