"""Separate world counts and affine sign checks for the penalty-share study."""
from fractions import Fraction
from pathlib import Path
import sys

from trade_math import require
from trade_sources import digest, file_digest, q, read, subject, validate_canvas, validate_image, validate_rows, w

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'research/reference-translation/0.1.0'))
from axis_certificate import exact_iou, maximum_matching
from compare_math import graph
from tools.perception_revision import checker


def geometry(row):
    return tuple(map(q, row['xyxy']))


def check_admission(original, world, admission):
    kind, edit = admission['kind'], admission['edit']; original_ids = {row['id'] for row in original}
    if kind == 'exact_projection':
        require(admission['radius'] is None and edit == {'operation': 'none'} and world == original,
                'Exact reference was changed'); return
    if kind == 'one_edit_per_image':
        require(admission['radius'] is None and set(edit) == {'operation', 'removed_reference', 'inserted_reference'}, 'Invalid arbitrary edit')
        removed, inserted = edit['removed_reference'], edit['inserted_reference']; op = edit['operation']
        require(op in ('none', 'insertion', 'deletion', 'replacement')
                and (removed is not None) == (op in ('deletion', 'replacement'))
                and (inserted is not None) == (op in ('insertion', 'replacement')), 'Wrong edit cardinality')
        require(removed is None or removed in original_ids, 'Removed reference missing')
        require(inserted is None or inserted['id'] not in original_ids, 'Inserted identity collision')
        expected = [row for row in original if row['id'] != removed]
        if inserted is not None: expected.append(inserted)
        require(world == expected, 'Arbitrary world differs from its single edit'); return
    require(kind in ('axis_translation', 'planar_translation'), 'Unknown source family')
    radius = q(admission['radius']); require(0 <= radius <= 64, 'Wrong source radius')
    if edit == {'operation': 'none'}:
        require(world == original, 'Unchanged translation world differs'); return
    source_id = edit['source_reference_id']; source = [row for row in original if row['id'] == source_id]
    require(len(source) == 1 and edit['source_reference_sha256'] == source[0]['record_sha256'], 'Translation source differs')
    source = source[0]; base = geometry(source); moved = edit['translated_reference']; box = geometry(moved)
    require(moved['id'] not in original_ids and world == [row for row in original if row['id'] != source_id] + [moved],
            'Translation changes more than one source')
    require(box[2] - box[0] == base[2] - base[0] and box[3] - box[1] == base[3] - base[1], 'Translation changed shape')
    offset = (box[0] - base[0], box[1] - base[1]); distance = max(map(abs, offset))
    require(distance <= radius, 'World exceeds its admitted radius')
    if kind == 'axis_translation':
        require(set(edit) == {'operation', 'source_reference_id', 'source_reference_sha256', 'axis', 'position', 'distance', 'translated_reference'}
                and edit['operation'] == 'translation' and type(edit['axis']) is int and edit['axis'] in (0, 1), 'Wrong axis edit')
        axis = edit['axis']
        require(offset[1-axis] == 0 and q(edit['position']) == box[axis] and q(edit['distance']) == distance, 'Axis motion differs')
    else:
        require(set(edit) == {'operation', 'source_reference_id', 'source_reference_sha256', 'reference_index', 'position', 'offset', 'linf_distance', 'translated_reference'}
                and edit['operation'] == 'translation_2d', 'Wrong planar edit')
        require(edit['reference_index'] == original.index(source) and tuple(map(q, edit['position'])) == box[:2]
                and tuple(map(q, edit['offset'])) == offset and q(edit['linf_distance']) == distance, 'Planar motion differs')


