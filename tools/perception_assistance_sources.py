"""Bounded source selection for later assistance; no reference judgments."""
from contextlib import ExitStack
from decimal import Decimal
import hashlib

from tools.perception_decision.contract import encoded
from tools.perception_inputs import catalog as inventory
from tools.perception_inputs.clock import identity, timestamp
from tools.perception_inputs.sensors import _rows, _table_streams
from tools.perception_inputs.source_io import document, require, snapshot
from tools.perception_observation.contract import closed

TABLES = ('sample.json', 'sample_annotation.json', 'instance.json',
          'category.json', 'attribute.json', 'visibility.json')
ANNOTATION_FIELDS = ('token', 'sample_token', 'instance_token', 'attribute_tokens',
                     'visibility_token', 'translation', 'size', 'rotation', 'prev', 'next',
                     'num_lidar_pts', 'num_radar_pts')
PREDICTION_FIELDS = ('sample_token', 'translation', 'size', 'rotation', 'velocity',
                     'detection_name', 'detection_score', 'attribute_name')
MAX_FRAMES = 256
MAX_ANNOTATIONS = 100000
MAX_SELECTED_BYTES = 24 << 20


def text(value):
    require(type(value) is str and len(value) <= 4096, 'ASSISTANCE_FIELD', 'Require bounded source text')
    return value


def number(value):
    """Exact decimal text; source nonfiniteness stays explicit, never zero."""
    require(type(value) in (int, Decimal), 'ASSISTANCE_NUMBER', 'Require a source number')
    if type(value) is int:
        require(len(str(value)) <= 64, 'ASSISTANCE_NUMBER', 'Oversized source integer')
    elif not value.is_finite():
        return {'state': 'nonfinite_source_value', 'source_text': str(value)}
    else:
        require(len(value.as_tuple().digits) <= 128 and abs(value.as_tuple().exponent) <= 1000,
                'ASSISTANCE_NUMBER', 'Oversized source decimal')
    return str(value)


def vector(value, length):
    require(type(value) is list and len(value) == length, 'ASSISTANCE_FIELD', 'Wrong source vector length')
    return [number(v) for v in value]


def count(value):
    require(type(value) is int and 0 <= value <= 1000000000,
            'ASSISTANCE_FIELD', 'Require a bounded nonnegative source count')
    return value


def selected_frames(catalog, windows, manifest):
    rows = catalog['anchors']
    require(type(rows) is list and 0 < len(rows) <= 50000, 'ASSISTANCE_LIMIT', 'Invalid catalog population')
    by_sample = {}
    for row in rows:
        sample = identity(row.get('sample_token'))
        require(sample not in by_sample, 'ASSISTANCE_POPULATION', 'Repeated catalog sample')
        identity(row.get('scene_token')); timestamp(row.get('anchor_timestamp_us'))
        by_sample[sample] = row
    intervals = {w['id']: w['interval_us'] for w in manifest['windows']}
    selected, occurrences = {}, []
    for w in windows:
        lo, hi = intervals[w['window_id']]
        members = sorted((r for r in rows if r['scene_token'] == w['scene_token'] and
                          lo <= r['anchor_timestamp_us']-w['anchor_timestamp_us'] <= hi),
                         key=lambda r: (r['anchor_timestamp_us'], r['sample_token']))
        require(members and w['sample_token'] in {r['sample_token'] for r in members},
                'ASSISTANCE_POPULATION', 'A window lacks its anchor')
        for r in members:
            token = r['sample_token']
            if token not in selected:
                require(len(selected) < MAX_FRAMES, 'ASSISTANCE_LIMIT', 'Too many selected keyframes')
                selected[token] = r | {'frame_id': f'frame-{len(selected)+1:04d}'}
        occurrences.append({'window_id': w['window_id'], 'interval_us': [lo, hi],
                            'keyframes': [{'frame_id': selected[r['sample_token']]['frame_id'],
                                           'time_offset_us': r['anchor_timestamp_us']-w['anchor_timestamp_us']}
                                          for r in members]})
    return selected, occurrences


def table_rows(stream, fields, limit):
    seen = set()
    for index, row in enumerate(_rows(stream, limit)):
        closed(row, fields, 'ASSISTANCE_FIELD')
        token = identity(row.get('token'))
        require(token not in seen, 'ASSISTANCE_DUPLICATE', 'Repeated source table identity')
        seen.add(token)
        yield index, row


