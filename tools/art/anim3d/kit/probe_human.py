"""Exercise MPFB game rig/Rigify and a synthetic rest-space corrective on CPU.

Does not change production anatomy, download assets, or save a .blend.
"""
import json
import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bpy
from kit.human import create_body, add_rig, add_hinge_corrective

bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
body = create_body({'gender': 1., 'muscle': 1., 'weight': .72}, 'Kit MPFB probe')
rig = add_rig(body, 'Kit game engine probe')
assert len(rig.data.bones) == 53 and len(body.data.vertices) == 19158
# Keep separate bodies: no double skeleton attached to a single mesh.
second = create_body({'gender': 1., 'muscle': 1., 'weight': .72}, 'Kit Rigify probe')
control = add_rig(second, 'Kit Rigify controls', rigify=True)
assert len(control.data.bones) > 100
bpy.ops.object.armature_add(); hinge = bpy.context.object
bone = hinge.pose.bones[0]; bone.rotation_mode = 'XYZ'
bpy.ops.mesh.primitive_plane_add(); plane = bpy.context.object
key = add_hinge_corrective(plane, hinge, 'Test elbow volume', bone.name,
                          {0: (.01, 0, 0)}, start=0, full=1)
bone.rotation_euler.x = .5
bpy.context.scene.frame_set(2); bpy.context.view_layer.update()
assert abs(key.value-.5) < 1e-5, key.value
assert abs(key.data[0].co.x-plane.data.shape_keys.key_blocks['Basis'].data[0].co.x-.01) < 1e-5
out = Path(os.environ['ANIM_ROOT'])/'review/3d-v2/kit-human-check.json'
out.write_text(json.dumps({'blender': bpy.app.version_string, 'mpfb_vertices': len(body.data.vertices),
    'game_bones': len(rig.data.bones), 'rigify_bones': len(control.data.bones),
    'armature_modifiers': [{'name': m.name, 'multi': m.use_multi_modifier} for m in second.modifiers if m.type=='ARMATURE'],
    'synthetic_corrective_value': key.value, 'anatomical_corrective_sculpt': 'not authored or claimed'}, indent=2)+'\n')
print('HUMAN_KIT_PASS', out)
