"""Actual top/front move-cycle renders, plus bone direction/contact evidence."""
import bpy, os, json, math, subprocess, hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector
R=Path(os.environ['ANIM_ROOT']);M=Path(os.environ['ANIM_MASTER'])
bpy.ops.wm.open_mainfile(filepath=str(M/'clips/move/move.blend'))
sc=bpy.context.scene;rig=bpy.data.objects['Spearman • MPFB game_engine'];cam=sc.camera
sc.render.engine='CYCLES';sc.cycles.device=os.environ.get('CYCLES_DEVICE','CPU');sc.cycles.samples=int(os.environ.get('SAMPLES','8'));sc.cycles.use_denoising=True
if sc.cycles.device=='GPU':
 prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices()
 assert any(d.type=='METAL' for d in prefs.devices)
 for d in prefs.devices:d.use=d.type=='METAL'
sc.render.resolution_x=sc.render.resolution_y=256;sc.render.resolution_percentage=100
sc.render.threads_mode='FIXED';sc.render.threads=3;sc.render.film_transparent=True;sc.render.image_settings.color_mode='RGBA'
out=M/'feet';out.mkdir(exist_ok=True);frames=json.loads(sc['sample_frames']);records=[]
for view in ['top','front']:
 cam.location=(0,0,4) if view=='top' else (0,-5,.28)
 target=Vector((0,0,.23));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=1.25
 # Cut above the ankles in the top view, so the torso cannot hide the sandals.
 cam.data.clip_start=3.6 if view=='top' else .1
 for i,frame in enumerate(frames):
  sc.frame_set(frame);bpy.context.view_layer.update()
  if view=='top':
   row={'frame':frame,'feet':{}}
   for side in ['l','r']:
    ankle=rig.matrix_world @ rig.pose.bones['foot_'+side].head;toe=rig.matrix_world @ rig.pose.bones['ball_'+side].head;v=toe-ankle
    sole=bpy.data.objects['Leather sandal sole '+side]
    evaluated=sole.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=evaluated.to_mesh()
    points=np.array([list(evaluated.matrix_world @ vertex.co) for vertex in mesh.vertices]);evaluated.to_mesh_clear()
    center=points.mean(axis=0);_,vectors=np.linalg.eigh(np.cov((points-center).T));axis=Vector(vectors[:,-1])
    if axis.dot(v)<0:axis=-axis
    row['feet'][side]={'ankle':list(ankle),'toe':list(toe),'yaw_deg':math.degrees(math.atan2(v.x,-v.y)),
      'sole_center':center.tolist(),'sole_yaw_deg':math.degrees(math.atan2(axis.x,-axis.y))}
   records.append(row)
  sc.render.filepath=str(out/f'{view}-{i:02}.png');bpy.ops.render.render(write_still=True)
motion=json.loads((M/'clips/move/clip.json').read_text())['motion']
contact=motion['contact'];fps=6;speed=contact['virtual_forward_speed_m_s']*2/(8/fps)
errors=[];support_yaws=[];sole_errors=[];sole_yaws=[]
for i,row in enumerate(records[:-1]):
 nextrow=records[i+1];a=25+round(i/8*48);b=25+round((i+1)/8*48)
 for side in ['l','r']:
  if contact['planted'].get(str(a),{}).get(side) and contact['planted'].get(str(b),{}).get(side):
   p=Vector(row['feet'][side]['ankle']);q=Vector(nextrow['feet'][side]['ankle']);error=q-p-Vector((0,speed/fps,0));error.z=0
   errors.append(error.length);support_yaws.append(abs(row['feet'][side]['yaw_deg']))
   delta=Vector(nextrow['feet'][side]['sole_center'])-Vector(row['feet'][side]['sole_center'])-Vector((0,speed/fps,0));delta.z=0
   sole_errors.append(delta.length);sole_yaws.append(abs(row['feet'][side]['sole_yaw_deg']))
contact_check={'tested_stance_intervals':len(errors),'max_virtual_ground_error_m':max(errors,default=0),'max_support_yaw_deg':max(support_yaws,default=0),'virtual_forward_speed_m_s':speed,'max_sole_ground_error_m':max(sole_errors,default=0),'max_sole_yaw_deg':max(sole_yaws,default=0)}
assert errors,'No planted intervals were measured'
(out/'evidence.json').write_text(json.dumps({'engine':'CYCLES','device':sc.cycles.device,'samples':sc.cycles.samples,'clip_sha256':hashlib.sha256((M/'clips/move/move.blend').read_bytes()).hexdigest(),'records':records,'contact_check':contact_check,'note':'In-place walk: planted feet move opposite virtual travel; no post-retarget foot orientation changes.'},indent=2))
subprocess.run([str(R/'venv/bin/python'),'tools/art/anim3d/units/spartan-hoplite/feet_sheet.py'],check=True)

assert contact_check['max_support_yaw_deg']<20,contact_check
# Bone displacement is diagnostic; evaluated sole contact is the delivery gate.
assert contact_check['max_sole_yaw_deg']<20,contact_check
assert contact_check['max_sole_ground_error_m']<.025,contact_check
print('FEET CONTACT',contact_check)
