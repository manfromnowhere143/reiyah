"""Blender 5.1.2 point-selection adapter; byte identity, never human-review authority.

Run with Blender --background --factory-startup --disable-autoexec --python-exit-code 2
--python tools/perception_viewer.py -- prepare|extract ... . Only the adapter runs;
prepared scenes contain no scripts. No third-party Python dependencies are required.
"""
import argparse
from array import array
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import struct
import sys
import tempfile

VERSION = '0.1.0'
MAX_POINTS = 1_000_000
MAX_SCENE_BYTES = 256 << 20
INDEX = 'original_index'
OPTIONS = dict(global_scale=1.0, use_scene_unit=False, forward_axis='Y',
               up_axis='Z', merge_verts=False, import_attributes=True)
IDENTITY = [[1., 0., 0., 0.], [0., 1., 0., 0.],
            [0., 0., 1., 0.], [0., 0., 0., 1.]]


class Invalid(ValueError):
    def __init__(self, code, detail):
        self.code, self.detail = code, detail
        super().__init__(f'{code}: {detail}')


def require(ok, code, detail):
    if not ok:
        raise Invalid(code, detail)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()


def closed(value, keys):
    require(type(value) is dict and set(value) == set(keys),
            'VIEW_BINDING', 'Unexpected or missing binding fields')


def digest(value):
    return type(value) is str and re.fullmatch('[0-9a-f]{64}', value) is not None


def read_bound(path, size, expected, limit):
    require(type(size) is int and 0 < size <= limit and digest(expected),
            'VIEW_BOUND', 'Invalid size or digest')
    fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
    with os.fdopen(fd, 'rb') as f:
        require(stat.S_ISREG(os.fstat(f.fileno()).st_mode), 'VIEW_BOUND', 'Not a regular file')
        data = f.read(size + 1)
    require(len(data) == size and sha(data) == expected,
            'VIEW_BOUND', 'Source bytes differ from separately supplied identity')
    return data


def parse_binding(data):
    def pairs(items):
        out = {}
        for k, v in items:
            require(k not in out, 'VIEW_BINDING', 'Duplicate JSON field')
            out[k] = v
        return out

    def bad_number(value):
        raise Invalid('VIEW_BINDING', 'Noninteger JSON number')

    require(len(data) <= 4096, 'VIEW_BINDING', 'Binding exceeds 4096 bytes')
    try:
        b = json.loads(data, object_pairs_hook=pairs, parse_float=bad_number,
                       parse_constant=bad_number)
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise Invalid('VIEW_BINDING', 'Malformed binding JSON') from exc
    closed(b, ('artifact_id', 'version', 'package_seal_sha256', 'capture_id', 'asset', 'point_count'))
    require(b['artifact_id'] == 'reiyah.perception-viewer.binding' and b['version'] == VERSION
            and digest(b['package_seal_sha256']) and type(b['capture_id']) is str
            and re.fullmatch('capture-[0-9]{6}', b['capture_id']) is not None,
            'VIEW_BINDING', 'Unsupported identity')
    closed(b['asset'], ('byte_size', 'sha256'))
    require(type(b['point_count']) is int and 0 < b['point_count'] <= MAX_POINTS
            and type(b['asset']['byte_size']) is int and digest(b['asset']['sha256']),
            'VIEW_BINDING', 'Invalid point count or asset identity')
    require(b['asset']['byte_size'] == len(ply_header(b['point_count'])) + 20*b['point_count'],
            'VIEW_BINDING', 'Asset size does not match the fixed PLY profile')
    return b


def ply_header(count):
    return (f'ply\nformat binary_little_endian 1.0\nelement vertex {count}\n'
            'property float x\nproperty float y\nproperty float z\n'
            'property float intensity\nproperty float ring\nend_header\n').encode('ascii')


def point_body(data, binding):
    header = ply_header(binding['point_count'])
    require(len(data) == binding['asset']['byte_size'] and sha(data) == binding['asset']['sha256'],
            'VIEW_BOUND', 'PLY differs from the selected capture')
    require(data.startswith(header), 'VIEW_PLY', 'Unsupported PLY header')
    body = data[len(header):]
    require(all(math.isfinite(x) for row in struct.iter_unpack('<5f', body) for x in row),
            'VIEW_PLY', 'Nonfinite point field')
    return body


