"""Complete source inventory; scene eligibility never depends on prediction values."""
from collections import Counter
import hashlib

from tools.perception_decision.contract import encoded
from tools.perception_decision.nuscenes import CLASSES, MAX_FRAME_PREDICTIONS, UNAVAILABLE, _number
from .clock import apply_exclusions, exposure_windows, identity, metadata_tables, population, validation_names
from .sensors import enrich
from .source_io import JSONStream, MAX_SOURCE_BYTES, digest_value, document, require, snapshot

ROLES = frozenset(('metadata', 'splits', 'base', 'camera', 'exposures'))
META_FIELDS = frozenset(('use_camera', 'use_lidar', 'use_radar', 'use_map', 'use_external'))


def validate_request(request):
    require(type(request) is dict and set(request) == {'artifact_id', 'version', 'sources'} and
            request['artifact_id'] == 'reiyah.perception-inputs.request' and request['version'] == '0.1.0',
            'INGEST_REQUEST', 'Unknown request fields, artifact identity or version')
    sources = request['sources']
    require(type(sources) is dict and set(sources) == ROLES, 'INGEST_REQUEST', 'Name exactly the five source roles')
    for role, source in sources.items():
        require(type(source) is dict and type(source.get('state')) is str, 'SOURCE_STATE', 'Explicit source state is required')
        if source['state'] == 'observed':
            require(set(source) == {'state', 'path', 'byte_size', 'sha256'}, 'SOURCE_STATE', 'Unknown observed-source fields')
            require(type(source['path']) is str and 0 < len(source['path']) <= 4096 and '\0' not in source['path'],
                    'SOURCE_IDENTITY', 'Invalid source path')
            require(type(source['byte_size']) is int and 0 <= source['byte_size'] <= MAX_SOURCE_BYTES and digest_value(source['sha256']),
                    'SOURCE_IDENTITY', 'Expected source byte size and SHA-256 are required')
        else:
            require(role in ('base', 'camera', 'exposures') and source['state'] in UNAVAILABLE and
                    set(source) == {'state', 'reason'} and type(source['reason']) is str and 0 < len(source['reason']) <= 1024,
                    'SOURCE_STATE', 'Invalid unavailable source; metadata and splits are required')
    return request


def validate_predictions(rows, sample):
    require(type(rows) is list and len(rows) <= MAX_FRAME_PREDICTIONS,
            'PREDICTION_FRAME', 'Frame is not a bounded prediction array')
    for row in rows:
        require(type(row) is dict and row.get('sample_token') == sample,
                'PREDICTION_SAMPLE', 'Prediction belongs to a different or unnamed sample')
        require(type(row.get('detection_name')) is str and row['detection_name'] in CLASSES,
                'PREDICTION_CLASS', 'Unknown detection class')
        center = row.get('translation')
        require(type(center) is list and len(center) == 3, 'PREDICTION_COORDINATES', 'Translation must have three source components')
        _number(center[0])
        _number(center[1])
        require(0 <= _number(row.get('detection_score')) <= 1, 'PREDICTION_SCORE', 'Score is outside [0,1]')


def prediction_index(stream, parent_sha256, sample_ids, chunk_bytes=65536):
    reader = JSONStream(stream, chunk_bytes=chunk_bytes)
    frames, header, fields = {}, None, set()
    for name in reader.members(2):
        fields.add(name)
        if name == 'meta':
            header, _ = reader.value(dict)
            require(set(header) == META_FIELDS and all(type(v) is bool for v in header.values()),
                    'PREDICTION_META', 'Unsupported prediction metadata declaration')
        elif name == 'results':
            for sample in reader.members(50000):
                identity(sample)
                require(sample in sample_ids, 'PREDICTION_POPULATION', 'Prediction key is outside the clock population')
                values, span = reader.value(list)
                validate_predictions(values, sample)
                frames[sample] = {'state': 'observed', 'row_count': len(values),
                                  'source_sha256': parent_sha256, **span}
        else:
            require(False, 'PREDICTION_META', 'Unknown top-level prediction field')
    reader.finish()
    require(fields == {'meta', 'results'}, 'PREDICTION_META', 'Prediction document is incomplete')
    return frames, header


