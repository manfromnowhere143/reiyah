"""Bounded exact-rational reference-edit witnesses after complete observation.

Axis sweeps cover every cell for their fixed shape and fixed orthogonal
position. The finite union of those sweeps is not an exhaustive search over
all possible rectangles. Every retained witness is checked as a full world.
"""
from fractions import Fraction
import time

from admission import digest, require
from compare_math import (ROLES, checked_ranks, graph_ranks, iou, measure, q, validate_canvas,
                          validate_rows, w)
from refine import rectangles as predecessor_rectangles

MAX_RECTANGLES = 100000
MAX_PAIRS = 2000000


def coordinates(row):
    return tuple(q(value) for value in row['xyxy'])


def record(values):
    geometry = [w(value) for value in values]
    identity = 'stress:' + digest(geometry)
    return {'id': identity, 'record_sha256': digest({'id': identity, 'xyxy': geometry}), 'xyxy': geometry}


def clipped(values, width, height):
    x1, y1, x2, y2 = values
    values = (max(Fraction(0), x1), max(Fraction(0), y1), min(Fraction(width), x2), min(Fraction(height), y2))
    return values if values[2] > values[0] and values[3] - values[1] >= 25 else None


def translation_interval(base, detection, axis, width, height):
    """Exact positions with IoU >= 1/2 for one fixed shape and orthogonal pose."""
    require(axis in (0, 1), 'GEOMETRY', 'Axis must be horizontal or vertical')
    base, detection = tuple(map(Fraction, base)), tuple(map(Fraction, detection))
    orthogonal = 1 - axis
    extent = base[axis + 2] - base[axis]
    other_extent = base[orthogonal + 2] - base[orthogonal]
    d_extent = detection[axis + 2] - detection[axis]
    d_other = detection[orthogonal + 2] - detection[orthogonal]
    overlap = min(base[orthogonal + 2], detection[orthogonal + 2]) - max(base[orthogonal], detection[orthogonal])
    if overlap <= 0:
        return None
    required = (extent * other_extent + d_extent * d_other) / (3 * overlap)
    if required > min(extent, d_extent):
        return None
    domain = (width if axis == 0 else height) - extent
    lower = max(Fraction(0), detection[axis] + required - extent)
    upper = min(Fraction(domain), detection[axis + 2] - required)
    return (lower, upper) if lower <= upper else None


def sweep(base, detections, axis, width, height):
    extent = base[axis + 2] - base[axis]
    limit = Fraction(width if axis == 0 else height) - extent
    require(limit >= 0, 'GEOMETRY', 'Base shape exceeds image')
    positions = {Fraction(0), limit, base[axis]}
    for detection in detections:
        bounds = translation_interval(base, detection, axis, width, height)
        if bounds is not None:
            positions.update(bounds)
    endpoints = sorted(positions)
    positions.update((first + second) / 2 for first, second in zip(endpoints, endpoints[1:]))
    for position in sorted(positions):
        values = list(base); values[axis] = position; values[axis + 2] = position + extent
        yield tuple(values)


def candidate_rectangles(image, references):
    """Declared fixed constructions plus complete one-axis translation cells."""
    width, height = image['width'], image['height']
    detections = {row['id']: row for role in ROLES for row in image[role]['value']}
    bases = {coordinates(row) for row in detections.values()} | {coordinates(row) for row in references}
    for values in predecessor_rectangles(image):
        candidate = clipped(tuple(q(value) for value in values), width, height)
        if candidate is not None:
            bases.add(candidate)
    # Include a legal small rectangle even for empty visible outputs. It is a
    # real edit candidate, not a fabricated claim that the reference was empty.
    bases.add((Fraction(0), Fraction(0), min(Fraction(25), Fraction(width)), Fraction(25)))
    require(height >= 25, 'GEOMETRY', 'No rectangle can satisfy the declared height policy')
    geometries = set(bases)
    detection_boxes = [coordinates(row) for row in detections.values()]
    for base in sorted(bases):
        require(clipped(base, width, height) == base, 'GEOMETRY', 'Unclipped or ineligible candidate base')
        for axis in (0, 1):
            for candidate in sweep(base, detection_boxes, axis, width, height):
                geometries.add(candidate)
                require(len(geometries) <= MAX_RECTANGLES, 'SEARCH_LIMIT', 'Rectangle construction limit reached')
    return [record(values) for values in sorted(geometries)], len(bases)


