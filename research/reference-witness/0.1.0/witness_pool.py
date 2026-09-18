"""Exact finite threshold-cell witnesses for existing optional references."""
from fractions import Fraction
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'research/reference-timing/0.1.0'))
sys.path.insert(0, str(ROOT/'research/reference-translation/0.1.0'))
from timing_bounds import ROLES, digest, iou, q, validate_canvas, validate_rows, w
from timing_metadata import require
from axis_cells import partition, translate

MAX_RECTANGLES = 100000
MAX_NEIGHBORHOODS = 4096


def build_pool(image, known, inherited, rectangle_limit=MAX_RECTANGLES,
               neighborhood_limit=MAX_NEIGHBORHOODS):
    require(type(rectangle_limit) is int and rectangle_limit >= 0
            and type(neighborhood_limit) is int and neighborhood_limit >= 0, 'Invalid pool limit')
    validate_rows(known); validate_canvas(known, image)
    predictions = {row['id']: row for role in ROLES for row in image[role]['value']}
    bases = {tuple(map(q, row['xyxy'])) for row in list(predictions.values())+known}
    bases.update(tuple(map(q, values)) for values in inherited)
    require(all(0 <= b[0] < b[2] <= image['width'] and 0 <= b[1] < b[3] <= image['height']
                and b[3]-b[1] >= 25 for b in bases), 'Ineligible candidate base')
    geometries = set(bases); cells = 0
    require(len(geometries) <= rectangle_limit, 'Rectangle construction limit')
    detections = [tuple(map(q, row['xyxy'])) for row in predictions.values()]
    for base in sorted(bases):
        for axis in (0, 1):
            divided, _ = partition(base, detections, axis, image['width'], image['height'])
            cells += len(divided)
            for cell in divided:
                geometries.add(translate(base, axis, cell.representative()))
                require(len(geometries) <= rectangle_limit, 'Rectangle construction limit')
    representatives = {}; empty = 0
    for geometry in sorted(geometries):
        neighbors = tuple(key for key, row in sorted(predictions.items())
                          if iou(row, {'xyxy': list(map(w, geometry))}) >= Fraction(1, 2))
        if not neighbors:
            empty += 1; continue
        representatives.setdefault(neighbors, geometry)
        require(len(representatives) <= neighborhood_limit, 'Neighborhood construction limit')
    ordered = sorted(representatives.items())
    return {'rectangles': [list(map(w, geometry)) for _, geometry in ordered],
            'neighborhoods': [list(neighbors) for neighbors, _ in ordered],
            'base_count': len(bases), 'axis_sweeps': 2*len(bases), 'axis_cells': cells,
            'unique_rectangles': len(geometries), 'empty_neighborhood_rectangles': empty,
            'geometry_sha256': digest([list(map(w, values)) for values in sorted(geometries)]),
            'rectangle_limit': rectangle_limit, 'neighborhood_limit': neighborhood_limit,
            'all_declared_axis_cells_constructed': True, 'all_arbitrary_rectangles_searched': False}


def seed_indices(image, parent, scope, pool):
    predictions = {row['id']: row for role in ROLES for row in image[role]['value']}
    lookup = {tuple(values): index for index, values in enumerate(pool['neighborhoods'])}
    seeds = []
    for direction in ('lower', 'upper'):
        found = parent['searches'][scope]['worlds'][direction]; indices = []
        for previous in found['candidate_indices']:
            geometry = parent['candidate_pool']['rectangles'][previous]
            neighbors = tuple(key for key, row in sorted(predictions.items())
                              if iou(row, {'xyxy': geometry}) >= Fraction(1, 2))
            if neighbors:
                require(neighbors in lookup, 'Inherited neighborhood absent from new pool')
                indices.append(lookup[neighbors])
        seeds.append({'indices': sorted(indices), 'measurement': found['measurement']})
    return seeds
