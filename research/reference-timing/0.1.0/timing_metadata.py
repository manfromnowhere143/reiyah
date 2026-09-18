"""Retain the complete preceding car census for the same 64 camera records.

This adapter reads metadata only. It never opens an image or prediction packet.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time

ARCHIVE_SHA256 = 'db48746b10e3544d5ef619eaa3d687e3960626fe1b4422ed856711da5aa7325b'
SELECTED_SHA256 = 'b2f53e74780c62414a477dd725bea1b1f16e8f2200fb45abf3e0d1cb77bc2bb6'
TABLES = ('sample', 'sample_annotation', 'instance')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def file_binding(path):
    path = Path(path).resolve(); digest = hashlib.sha256(); size = 0
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(block); size += len(block)
    return {'path': str(path), 'sha256': digest.hexdigest(), 'bytes': size}


def read(path):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'Duplicate JSON key')
            result[key] = value
        return result
    def invalid(value):
        raise ValueError('Nonfinite JSON constant: ' + value)
    return json.loads(Path(path).read_bytes(), object_pairs_hook=pairs, parse_constant=invalid)


def put(path, value):
    with Path(path).open('x') as handle:
        json.dump(value, handle, sort_keys=True, indent=2, allow_nan=False); handle.write('\n')


def collect_rows(selected, rows):
    targets = {sample['prev'] for sample in selected['sample'].values() if sample['prev']}
    car_categories = {key for key, value in selected['category'].items() if value['name'] == 'vehicle.car'}
    require(len(car_categories) == 1, 'Exactly one car category required')
    tables = {name: {} for name in TABLES}; scanned = Counter()
    # Do not depend on table order. All instance joins are filtered after the
    # selected sample annotations have been collected, then discarded.
    for filename, row in rows:
        name = filename.removesuffix('.json')
        require(name in TABLES and type(row) is dict and type(row.get('token')) is str
                and row['token'], 'Invalid metadata row')
        scanned[name] += 1
        if name == 'sample' and row['token'] not in targets:
            continue
        if name == 'sample_annotation' and row['sample_token'] not in targets:
            continue
        if name == 'instance':
            require(row['category_token'] in selected['category'], 'Unknown instance category')
        require(row['token'] not in tables[name], 'Duplicate retained metadata record')
        tables[name][row['token']] = row
    require(set(tables['sample']) == targets, 'Incomplete preceding sample membership')
    require(set(scanned) == set(TABLES), 'Missing streamed metadata table')
    for sample in selected['sample'].values():
        if not sample['prev']:
            continue
        previous = tables['sample'][sample['prev']]
        require(previous['scene_token'] == sample['scene_token']
                and previous['next'] == sample['token']
                and type(previous['timestamp']) is int and type(sample['timestamp']) is int
                and previous['timestamp'] < sample['timestamp'], 'Inconsistent preceding sample link')
        if previous['token'] in selected['sample']:
            require(previous == selected['sample'][previous['token']], 'Inherited sample record changed')
    # A car annotation is determined by the complete instance/category tables,
    # never by projection visibility or a previous prediction match.
    require(all(value['instance_token'] in tables['instance'] for value in tables['sample_annotation'].values()),
            'Missing annotation instance')
    car_instances = {key for key, value in tables['instance'].items() if value['category_token'] in car_categories}
    car_annotations = {key: value for key, value in tables['sample_annotation'].items()
                       if value['instance_token'] in car_instances}
    identities = set()
    for annotation in car_annotations.values():
        identity = annotation['sample_token'], annotation['instance_token']
        require(identity not in identities, 'Duplicate instance in a preceding sample')
        identities.add(identity)
        if annotation['token'] in selected['sample_annotation']:
            require(annotation == selected['sample_annotation'][annotation['token']],
                    'Inherited annotation record changed')
    instances = {value['instance_token'] for value in car_annotations.values()}
    tables['instance'] = {key: tables['instance'][key] for key in sorted(instances)}
    tables['sample_annotation'] = car_annotations
    for key, value in tables['instance'].items():
        if key in selected['instance']:
            require(value == selected['instance'][key], 'Inherited instance record changed')
    return tables, dict(scanned)


def run(freeze_path, output):
    tick = time.perf_counter(); started = datetime.now(timezone.utc).isoformat()
    freeze = read(freeze_path)
    for row in freeze['bindings']:
        require(file_binding(row['path']) == row, 'Preparation input or code changed')
    selected = read(freeze['selected_metadata'])
    require(file_binding(freeze['selected_metadata'])['sha256'] == SELECTED_SHA256,
            'Wrong selected metadata')
    require(file_binding(freeze['archive'])['sha256'] == ARCHIVE_SHA256, 'Wrong source archive')
    require(len(selected['sample']) == len(selected['sample_data']) == 64, 'Wrong camera allocation')
    output = Path(output).resolve(); output.mkdir()
    root = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(root / 'tools/measure'))
    from reference_study import metadata
    tables, scanned = collect_rows(selected, metadata(freeze['archive'], [name + '.json' for name in TABLES]))
    put(output / 'PRECEDING_METADATA.json', tables)
    report = {'artifact_id': 'reiyah.reference-timing.metadata', 'version': '0.1.0',
              'started_utc': started, 'finished_utc': datetime.now(timezone.utc).isoformat(),
              'seconds': time.perf_counter() - tick, 'freeze': file_binding(freeze_path),
              'selected_metadata': file_binding(freeze['selected_metadata']),
              'metadata': file_binding(output / 'PRECEDING_METADATA.json'),
              'scanned_by_table': scanned, 'retained_by_table': {key: len(value) for key, value in tables.items()},
              'selected_samples': 64, 'without_preceding_sample': sum(not s['prev'] for s in selected['sample'].values()),
              'new_image_reads': 0, 'model_calls': 0, 'scored_comparisons': 0, 'reserved_outcomes_accessed': 0,
              'human_seconds': None, 'economic_cost': None}
    put(output / 'RESULT.json', report)
    print(json.dumps(report), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--freeze', required=True); parser.add_argument('--output', required=True)
    args = parser.parse_args(); run(args.freeze, args.output)
