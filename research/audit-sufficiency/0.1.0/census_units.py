"""Rebuild the 3,000 census decision units from Reiyah's own custody of the nuScenes tables and
the five retained prediction files, under the frozen scale-study protocol
(4c601ca94bc1e34e155fda0b16a7e45d660c5084e913f5630938224b74686368) and the vendored
qualification, suppression and edge semantics of the research lane's scale_study 0.2.0.

Usage: python -B census_units.py META_DIR PREDICTIONS_DIR OUT_DIR [--gate BEFORE_INPUT.json]

Writes one comparison input per unit in the Engine input format consumed by sufficiency.py,
named <base>__<addition>__<scene>.json, plus an index. The gate option checks the rebuilt
scene-0101 mapillary-to-megvii unit against the sealed forty-frame case object for object.
No table row is modified; inputs stay private (annotation tokens).
"""
import hashlib
import json
import math
import os
import re
import sys
import time
from fractions import Fraction

SCORE_CUTOFF = 0.30
RANGE_LIMIT = 50.0
NEAR = 4.0
CLASSES = ("car", "truck", "bus", "trailer", "construction_vehicle",
           "pedestrian", "motorcycle", "bicycle", "traffic_cone", "barrier")
DETECTORS = ("centerpoint", "fcos3d", "mapillary", "megvii", "pointpillars")
PREDICTION_FILES = {"centerpoint": "centerpoint_val.json", "fcos3d": "fcos3d_val.json",
                    "mapillary": "mapillary_val.json", "megvii": "megvii_val.json",
                    "pointpillars": "pointpillars-val.json"}
# nuScenes devkit category_to_detection_name
CATEGORY_MAP = {
    'human.pedestrian.adult': 'pedestrian', 'human.pedestrian.child': 'pedestrian',
    'human.pedestrian.construction_worker': 'pedestrian', 'human.pedestrian.police_officer': 'pedestrian',
    'vehicle.car': 'car', 'vehicle.truck': 'truck', 'vehicle.bus.bendy': 'bus', 'vehicle.bus.rigid': 'bus',
    'vehicle.trailer': 'trailer', 'vehicle.construction': 'construction_vehicle',
    'vehicle.motorcycle': 'motorcycle', 'vehicle.bicycle': 'bicycle',
    'movable_object.trafficcone': 'traffic_cone', 'movable_object.barrier': 'barrier'}

OBJ = re.compile(rb'\{[^{}]*\}')


def scan(path, want):
    """Stream a flat JSON array of flat objects; yield parsed objects for which want(raw) is true."""
    carry = b''
    with open(path, 'rb') as f:
        while True:
            chunk = f.read(1 << 26)
            if not chunk:
                break
            data = carry + chunk
            last = 0
            for m in OBJ.finditer(data):
                last = m.end()
                raw = m.group(0)
                if want(raw):
                    yield json.loads(raw)
            carry = data[last:]


