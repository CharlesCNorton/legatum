"""Render actual lower-leg geometry from above/front and measure the move cycle."""
import bpy
import bmesh
import hashlib
import json
import math
import os
import statistics
import sys
from pathlib import Path
from mathutils import Vector

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'infantry'))
from contact import sole_points, landmarks

root = Path(os.environ['ANIM_ROOT'])
master = root/'masters/spearman-3d-v2'
diagnostic = os.environ.get('MOTION_DIAGNOSTIC') == '1'
path = master/'clips/move'/('move-diagnostic.blend' if diagnostic else 'move.blend')
bpy.ops.wm.open_mainfile(filepath=str(path))
sc = bpy.context.scene
rig = bpy.data.objects['Spearman • MPFB game_engine']
# Inspect/render the full 24 Hz cycle, including its duplicate loop endpoint.
frames = list(range(25, sc.frame_end+1))
out = master/'feet-check'
out.mkdir(exist_ok=True)
rows = []
for frame in frames:
    sc.frame_set(frame)
    row = {'frame': frame, 'feet': {}}
    for side in ['l', 'r']:
        foot = rig.pose.bones['foot_'+side]
        direction = (rig.matrix_world.to_3x3() @ foot.matrix.to_3x3()
                     @ foot.bone.matrix_local.to_3x3().inverted() @ Vector((0,-1,0)))
        sole = bpy.data.objects['Leather sandal sole '+side]
        points = sole_points(side)
        center = sum(points, Vector())/len(points)
        actual=landmarks(side,points);direction=actual['toe']-actual['heel']
        row['feet'][side] = {'yaw_degrees': math.degrees(math.atan2(direction.x, -direction.y)),
                            'heading_projection_m': math.hypot(direction.x,direction.y),
                            'ankle': list(rig.matrix_world @ foot.head),
                            'sole_center': list(center), 'sole_min_z': min(v.z for v in points)}
    rows.append(row)
source = json.loads(sc['motion_source'])
source_samples = source.get('samples', [])
dense, velocities = [], []
if source_samples:
    active = source_samples[24:]
    minima = {s: min(a['ankles'][s][2] for a in active) for s in ['l','r']}
    for f in range(25, sc.frame_end+1):
        sc.frame_set(f)
        sample = source_samples[f-1]
        entry = {'frame': f, 'feet': {}}
        for side in ['l','r']:
            ankle = sample['ankles'][side]
            planted = source['contact']['planted'].get(str(f),{}).get(side,False)
            foot = rig.pose.bones['foot_'+side]
            sole = bpy.data.objects['Leather sandal sole '+side]
            points = sole_points(side)
            direction = rig.matrix_world.to_3x3() @ foot.matrix.to_3x3() @ foot.bone.matrix_local.to_3x3().inverted() @ Vector((0,-1,0))
            actual=landmarks(side,points)
            toe,heel=actual['toe'],actual['heel']
            direction=toe-heel
            mode='toe' if toe.z<heel.z else 'heel'
            contact_point=toe if mode=='toe' else heel
            entry['feet'][side] = {'planted': planted, 'ankle': list(rig.matrix_world @ foot.head),
                                   'sole_z': min(v.z for v in points), 'contact_mode': mode, 'contact_point': list(contact_point),
                                   'heading_projection_m': math.hypot(direction.x,direction.y), 'heading': math.degrees(math.atan2(direction.x,-direction.y))}
            if planted and f>25 and dense[-1]['feet'][side]['planted']:
                previous = source_samples[f-2]['ankles'][side]
                velocities.append((ankle[1]-previous[1])*24*source['leg_scale'])
        dense.append(entry)
    velocity = source['contact']['virtual_forward_speed_m_s']
    residuals, gaps, headings, sole_slip = [], [], [], []
    for side in ['l','r']:
        anchor = None
        sole_anchor=None; previous_mode=None
        for row in dense:
            foot = row['feet'][side]
            if not foot['planted']:
                anchor = None; sole_anchor=None; previous_mode=None
                continue
            world = Vector(foot['ankle'])-Vector((0, velocity*(row['frame']-25)/24, 0))
            if anchor is None: anchor = world
            residuals.append((Vector((world.x,world.y,0))-Vector((anchor.x,anchor.y,0))).length)
            point=Vector(foot['contact_point'])-Vector((0,velocity*(row['frame']-25)/24,0))
            point.z=0
            if sole_anchor is None or previous_mode!=foot['contact_mode']:sole_anchor=point.copy()
            sole_slip.append((point-sole_anchor).length)
            previous_mode=foot['contact_mode']
            gaps.append(abs(foot['sole_z']-.106))
            headings.append(abs(foot['heading']))
    seam_positions={}
    for frame in [25,sc.frame_end]:
        sc.frame_set(frame)
        seam_positions[frame]={side: rig.matrix_world @ rig.pose.bones['foot_'+side].head for side in ['l','r']}
    seam=max((seam_positions[25][side]-seam_positions[sc.frame_end][side]).length for side in ['l','r'])
    checks = {'virtual_forward_speed_m_s': velocity, 'max_ankle_roll_travel_m': max(residuals),
              'max_sole_contact_slip_m': max(sole_slip), 'max_planted_floor_error_m': max(gaps), 'max_planted_heading_degrees': max(headings),
              'dense_frames': len(dense), 'planted_samples': len(gaps), 'loop_seam_m': seam,
              'max_raw_foot_yaw_degrees': max(abs(f['heading']) for row in dense for f in row['feet'].values()),
              'max_root_xy_correction_m': source['contact']['max_root_xy_correction_m'],
              'max_foot_ik_correction_m': source['contact']['max_foot_ik_correction_m'],
              'max_sole_translation_m': source['max_sole_translation_m'],
              'max_readable_heading_degrees': max(abs(f['heading']) for row in dense for f in row['feet'].values() if f['heading_projection_m']>=.08),
              'ankle_note': 'Ankle travel above a rolling sole is not contact slip; measure heel/toe landmarks.',
              'heading_note': 'Yaw is ill-conditioned when a raised toe-down foot projects under 8 cm onto the ground; retain raw angles but gate planted and readable footprints.'}
