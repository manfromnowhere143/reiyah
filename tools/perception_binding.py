"""Bind a comparison to its exact observation population and retained asset bytes.

This is an offline, private provenance check. It neither admits reference judgments
nor recomputes upstream normalization, catalog construction or nominal geometry.
"""
import argparse
from copy import deepcopy
import hashlib
from importlib.metadata import version as distribution_version
import os
from pathlib import Path
import re
import sys

from tools import perception_reference
from tools.perception_decision import contract as decision
from tools.perception_decision.cli import atomic_write
from tools.perception_discovery.custody import manifest as verified_manifest
from tools.perception_geometry.bind import read, source
from tools.perception_inputs.clock import identity, timestamp
from tools.perception_inputs.source_io import digest_value, require, snapshot
from tools.perception_observation import contract, formats, package
from tools.perception_windows import payloads

VERSION = '0.1.0'
LIMITS = {'comparison': decision.MAX_INPUT_BYTES, 'normalizations': 64 << 20,
          'catalog': 128 << 20, 'observation_custody': 128 << 20}
REQUEST_LIMIT = 32 << 10
REPORT_LIMIT = 128 << 20


def code_identities():
    root = Path(__file__).resolve().parent.parent
    extra = [Path(__file__), root/'tools/perception_reference.py', decision.SCHEMA]
    extra += sorted((root/'tools/perception_discovery').glob('*.py'))
    return sorted([['tools/'+name, digest] for name, digest in package.code_identities()] +
                  [[str(p.relative_to(root)), hashlib.sha256(p.read_bytes()).hexdigest()] for p in extra])


def runtime():
    return package.runtime() | {'jsonschema': distribution_version('jsonschema')}


def absolute_path(value):
    require(type(value) is str and 0 < len(value) <= 4096 and '\0' not in value
            and Path(value).is_absolute(), 'BINDING_REQUEST', 'Require an explicit absolute path')
    return Path(value)


def request_contract(request):
    contract.closed(request, ('artifact_id', 'version', *LIMITS, 'package'), 'BINDING_REQUEST')
    require(request['artifact_id'] == 'reiyah.perception-binding.request' and request['version'] == VERSION,
            'BINDING_REQUEST', 'Unsupported binding request')
    for role, limit in LIMITS.items():
        source(request[role], limit)
        absolute_path(request[role]['path'])
        require(digest_value(request[role]['sha256']), 'BINDING_REQUEST', 'Invalid expected source digest')
    contract.closed(request['package'], ('path', 'seal_sha256'), 'BINDING_REQUEST')
    absolute_path(request['package']['path'])
    require(digest_value(request['package']['seal_sha256']), 'BINDING_REQUEST', 'Invalid expected package seal')


def custody_request(custody, expected_package):
    contract.closed(custody, ('artifact_id', 'version', 'lifecycle_status', 'request', 'request_sha256',
        'output', 'expected_seal_sha256', 'source_identities', 'runtime', 'windows', 'captures', 'summary',
        'geometry_computation', 'authority', 'blinding'), 'BINDING_CUSTODY')
    require(custody['artifact_id'] == 'reiyah.perception-observation.custody' and custody['version'] == VERSION
            and custody['lifecycle_status'] == 'exploratory', 'BINDING_CUSTODY', 'Unsupported observation custody')
    req = custody['request']
    contract.closed(req, ('artifact_id', 'version', 'package_id', 'window_report', 'geometry_report',
                         'inventory', 'raw_root'), 'BINDING_CUSTODY')
    require(req['artifact_id'] == 'reiyah.perception-observation.request' and req['version'] == VERSION
            and type(req['package_id']) is str and re.fullmatch('[0-9a-f]{32}', req['package_id']) is not None,
            'BINDING_CUSTODY', 'Unsupported observation request')
    absolute_path(req['raw_root'])
    require(custody['request_sha256'] == hashlib.sha256(decision.encoded(req)).hexdigest()
            and custody['expected_seal_sha256'] == expected_package['seal_sha256']
            and absolute_path(custody['output']).resolve() == Path(expected_package['path']).resolve(),
            'BINDING_CUSTODY', 'Custody request, package location or expected seal differs')
    return req


