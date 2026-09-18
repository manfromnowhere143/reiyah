"""Admit exact, byte-bound predecessor worlds without a new geometry search."""
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys

from trade_math import require

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'research/public-predictions/0.1.0'))
from compare_math import digest, linked, q, subject, validate_canvas, validate_image, validate_rows, w
from geometric_worlds import alter

AXIS_RADII = (Fraction(1), Fraction(2), Fraction(4), Fraction(8), Fraction(16), Fraction(32), Fraction(64))
PLANAR_RADII = (Fraction(1), Fraction(2), Fraction(4), Fraction(5), Fraction(161, 32),
                Fraction(8), Fraction(16), Fraction(32), Fraction(64))


def read(path):
    return json.loads(Path(path).read_text())


def file_digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def radius_key(radius):
    radius = Fraction(radius)
    return str(radius.numerator) + '_' + str(radius.denominator)


def families():
    result = [{'id': key, 'kind': key, 'radius': None} for key in
              ('exact_projection', 'one_edit_global', 'one_edit_per_image')]
    for kind, radii in [('axis_translation', AXIS_RADII), ('planar_translation', PLANAR_RADII)]:
        result.extend({'id': kind + '_' + radius_key(radius), 'kind': kind, 'radius': w(radius)} for radius in radii)
    return result


def checked_index(entries, expected_ids, directory, prefix=''):
    result = {}
    for entry in entries:
        iid = entry['image_id']
        require(iid in expected_ids and iid not in result, 'Unknown or repeated source image')
        require(entry['path'] == prefix + iid + '.json', 'Source path changes image identity')
        path = directory / entry['path']
        require(path.is_file() and file_digest(path) == entry['sha256'], 'Missing or changed source record')
        result[iid] = path
    require(set(result) == set(expected_ids), 'Source omits an allocated image')
    return result


def source_pair(directory, flag):
    path = directory / 'RESULTS.json'; result = read(path); verification = read(directory / 'VERIFICATION.json')
    require(verification['results_sha256'] == file_digest(path) and verification[flag] is True,
            'Predecessor results do not match their successful verification')
    require(verification['independent_scientific_replication'] is False, 'Source verification scope differs')
    return result, verification


def translated_world(references, edit):
    if edit['operation'] == 'none':
        require(edit == {'operation': 'none'}, 'Unknown unchanged-world fields')
        return references
    require(edit['operation'] in ('translation', 'translation_2d'), 'Unknown translation operation')
    ids = [row['id'] for row in references]
    require(edit['source_reference_id'] in ids, 'Translated source does not exist')
    source = references[ids.index(edit['source_reference_id'])]
    require(source['record_sha256'] == edit['source_reference_sha256'], 'Translated source bytes differ')
    require(edit['translated_reference']['id'] not in ids, 'Translated identity collides')
    return [row for row in references if row['id'] != source['id']] + [edit['translated_reference']]


def component(image, original, world, measurement, proof, source_path, pointer, admission):
    validate_rows(world); validate_canvas(world, image)
    counts = [len(image[role]['value']) for role in ('output_a', 'output_b')]
    ranks = measurement['ranks']
    require(len(ranks) == 2 and all(type(rank) is int and 0 <= rank <= min(count, len(world))
                                  for rank, count in zip(ranks, counts)), 'Invalid retained matching count')
    require(q(measurement['delta']) == counts[0] - counts[1] + 2 * (ranks[1] - ranks[0]),
            'Retained unit difference contradicts its counts')
    source = {'path': str(source_path), 'sha256': file_digest(source_path), 'pointer': pointer}
    key = digest({'subject_sha256': subject(image), 'world': world, 'source': source})
    return key, {'image_id': image['id'], 'subject_sha256': subject(image),
                 'original_reference_sha256': digest(original), 'world_reference_sha256': digest(world),
                 'world': world, 'measurement': measurement, 'native_proof': proof, 'source': source,
                 'admission': admission, 'prediction_counts': counts, 'reference_count': len(world)}


