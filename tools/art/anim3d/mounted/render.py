"""Render mounted masters through the shared slot wrapper; no engine fallback."""
import bpy,os,sys,json,hashlib,shutil
from pathlib import Path
root=Path(os.environ['ANIM_ROOT']);master=root/'masters/horseman-3d';stage=sys.argv[sys.argv.index('--')+1]
clip=stage[2:] if stage.startswith('e-') else 'attack' if stage=='d' else None
path=master/'clips'/f'{clip}.blend' if clip else master/'horseman.blend'
bpy.ops.wm.open_mainfile(filepath=str(path));sc=bpy.context.scene;sc.render.engine=os.environ.get('RENDER_ENGINE','CYCLES')
if sc.render.engine=='CYCLES':
 sc.cycles.samples=int(os.environ.get('SAMPLES','8'));sc.cycles.device=os.environ.get('CYCLES_DEVICE','CPU')
 if sc.cycles.device=='GPU':
  prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices()
  devices=[d for d in prefs.devices if d.type=='METAL'];assert devices,'No Metal Cycles device; no silent CPU fallback'
  for d in prefs.devices:d.use=d.type=='METAL'
 sc.cycles.use_denoising=True
sc.render.threads_mode='FIXED';sc.render.threads=3;sc.render.resolution_x=sc.render.resolution_y=int(os.environ.get('RESOLUTION','256'))
sc.render.use_persistent_data=True
out=master/'renders'/stage;out.mkdir(parents=True,exist_ok=True)
if stage=='b':
 # Actual plain geometry evidence from the same registered model.
 mat=bpy.data.materials.new('Horseman plain clay');mat.diffuse_color=(.55,.45,.30,1);mat.use_nodes=True
 mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.55,.45,.30,1)
 mat.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.8
 sc.view_layers[0].material_override=mat
frames=json.loads(sc['sample_frames']) if clip else [0]
if stage=='d':frames=[frames[i] for i in [0,2,5,9]]
rendered={}
for i,f in enumerate(frames):
 destination=out/f'{i:02}.png'
 if f in rendered:shutil.copyfile(rendered[f],destination)
 else:
  sc.frame_set(f);sc.render.filepath=str(destination);bpy.ops.render.render(write_still=True);rendered[f]=destination
(out/'render.json').write_text(json.dumps({'engine':sc.render.engine,'resolution':sc.render.resolution_x,'samples':sc.cycles.samples,'device':sc.cycles.device if sc.render.engine=='CYCLES' else 'Metal','blend_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'frames':frames,'held_samples_reused':True},indent=2))

if stage=='b':
 for size in (512,256):
  if sc.render.resolution_x==size:
   target=root/'masters/horseman'/str(size)/stage;target.mkdir(parents=True,exist_ok=True)
   shutil.copyfile(out/'00.png',target/'00.png')
