"""Native Blender save/reopen adversaries on one separately bound local capture.

This is a programmatic engineering exercise. It never performs GUI interactions,
produces screenshots, populates discovery records or creates human judgments.
Run with the same background/factory/disable-autoexec flags as the adapter,
then --python this_file.py -- /private/probe-spec.json .
"""
from array import array
from pathlib import Path
import json
import struct
import sys
import time

import bmesh
import bpy

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools import perception_viewer as v


def main(spec):
    started = time.monotonic()
    rb = v.read_bound(**spec['binding'], limit=4096)
    binding = v.parse_binding(rb); binding_sha = v.sha(rb)
    data = v.read_bound(**spec['asset'], limit=20*v.MAX_POINTS+256)
    pristine = v.read_bound(**spec['scene'], limit=v.MAX_SCENE_BYTES)
    output = Path(spec['output']); output.mkdir()
    results = []

    def open_scene():
        bpy.ops.wm.open_mainfile(filepath=spec['scene']['path'], load_ui=True, use_scripts=False)
        obj = bpy.context.scene.objects[0]
        return obj

    obj = open_scene()
    initial = {'object_mode': obj.mode, 'vertex_select_mode': list(bpy.context.scene.tool_settings.mesh_select_mode),
               'points': len(obj.data.vertices), 'embedded_texts': len(bpy.data.texts),
               'views': [{'type': a.spaces.active.region_3d.view_perspective,
                          'xray': a.spaces.active.shading.show_xray}
                         for s in bpy.data.screens for a in s.areas if a.type == 'VIEW_3D']}
    assert obj.mode == 'EDIT' and initial['vertex_select_mode'] == [True, False, False]
    assert initial['views'] and all(x == {'type': 'ORTHO', 'xray': True} for x in initial['views'])
    assert initial['embedded_texts'] == 0
    try:
        v.extract(binding, binding_sha, data, pristine)
    except v.Invalid as e:
        assert e.code == 'VIEW_EMPTY_SELECTION'; results.append({'case': 'pristine_has_no_selection', 'result': e.code})
    else:
        raise AssertionError('A pristine scene must not become an empty reference')

    desired = [0, binding['point_count']//2, binding['point_count']-1]

    def select():
        obj = open_scene()
        if obj.mode != 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')
        bm = bmesh.from_edit_mesh(obj.data); layer = bm.verts.layers.int[v.INDEX]
        for vert in bm.verts:
            vert.select_set(vert[layer] in desired)
        bmesh.update_edit_mesh(obj.data)
        return obj, bm, layer

    def save(name):
        target = output/(name+'.blend')
        bpy.context.preferences.filepaths.save_version = 0
        assert not target.exists()
        assert bpy.ops.wm.save_as_mainfile(filepath=str(target)) == {'FINISHED'}
        return target.read_bytes()

    obj, bm, layer = select()
    selected_scene = save('programmatic-selection')
    report = v.extract(binding, binding_sha, data, selected_scene)
    assert report['point_indices'] == desired
    # Independently slice the fixed PLY body, rather than reconstructing expected
    # results from the adapter's scene/row verifier.
    body = data.split(b'end_header\n', 1)[1]
    for row in report['records']:
        i = row['point_index']
        assert bytes.fromhex(row['float32_le_hex']) == body[20*i:20*i+20]
        assert row['raw_byte_offset'] == 20*i
        assert data[row['ply_byte_offset']:row['ply_byte_offset']+20] == body[20*i:20*i+20]
    (output/'programmatic-selection.json').write_bytes(v.encoded(report))
    results.append({'case': 'save_reopen_selection', 'result': 'pass', 'point_indices': desired})

    obj, bm, layer = select()
    bm.verts.sort(key=lambda x: -x[layer]); bm.verts.index_update()
    bmesh.update_edit_mesh(obj.data)
    bpy.ops.object.mode_set(mode='OBJECT')
    ids = array('i', [0])*binding['point_count']
    obj.data.attributes[v.INDEX].data.foreach_get('value', ids)
    assert ids[0] == binding['point_count']-1 and ids[-1] == 0  # Reorder actually happened.
    bpy.ops.object.mode_set(mode='EDIT')
    reordered = save('reordered-selection')
    rr = v.extract(binding, binding_sha, data, reordered)
    assert rr['point_indices'] == desired and rr['records'] == report['records']
    (output/'reordered-selection.json').write_bytes(v.encoded(rr))
    results.append({'case': 'persistent_index_survives_reverse_vertex_order', 'result': 'pass'})

    def attack(name, code, mutate):
        obj, bm, layer = select()
        # Source edits here are deliberate counterexamples in this temporary
        # background scene; immutable PLY and pristine .blend remain untouched.
        mutate(obj, bm, layer)
        if obj.mode == 'EDIT':
            bmesh.update_edit_mesh(obj.data)
        scene = save(name)
        try:
            v.extract(binding, binding_sha, data, scene)
        except v.Invalid as exc:
            assert exc.code == code, (name, code, exc.code)
            results.append({'case': name, 'result': exc.code})
        else:
            raise AssertionError('Accepted adversary: '+name)

    def bump(obj, bm, layer, field):
        vert = next(x for x in bm.verts if x[layer] == 1)  # Not selected.
        if field < 3:
            value = vert.co[field]
        else:
            attr = bm.verts.layers.float['intensity' if field == 3 else 'ring']; value = vert[attr]
        bits = struct.unpack('<I', struct.pack('<f', value))[0]
        changed = struct.unpack('<f', struct.pack('<I', bits+1))[0]
        if field < 3:
            vert.co[field] = changed
        else:
            vert[attr] = changed

    for field, name in enumerate(('x', 'y', 'z', 'intensity', 'ring')):
        attack('unselected_'+name+'_one_ulp', 'VIEW_FIELDS', lambda o, b, l, f=field: bump(o, b, l, f))

    def duplicate(obj, bm, layer):
        next(x for x in bm.verts if x[layer] == 0)[layer] = 1

    def missing(obj, bm, layer):
        bm.verts.layers.int.remove(layer)

    def deleted(obj, bm, layer):
        bm.verts.remove(next(iter(bm.verts)))

    def edge(obj, bm, layer):
        bm.verts.ensure_lookup_table(); bm.edges.new((bm.verts[0], bm.verts[1]))

    attack('duplicate_original_index', 'VIEW_INDEX', duplicate)
    attack('removed_original_index', 'VIEW_INDEX', missing)
    attack('deleted_point', 'VIEW_SCENE', deleted)
    attack('added_edge', 'VIEW_SCENE', edge)
    attack('changed_transform', 'VIEW_TRANSFORM', lambda o, b, l: setattr(o, 'location', (1., 0., 0.)))
    attack('wrong_capture', 'VIEW_BINDING', lambda o, b, l: o.__setitem__('capture_id', 'capture-999999'))
    attack('wrong_binding', 'VIEW_BINDING', lambda o, b, l: o.__setitem__('binding_sha256', 'f'*64))
    attack('added_modifier', 'VIEW_SCENE', lambda o, b, l: o.modifiers.new('changed', 'DECIMATE'))
    attack('embedded_text', 'VIEW_SCENE', lambda o, b, l: bpy.data.texts.new('forbidden.py'))
    assert v.read_bound(**spec['scene'], limit=v.MAX_SCENE_BYTES) == pristine
    assert v.read_bound(**spec['asset'], limit=20*v.MAX_POINTS+256) == data
    final = {'artifact_id': 'reiyah.perception-viewer.native-probe', 'version': '0.1.0',
             'runtime': v.runtime(), 'initial_scene': initial, 'results': results,
             'elapsed_seconds': time.monotonic()-started,
             'binding_sha256': binding_sha, 'pristine_scene_sha256': v.sha(pristine),
             'adapter_sha256': v.sha(Path(v.__file__).read_bytes()),
             'probe_sha256': v.sha(Path(__file__).read_bytes()),
             'interactive_observation': False, 'human_review': False,
             'selection_origin': 'programmatically_constructed_engineering_check'}
    (output/'report.json').write_bytes(v.encoded(final))
    print(json.dumps(final, sort_keys=True))


if __name__ == '__main__':
    main(json.loads(Path(sys.argv[sys.argv.index('--')+1]).read_bytes()))