def load_sources(freeze):
    comparison = Path(freeze['predecessor_comparison']); analysis = comparison / 'runs/analysis-01'
    axis = Path(freeze['axis_run']); planar = Path(freeze['planar_run'])
    visible = read(comparison / 'inputs/visible.json'); images = {row['id']: row for row in visible['images']}
    require(len(images) == len(visible['images']) == 64 and len(visible['cases']) == 73, 'Wrong exposed allocation')
    require(len({row['id'] for row in visible['cases']}) == 73, 'Repeated case identity')
    for case in visible['cases']:
        require(case['images'] and len(case['images']) == len(set(case['images'])) and set(case['images']) <= set(images),
                'Case membership is incomplete or repeated')
    analysis_result, analysis_check = source_pair(analysis, 'all_assigned_rows_verified')
    axis_result, _ = source_pair(axis, 'all_assigned_rows_verified')
    planar_result, planar_check = source_pair(planar, 'all_complete_rows_verified')
    require(analysis_check['achieved_universal_extrema_images'] == {'lower': 64, 'upper': 64}
            and planar_check['all_assigned_rows_accounted_for'] is True
            and planar_check['totals']['bound_gap_image_radius_rows'] == 0,
            'Transfer requires verified attained extrema')
    require(not analysis_result['search_failures'] and not axis_result['failures'], 'A predecessor search failed')
    analysis_paths = checked_index(analysis_result['image_records'], images, analysis)
    axis_paths = checked_index(axis_result['image_records'], images, axis)
    planar_paths = {}
    for radius in PLANAR_RADII:
        key = 'r' + radius_key(radius); batch = planar_result['batches'][key]
        require(q(batch['radius']) == radius, 'Wrong planar radius batch')
        planar_paths[radius] = checked_index(batch['records'], images, planar, key + '-')
    pool, contexts = {}, {}
    for iid, image in images.items():
        validate_image(image); require(linked(image), 'Unavailable input is not an empty answer')
        oracle = read(comparison / 'oracle' / (iid + '.json')); original = oracle['answer']
        require(oracle['subject_sha256'] == subject(image), 'Oracle context differs')
        validate_rows(original); validate_canvas(original, image)
        axis_row = read(axis_paths[iid]); broad = read(analysis_paths[iid])
        require(axis_row['subject_sha256'] == subject(image) and axis_row['reference_sha256'] == digest(original),
                'Axis operand context differs')
        require(broad['image_id'] == iid and broad['search_state'] == 'complete', 'Broad source is incomplete')
        context = {'image': image, 'original': original, 'count_difference': len(image['output_a']['value']) - len(image['output_b']['value']),
                   'families': {}}

        def admit(world, measured, proof, path, pointer, admission):
            key, value = component(image, original, world, measured, proof, path, pointer, admission)
            require(key not in pool or pool[key] == value, 'Conflicting source alias')
            pool[key] = value
            return key

        nominal_witness = axis_row['radii']['0']['lower']; nominal_proof = axis_row['proofs'][nominal_witness['proof_key']]
        require(nominal_witness['edit'] == {'operation': 'none'} and nominal_proof['reference_sha256'] == digest(original),
                'Nominal reference world changed')
        nominal = admit(original, nominal_proof['measurement'], nominal_proof['proof'], axis_paths[iid],
                        '/radii/0/lower', {'kind': 'exact_projection', 'radius': None, 'edit': {'operation': 'none'}})
        require(pool[nominal]['measurement'] == broad['nominal']['nominal'], 'Nominal source measurements differ')
        context['nominal'] = nominal; context['families']['exact_projection'] = {'worlds': [nominal, nominal],
            'unit_bounds': [pool[nominal]['measurement']['delta']] * 2}
        broad_keys = []
        for index, direction in enumerate(('lower', 'upper')):
            witness = broad['search']['witnesses'][direction]; world = alter(original, witness['edit'])
            require(world == witness['altered_references']
                    and witness['measurement']['delta'] == broad['nominal']['edit_bounds'][index],
                    'Broad bound is not attained by its retained edit')
            broad_keys.append(admit(world, witness['measurement'], witness['native_proof'], analysis_paths[iid],
                '/search/witnesses/' + direction, {'kind': 'one_edit_per_image', 'radius': None, 'edit': witness['edit']}))
        for name in ('one_edit_global', 'one_edit_per_image'):
            context['families'][name] = {'worlds': broad_keys, 'unit_bounds': broad['nominal']['edit_bounds']}
        for radius in AXIS_RADII:
            radius_text = str(radius.numerator); witnesses = axis_row['radii'][radius_text]; keys = []; values = []
            for direction in ('lower', 'upper'):
                witness = witnesses[direction]; world = translated_world(original, witness['edit']); proof = axis_row['proofs'][witness['proof_key']]
                require(proof['subject_sha256'] == subject(image) and proof['reference_sha256'] == digest(world)
                        and proof['measurement']['delta'] == witness['delta'], 'Axis witness proof binding differs')
                keys.append(admit(world, proof['measurement'], proof['proof'], axis_paths[iid], '/radii/' + radius_text + '/' + direction,
                    {'kind': 'axis_translation', 'radius': w(radius), 'edit': witness['edit']})); values.append(witness['delta'])
            context['families']['axis_translation_' + radius_key(radius)] = {'worlds': keys, 'unit_bounds': values}
        for radius in PLANAR_RADII:
            path = planar_paths[radius][iid]; record = read(path)
            require(record['subject_sha256'] == subject(image) and record['reference_sha256'] == digest(original)
                    and q(record['radius']) == radius and record['exact_extrema'] is True
                    and record['universal_bounds'] == record['attained_bounds'], 'Planar source is not exact in this context')
            keys = []
            for direction in ('lower', 'upper'):
                witness = record['witnesses'][direction]; world = translated_world(original, witness['edit']); proof = record['proofs'][witness['proof_key']]
                require(proof['subject_sha256'] == subject(image) and proof['reference_sha256'] == digest(world)
                        and proof['measurement']['delta'] == witness['delta'], 'Planar witness proof binding differs')
                keys.append(admit(world, proof['measurement'], proof['proof'], path, '/witnesses/' + direction,
                    {'kind': 'planar_translation', 'radius': w(radius), 'edit': witness['edit']}))
            context['families']['planar_translation_' + radius_key(radius)] = {'worlds': keys, 'unit_bounds': record['universal_bounds']}
        require(set(context['families']) == {row['id'] for row in families()}, 'Missing image family')
        center = q(pool[nominal]['measurement']['delta'])
        for value in context['families'].values():
            require(q(value['unit_bounds'][0]) <= center <= q(value['unit_bounds'][1]), 'Source interval excludes its nominal world')
        contexts[iid] = context
    return visible, contexts, pool


