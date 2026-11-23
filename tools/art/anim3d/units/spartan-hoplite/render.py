"""Resumable fixed-camera Cycles masters; one render process, honest manifests."""
import bpy, os, json, hashlib, subprocess, shutil
from pathlib import Path
from mathutils import Vector
R=Path(os.environ['ANIM_ROOT']);M=Path(os.environ['ANIM_MASTER']);stage=os.environ['HOPLITE_STAGE']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def render_stage(stage):
 clip=stage[2:] if stage.startswith('e-') else 'attack' if stage=='d' else None
 path=M/'clips'/clip/(clip+'.blend') if clip else M/('plain.blend' if stage=='b' else 'spearman.blend')
 bpy.ops.wm.open_mainfile(filepath=str(path));sc=bpy.context.scene
 engine=os.environ.get('RENDER_ENGINE','CYCLES');device=os.environ.get('CYCLES_DEVICE','CPU');sc.render.engine=engine
 if engine=='CYCLES':
  sc.cycles.device=device;sc.cycles.samples=int(os.environ.get('SAMPLES','12'));sc.cycles.use_denoising=True
  if device=='GPU':
   prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices()
   assert any(d.type=='METAL' for d in prefs.devices),'Metal unavailable; refusing CPU fallback'
   for d in prefs.devices:d.use=d.type=='METAL'
 size=int(os.environ.get('RESOLUTION','256'));sc.render.resolution_x=sc.render.resolution_y=size;sc.render.resolution_percentage=100
 sc.render.threads_mode='FIXED';sc.render.threads=3;sc.render.image_settings.color_mode='RGBA';sc.render.film_transparent=True
 sc.cycles.max_bounces=5;sc.render.use_persistent_data=True
 out=M/'renders'/stage;out.mkdir(parents=True,exist_ok=True);(out/'render.json').unlink(missing_ok=True)
 for resolution in [256,512]:(M/str(resolution)/stage/'render.json').unlink(missing_ok=True)
 frames=json.loads(sc['sample_frames']) if clip else [1]
 if stage=='d':frames=[frames[i] for i in [0,2,4,9]]
 views=[(0,-7,2.8),(2.5,-7,2.8),(7,-.3,2.8)] if stage=='b' else [None]*len(frames)
 if stage=='b':frames=[1]*3
 for i,(f,pos) in enumerate(zip(frames,views)):
  sc.frame_set(f)
  if pos:
   sc.camera.location=pos;sc.camera.rotation_euler=(Vector((0,0,1.13))-sc.camera.location).to_track_quat('-Z','Y').to_euler()
  if i and f == frames[i-1] and pos is None:
   shutil.copyfile(out/f'{i-1:02}.png',out/f'{i:02}.png')
  else:
   sc.render.filepath=str(out/f'{i:02}.png');bpy.ops.render.render(write_still=True)
 (out/'render.json').write_text(json.dumps({'stage':stage,'engine':engine,'device':device,'resolution':size,'samples':sc.cycles.samples,'blend_sha256':sha(path),'source_master_sha256':sha(M/'spearman.blend'),'frames':frames,'blender':bpy.app.version_string},indent=2))
 subprocess.run([str(R/'venv/bin/python'),'tools/art/anim3d/units/spartan-hoplite/deliver.py','review',stage],check=True)
if stage=='all-renders':
 for item in ['c','d','e-idle','e-move','e-attack','e-hit','e-death']:render_stage(item)
else:render_stage(stage)
