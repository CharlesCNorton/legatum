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
painted = os.environ.get('SPEARMAN_LOOK') == 'painted' and stage != 'b'
look_hash = None
if painted:
 assert sc.render.engine == 'BLENDER_EEVEE', 'Painted final look requires Eevee on the host'
 sys.path.insert(0, str(Path(__file__).parent/'units/spearman'))
 import look
 from look_receipt import verify
 look_dir = master/'look'
 look_hash = verify(master, look_dir)
 look.configure_render(sc, 'beauty', int(os.environ.get('RESOLUTION','512')), int(os.environ.get('SAMPLES','64')))
 look.apply_materials(sc, 'beauty', look_dir, dict(look.LOOK))
 sc.eevee.taa_render_samples = int(os.environ.get('SAMPLES', '64'))
sc.render.resolution_x=sc.render.resolution_y=int(os.environ.get('RESOLUTION','256'))
sc.render.threads_mode='FIXED';sc.render.threads=3
assert sc.camera is not None, 'A saved calibrated camera is required'
if stage == 'b' and os.environ.get('SPEARMAN_PLAIN') == '1':
 plain=bpy.data.materials.new('Spearman geometry review clay');plain.use_nodes=True
 plain.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.42,.36,.26,1)
 plain.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.8
 sc.view_layers[0].material_override=plain
out=master/'renders'/stage;out.mkdir(parents=True,exist_ok=True)
# A failed rerender must not leave a valid manifest beside a partial frame set.
(out/'render.json').unlink(missing_ok=True)
if clip:
 assert sc.get('cloth_baked'), 'Per-clip cloth must be baked before rendering'
 frames=json.loads(sc['sample_frames'])
 if stage=='d': frames=[frames[i] for i in [0,2,4,9]]
 def render_sample(frame,destination):
  if painted: look.render_frame(sc,destination,frame)
  else:
   sc.frame_set(frame);sc.render.filepath=str(destination);bpy.ops.render.render(write_still=True)
 render_samples(frames,out,render_sample)
else:
 views=[('front',(0,-7,3.0)),('three-quarter',None),('side',(7,-.3,3.0))] if stage=='b' else [('three-quarter',None)]
 camera_matrix=sc.camera.matrix_world.copy()
 for name,pos in views:
  if stage=='b': sc.camera.matrix_world=camera_matrix
  if pos is not None:
   sc.camera.location=pos;sc.camera.rotation_euler=(Vector((0,0,1.25))-sc.camera.location).to_track_quat('-Z','Y').to_euler()
  if painted: look.render_frame(sc,out/(name+'.png'))
  else:
   sc.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)
(out/'render.json').write_text(json.dumps({'engine':sc.render.engine,'device':sc.cycles.device if sc.render.engine=='CYCLES' else 'GPU','resolution':sc.render.resolution_x,'samples':sc.cycles.samples if sc.render.engine=='CYCLES' else sc.eevee.taa_render_samples,'look_sha256':look_hash,'colour_space':'display' if painted else 'linear','blend_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'blender':bpy.app.version_string,'held_frames':{str(i):frame for i,frame in enumerate(frames)} if clip else {}},indent=2))
print('RENDER_READY',out)
