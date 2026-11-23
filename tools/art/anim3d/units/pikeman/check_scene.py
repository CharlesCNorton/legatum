"""Check physical geometry/projection invariants and the requested GPU device."""
import json
import os
from pathlib import Path

import bpy

root = Path(os.environ['ANIM_ROOT'])
master = root / 'masters/pikeman'
bpy.ops.wm.open_mainfile(filepath=str(master / 'pikeman.blend'))
scene = bpy.context.scene
assert len(bpy.data.objects['RIG-pikeman'].data.bones) == 53
assert scene.camera.name == 'CAM-painting'
assert scene.view_settings.view_transform == 'Standard'
records = json.loads((master / 'projection.json').read_text())
assert len(records) >= 40
for obj in scene.objects:
    assert min(abs(v) for v in obj.scale) > .0001, obj.name
    if obj.type != 'MESH' or obj.hide_render:
        continue
    assert obj.get('finished_surface'), obj.name
    assert not obj.data.shape_keys, obj.name
    assert all(m.type == 'ARMATURE' or not m.show_render for m in obj.modifiers), obj.name
    armature = next((m.object for m in obj.modifiers if m.type == 'ARMATURE'), None)
    if armature:
        for vertex in obj.data.vertices:
            values = [g.weight for g in vertex.groups if obj.vertex_groups[g.group].name in armature.data.bones]
            assert all(0 <= w <= 1.00001 for w in values), (obj.name, vertex.index, 'invalid deform weights')
            assert not values or abs(sum(values)-1) < .001, (obj.name, vertex.index, 'unnormalized weights')
    if obj.name == 'GEO-cream-stone-base':
        assert not obj.data.uv_layers.get('PaintingCamera'), 'Painted feet on static stone'
        assert obj.data.uv_layers.get('CleanStoneCamera'), 'Missing clean stone fill'
        assert obj.get('stone_pigment'), 'Missing stone source record'
    else:
        assert obj.data.uv_layers.get('PaintingCamera'), obj.name
        assert all(slot.material.node_tree.nodes.get('Camera-only painted illumination')
                   for slot in obj.material_slots), obj.name
    if obj.name == 'GEO-wrinkled-trousers':
        assert all(g.name.startswith(('pelvis','thigh','calf','foot','ball'))
                   for g in obj.vertex_groups), 'Cross-limb trouser weights'
if os.environ.get('CHECK_GPU') == '1' or os.environ.get('CYCLES_DEVICE') == 'GPU':
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'METAL'
    prefs.get_devices()
    assert any(d.type == 'METAL' for d in prefs.devices), 'Metal GPU unavailable; no CPU fallback'
print('SCENE_OK: finished weighted surfaces, 53 bones, camera-only paint, physical stone')
