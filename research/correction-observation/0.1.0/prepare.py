"""Read only the closed, already-exposed development exports; never full containers."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import time
from common import VERSION, digest, file_digest, linked, need, put, subject, utc, validate_rows


def project(source, ordinal, policy_sha):
    need(len(source['anchors']) == 1, 'Singleton source required')
    a = source['anchors'][0]
    image = {'id': 'image-' + format(ordinal, '02d'), 'ordinal': ordinal, 'policy_sha256': policy_sha,
             'output_a': deepcopy(a['output_a']), 'output_b': deepcopy(a['output_b']),
             'original_reference': deepcopy(a['reference'].get('before'))}
    if linked(image):
        need(a['reference']['state'] == 'alternatives', 'Missing published correction')
        for rows in [image['original_reference'], image['output_a']['value'], image['output_b']['value']]:
            validate_rows(rows)
        answer = deepcopy(a['reference']['after'])
        validate_rows(answer)
    else:
        need(a['reference']['state'] == 'open', 'Blocked reference scope changed')
        answer = None
    return image, answer


def main(area, source):
    started = utc(); tick = time.perf_counter()
    area, source = Path(area).resolve(), Path(source).resolve()
    manifest_path = source / 'OUTBOX/reference-corrections-0.1.0/MANIFEST.json'
    manifest = json.loads(manifest_path.read_text())
    index = {p['path']: p for p in manifest['payloads']}
    reads = []
    def read(relative):
        path = source / relative
        need(relative in index, 'Source missing from retained manifest')
        need(file_digest(path) == index[relative]['sha256'] and path.stat().st_size == index[relative]['bytes'],
             'Source bytes differ from retained manifest')
        reads.append({'path': str(path), 'sha256': file_digest(path), 'bytes': path.stat().st_size})
        return json.loads(path.read_text())
    boundary = read('private/OUTCOME_ACCESS.json')
    policy = read('private/OPERAND_POLICY.json')
    preparation = read('private/development/PREPARATION.json')
    read('sources/LEDGER.json'); read('sources/LEDGER_02.json')
    ids = boundary['development_ids']
    need(len(ids) == 64 and len(set(ids)) == 64 and not (set(ids) & set(boundary['reserved_ids'])), 'Exposure membership changed')
    policy_sha = file_digest(source / 'private/OPERAND_POLICY.json')
    images, source_map = [], []
    for ordinal, image_id in enumerate(ids):
        path = 'private/development/' + image_id + '.boxes.json'
        data = read(path)
        image, answer = project(data, ordinal, policy_sha)
        images.append(image)
        source_map.append({'id': image['id'], 'source_image_id': image_id, 'source': reads[-1]})
        if answer is not None:
            put(area / 'oracle' / (image['id'] + '.json'),
                {'subject_sha256': subject(image), 'answer': answer, 'source_sha256': reads[-1]['sha256']})
    admitted = [im['id'] for im in images if linked(im)]
    need(len(admitted) == preparation['linked'] == 58, 'Input availability changed')
    cases = [{'id': im['id'], 'group': 'singleton', 'images': [im['id']]} for im in images]
    cases += [{'id': 'block-' + format(i // 4, '02d'), 'group': 'block',
               'images': [im['id'] for im in images[i:i+4]]} for i in range(0, 64, 4)]
    cases += [{'id': 'all-64', 'group': 'complete_cohort', 'images': [im['id'] for im in images]},
              {'id': 'linked-58', 'group': 'admitted_cohort', 'images': admitted}]
    visible = {'artifact_id': 'reiyah.correction-observation.visible', 'version': VERSION,
               'images': images, 'cases': cases, 'information': 'Original operands only. No corrected alternatives, sizes or digests.'}
    put(area / 'inputs/visible.json', visible)
    put(area / 'sources/BINDINGS.json', {'artifact_id': 'reiyah.correction-observation.sources', 'version': VERSION,
        'manifest': str(manifest_path), 'manifest_sha256': file_digest(manifest_path),
        'source_commit': manifest['source_commit'], 'reads': reads, 'source_map': source_map,
        'reserved_outcomes_opened': False, 'full_source_containers_opened': False,
        'distribution': 'Private local normalized coordinates only; retained source custody and terms unchanged.'})
    put(area / 'PREPARATION.json', {'artifact_id': 'reiyah.correction-observation.preparation', 'version': VERSION,
        'started_utc': started, 'completed_utc': utc(), 'seconds': time.perf_counter() - tick,
        'visible_sha256': file_digest(area / 'inputs/visible.json'), 'images': 64, 'linked': 58,
        'blocked': 6, 'cases': len(cases), 'source_bindings': len(reads),
        'human_preparation_seconds': None, 'engineering_integration_seconds': None,
        'policy': policy['matching'], 'reserved_outcomes_opened': False})
    print(json.dumps({'prepared_cases': len(cases), 'images': 64, 'linked': 58, 'bound_sources': len(reads)}))


if __name__ == '__main__':
    main(*sys.argv[1:])
