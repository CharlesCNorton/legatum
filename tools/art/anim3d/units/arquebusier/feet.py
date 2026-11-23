"""Render real front/top foot views and measure the retargeted stance path."""
import hashlib
import json
import math
import os
import subprocess
from pathlib import Path

import bpy
from mathutils import Vector

R = Path(os.environ['ANIM_ROOT'])
M = R / 'masters/arquebusier'
source = M / 'clips/move.blend'
bpy.ops.wm.open_mainfile(filepath=str(source))
sc = bpy.context.scene
rig = bpy.data.objects['RIG-Arquebusier MPFB']
cam = sc.camera
sc.render.engine = 'CYCLES'
sc.cycles.device = os.environ.get('CYCLES_DEVICE', 'CPU')
sc.cycles.samples = int(os.environ.get('SAMPLES', '8'))
sc.cycles.use_denoising = True
if sc.cycles.device == 'GPU':
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'METAL'
    prefs.get_devices()
    assert any(d.type == 'METAL' for d in prefs.devices), 'Metal required'
    for d in prefs.devices:
        d.use = d.type == 'METAL'
sc.render.threads_mode = 'FIXED'
sc.render.threads = 3
sc.render.resolution_x = sc.render.resolution_y = int(os.environ.get('RESOLUTION', '256'))
sc.render.resolution_percentage = 100
sc.render.film_transparent = True
sc.render.image_settings.color_mode = 'RGBA'
out = M / 'feet'
out.mkdir(exist_ok=True)
(out / 'evidence.json').unlink(missing_ok=True)
records = []
visibility = {o: o.hide_render for o in sc.objects if o.type == 'MESH'}
for view in ('top', 'front'):
    cam.location = (0, 0, 4) if view == 'top' else (0, -5, .25)
    target = Vector((0, 0, .23))
    cam.rotation_euler = (target-cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam.data.ortho_scale = 1.15
    cam.data.clip_start = .1
    for o, hidden in visibility.items():
        # Isolate the actual shoes above; clipping through the calves would also
        # cut off high swing-phase toes. Front view retains garment connections.
        o.hide_render = hidden or (view == 'top' and 'shoe' not in o.name and 'base' not in o.name)
    for i in range(8):
        sc.frame_set(i+1)
        bpy.context.view_layer.update()
        if view == 'top':
            feet = {}
            for side in ('l', 'r'):
                ankle = rig.matrix_world @ rig.pose.bones['foot_'+side].head
                toe = rig.matrix_world @ rig.pose.bones['ball_'+side].head
                direction = toe-ankle
                shoe=bpy.data.objects['GEO-latchet shoe '+side]
                def landmark(key):
                    indices=shoe[key]
                    return sum((shoe.matrix_world @ shoe.data.vertices[i].co for i in indices),Vector())/len(indices)
                shoe_axis=landmark('toe_vertices')-landmark('heel_vertices')
                feet[side] = {'shoe_yaw_deg': math.degrees(math.atan2(shoe_axis.x,-shoe_axis.y)), 'ankle': list(ankle), 'toe': list(toe),
                              'yaw_deg': math.degrees(math.atan2(direction.x, -direction.y))}
            records.append({'frame': i+1, 'feet': feet})
        sc.render.filepath = str(out / f'{view}-{i:02}.png')
        bpy.ops.render.render(write_still=True)
motion = json.loads((M / 'clips/move-motion.json').read_text())
speed = motion['contact']['virtual_ground_m_per_sample'] * rig.scale.y
errors, yaws, shoe_yaws = [], [], []
for side, start, end in [('l', 0, 4), ('r', 4, 8)]:
    for i in range(start, end-1):
        current, following = records[i]['feet'][side], records[i+1]['feet'][side]
        delta = Vector(following['toe'])-Vector(current['toe'])-Vector((0, speed, 0))
        delta.z = 0
        errors.append(delta.length)
        yaws.append(abs(current['yaw_deg']))
        shoe_yaws.append(abs(current['shoe_yaw_deg']))
check = {'tested_stance_intervals': len(errors), 'max_stance_error_m': max(errors),
         'max_support_yaw_deg': max(yaws), 'max_actual_shoe_yaw_deg': max(shoe_yaws), 'virtual_ground_m_per_sample': speed}
report = {'engine': 'CYCLES', 'device': sc.cycles.device, 'samples': sc.cycles.samples,
          'resolution': sc.render.resolution_x,
          'clip_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
          'records': records, 'contact': check,
          'limits': 'Sampled toe path on virtual moving ground; inspect shoe geometry and heel rollover separately.'}
(out / 'evidence.json').write_text(json.dumps(report, indent=2))
subprocess.run([str(R/'venv/bin/python'), str(Path(__file__).with_name('finish.py')), 'feet'], check=True)
assert check['max_support_yaw_deg'] < 20, check
assert check['max_actual_shoe_yaw_deg'] < 20, check
assert check['max_stance_error_m'] < .025, check
print('FEET CHECK', check)
