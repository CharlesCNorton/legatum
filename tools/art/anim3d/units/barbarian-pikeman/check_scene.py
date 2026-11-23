"""Check physical geometry/projection invariants and the requested GPU device."""
import hashlib
import json
import os
from pathlib import Path

import bpy

root = Path(os.environ['ANIM_ROOT'])
master = root / 'masters/barbarian-pikeman'
lock = json.loads(Path(__file__).with_name('assets.lock.json').read_text())
for relative, digest in lock.items():
    assert hashlib.sha256((root/relative).read_bytes()).hexdigest() == digest, relative
bpy.ops.wm.open_mainfile(filepath=str(master / 'barbarian-pikeman.blend'))
scene = bpy.context.scene
assert len(bpy.data.objects['RIG-pikeman'].data.bones) == 53
assert scene.camera.name == 'CAM-painting'
assert scene.view_settings.view_transform == 'Standard'
records = json.loads((master / 'projection.json').read_text())
assert len(records) >= 60
for obj in scene.objects:
    assert min(abs(v) for v in obj.scale) > .0001, obj.name
    if obj.type != 'MESH' or obj.hide_render:
        continue
    assert obj.get('finished_surface'), obj.name
    assert not obj.data.shape_keys, obj.name
    assert all(m.type == 'ARMATURE' or not m.show_render for m in obj.modifiers), obj.name
    if obj.name == 'GEO-cream-stone-base':
        record = next(r for r in records if r['mesh'] == obj.name)
        assert record['safe_stone_cutoff_token_y'] == 225
        uv = obj.data.uv_layers['PaintingCamera']; mask = obj.data.color_attributes['PaintingFacing']
        normals = obj.matrix_world.to_3x3().inverted().transposed()
        assert all(mask.data[i].color[0] == 0 for i,loop in enumerate(obj.data.loops)
                   if (normals @ obj.data.vertices[loop.vertex_index].normal).normalized().z > .35), 'Painting on stone top'
        assert all(mask.data[i].color[0] == 0 for i in range(len(obj.data.loops)) if (1-uv.data[i].uv.y)*256 < 225), 'Painted feet on static stone'
    else:
        assert obj.data.uv_layers.get('PaintingCamera'), obj.name
        assert all(slot.material.node_tree.nodes.get('Camera-only painted illumination')
                   for slot in obj.material_slots), obj.name
if os.environ.get('CHECK_GPU') == '1' or os.environ.get('CYCLES_DEVICE') == 'GPU':
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'METAL'
    prefs.get_devices()
    assert any(d.type == 'METAL' for d in prefs.devices), 'Metal GPU unavailable; no CPU fallback'
print('SCENE_OK: finished weighted surfaces, 53 bones, camera-only paint, physical stone')
