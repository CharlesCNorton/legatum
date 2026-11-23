"""Render one review stage, fail closed on GPU availability, record provenance."""
import bpy, os, sys, json, hashlib, shutil
from pathlib import Path
from mathutils import Vector
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/barbarian-spearman'
stage=sys.argv[sys.argv.index('--')+1]
clip=stage[2:] if stage.startswith('e-') else 'attack' if stage=='d' else 'move' if stage=='g-feet' else None
path=M/'clips'/f'{clip}.blend' if clip else M/('registered.blend' if stage=='b' else 'barbarian-spearman.blend')
bpy.ops.wm.open_mainfile(filepath=str(path));sc=bpy.context.scene
if clip:assert sc['source_sha256']==hashlib.sha256((M/'barbarian-spearman.blend').read_bytes()).hexdigest(),'Stale clip source'
sc.render.engine=os.environ.get('RENDER_ENGINE','CYCLES')
if sc.render.engine=='CYCLES':
 sc.cycles.device=os.environ.get('CYCLES_DEVICE','CPU');sc.cycles.samples=int(os.environ.get('SAMPLES','8'));sc.cycles.use_denoising=True
 if sc.cycles.device=='GPU':
  prefs=bpy.context.preferences.addons['cycles'].preferences;backend=os.environ.get('CYCLES_BACKEND','METAL');prefs.compute_device_type=backend;prefs.get_devices()
  gpu=[d for d in prefs.devices if d.type==backend];assert gpu,f'No {backend} device; no silent fallback'
  for d in prefs.devices:d.use=d.type==backend
size=int(os.environ.get('RESOLUTION','256'));sc.render.resolution_x=sc.render.resolution_y=size
out=M/'renders'/stage;out.mkdir(parents=True,exist_ok=True);(out/'render.json').unlink(missing_ok=True)
if (out/'raw').exists():shutil.rmtree(out/'raw')
assert sc.camera,'Missing camera'
sc.render.use_persistent_data=True
if stage=='g-feet':
 # Diagnostic cutaway: actual footwear and calf wraps, all eight saved move samples.
 for ob in sc.objects:
  if ob.type=='MESH' and not any(key in ob.name for key in ['Lasted leather shoe','Leather boot','Shoe wrap','Crossed calf bindings','Stationary cream base']):ob.hide_render=True
 sc.camera.data.ortho_scale=1.65
 for row,(pos,target) in enumerate([((0,0,5),(0,0,0)),((0,-5,.32),(0,0,.32))]):
  sc.camera.location=pos;sc.camera.rotation_euler=(Vector(target)-sc.camera.location).to_track_quat('-Z','Y').to_euler()
  for i,frame in enumerate(json.loads(sc['sample_frames'])):
   sc.frame_set(frame);sc.render.filepath=str(out/f'{row*8+i:02}.png');bpy.ops.render.render(write_still=True)
elif clip:
 frames=json.loads(sc['sample_frames']);frames=[frames[i] for i in [0,2,4,9]] if stage=='d' else frames
 for i,frame in enumerate(frames):
  if i and frame==frames[i-1]:
   shutil.copy2(out/f'{i-1:02}.png',out/f'{i:02}.png');continue
  sc.frame_set(frame);sc.cycles.seed=17;sc.cycles.use_animated_seed=False;sc.render.filepath=str(out/f'{i:02}.png');bpy.ops.render.render(write_still=True)
else:
 views=[('00',None),('01',(6,-4,3.5)),('02',(7,0,3.5))] if stage=='b' else [('00',None)]
 for name,pos in views:
  if pos:sc.camera.location=pos;sc.camera.rotation_euler=(Vector((0,0,1.02))-sc.camera.location).to_track_quat('-Z','Y').to_euler()
  sc.render.filepath=str(out/f'{name}.png');bpy.ops.render.render(write_still=True)
(out/'render.json').write_text(json.dumps({'engine':sc.render.engine,'device':sc.cycles.device,'samples':sc.cycles.samples,'resolution':size,'blend_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'blender':bpy.app.version_string,'source_sha256':sc.get('source_sha256')},indent=2))
print('RENDER_READY',stage)