def finite(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def rotate_inverse(q, v):
    w, x, y, z = q
    r = [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
         [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
         [2 * (x * z + y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]
    return [sum(r[j][i] * v[j] for j in range(3)) for i in range(3)]


RANGE_RULE = 'global_xy'   # set by --range-rule; 'global_xy' reproduces the retained census index


def within_range(xyz, pose):
    """Common nominal XY range against the LIDAR_TOP keyframe ego pose.

    'global_xy': planar distance in the global frame (no rotation). This is the rule the retained
    research-lane census index (0.2.0) is consistent with on every unit checked.
    'ego_rotated': the ego-frame planar distance described in scale_study.py's docstring; it
    differs from global_xy by the small pitch and roll of the pose and changes one annotation or
    one detection on about a quarter of the scenes.
    """
    tr = pose['translation']
    if RANGE_RULE == 'ego_rotated':
        rel = rotate_inverse(pose['rotation'], [xyz[0] - tr[0], xyz[1] - tr[1], xyz[2] - tr[2]])
        return rel[0] * rel[0] + rel[1] * rel[1] <= RANGE_LIMIT * RANGE_LIMIT
    return (xyz[0] - tr[0]) ** 2 + (xyz[1] - tr[1]) ** 2 <= RANGE_LIMIT * RANGE_LIMIT


def qualify(rows, pose):
    kept = []
    for index, row in enumerate(rows):
        name, score, g = row.get('detection_name'), row.get('detection_score'), row.get('translation')
        if name not in CLASSES or not finite(score) or score < SCORE_CUTOFF:
            continue
        if not (isinstance(g, list) and len(g) == 3 and all(finite(v) for v in g)):
            continue
        if not within_range(g, pose):
            continue
        kept.append({'i': index, 'c': name, 'x': g[0], 'y': g[1]})
    return kept


def suppress(base, candidates):
    retained = []
    for row in sorted(candidates, key=lambda r: r['i']):
        hit = False
        for other in base:
            if other['c'] == row['c'] and (row['x'] - other['x']) ** 2 + (row['y'] - other['y']) ** 2 < NEAR:
                hit = True
                break
        if not hit:
            for other in retained:
                if other['c'] == row['c'] and (row['x'] - other['x']) ** 2 + (row['y'] - other['y']) ** 2 < NEAR:
                    hit = True
                    break
        if not hit:
            retained.append(row)
    return retained


def load_split_scenes(splits_path):
    ns = {}
    src = open(splits_path).read()
    # the devkit file defines `val = [...]` at module level; execute only that assignment safely
    start = src.index('\nval = ')
    end = src.index(']', start) + 1
    exec(src[start:end].strip(), {}, ns)
    return set(ns['val'])


def main():
    meta, preds, out = sys.argv[1], sys.argv[2], sys.argv[3]
    gate = sys.argv[sys.argv.index('--gate') + 1] if '--gate' in sys.argv else None
    splits = sys.argv[sys.argv.index('--splits') + 1]
    global RANGE_RULE
    if '--range-rule' in sys.argv:
        RANGE_RULE = sys.argv[sys.argv.index('--range-rule') + 1]
        assert RANGE_RULE in ('global_xy', 'ego_rotated')
    os.makedirs(out, exist_ok=True)
    t0 = time.perf_counter()
    val_scenes = load_split_scenes(splits)
    scenes = {s['token']: s for s in json.load(open(os.path.join(meta, 'scene.json'))) if s['name'] in val_scenes}
    assert len(scenes) == 150, len(scenes)
    samples = {s['token']: s for s in json.load(open(os.path.join(meta, 'sample.json'))) if s['scene_token'] in scenes}
    # order frames within a scene by following next pointers from first_sample_token
    order = {}
    for st, s in scenes.items():
        tok, k = s['first_sample_token'], 0
        while tok:
            order[tok] = (st, k)
            tok = samples[tok]['next']
            k += 1
    assert len(order) == len(samples)
    print('val samples', len(samples), round(time.perf_counter() - t0, 1), flush=True)
    # LIDAR_TOP keyframe sample_data -> ego_pose_token
    wanted = set(samples)
    ego_token = {}
    for row in scan(os.path.join(meta, 'sample_data.json'),
                    lambda raw: b'"is_key_frame": true' in raw and b'LIDAR_TOP' in raw):
        if row['sample_token'] in wanted:
            ego_token[row['sample_token']] = row['ego_pose_token']
    assert len(ego_token) == len(samples), (len(ego_token), len(samples))
    print('lidar keyframes', len(ego_token), round(time.perf_counter() - t0, 1), flush=True)
    needed = set(ego_token.values())
    poses = {}
    for row in scan(os.path.join(meta, 'ego_pose.json'), lambda raw: True):
        if row['token'] in needed:
            poses[row['token']] = row
    assert len(poses) == len(needed)
    print('poses', len(poses), round(time.perf_counter() - t0, 1), flush=True)
    categories = {c['token']: c['name'] for c in json.load(open(os.path.join(meta, 'category.json')))}
    instance_cat = {i['token']: categories[i['category_token']]
                    for i in json.load(open(os.path.join(meta, 'instance.json')))}
    refs = {t: [] for t in samples}
    excluded = {'unmapped_category': 0, 'out_of_range': 0}
    for row in scan(os.path.join(meta, 'sample_annotation.json'), lambda raw: True):
        st = row['sample_token']
        if st not in wanted:
            continue
        cls = CATEGORY_MAP.get(instance_cat[row['instance_token']])
        if cls is None:
            excluded['unmapped_category'] += 1
            continue
        if not within_range(row['translation'], poses[ego_token[st]]):
            excluded['out_of_range'] += 1
            continue
        refs[st].append({'token': row['token'], 'c': cls, 'x': row['translation'][0], 'y': row['translation'][1]})
    print('references', sum(len(v) for v in refs.values()), excluded, round(time.perf_counter() - t0, 1), flush=True)
    detections = {}
    for name in DETECTORS:
        p = json.load(open(os.path.join(preds, PREDICTION_FILES[name])))['results']
        detections[name] = {st: qualify(p.get(st, []), poses[ego_token[st]]) for st in samples}
        print('qualified', name, sum(len(v) for v in detections[name].values()), round(time.perf_counter() - t0, 1), flush=True)
    index = []
    for st, s in scenes.items():
        frames = sorted((t for t in samples if order[t][0] == st), key=lambda t: order[t][1])
        for base_name in DETECTORS:
            for add_name in DETECTORS:
                if base_name == add_name:
                    continue
                anchors = []
                w = Fraction(1, len(frames))
                for t in frames:
                    base = detections[base_name][t]
                    adds = suppress(base, detections[add_name][t])
                    objs = refs[t]
                    dets = [('base:%d' % r['i'], r) for r in base] + [('additions:%d' % r['i'], r) for r in adds]
                    edges = [{'detection': did, 'object': o['token'], 'when': []}
                             for did, r in dets for o in objs
                             if o['c'] == r['c'] and (r['x'] - o['x']) ** 2 + (r['y'] - o['y']) ** 2 < NEAR]
                    anchors.append({'id': 'a-%d' % order[t][1], 'weight': {'numerator': str(w.numerator), 'denominator': str(w.denominator)},
                                    'base': {'state': 'observed', 'value': [{'id': did, 'class': r['c'], 'xy': [r['x'], r['y']]} for did, r in dets[:len(base)]]},
                                    'additions': {'state': 'observed', 'value': [{'id': did, 'class': r['c'], 'xy': [r['x'], r['y']]} for did, r in dets[len(base):]]},
                                    'reference': {'state': 'finite', 'objects': [{'id': o['token'], 'class': o['c'], 'xy': [o['x'], o['y']], 'when': []} for o in objs],
                                                  'edges': edges}})
                case = {'artifact_id': 'reiyah.research.audit-sufficiency.census-unit', 'version': '0.1.0',
                        'comparison_id': '%s__%s__%s' % (base_name, add_name, s['name']),
                        'cohort_id': s['name'], 'evidence_kind': 'conditional_reference_graph',
                        'input_scope': 'rebuilt_census_unit', 'assumptions': ['scale-study protocol semantics', 'range_rule=' + RANGE_RULE],
                        'loss': {'false_negative': {'numerator': '1', 'denominator': '1'},
                                 'false_positive': {'numerator': '1', 'denominator': '1'},
                                 'tolerance': {'numerator': '1', 'denominator': '10'}},
                        'model': {'variables': [], 'clauses': []}, 'anchors': anchors}
                data = json.dumps(case, sort_keys=True).encode()
                fname = case['comparison_id'] + '.json'
                open(os.path.join(out, fname), 'wb').write(data)
                index.append({'file': fname, 'base': base_name, 'addition': add_name, 'scene': s['name'],
                              'frames': len(frames), 'annotations': sum(len(refs[t]) for t in frames),
                              'base_detections': sum(len(detections[base_name][t]) for t in frames),
                              'additions': sum(len(a['additions']['value']) for a in anchors),
                              'sha256': hashlib.sha256(data).hexdigest()})
    json.dump({'units': index, 'range_rule': RANGE_RULE, 'excluded_annotations': excluded, 'seconds': round(time.perf_counter() - t0, 1)},
              open(os.path.join(out, 'INDEX.json'), 'w'), indent=1)
    print('units', len(index), round(time.perf_counter() - t0, 1), flush=True)
    if gate:
        g = json.load(open(gate))
        mine = json.load(open(os.path.join(out, 'mapillary__megvii__scene-0101.json')))
        gk = {(a['id'], o['id']) for a in g['anchors'] for o in a['reference']['objects']}
        mk = {(a['id'], o['id']) for a in mine['anchors'] for o in a['reference']['objects']}
        ge = {(a['id'], e['detection'], e['object']) for a in g['anchors'] for e in a['reference']['edges']}
        me = {(a['id'], e['detection'], e['object']) for a in mine['anchors'] for e in a['reference']['edges']}
        gb = [(a['id'], len(a['base']['value']), len(a['additions']['value'])) for a in g['anchors']]
        mb = [(a['id'], len(a['base']['value']), len(a['additions']['value'])) for a in mine['anchors']]
        equal = gk == mk and ge == me and gb == mb
        print('GATE objects equal', gk == mk, len(gk), len(mk), 'edges equal', ge == me, len(ge), len(me), 'counts equal', gb == mb, flush=True)
        if '--gate-negative-control' in sys.argv:
            # the gate must reject a deliberately altered rebuild: drop one object from the rebuilt unit
            mk_alt = set(list(mk)[:-1])
            if mk_alt == gk:
                raise SystemExit('GATE NEGATIVE CONTROL FAILED: altered rebuild passed')
            print('GATE negative control: altered rebuild rejected', flush=True)
        if not equal:
            raise SystemExit('GATE FAILED: rebuilt unit differs from the sealed case')


if __name__ == '__main__':
    main()