def compose(case, family, contexts, pool):
    members = case['images']; nominal = {iid: contexts[iid]['nominal'] for iid in members}
    worlds, limits = [], []
    for index in (0, 1):
        selected = {iid: contexts[iid]['families'][family['id']]['worlds'][index] for iid in members}
        if family['kind'] == 'one_edit_global':
            changes = {iid: q(pool[selected[iid]]['measurement']['delta']) - q(pool[nominal[iid]]['measurement']['delta']) for iid in members}
            best = min(changes, key=lambda iid: (changes[iid], iid)) if index == 0 else max(changes, key=lambda iid: (changes[iid], iid))
            selected = dict(nominal)
            if changes[best]: selected[best] = contexts[best]['families'][family['id']]['worlds'][index]
            total = sum((q(pool[key]['measurement']['delta']) for key in selected.values()), Fraction(0))
        else:
            total = sum((q(contexts[iid]['families'][family['id']]['unit_bounds'][index]) for iid in members), Fraction(0))
        attained = sum((q(pool[selected[iid]]['measurement']['delta']) for iid in members), Fraction(0))
        require(attained == total, 'Composed source extremum is not attained')
        limits.append(total / len(members)); worlds.append([{'image_id': iid, 'component': selected[iid]} for iid in members])
    require(limits[0] <= limits[1], 'Reversed source enclosure')
    return {'unit_bounds': list(map(w, limits)), 'worlds': worlds,
            'count_difference': w(Fraction(sum(contexts[iid]['count_difference'] for iid in members), len(members)))}
