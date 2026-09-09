"""Immutable submitted-record bytes, fresh package checks and explicit custody limits."""
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path

from tools.perception_decision.cli import atomic_write
from tools.perception_decision.contract import encoded, load, parse
from tools.perception_inputs.source_io import digest_value, require
from tools.perception_observation import package as observations
from tools.perception_observation.contract import closed
from . import records


def source_digest():
    own = [[p.name, hashlib.sha256(p.read_bytes()).hexdigest()] for p in sorted(Path(__file__).parent.glob('*.py'))]
    return hashlib.sha256(encoded({'discovery':own, 'observation_dependencies':observations.code_identities()})).hexdigest()


def manifest(path, expected_seal):
    observations.verify(path, expected_seal)
    # Verify the exact manifest bytes reopened for record binding. The separate
    # consumer pass above does not make a later unverified path read trustworthy.
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        seal = parse(observations.read_relative(fd, 'SEAL.json', 8192, expected_seal))
        s = seal['manifest']
        return parse(observations.read_relative(fd, 'manifest.json', s['byte_size'], s['sha256']))
    finally:
        os.close(fd)


def make_draft(package, expected_seal, record_id, output):
    require(not os.path.lexists(output), 'OUTPUT_EXISTS', 'Draft identity already exists')
    m = manifest(package, expected_seal)
    draft = records.draft(m, expected_seal, record_id)
    summary = records.validate(draft, m, expected_seal)
    data = encoded(draft)
    require(len(data) <= records.MAX_RECORD, 'DISCOVERY_LIMIT', 'Draft exceeds byte limit')
    atomic_write(output, data)
    return {'record_sha256':hashlib.sha256(data).hexdigest(), 'summary':summary, 'submission_state':'unassigned_draft'}


def seal_record(record_path, expected_record, package, expected_package_seal, output):
    require(not os.path.lexists(output), 'OUTPUT_EXISTS', 'Sealed record identity already exists')
    before, environment = source_digest(), observations.runtime()
    record = load(record_path, expected_record, records.MAX_RECORD, validate_input=False)
    m = manifest(package, expected_package_seal)
    summary = records.validate(record, m, expected_package_seal, submission=True)
    result = {'artifact_id':'reiyah.perception-discovery.sealed-record', 'version':'0.1.0',
              'record':record, 'submitted_file_sha256':expected_record,
              'canonical_record_sha256':hashlib.sha256(encoded(record)).hexdigest(),
              'sealed_at_utc':datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
              'seal_clock_basis':'local_system_clock_not_independently_attested',
              'producer_sha256':before, 'summary':summary}
    require(before == source_digest() and environment == observations.runtime(),
            'DISCOVERY_CODE_CHANGED', 'Code or runtime changed during record sealing')
    data = encoded(result)
    require(len(data) <= records.MAX_RECORD, 'DISCOVERY_LIMIT', 'Sealed record exceeds byte limit')
    atomic_write(output, data)
    return {'sealed_record_sha256':hashlib.sha256(data).hexdigest(), 'record_id':record['record_id'], 'summary':summary}


def verified_record(path, expected, package_manifest, expected_package_seal):
    value = load(path, expected, records.MAX_RECORD, validate_input=False)
    closed(value, ('artifact_id', 'version', 'record', 'submitted_file_sha256', 'canonical_record_sha256',
                   'sealed_at_utc', 'seal_clock_basis', 'producer_sha256', 'summary'), 'DISCOVERY_SEAL')
    require(value['artifact_id'] == 'reiyah.perception-discovery.sealed-record' and value['version'] == '0.1.0'
            and value['seal_clock_basis'] == 'local_system_clock_not_independently_attested',
            'DISCOVERY_SEAL', 'Unsupported record seal')
    require(all(digest_value(value[k]) for k in ('submitted_file_sha256','canonical_record_sha256','producer_sha256')),
            'DISCOVERY_SEAL', 'Invalid retained digest')
    records.reported_time({'state':'reported','utc':value['sealed_at_utc']})
    require(value['canonical_record_sha256'] == hashlib.sha256(encoded(value['record'])).hexdigest(),
            'DISCOVERY_SEAL', 'Canonical record identity differs')
    summary = records.validate(value['record'], package_manifest, expected_package_seal, submission=True)
    require(encoded(summary) == encoded(value['summary']), 'DISCOVERY_SEAL', 'Stored summary differs from record accounting')
    return value


def verify_record(path, expected, package, expected_package_seal):
    m = manifest(package, expected_package_seal)
    value = verified_record(path, expected, m, expected_package_seal)
    return {'sealed_record_verified':True, 'record_id':value['record']['record_id'], 'summary':value['summary'],
            'producer_matches_current_source':value['producer_sha256'] == source_digest(),
            'source_file_identity':'retained_producer_assertion; verification binds the embedded canonical record'}


def verify_pair(first, first_sha, second, second_sha, package, expected_package_seal):
    m = manifest(package, expected_package_seal)
    a = verified_record(first, first_sha, m, expected_package_seal)
    b = verified_record(second, second_sha, m, expected_package_seal)
    return records.pair_report(a,b)