def check_component(image, original, component, cache, allowed_sources):
    validate_image(image); world = component['world']; validate_rows(world); validate_canvas(world, image)
    require(component['image_id'] == image['id'] and component['subject_sha256'] == subject(image)
            and component['original_reference_sha256'] == digest(original)
            and component['world_reference_sha256'] == digest(world), 'Component subject changed')
    source = component['source']; path = source['path']
    require(path in allowed_sources and source['sha256'] == allowed_sources[path], 'Unbound predecessor source')
    if path not in cache['sources']:
        require(file_digest(path) == source['sha256'], 'Predecessor source bytes changed')
        cache['sources'][path] = read(path)
    require(type(source['pointer']) is str and source['pointer'].startswith('/'), 'Source pointer missing')
    selected = cache['sources'][path]
    for part in source['pointer'].split('/')[1:]:
        require(type(selected) is dict and part in selected, 'Source pointer does not resolve')
        selected = selected[part]
    admission = component['admission']; check_admission(original, world, admission)
    require(selected['edit'] == admission['edit'], 'Component changes the retained source edit')
    if admission['kind'] == 'one_edit_per_image':
        require(selected['measurement'] == component['measurement'] and selected['native_proof'] == component['native_proof']
                and selected['altered_references'] == world, 'Arbitrary source witness changed')
    else:
        owner = cache['sources'][path]; proof = owner['proofs'][selected['proof_key']]
        require(proof['measurement'] == component['measurement'] and proof['proof'] == component['native_proof']
                and proof['subject_sha256'] == subject(image) and proof['reference_sha256'] == digest(world), 'Source proof changed')
    context_key = digest({'subject': subject(image), 'references': world})
    if context_key not in cache['counts']:
        counts = []
        for role in ('output_a', 'output_b'):
            predictions = image[role]['value']
            adjacency = {row['id']: {ref['id'] for ref in world if exact_iou(geometry(row), geometry(ref)) >= Fraction(1, 2)}
                         for row in predictions}
            matching = maximum_matching(adjacency)
            counts.append({'predictions': len(predictions), 'references': len(world), 'matches': matching,
                           'false_positives': len(predictions)-matching, 'misses': len(world)-matching})
        cache['counts'][context_key] = counts
    counts = cache['counts'][context_key]; unit = sum(counts[0][name] - counts[1][name] for name in ('false_positives', 'misses'))
    require(component['prediction_counts'] == [counts[0]['predictions'], counts[1]['predictions']]
            and component['reference_count'] == len(world)
            and component['measurement'] == {'ranks': [counts[0]['matches'], counts[1]['matches']], 'delta': w(Fraction(unit))},
            'Retained ranks or counts disagree with independent matching')
    native = graph(image, world); proof = component['native_proof']; proof_key = digest({'graph': native, 'payload': proof['payload']})
    require(proof['graph_sha256'] == digest(native), 'Native graph context changed')
    if proof_key not in cache['native']:
        checker.check(native, proof['payload']); cache['native'].add(proof_key)
    require(proof['payload']['result']['bounds']['lower'] == w(Fraction(unit))
            and proof['payload']['result']['bounds']['upper'] == w(Fraction(unit)), 'Native unit result differs')
    return {'counts': counts, 'false_positive_difference': counts[0]['false_positives'] - counts[1]['false_positives'],
            'miss_difference': counts[0]['misses'] - counts[1]['misses'], 'unit': Fraction(unit)}


def linear_world(components, verified, members):
    require([row['image_id'] for row in components] == members, 'Composed world drops or changes a member')
    fp = fn = Fraction(0)
    for row in components:
        require(row['component'] in verified, 'Unverified source world')
        value = verified[row['component']]
        require(value['image_id'] == row['image_id'], 'World assigned to wrong image')
        fp += value['false_positive_difference']; fn += value['miss_difference']
    return fp / len(members), (fn - fp) / len(members)


def evaluate(functions, p):
    return tuple(intercept + slope * p for intercept, slope in functions)


def outcome(interval):
    low, high = interval
    require(low <= high, 'Weighted interval reversed')
    if low > 0: return 'supported'
    if high <= 0: return 'excluded'
    return 'unresolved'


def check_cells(cells, functions):
    roots = {Fraction(0), Fraction(1)}
    for intercept, slope in functions:
        if slope:
            root = -intercept / slope
            if 0 <= root <= 1: roots.add(root)
    ordered = sorted(roots); expected = []
    for index, cut in enumerate(ordered):
        if index: expected.append((ordered[index-1], cut, False))
        expected.append((cut, cut, True))
    require(len(cells) == len(expected), 'Missing continuum point or open cell')
    for cell, (left, right, point) in zip(cells, expected):
        representative = (left + right) / 2
        require(q(cell['left']) == left and q(cell['right']) == right and cell['point'] is point
                and q(cell['representative']) == representative, 'Continuum coverage or endpoint changed')
        interval = evaluate(functions, representative)
        require(cell['bounds'] == list(map(w, interval)) and cell['decision'] == outcome(interval), 'Continuum decision differs')
    return len(cells)