else:
    checks = {'error': 'Missing source contact trace; rebuild motion'}
report = {'blend_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
          'forward': [0, -1, 0], 'frames': rows, 'checks': checks, 'dense': dense,
          'meaning': 'In-place locomotion: subtract virtual forward travel before judging stance slip.'}
(out/'metrics.json').write_text(json.dumps(report, indent=2))
(root/'review/3d-v2/spearman-motion-checks.json').write_text(json.dumps(report,indent=2))
failures=[]
for metric,limit in [('max_sole_contact_slip_m',.001),('max_planted_floor_error_m',.002),
                     ('max_planted_heading_degrees',10),('max_readable_heading_degrees',10),('loop_seam_m',.003),
                     ('max_root_xy_correction_m',.05),('max_foot_ik_correction_m',.05),('max_sole_translation_m',.04)]:
    if metric not in checks or checks[metric]>limit:failures.append(f'{metric}: {checks.get(metric)} exceeds {limit}')
report['failures']=failures
(out/'metrics.json').write_text(json.dumps(report,indent=2))
(root/'review/3d-v2/spearman-motion-checks.json').write_text(json.dumps(report,indent=2))
print('FEET_CHECKS',json.dumps(checks),flush=True)

if os.environ.get('FEET_METRICS_ONLY') == '1':
    assert not failures, failures
    raise SystemExit(0)
sc.render.engine = 'CYCLES'
sc.cycles.device = os.environ.get('CYCLES_DEVICE', 'CPU')
if sc.cycles.device == 'GPU':
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = os.environ.get('CYCLES_BACKEND', 'METAL')
    prefs.get_devices()
    devices = [d for d in prefs.devices if d.type == prefs.compute_device_type]
    assert devices
    for d in prefs.devices: d.use = d in devices
sc.cycles.samples = int(os.environ.get('FEET_SAMPLES', '8'))
sc.cycles.use_denoising = True
sc.render.resolution_x = sc.render.resolution_y = 192
sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = 'PNG'
sc.render.image_settings.color_mode = 'RGBA'
# Hide original render objects; snapshot only lower-leg surfaces. This prevents
# the top view being occluded by helmet/shield. Never change the saved clip.
originals = [o for o in sc.objects if o.type in {'MESH', 'CURVE'} and not o.hide_render]
keep = [o for o in originals if o.name.startswith(('MPFB anatomical', 'Leather sandal', 'Sandal', 'Contoured greave', 'Greave chased'))]
for o in originals: o.hide_render = True
camera = sc.camera
camera.data.type = 'ORTHO'
camera.data.ortho_scale = 1.3
camera.data.dof.use_dof = False
for index, frame in enumerate(frames):
    sc.frame_set(frame)
    dg = bpy.context.evaluated_depsgraph_get()
    copies = []
    for ob in keep:
        mesh = bpy.data.meshes.new_from_object(ob.evaluated_get(dg), depsgraph=dg)
        bm = bmesh.new(); bm.from_mesh(mesh)
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if (ob.matrix_world @ v.co).z > .51], context='VERTS')
        bm.to_mesh(mesh); bm.free()
        copy = bpy.data.objects.new('Feet review '+ob.name, mesh)
        sc.collection.objects.link(copy); copy.matrix_world = ob.matrix_world.copy(); copies.append(copy)
    for view, position, target in [('top', (0,0,4), (0,0,0)), ('front',(0,-4,.31),(0,0,.31))]:
        camera.location = position
        camera.rotation_euler = (Vector(target)-camera.location).to_track_quat('-Z', 'Y').to_euler()
        if view=='top': camera.rotation_euler=(0,0,math.pi)
        sc.render.filepath = str(out/f'{view}-{index:02}.png')
        bpy.ops.render.render(write_still=True)
    for ob in copies:
        mesh = ob.data; bpy.data.objects.remove(ob, do_unlink=True); bpy.data.meshes.remove(mesh)
print('FEET_RENDER_READY',out,flush=True)
assert not failures, failures