def metadata(source, selected, windows, occurrences):
    """Read whole tables and check exact source membership before projection."""
    with snapshot(source) as stream, ExitStack() as stack:
        tables = _table_streams(stream, stack, TABLES)
        table_ids = []
        for name, f in sorted(tables.items()):
            h, size = hashlib.sha256(), 0
            while chunk := f.read(1 << 20):
                h.update(chunk); size += len(chunk)
            table_ids.append({'member': 'v1.0-trainval/'+name, 'byte_size': size, 'sha256': h.hexdigest()})
            f.seek(0)
        all_samples, wanted = {}, set()
        for _, row in table_rows(tables['sample.json'], ('token', 'scene_token', 'timestamp', 'prev', 'next'), 50000):
            sample, scene, time = row['token'], identity(row['scene_token']), timestamp(row['timestamp'])
            all_samples[sample] = (scene, time)
            for w, occurrence in zip(windows, occurrences):
                lo, hi = occurrence['interval_us']
                if scene == w['scene_token'] and lo <= time-w['anchor_timestamp_us'] <= hi:
                    wanted.add(sample)
        require(wanted == set(selected), 'ASSISTANCE_POPULATION', 'Source keyframes differ from the selected catalog population')
        for token, row in selected.items():
            require(all_samples[token] == (row['scene_token'], row['anchor_timestamp_us']),
                    'ASSISTANCE_POPULATION', 'Selected source scene or clock differs')
        annotations, all_annotations, selected_bytes = [], set(), 0
        for index, row in table_rows(tables['sample_annotation.json'], ANNOTATION_FIELDS, 2000000):
            all_annotations.add(row['token'])
            require(identity(row['sample_token']) in all_samples, 'ASSISTANCE_JOIN', 'Annotation sample is absent')
            if row['sample_token'] in selected:
                require(len(annotations) < MAX_ANNOTATIONS, 'ASSISTANCE_LIMIT', 'Too many selected annotations')
                for key in ('prev', 'next', 'instance_token', 'visibility_token'):
                    require(type(row[key]) is str and len(row[key]) <= 96,
                            'ASSISTANCE_FIELD', 'Malformed selected annotation identity')
                selected_bytes += len(encoded(_source_wire(row)))
                require(selected_bytes <= MAX_SELECTED_BYTES, 'ASSISTANCE_LIMIT', 'Selected annotation bytes exceed limit')
                annotations.append((index, row))
        # Resolve immediate source links as links, including neighbors outside the
        # selected package. A temporal label must not bless a broken or wrong track.
        links = {r[k] for _, r in annotations for k in ('prev', 'next') if r[k] != ''}
        require(all(type(t) is str for t in links), 'ASSISTANCE_JOIN', 'Malformed annotation link')
        linked = {}
        tables['sample_annotation.json'].seek(0)
        for row in _rows(tables['sample_annotation.json'], 2000000):
            if row['token'] in links:
                linked[row['token']] = (row['instance_token'], row['sample_token'], row['prev'], row['next'])
        require(set(linked) == links, 'ASSISTANCE_JOIN', 'Annotation temporal link is absent')
        for _, r in annotations:
            scene, time = all_samples[r['sample_token']]
            for direction in ('prev', 'next'):
                if r[direction] == '':
                    continue
                instance, sample, prev, next_ = linked[r[direction]]
                other_scene, other_time = all_samples[sample]
                require(instance == r['instance_token'] and scene == other_scene
                        and (other_time < time if direction == 'prev' else other_time > time)
                        and (next_ if direction == 'prev' else prev) == r['token'],
                        'ASSISTANCE_JOIN', 'Inconsistent annotation temporal link')
        instances = {}
        wanted_instances = {identity(r['instance_token']) for _, r in annotations}
        for _, row in table_rows(tables['instance.json'], ('token', 'category_token', 'first_annotation_token',
                                                          'last_annotation_token', 'nbr_annotations'), 1000000):
            if row['token'] in wanted_instances:
                count(row['nbr_annotations'])
                identity(row['first_annotation_token']); identity(row['last_annotation_token'])
                require(row['first_annotation_token'] in all_annotations and row['last_annotation_token'] in all_annotations,
                        'ASSISTANCE_JOIN', 'Instance endpoint is absent')
                instances[row['token']] = row
        require(set(instances) == wanted_instances, 'ASSISTANCE_JOIN', 'Selected instance is absent')
        for _, row in annotations:
            instance = instances[row['instance_token']]
            require((row['prev'] == '') == (row['token'] == instance['first_annotation_token'])
                    and (row['next'] == '') == (row['token'] == instance['last_annotation_token']),
                    'ASSISTANCE_JOIN', 'Annotation endpoint contradicts its source instance')
        lookups = {}
        for name, fields in [('category.json', ('token', 'name', 'description')),
                             ('attribute.json', ('token', 'name', 'description')),
                             ('visibility.json', ('token', 'level', 'description'))]:
            lookups[name] = {r['token']: {k: text(v) for k, v in r.items() if k != 'token'}
                             for _, r in table_rows(tables[name], fields, 10000)}
    return annotations, instances, lookups, all_annotations, table_ids