def verify_rows(body, rows, selected, matrix):
    """Verify a bijection onto ALL original records, including unselected records.

    Each row is (persistent original index, x, y, z, intensity, ring). A pure
    permutation is allowed; coordinates or attributes are never rounded to fit.
    Return sorted original indices, not transient Blender vertex numbers.
    """
    n = len(body)//20
    require(matrix == IDENTITY, 'VIEW_TRANSFORM', 'Object transform is not identity')
    require(len(rows) == n, 'VIEW_INDEX', 'Point population changed')
    seen = set()
    for row in rows:
        require(len(row) == 6 and type(row[0]) is int and 0 <= row[0] < n
                and row[0] not in seen, 'VIEW_INDEX', 'Missing, duplicate or invalid original index')
        seen.add(row[0])
    for row in rows:
        i = row[0]
        try:
            record = struct.pack('<5f', *row[1:])
        except (TypeError, OverflowError, struct.error) as exc:
            raise Invalid('VIEW_FIELDS', 'Invalid float32 fields') from exc
        require(record == body[20*i:20*(i+1)], 'VIEW_FIELDS', 'Point fields differ from source bytes')
    require(type(selected) is list and len(selected) <= n
            and all(type(i) is int and 0 <= i < n for i in selected)
            and len(set(selected)) == len(selected), 'VIEW_SELECTION', 'Invalid selection indices')
    return sorted(selected)


def runtime():
    import bpy
    require(bpy.app.background and bpy.app.version == (5, 1, 2),
            'VIEW_RUNTIME', 'Require background Blender 5.1.2')
    require(not bpy.context.preferences.filepaths.use_scripts_auto_execute,
            'VIEW_RUNTIME', 'Require --disable-autoexec')
    return {'blender_version': bpy.app.version_string,
            'blender_build_hash': bpy.app.build_hash.decode(), 'python': sys.version.split()[0]}


def inspect_scene(binding, binding_sha, body):
    import bpy
    require(len(bpy.data.objects) == 1 and len(bpy.context.scene.objects) == 1,
            'VIEW_SCENE', 'Require exactly one point object')
    obj = bpy.context.scene.objects[0]
    require(obj.type == 'MESH' and not obj.modifiers and not obj.constraints
            and obj.parent is None and not obj.data.shape_keys
            and not obj.animation_data and not obj.data.animation_data
            and not obj.data.materials and not bpy.data.texts and not bpy.data.libraries,
            'VIEW_SCENE', 'Unsupported geometry, scripts or linked content')
    require(obj.get('binding_sha256') == binding_sha
            and obj.get('capture_id') == binding['capture_id'],
            'VIEW_BINDING', 'Scene is not bound to the selected capture')
    # Native Edit Mode maintains its own BMesh. In 5.1.2 update_from_editmode
    # alone leaves attribute arrays empty. Exit Edit Mode in this temporary
    # background copy before reading attributes and the persisted selection.
    if obj.mode == 'EDIT':
        bpy.context.view_layer.objects.active = obj
        require(bpy.ops.object.mode_set(mode='OBJECT') == {'FINISHED'},
                'VIEW_SCENE', 'Cannot read the saved edit selection')
    mesh = obj.data; n = binding['point_count']
    require(len(mesh.vertices) == n and not mesh.edges and not mesh.polygons,
            'VIEW_SCENE', 'Point population or topology changed')
    attrs = {}
    for name, kind, code in ((INDEX, 'INT', 'i'), ('intensity', 'FLOAT', 'f'), ('ring', 'FLOAT', 'f')):
        a = mesh.attributes.get(name)
        require(a is not None and a.domain == 'POINT' and a.data_type == kind and len(a.data) == n,
                'VIEW_INDEX' if name == INDEX else 'VIEW_FIELDS', 'Missing or changed point attribute')
        attrs[name] = array(code, [0])*n
        a.data.foreach_get('value', attrs[name])
    co = array('f', [0.])*(3*n); mesh.vertices.foreach_get('co', co)
    rows = [(attrs[INDEX][i], *co[3*i:3*i+3], attrs['intensity'][i], attrs['ring'][i]) for i in range(n)]
    selected = [attrs[INDEX][i] for i, v in enumerate(mesh.vertices) if v.select]
    return verify_rows(body, rows, selected, [list(r) for r in obj.matrix_world])