def alter(references, edit):
    require(set(edit) == {'operation', 'removed_reference', 'inserted_reference'}, 'EDIT', 'Unknown edit field')
    operation, removed, inserted = edit['operation'], edit['removed_reference'], edit['inserted_reference']
    require(operation in ('none', 'deletion', 'insertion', 'replacement'), 'EDIT', 'Unknown edit operation')
    require((removed is not None) == (operation in ('deletion', 'replacement'))
            and (inserted is not None) == (operation in ('insertion', 'replacement')), 'EDIT', 'Edit cardinality differs')
    ids = {row['id'] for row in references}
    require(removed is None or removed in ids, 'EDIT', 'Deleted reference does not exist')
    require(inserted is None or inserted['id'] not in ids, 'EDIT', 'Inserted reference identity already exists')
    return [row for row in references if row['id'] != removed] + ([] if inserted is None else [inserted])


def search_image(image, references):
    start = time.perf_counter(); validate_rows(references); validate_canvas(references, image)
    nominal = measure(image, references, 'one_edit_per_image', 'conventional')
    detections = {row['id']: row for role in ROLES for row in image[role]['value']}
    original_edges = {(did, reference['id']) for did, detection in detections.items() for reference in references
                      if iou(detection, reference) >= Fraction(1, 2)}
    candidates, bases = candidate_rectangles(image, references)
    neighborhoods = {}
    for candidate in candidates:
        edges = tuple(did for did, detection in sorted(detections.items()) if iou(detection, candidate) >= Fraction(1, 2))
        neighborhoods.setdefault(edges, candidate)
    removals = [None] + [reference['id'] for reference in references]
    require(len(neighborhoods) * len(removals) <= MAX_PAIRS, 'SEARCH_LIMIT', 'Neighborhood evaluation limit reached')
    none = {'operation': 'none', 'removed_reference': None, 'inserted_reference': None}
    low = high = {'edit': none, 'measurement': nominal['nominal']}
    evaluated = 0
    for removed in removals:
        current = graph_ranks(image, references, original_edges, removed)
        edit = {'operation': 'none' if removed is None else 'deletion', 'removed_reference': removed, 'inserted_reference': None}
        worlds = [(current, edit)]
        for neighbors, candidate in neighborhoods.items():
            require(candidate['id'] not in {row['id'] for row in references}, 'EDIT', 'Stress identity collides with source reference')
            edges = original_edges | {(did, candidate['id']) for did in neighbors}
            measured = graph_ranks(image, references + [candidate], edges, removed)
            worlds.append((measured, {'operation': 'insertion' if removed is None else 'replacement',
                                     'removed_reference': removed, 'inserted_reference': candidate}))
            evaluated += 1
        for measured, edit in worlds:
            if q(measured['delta']) < q(low['measurement']['delta']):
                low = {'edit': edit, 'measurement': measured}
            if q(measured['delta']) > q(high['measurement']['delta']):
                high = {'edit': edit, 'measurement': measured}
    witnesses = {}
    for direction, found in (('lower', low), ('upper', high)):
        world = alter(references, found['edit']); validate_rows(world); validate_canvas(world, image)
        checked, proof, timing = checked_ranks(image, world)
        require(checked == found['measurement'], 'MATCHING', 'Adverse graph and checked geometric world differ')
        require(q(nominal['edit_bounds'][0]) <= q(checked['delta']) <= q(nominal['edit_bounds'][1]),
                'BOUND', 'Adverse world lies outside a supposedly sound edit bound')
        witnesses[direction] = {**found, 'altered_references': world, 'native_proof': proof, 'native_timing': timing}
    return {'image_id': image['id'], 'nominal': nominal, 'witnesses': witnesses,
        'candidate_rectangles': len(candidates), 'candidate_bases': bases, 'neighborhoods': len(neighborhoods),
        'base_candidate_evaluations': evaluated, 'seconds': time.perf_counter() - start,
        'all_rectangles_exhaustively_searched': False, 'axis_cells_exhaustively_searched': True}
