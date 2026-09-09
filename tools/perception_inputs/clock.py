"""Clock population and historical-exposure exclusions, independent of predictions."""
import ast
from collections import Counter, defaultdict
from pathlib import PurePosixPath
import re
import tarfile

from tools.perception_decision.contract import Invalid
from .source_io import digest_value, document, require

CONTEXT_US = 2_000_000
MAX_DOCUMENT_BYTES = 16 << 20


def identity(value):
    require(type(value) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:-]{0,95}', value) is not None,
            'CLOCK_IDENTITY', 'Invalid metadata identity')
    return value


def timestamp(value):
    require(type(value) is int and 0 < value < (1 << 63), 'CLOCK_TIME', 'Require a positive integer microsecond timestamp')
    return value


def validation_names(stream):
    data = stream.read((1 << 20) + 1)
    require(len(data) <= 1 << 20, 'SPLIT_SIZE', 'Split source exceeds its byte limit')
    try:
        tree = ast.parse(data.decode('utf-8'))
        nodes = [node.value for node in tree.body if isinstance(node, ast.Assign)
                 and any(isinstance(target, ast.Name) and target.id == 'val' for target in node.targets)]
        require(len(nodes) == 1, 'SPLIT_ASSIGNMENT', 'Require one literal validation split')
        names = ast.literal_eval(nodes[0])
    except (UnicodeError, SyntaxError, ValueError, RecursionError) as exc:
        if isinstance(exc, Invalid):
            raise
        raise Invalid('SPLIT_ASSIGNMENT', 'Validation split is not a literal assignment') from exc
    require(type(names) is list and 0 < len(names) <= 1000 and all(type(n) is str for n in names),
            'SPLIT_ASSIGNMENT', 'Invalid validation scene list')
    for name in names:
        identity(name)
    require(len(names) == len(set(names)), 'SPLIT_ASSIGNMENT', 'Duplicate validation scene name')
    return names


def metadata_tables(stream):
    """Read only scene/sample tables; never extract archive paths into the filesystem."""
    wanted = {'scene.json', 'sample.json'}
    tables, seen, expanded = {}, set(), 0
    try:
        with tarfile.open(fileobj=stream, mode='r|gz') as archive:
            for member in archive:
                path = PurePosixPath(member.name)
                require(not path.is_absolute() and '..' not in path.parts and '\\' not in member.name,
                        'METADATA_ARCHIVE', 'Unsafe archive member name')
                require(member.name not in seen and len(seen) < 10000 and (member.isfile() or member.isdir()),
                        'METADATA_ARCHIVE', 'Duplicate, linked or unsupported archive member')
                seen.add(member.name)
                expanded += member.size
                require(0 <= member.size and expanded <= 4 << 30, 'METADATA_SIZE', 'Expanded metadata exceeds its limit')
                if path.name not in wanted:
                    continue
                require(member.name == 'v1.0-trainval/' + path.name and member.isfile() and path.name not in tables,
                        'METADATA_ARCHIVE', 'Ambiguous metadata table identity')
                require(member.size <= MAX_DOCUMENT_BYTES, 'METADATA_SIZE', 'Selected table exceeds its byte limit')
                source = archive.extractfile(member)
                require(source is not None, 'METADATA_ARCHIVE', 'Missing table bytes')
                data = source.read(member.size + 1)
                require(len(data) == member.size, 'METADATA_SIZE', 'Truncated metadata table')
                rows = document(data)
                require(type(rows) is list and len(rows) <= 50000, 'METADATA_TABLE', 'Invalid or oversized metadata table')
                tables[path.name] = rows
    except (tarfile.TarError, EOFError) as exc:
        raise Invalid('METADATA_ARCHIVE', 'Malformed metadata archive') from exc
    require(set(tables) == wanted, 'METADATA_TABLE', 'Required metadata table is missing')
    return tables