def prepare(binding, binding_sha, data, output):
    import bpy
    runtime()
    # The caller uses factory startup; these mutations affect this background
    # process only, never an existing person's open Blender scene.
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    with tempfile.TemporaryDirectory(prefix='reiyah-points-') as td:
        snapshot = Path(td)/'points.ply'; snapshot.write_bytes(data)
        require(bpy.ops.wm.ply_import(filepath=str(snapshot), **OPTIONS) == {'FINISHED'},
                'VIEW_IMPORT', 'Native PLY import failed')
    require(len(bpy.context.selected_objects) == 1, 'VIEW_IMPORT', 'Unexpected native import objects')
    obj = bpy.context.selected_objects[0]; obj.name = binding['capture_id']; obj.data.name = obj.name
    obj['capture_id'] = binding['capture_id']; obj['binding_sha256'] = binding_sha
    n = binding['point_count']
    a = obj.data.attributes.new(INDEX, 'INT', 'POINT')
    a.data.foreach_set('value', array('i', range(n)))
    for v in obj.data.vertices:
        v.select = False
    inspect_scene(binding, binding_sha, point_body(data, binding))
    bpy.context.view_layer.objects.active = obj
    bpy.context.scene.tool_settings.mesh_select_mode = (True, False, False)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    # A declared orthographic top view; no decimation, registration or invented
    # surfaces. UI visibility and practical density still require observation.
    extent = max(abs(c) for v in obj.data.vertices for c in v.co)
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                space = area.spaces.active
                space.region_3d.view_rotation = (1., 0., 0., 0.)
                space.region_3d.view_location = (0., 0., 0.)
                space.region_3d.view_distance = max(10., 2.5*extent)
                space.region_3d.view_perspective = 'ORTHO'
                space.clip_end = max(1000., 10.*extent)
                space.shading.type = 'SOLID'; space.shading.show_xray = True
                space.shading.background_type = 'VIEWPORT'
                space.shading.background_color = (.65, .65, .65)
                space.overlay.show_floor = False
                space.overlay.show_axis_x = False; space.overlay.show_axis_y = False
    bpy.context.preferences.filepaths.save_version = 0
    output = Path(output)
    output.mkdir()  # Existing/partial outputs are never reused.
    target = output/(binding['capture_id']+'.blend')
    require(bpy.ops.wm.save_as_mainfile(filepath=str(target), check_existing=True) == {'FINISHED'},
            'VIEW_SAVE', 'Scene save failed')
    return target


def extract(binding, binding_sha, data, scene_bytes):
    import bpy
    runtime()
    with tempfile.TemporaryDirectory(prefix='reiyah-selection-') as td:
        snapshot = Path(td)/'selection.blend'; snapshot.write_bytes(scene_bytes)
        require(bpy.ops.wm.open_mainfile(filepath=str(snapshot), load_ui=False, use_scripts=False) == {'FINISHED'},
                'VIEW_OPEN', 'Native scene open failed')
        selected = inspect_scene(binding, binding_sha, point_body(data, binding))
    require(selected, 'VIEW_EMPTY_SELECTION', 'No selected points; no empty reference is inferred')
    body = point_body(data, binding)
    return {'artifact_id': 'reiyah.perception-viewer.selection', 'version': VERSION,
            'binding_sha256': binding_sha, 'source': binding,
            'scene': {'byte_size': len(scene_bytes), 'sha256': sha(scene_bytes)},
            'source_point_body_sha256': sha(body), 'point_indices': selected,
            'records': [{'point_index': i, 'raw_byte_offset': i*20,
                         'ply_byte_offset': len(ply_header(binding['point_count']))+i*20,
                         'float32_le_hex': body[20*i:20*(i+1)].hex()} for i in selected],
            'all_point_fields_verified': True, 'runtime': runtime(),
            'interactive_observation': 'not_established_by_extraction',
            'human_review': 'not_established', 'reference_judgment': 'not_created'}


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'extract'))
    parser.add_argument('--binding', required=True)
    parser.add_argument('--binding-sha256', required=True)
    parser.add_argument('--asset', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--scene')
    parser.add_argument('--scene-sha256')
    parser.add_argument('--scene-bytes', type=int)
    args = parser.parse_args(argv)
    binding_size = Path(args.binding).stat().st_size
    raw_binding = read_bound(args.binding, binding_size, args.binding_sha256, 4096)
    binding = parse_binding(raw_binding)
    data = read_bound(args.asset, binding['asset']['byte_size'], binding['asset']['sha256'], 20*MAX_POINTS+256)
    point_body(data, binding)
    if args.action == 'prepare':
        require(args.scene is None and args.scene_sha256 is None and args.scene_bytes is None,
                'VIEW_ARGUMENT', 'Scene input is only valid for extraction')
        target = prepare(binding, args.binding_sha256, data, args.output)
        print(json.dumps({'state': 'prepared_not_interactively_observed', 'scene': str(target),
                          'runtime': runtime()}, sort_keys=True))
    else:
        require(args.scene is not None, 'VIEW_ARGUMENT', 'Extraction requires a separately bound scene')
        scene = read_bound(args.scene, args.scene_bytes, args.scene_sha256, MAX_SCENE_BYTES)
        report = extract(binding, args.binding_sha256, data, scene)
        with open(args.output, 'xb') as f:
            f.write(encoded(report))
        print(json.dumps({'state': 'selection_bytes_verified', 'selected_points': len(report['point_indices'])}, sort_keys=True))


if __name__ == '__main__':
    try:
        main(sys.argv[sys.argv.index('--')+1:])
    except (Invalid, OSError, ValueError) as exc:
        print(json.dumps({'state': 'invalid', 'code': getattr(exc, 'code', 'VIEW_IO'),
                          'detail': str(exc)}, sort_keys=True), file=sys.stderr)
        raise SystemExit(2)
