"""Actual top/front move-cycle renders and source-derived foot direction audit."""
import bpy, os, json, subprocess
from pathlib import Path
from mathutils import Vector
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/pikeman';bpy.ops.wm.open_mainfile(filepath=str(M/'clips/move.blend'));sc=bpy.context.scene;rig=bpy.data.objects['RIG-pikeman'];cam=sc.camera
motion=json.loads(sc['clip_info'])['motion'];contacts=motion['contact']['planted']
sc.render.engine='CYCLES';sc.cycles.device=os.environ.get('CYCLES_DEVICE','CPU');sc.cycles.samples=int(os.environ.get('SAMPLES','8'));sc.cycles.use_denoising=True;sc.cycles.max_bounces=3
if sc.cycles.device=='GPU':
 prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices();assert any(d.type=='METAL' for d in prefs.devices),'GPU unavailable'
 for d in prefs.devices:d.use=d.type=='METAL'
sc.render.resolution_x=sc.render.resolution_y=128;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA'
out=M/'feet';out.mkdir(exist_ok=True);records=[]
# Clip upper body for this diagnostic only; no scene save or geometry mutation.
cam.data.type='ORTHO';cam.data.ortho_scale=1.15
for view in ['top','front']:
 for i in range(8):
  sc.frame_set(i+1);bpy.context.view_layer.update();center=rig.location.copy();center.z=.22
  cam.location=center+Vector((0,0,4) if view=='top' else (0,-4,.15));cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
  if view=='top':cam.data.clip_start=3.6;cam.data.clip_end=4.6
  else:cam.data.clip_start=.01;cam.data.clip_end=100
  sc.render.filepath=str(out/f'{view}-{i:02}.png');bpy.ops.render.render(write_still=True)
  if view=='top':
   frame={'frame':i+1,'feet':{}}
   for s in ['l','r']:
    ankle=rig.matrix_world@rig.pose.bones['foot_'+s].head;toe=rig.matrix_world@rig.pose.bones['ball_'+s].tail;direction=toe-ankle;xy=Vector((direction.x,direction.y,0)).normalized()
    frame['feet'][s]={'ankle':list(ankle),'toe':list(toe),'forward_dot':xy.dot(Vector((0,-1,0))),'planted':contacts[str(25+round(i*24/8))][s]}
   records.append(frame)
planted=[v for f in records for v in f['feet'].values() if v['planted']]
assert all(v['forward_dot']>.95 for v in planted),'Planted feet not aligned with travel'
speed=motion['contact']['virtual_forward_speed_m_s']*12/8
residual=[]
for first,second in zip(records,records[1:]):
 for side in ['l','r']:
  a,b=first['feet'][side],second['feet'][side]
  if a['planted'] and b['planted']:
   delta=Vector(b['ankle'])-Vector(a['ankle']);residual.append((delta.x**2+(delta.y-speed/12)**2)**.5)
max_slide=max(residual,default=0)
assert max_slide<.015,('Planted stance slips against virtual travel',max_slide)
(out/'audit.json').write_text(json.dumps({'device':sc.cycles.device,'travel_forward':[0,-1,0],'virtual_speed_m_s':speed,'max_sampled_stance_residual_m':max_slide,'frames':records},indent=2))
subprocess.run([str(R/'venv/bin/python'),str(Path(__file__).with_name('feet_review.py'))],check=True)
