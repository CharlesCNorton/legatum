"""Render masters with CPU previews or host Eevee. No silent engine fallback."""
import bpy,os,sys,json,hashlib
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).parent))
from sequence import render_samples
root=Path(os.environ['ANIM_ROOT']);master=root/'masters/spearman-3d-v2'
stage=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'b'
clip=stage[2:] if stage.startswith('e-') else 'attack' if stage=='d' else None
path=master/'clips'/clip/(clip+'.blend') if clip else master/'spearman.blend'
bpy.ops.wm.open_mainfile(filepath=str(path))
sc=bpy.context.scene;sc.render.engine=os.environ.get('RENDER_ENGINE','CYCLES')
if sc.render.engine=='CYCLES':
 sc.cycles.device=os.environ.get('CYCLES_DEVICE','CPU').upper()
 if sc.cycles.device=='GPU':
  prefs=bpy.context.preferences.addons['cycles'].preferences
  prefs.compute_device_type=os.environ.get('CYCLES_BACKEND','METAL')
  prefs.get_devices()
  devices=[d for d in prefs.devices if d.type!='CPU']
  assert devices, 'No Cycles GPU device available; request CPU explicitly for a preview'
  for device in prefs.devices:device.use=device.type!='CPU'
  print('CYCLES_GPU',[(d.name,d.type) for d in devices])
 sc.cycles.samples=int(os.environ.get('SAMPLES','64' if sc.cycles.device=='GPU' else '16'))
 sc.cycles.use_denoising=True
 sc.cycles.use_adaptive_sampling=True
 sc.cycles.adaptive_threshold=.025
 sc.cycles.seed=17
sc.render.resolution_x=sc.render.resolution_y=int(os.environ.get('RESOLUTION','256'))
sc.render.threads_mode='FIXED';sc.render.threads=3
assert sc.camera is not None, 'A saved calibrated camera is required'
out=master/'renders'/stage;out.mkdir(parents=True,exist_ok=True)
# A failed rerender must not leave a valid manifest beside a partial frame set.
(out/'render.json').unlink(missing_ok=True)
if clip:
 assert sc.get('cloth_baked'), 'Per-clip cloth must be baked before rendering'
 frames=json.loads(sc['sample_frames'])
 if stage=='d': frames=[frames[i] for i in [0,2,4,9]]
 def render_sample(frame,destination):
  sc.frame_set(frame);sc.render.filepath=str(destination);bpy.ops.render.render(write_still=True)
 render_samples(frames,out,render_sample)
else:
 views=[('front',(0,-7,3.0)),('three-quarter',(2.5,-7,3.0)),('side',(7,-.3,3.0))] if stage=='b' else [('three-quarter',None)]
 for name,pos in views:
  if pos is not None:
   sc.camera.location=pos;sc.camera.rotation_euler=(Vector((0,0,1.25))-sc.camera.location).to_track_quat('-Z','Y').to_euler()
  sc.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)
(out/'render.json').write_text(json.dumps({'engine':sc.render.engine,'device':sc.cycles.device if sc.render.engine=='CYCLES' else 'GPU','resolution':sc.render.resolution_x,'samples':sc.cycles.samples if sc.render.engine=='CYCLES' else None,'blend_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'blender':bpy.app.version_string,'held_frames':{str(i):frame for i,frame in enumerate(frames)} if clip else {}},indent=2))
print('RENDER_READY',out)