def population(tables, names):
    scenes, samples = {}, {}
    for table, fields, output in [('scene.json', ('name', 'nbr_samples', 'first_sample_token', 'last_sample_token'), scenes),
                                   ('sample.json', ('scene_token', 'timestamp', 'prev', 'next'), samples)]:
        for row in tables[table]:
            require(type(row) is dict and all(k in row for k in ('token', *fields)), 'METADATA_ROW', 'Required metadata field is missing')
            token = identity(row['token'])
            require(token not in output, 'CLOCK_IDENTITY', 'Duplicate metadata token')
            output[token] = {k: row[k] for k in fields}
    chosen = {token for token, row in scenes.items() if row['name'] in names}
    require(Counter(scenes[t]['name'] for t in chosen) == Counter(names), 'CLOCK_SPLIT', 'Requested scene membership differs')
    by_scene = defaultdict(list)
    for token, row in samples.items():
        scene = identity(row['scene_token'])
        require(scene in scenes, 'CLOCK_IDENTITY', 'Sample has an unknown scene')
        by_scene[scene].append((timestamp(row['timestamp']), token))
        for role in ('prev', 'next'):
            if row[role] != '':
                identity(row[role])
    anchors = []
    for scene, definition in sorted(scenes.items()):
        identity(definition['name'])
        count = definition['nbr_samples']
        require(type(count) is int and count > 0, 'CLOCK_CHAIN', 'Invalid declared scene count')
        ordered = sorted(by_scene[scene])
        require(len(ordered) == count, 'CLOCK_CHAIN', 'Scene sample count differs')
        require(ordered[0][1] == definition['first_sample_token'] and ordered[-1][1] == definition['last_sample_token'],
                'CLOCK_CHAIN', 'Scene endpoint identity differs')
        times = [t for t, _ in ordered]
        require(all(a < b for a, b in zip(times, times[1:])), 'CLOCK_CHAIN', 'Sample times are not strictly increasing')
        for i, (time, token) in enumerate(ordered):
            require(samples[token]['prev'] == (ordered[i-1][1] if i else '') and
                    samples[token]['next'] == (ordered[i+1][1] if i+1 < len(ordered) else ''),
                    'CLOCK_CHAIN', 'Sample links disagree with clock order')
            if scene in chosen:
                anchors.append({'sample_token': token, 'scene_token': scene, 'scene_name': definition['name'],
                                'anchor_timestamp_us': time, 'context_window_us': [time-CONTEXT_US, time+CONTEXT_US],
                                'has_declared_scene_context': time-times[0] >= CONTEXT_US and times[-1]-time >= CONTEXT_US,
                                'sensor_window_validity': 'not_checked'})
    require(bool(anchors), 'CLOCK_SPLIT', 'Empty clock population')
    return anchors


def exposure_windows(stream, anchors):
    """Consume only time/asset-presence fields from the hash-bound historical packets."""
    data = stream.read(MAX_DOCUMENT_BYTES + 1)
    require(len(data) <= MAX_DOCUMENT_BYTES, 'EXPOSURE_SIZE', 'Exposure records exceed their byte limit')
    packets = document(data)
    require(type(packets) is list and len(packets) <= 10000, 'EXPOSURE_RECORD', 'Invalid exposure packet list')
    clock = defaultdict(list)
    for row in anchors:
        clock[row['anchor_timestamp_us']].append(row)
    seen, windows, boundary_count, exposed_count = set(), defaultdict(list), 0, 0
    for packet in packets:
        require(type(packet) is dict and all(k in packet for k in ('case_id', 'candidate_sample_timestamp_us', 'evidence')),
                'EXPOSURE_RECORD', 'Missing exposure packet fields')
        case = identity(packet['case_id'])
        require(case not in seen, 'EXPOSURE_RECORD', 'Duplicate exposed case')
        seen.add(case)
        anchor_time = timestamp(packet['candidate_sample_timestamp_us'])
        require(len(clock[anchor_time]) == 1, 'EXPOSURE_JOIN', 'Exposed anchor is absent or ambiguous in the clock')
        evidence = packet['evidence']
        require(type(evidence) is list and len(evidence) <= 128, 'EXPOSURE_RECORD', 'Invalid exposure evidence list')
        times, evidence_ids = [anchor_time-CONTEXT_US, anchor_time+CONTEXT_US], set()
        for row in evidence:
            require(type(row) is dict and 'state' in row and 'evidence_id' in row, 'EXPOSURE_RECORD', 'Missing exposure identity or state')
            eid = row['evidence_id']
            # Historical evidence IDs include signed frame offsets, e.g. -1:CAM_FRONT.
            # They are opaque record keys, not dataset sample tokens or core graph IDs.
            require(type(eid) is str and re.fullmatch(r'[A-Za-z0-9_.:+-]{1,128}', eid) is not None,
                    'EXPOSURE_RECORD', 'Invalid historical evidence identity')
            require(eid not in evidence_ids, 'EXPOSURE_RECORD', 'Repeated evidence identity within a case')
            evidence_ids.add(eid)
            if row['state'] == 'available':
                require(digest_value(row.get('asset_sha256')) and 'sensor_timestamp_us' in row,
                        'EXPOSURE_INCOMPLETE', 'Exposed asset lacks its identity or timestamp')
                times.append(timestamp(row['sensor_timestamp_us']))
                exposed_count += 1
            else:
                require(row['state'] == 'scene_boundary' and row.get('asset_sha256') is None and
                        row.get('sensor_timestamp_us') is None and row.get('relative_asset_path') is None,
                        'EXPOSURE_INCOMPLETE', 'Unknown exposure cannot be treated as a boundary placeholder')
                boundary_count += 1
        windows[clock[anchor_time][0]['scene_token']].append((min(times), max(times)))
    return windows, {'case_count': len(seen), 'exposed_assets': exposed_count, 'scene_boundary_placeholders': boundary_count}


def apply_exclusions(anchors, windows):
    for row in anchors:
        if not row['has_declared_scene_context']:
            row['eligibility'] = 'outside_scene_context'
        elif windows is None:
            row['eligibility'] = 'exposure_history_unavailable'
        else:
            start, end = row['context_window_us']
            overlaps = any(start <= hi and end >= lo for lo, hi in windows.get(row['scene_token'], []))
            row['eligibility'] = 'excluded_prior_exposure' if overlaps else 'eligible_under_declared_rule'
