"""Check physical geometry/projection invariants and the requested GPU device."""
import hashlib
import json
import os
import sys
from pathlib import Path

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rig_constants import PIKE_START, PIKE_END

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
for position, expected in [(PIKE_START, (12.5, 221.8)), (PIKE_END, (243.5, 16))]:
    point = world_to_camera_view(scene, scene.camera, Vector(position))
    actual = (256 * point.x, 256 * (1 - point.y))
    assert max(abs(a - b) for a, b in zip(actual, expected)) < .05, ('Pike registration', actual)
for image in bpy.data.images:
    path = Path(bpy.path.abspath(image.filepath))
    if not path.is_relative_to(root):
        continue
    expected = lock.get(str(path.relative_to(root)))
    if expected:
        assert image.packed_file, ('Unpacked source image', image.name)
        assert hashlib.sha256(image.packed_file.data).hexdigest() == expected, ('Stale packed pigment', image.name)
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
        assert record['stone_pigment'] == 'stone-registered.png'
        images = [n.image.name for s in obj.material_slots for n in s.material.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image]
        assert 'stone-registered.png' in images and 'painting-aligned.png' not in images, 'Painted feet on static stone'
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
