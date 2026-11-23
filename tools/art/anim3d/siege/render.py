"""Render saved siege geometry through CPU preview or host Metal Eevee."""
import bpy,os,sys,json,hashlib,shutil,time
from pathlib import Path
from mathutils import Vector
root=Path(os.environ['ANIM_ROOT']);m=root/'masters/field-cannon';stage=sys.argv[sys.argv.index('--')+1]
clip=stage[2:] if stage.startswith('e-') else 'attack' if stage=='d' else None
path=m/'clips'/f'{clip}.blend' if clip else m/('field-cannon-plain.blend' if stage=='b' else 'field-cannon.blend')
bpy.ops.wm.open_mainfile(filepath=str(path));sc=bpy.context.scene;assert sc.camera is not None,'Saved siege camera is missing'
sc.render.engine=os.environ.get('RENDER_ENGINE','CYCLES')
if sc.render.engine=='CYCLES':
 sc.cycles.device=os.environ.get('CYCLES_DEVICE','CPU');sc.cycles.samples=int(os.environ.get('SAMPLES','12'));sc.cycles.use_denoising=True
 if sc.cycles.device=='GPU':
  prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices()
  for device in prefs.devices:device.use=device.type=='METAL'
  assert any(d.use for d in prefs.devices),'No Metal Cycles device; use CPU explicitly for sandbox previews'
sc.render.threads_mode='FIXED';sc.render.threads=3;sc.render.resolution_x=sc.render.resolution_y=int(os.environ.get('RESOLUTION','512'))
out=m/'renders'/stage;out.mkdir(parents=True,exist_ok=True)
if clip:
 frames=json.loads(sc['sample_frames'])
 if stage=='d':frames=[frames[i] for i in [0,2,4,9]]
 held_pose=None
 for i,f in enumerate(frames):
  sc.frame_set(f);bpy.context.view_layer.update()
  if stage=='e-death' and i>=len(frames)-2:
   values=[v for o in sc.objects for row in o.matrix_world for v in row]
   values.extend(v for o in sc.objects if o.type=='ARMATURE' for p in o.pose.bones for row in p.matrix for v in row)
   if held_pose is not None:
    assert max(abs(a-b) for a,b in zip(values,held_pose))<1e-6,'Terminal geometry changed during hold'
    shutil.copyfile(out/f'{i-1:02}.png',out/f'{i:02}.png');continue
   held_pose=values
  sc.render.filepath=str(out/f'{i:02}.png');bpy.ops.render.render(write_still=True)
else:
 views=[('three-quarter',None),('front',(0,-7,3)),('side',(7,0,3))] if stage=='b' else [('three-quarter',None)]
 base_scale=sc.camera.data.ortho_scale
 for name,pos in views:
  sc.camera.data.ortho_scale=base_scale
  if pos is not None:
   # Auxiliary views need room for the barrel's full length; preserve the hero camera.
   offset=Vector((.20,0,0)) if name=='front' else Vector((0,0,0))
   sc.camera.location=Vector(pos)+offset
   sc.camera.rotation_euler=(Vector((0,0,.95))+offset-sc.camera.location).to_track_quat('-Z','Y').to_euler()
   sc.camera.data.ortho_scale=3.2 if name=='front' else 3.0
  sc.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)
(out/'render.json').write_text(json.dumps({'render_id':time.time_ns(),'engine':sc.render.engine,'device':sc.cycles.device if sc.render.engine=='CYCLES' else 'Metal','held_output_samples':{'9':8} if stage=='e-death' else {},'samples':sc.cycles.samples if sc.render.engine=='CYCLES' else None,'resolution':sc.render.resolution_x,'blend_sha256':hashlib.sha256(path.read_bytes()).hexdigest()},indent=2))