def annotation_rows(selected, annotations, instances, lookups, all_tokens):
    ids = {r['token']: f'annotation-{i+1:06d}' for i, (_, r) in enumerate(annotations)}
    tracks = {token: f'track-{i+1:06d}' for i, token in enumerate(dict.fromkeys(r['instance_token'] for _, r in annotations))}
    rows, custody, projected_bytes = {s: [] for s in selected}, [], 0
    for index, r in annotations:
        require(type(r['attribute_tokens']) is list and len(r['attribute_tokens']) <= 32
                and all(type(t) is str for t in r['attribute_tokens'])
                and len(set(r['attribute_tokens'])) == len(r['attribute_tokens']),
                'ASSISTANCE_FIELD', 'Invalid source attribute identities')
        category = identity(instances[r['instance_token']]['category_token'])
        visibility = r['visibility_token']
        require(type(visibility) is str and category in lookups['category.json']
                and (visibility == '' or visibility in lookups['visibility.json'])
                and all(t in lookups['attribute.json'] for t in r['attribute_tokens']),
                'ASSISTANCE_JOIN', 'Category, visibility or attribute join is absent')
        links = {}
        for direction in ('prev', 'next'):
            token = r[direction]
            require(type(token) is str and (token == '' or token in all_tokens),
                    'ASSISTANCE_JOIN', 'Annotation temporal link is absent from the source table')
            links[direction] = ({'state': 'source_endpoint'} if token == '' else
                                {'state': 'in_package', 'annotation_id': ids[token]} if token in ids else
                                {'state': 'outside_package'})
        row = {'id': ids[r['token']], 'track_id': tracks[r['instance_token']],
               'category': lookups['category.json'][category],
               'attributes': [lookups['attribute.json'][t] for t in r['attribute_tokens']],
               'visibility': ({'state': 'not_annotated'} if visibility == '' else
                              {'state': 'source_value', **lookups['visibility.json'][visibility]}),
               'translation': vector(r['translation'], 3), 'size': vector(r['size'], 3),
               'rotation': vector(r['rotation'], 4), 'num_lidar_pts': count(r['num_lidar_pts']),
               'num_radar_pts': count(r['num_radar_pts']), **links}
        projected_bytes += len(encoded(row))
        require(projected_bytes <= MAX_SELECTED_BYTES, 'ASSISTANCE_LIMIT', 'Projected annotation bytes exceed limit')
        rows[r['sample_token']].append(row)
        custody.append({'annotation_id': row['id'], 'source_row_index': index, 'source_row': _source_wire(r),
                        'instance': instances[r['instance_token']]})
    return rows, custody


def _source_wire(value):
    # Private reconstruction record; decimals are tagged to avoid lossy JSON floats.
    if type(value) is Decimal:
        return {'source_decimal': str(value)}
    if type(value) is list:
        return [_source_wire(v) for v in value]
    if type(value) is dict:
        return {k: _source_wire(v) for k, v in value.items()}
    return value


def predictions(catalog, selected):
    result = {s: {} for s in selected}
    sample_ids = {r['sample_token'] for r in catalog['anchors']}
    selected_bytes = 0
    for role in ('base', 'camera'):
        source = catalog['sources'][role]
        if source.get('state') != 'observed':
            require(source.get('state') in inventory.UNAVAILABLE and set(source) == {'state', 'reason'},
                    'ASSISTANCE_SOURCE', 'Malformed unavailable source')
            text(source['reason'])
            for s, r in selected.items():
                require(r[role] == source, 'ASSISTANCE_PREDICTION', 'Unavailable source state differs')
                result[s][role] = dict(source)
            continue
        with snapshot(source) as stream:
            # Complete source scan proves absence as well as exact frame spans.
            index, _ = inventory.prediction_index(stream, source['sha256'], sample_ids)
            for sample, anchor in selected.items():
                descriptor = index.get(sample, {'state': 'missing', 'reason': 'No results key in verified source',
                                                'source_sha256': source['sha256']})
                require(encoded(descriptor) == encoded(anchor[role]), 'ASSISTANCE_PREDICTION',
                        'Selected prediction descriptor differs from full source scan')
                if descriptor['state'] != 'observed':
                    result[sample][role] = {'state': descriptor['state'], 'reason': descriptor['reason']}
                    continue
                stream.seek(descriptor['byte_offset'])
                selected_bytes += descriptor['byte_size']
                require(selected_bytes <= MAX_SELECTED_BYTES, 'ASSISTANCE_LIMIT', 'Selected prediction bytes exceed limit')
                data = stream.read(descriptor['byte_size'])
                require(hashlib.sha256(data).hexdigest() == descriptor['sha256'],
                        'ASSISTANCE_PREDICTION', 'Selected frame span changed')
                rows = document(data)
                inventory.validate_predictions(rows, sample)
                for row in rows:
                    closed(row, PREDICTION_FIELDS, 'ASSISTANCE_FIELD')
                    vector(row['translation'], 3); vector(row['size'], 3)
                    vector(row['rotation'], 4); vector(row['velocity'], 2); text(row['attribute_name'])
                result[sample][role] = {'state': 'observed', 'value': rows}
    return result


def prediction_rows(output, label):
    if output['state'] != 'observed':
        # Free-form source reasons remain in operator custody; fixed common reason.
        return {'state': output['state'], 'reason': 'Source output unavailable; no empty array is inferred'}
    return {'state': 'observed', 'value': [
        {'id': f'{label}-row-{i+1:04d}', 'translation': vector(r['translation'], 3),
         'size': vector(r['size'], 3), 'rotation': vector(r['rotation'], 4),
         'velocity': vector(r['velocity'], 2), 'detection_name': r['detection_name'],
         'detection_score': number(r['detection_score']), 'attribute_name': text(r['attribute_name'])}
        for i, r in enumerate(output['value'])]}