def population(case, normalizations, catalog, windows, geometry, mappings, catalog_spec):
    require(type(catalog) is dict and type(catalog.get('sources')) is dict,
            'BINDING_SOURCE', 'Catalog has no source identities')
    metadata = catalog['sources'].get('metadata')
    require(package.same_identity(metadata, metadata), 'BINDING_SOURCE', 'Catalog metadata lacks a typed size and digest')
    contract.integer(metadata['byte_size'], 0, 1 << 30, 'BINDING_SOURCE')
    for report in (windows, geometry):
        inputs = report.get('inputs')
        require(type(inputs) is dict and package.same_identity(inputs.get('catalog'), catalog_spec)
                and package.same_identity(inputs.get('metadata'), metadata),
                'BINDING_SOURCE', 'Window, geometry, catalog or metadata identities differ')
    joined = perception_reference._joined_detections(case, normalizations, catalog)
    receipts = {r['anchor_id']: r for r in normalizations}
    clock = {r['sample_token']: r for r in catalog['anchors']}
    require({m['anchor_id'] for m in mappings} == set(joined),
            'BINDING_POPULATION', 'Comparison and observation anchor populations differ')
    # The joined-detection consumer already rejects repeated catalog samples and
    # normalization anchors, and requires one distinct sample per comparison anchor.
    for m in mappings:
        sample = identity(m['sample_token'])
        require(sample == receipts[m['anchor_id']]['sample_token'],
                'BINDING_POPULATION', 'Observation window names a different comparison sample')
        row = clock[sample]
        require(identity(m['scene_token']) == identity(row.get('scene_token'))
                and timestamp(m['anchor_timestamp_us']) == timestamp(row.get('anchor_timestamp_us'))
                == joined[m['anchor_id']]['time'],
                'BINDING_POPULATION', 'Observation scene or anchor clock differs from the comparison catalog')