def extract_frame(source, sample, descriptor):
    """Retrieve one indexed array after verifying the full parent source again."""
    require(type(source) is dict and set(source) == {'state', 'path', 'byte_size', 'sha256'} and
            source['state'] == 'observed' and type(source['path']) is str and 0 < len(source['path']) <= 4096 and
            '\0' not in source['path'] and type(source['byte_size']) is int and 0 <= source['byte_size'] <= MAX_SOURCE_BYTES and
            digest_value(source['sha256']), 'FRAME_BINDING', 'Extraction requires an identified observed source')
    require(type(descriptor) is dict and set(descriptor) == {'state', 'row_count', 'source_sha256', 'byte_offset', 'byte_size', 'sha256'}
            and descriptor['state'] == 'observed' and descriptor['source_sha256'] == source['sha256'],
            'FRAME_BINDING', 'Frame descriptor belongs to another source or state')
    offset, size = descriptor['byte_offset'], descriptor['byte_size']
    require(type(offset) is int and offset >= 0 and type(size) is int and 0 < size <= 1 << 20 and
            offset + size <= source['byte_size'] and digest_value(descriptor['sha256']) and
            type(descriptor['row_count']) is int and 0 <= descriptor['row_count'] <= MAX_FRAME_PREDICTIONS,
            'FRAME_BINDING', 'Frame span or count is invalid')
    with snapshot(source) as stream:
        stream.seek(offset)
        data = stream.read(size)
    require(hashlib.sha256(data).hexdigest() == descriptor['sha256'], 'FRAME_DIGEST', 'Frame bytes differ from indexed identity')
    values = document(data)
    validate_predictions(values, sample)
    require(len(values) == descriptor['row_count'], 'FRAME_BINDING', 'Frame count differs')
    return values


def build(request):
    validate_request(request)
    sources = request['sources']
    with snapshot(sources['splits']) as stream:
        names = validation_names(stream)
    with snapshot(sources['metadata']) as stream:
        anchors = population(metadata_tables(stream), names)
        exposure = sources['exposures']
        if exposure['state'] == 'observed':
            with snapshot(exposure) as history:
                windows, exposure_summary = exposure_windows(history, anchors)
        else:
            windows, exposure_summary = None, {'state': exposure['state'], 'reason': exposure['reason']}
        apply_exclusions(anchors, windows)
        # Population/exclusion identity precedes sensor joins and prediction parsing.
        clock_sha256 = hashlib.sha256(encoded(anchors)).hexdigest()
        stream.seek(0)
        sensor_summary = enrich(stream, anchors)
    sample_ids = {row['sample_token'] for row in anchors}
    source_headers = {}
    for role in ('base', 'camera'):
        source = sources[role]
        if source['state'] == 'observed':
            with snapshot(source) as stream:
                frames, source_headers[role] = prediction_index(stream, source['sha256'], sample_ids)
            for row in anchors:
                row[role] = frames.get(row['sample_token'], {'state': 'missing', 'reason': 'No results key in verified source',
                                                           'source_sha256': source['sha256']})
        else:
            source_headers[role] = None
            for row in anchors:
                row[role] = dict(source)
    context = [row for row in anchors if row['has_declared_scene_context']]
    eligible = [row for row in anchors if row['eligibility'] == 'eligible_under_declared_rule']
    summary = {'scene_count': len(names), 'clock_anchor_count': len(anchors), 'context_anchor_count': len(context),
               'eligible_anchor_count': len(eligible) if windows is not None else None,
               'eligible_scene_count': len({r['scene_token'] for r in eligible}) if windows is not None else None,
               'prediction_availability': {role: dict(Counter(row[role]['state'] for row in anchors)) for role in ('base', 'camera')},
               'exposure_history': exposure_summary, 'selected_cohort': None, 'cohort_seed': None,
               'sensor_window_validity': 'not_checked', 'physical_reference_validity': 'not_established',
               'prediction_comparison': 'not_performed'}
    summary['sensor_metadata'] = sensor_summary
    return {'artifact_id': 'reiyah.perception-inputs.catalog', 'version': '0.1.0', 'lifecycle_status': 'exploratory',
            'request_sha256': hashlib.sha256(encoded(request)).hexdigest(), 'request_identity_kind': 'canonical_semantic_content',
            'sources': sources, 'clock_and_exclusion_sha256': clock_sha256, 'anchors': anchors,
            'source_metadata_declarations': source_headers, 'source_metadata_authority': 'unverified_producer_declarations',
            'summary': summary, 'scope': 'full_source_inventory_not_study_selection',
            'required_prediction_fields': ['sample_token', 'detection_name', 'translation[0:2]', 'detection_score'],
            'unused_prediction_fields': ['translation_z', 'size', 'rotation', 'velocity', 'attribute_name'],
            'eligibility_operands': ['official_validation_scene_membership', 'sample_clock', 'scene_extent', 'historical_exposure_intervals'],
            'historical_exposure_limits': 'Only the supplied history is covered; other benchmark or author exposure is not excluded.',
            'authority_state': 'offline_research_only'}