def asset_bindings(path, manifest, source_rows, tokens, inventory):
    result = []
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for record, (token, row) in zip(manifest['captures'], source_rows.items()):
            spec = inventory.get(row['filename'])
            evidence = record['evidence']
            state = evidence['state']
            allowed = (('not_listed',) if spec is None else ('unavailable',) if spec['state'] == 'unavailable'
                       else ('delivered', 'missing', 'invalid', 'sensor_invalid', 'not_checked', 'withheld'))
            require(state in allowed, 'BINDING_AVAILABILITY', 'Disclosed availability contradicts the retained inventory')
            body_identity = None
            if state == 'delivered':
                asset = evidence['asset']
                data = package.read_relative(fd, asset['filename'], asset['byte_size'], asset['sha256'])
                require(len(data) == asset['byte_size'], 'BINDING_ASSET', 'Delivered asset length differs')
                if row['channel'] == 'LIDAR_TOP':
                    formats.verify_ply(data, evidence['point_count'])
                    data = data[len(formats.ply_header(evidence['point_count'])):]
                body_identity = {'byte_size': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
                require(package.same_identity(body_identity, spec), 'BINDING_ASSET',
                        'Delivered image or lidar point body differs from the retained source inventory')
            result.append({'capture_id': tokens[token], 'sample_data_token': token, 'source': row,
                           'raw_identity': spec, 'disclosed_evidence': evidence,
                           'source_content_check': 'matched' if body_identity is not None else 'not_delivered',
                           'delivered_source_body': body_identity})
    finally:
        os.close(fd)
    return result


def _build(request):
    request_contract(request)
    code, environment = code_identities(), runtime()
    docs = {role: read(request[role], limit) for role, limit in LIMITS.items()}
    case = decision.validate(docs['comparison'])
    custody = docs['observation_custody']
    observation = custody_request(custody, request['package'])
    upstream = {key: observation[key] for key in ('window_report', 'geometry_report', 'inventory')}
    windows = read(upstream['window_report'], contract.MAX_MANIFEST)
    geometry = read(upstream['geometry_report'], contract.MAX_MANIFEST)
    inventory = payloads.inventory(read(upstream['inventory'], 64 << 20))
    m = verified_manifest(request['package']['path'], request['package']['seal_sha256'])
    projected, rows, tokens, mappings = package.project(observation, windows, geometry)
    neutral = deepcopy(m)
    for row in neutral['captures']:
        row['evidence'] = {'state': 'not_checked'}
    require(decision.encoded(neutral) == decision.encoded(projected), 'BINDING_PROJECTION',
            'Package differs from the exact source-bound neutral projection')
    population(case, docs['normalizations'], docs['catalog'], windows, geometry, mappings, request['catalog'])
    captures = asset_bindings(request['package']['path'], m, rows, tokens, inventory)
    summary = contract.validate(m)
    expected_captures = [{k: row[k] for k in ('capture_id', 'sample_data_token', 'source', 'raw_identity',
                                              'disclosed_evidence')} for row in captures]
    require(decision.encoded(custody['windows']) == decision.encoded(mappings)
            and decision.encoded(custody['captures']) == decision.encoded(expected_captures)
            and decision.encoded(custody['summary']) == decision.encoded(summary),
            'BINDING_CUSTODY', 'Copied custody mappings or accounting differ from rederived values')
    # Snapshots fixed the bytes consumed above; this additional pass rejects a
    # source path whose bytes changed during the operation. Original raw paths
    # are intentionally not reopened: their separately retained inventory is the premise.
    inputs = {role: request[role] for role in LIMITS} | upstream
    for spec in inputs.values():
        with snapshot(spec):
            pass
    require(code == code_identities() and environment == runtime(), 'BINDING_CODE_CHANGED',
            'Source code or recorded runtime changed during binding')
    return {'artifact_id': 'reiyah.perception-binding.report', 'version': VERSION,
        'lifecycle_status': 'exploratory', 'status': 'bound',
        'request_sha256': hashlib.sha256(decision.encoded(request)).hexdigest(),
        'comparison_id': case['comparison_id'], 'cohort_id': case['cohort_id'],
        'inputs': inputs, 'package': request['package'] | {'package_id': m['package_id']},
        'windows': mappings, 'captures': captures, 'summary': summary,
        'comparison_output_states': [{'anchor_id': a['id'], 'base': a['base']['state'],
                                     'additions': a['additions']['state']} for a in case['anchors']],
        'source_identities': code, 'runtime': environment,
        'checked': ['expected_package_seal_and_files', 'source_bound_neutral_projection',
                    'comparison_window_sample_scene_clock_bijection', 'catalog_metadata_and_normalization_roles',
                    'delivered_images_and_lidar_point_bodies_against_inventory', 'copied_custody_accounting',
                    'source_input_bytes_before_and_after'],
        'trusted': ['separately_selected_expected_input_identities_and_original_inventory',
                    'upstream_catalog_and_normalization_not_recomputed',
                    'upstream_nominal_geometry_not_recomputed',
                    'shared_parsers_projection_package_verifier_and_joined_detection_consumer',
                    'local_python_imports_jsonschema_and_image_decoder',
                    'nondelivered_reason_assertions_not_reobserved'],
        'physical_reference_coverage': 'not_established', 'human_review': 'not_established',
        'reference_constraints_admitted': False, 'decision_evaluated': False,
        'study_selection_performed': False,
        'authority': 'population_and_byte_binding_only_not_physical_truth_or_operator_acceptance'}


def build(request):
    """Check already parsed request operands; use run() for the file/output boundary."""
    try:
        return _build(request)
    except (KeyError, TypeError, AttributeError, IndexError) as exc:
        # Upstream report consumers have deliberately narrower schema projections.
        # Malformed required fields must yield no binding, including at their joins.
        raise decision.Invalid('BINDING_INPUT', 'Malformed required upstream input structure') from exc


def run(request_path, expected, output):
    require(not os.path.lexists(output), 'OUTPUT_EXISTS', 'Binding report identity already exists')
    request = decision.load(request_path, expected, REQUEST_LIMIT, validate_input=False)
    request_contract(request)
    require(not Path(output).resolve().is_relative_to(Path(request['package']['path']).resolve()),
            'BINDING_PRIVATE_OUTPUT', 'Private binding report must be outside the observation package')
    report = build(request)
    decision.load(request_path, expected, REQUEST_LIMIT, validate_input=False)
    report['request_file_sha256'] = expected
    data = decision.encoded(report)
    require(len(data) <= REPORT_LIMIT, 'BINDING_LIMIT', 'Private report exceeds its byte limit')
    atomic_write(output, data)
    return {'status': 'bound', 'report_sha256': hashlib.sha256(data).hexdigest(),
            'summary': report['summary'], 'decision_evaluated': False, 'reference_constraints_admitted': False}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--request', type=Path, required=True)
    p.add_argument('--request-sha256', required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args(argv)
    try:
        sys.stdout.buffer.write(decision.encoded(run(args.request, args.request_sha256, args.output)))
        return 0
    except decision.Invalid as exc:
        diagnostic = exc.diagnostic()
    except OSError as exc:
        diagnostic = {'code': 'IO_ERROR', 'detail': str(exc)}
    sys.stderr.buffer.write(decision.encoded({'status': 'invalid', 'decision_evaluated': False, **diagnostic}))
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
