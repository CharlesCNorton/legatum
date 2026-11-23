"""Render mounted masters through the shared slot wrapper; no engine fallback."""
import bpy,os,sys,json,hashlib,shutil
from mathutils import Vector
from pathlib import Path
root=Path(os.environ['ANIM_ROOT']);master=root/'masters/cavalry';stage=sys.argv[sys.argv.index('--')+1]
clip=stage[2:] if stage.startswith('e-') else 'attack' if stage=='d' else None
path=master/'clips'/f'{clip}.blend' if clip else master/('cavalry-plain.blend' if stage=='b' else 'cavalry.blend')
bpy.ops.wm.open_mainfile(filepath=str(path));sc=bpy.context.scene;sc.render.engine=os.environ.get('RENDER_ENGINE','CYCLES')
if sc.render.engine=='CYCLES':
 sc.cycles.samples=int(os.environ.get('SAMPLES','8'));sc.cycles.device=os.environ.get('CYCLES_DEVICE','CPU')
 if sc.cycles.device=='GPU':
  prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices()
  devices=[d for d in prefs.devices if d.type=='METAL'];assert devices,'No Metal Cycles device; no silent CPU fallback'
  for d in prefs.devices:d.use=d.type=='METAL'
 sc.cycles.use_denoising=True
sc.render.threads_mode='FIXED';sc.render.threads=3;sc.render.resolution_x=sc.render.resolution_y=int(os.environ.get('RESOLUTION','256'))
out=master/'renders'/stage;out.mkdir(parents=True,exist_ok=True)
manifest=out/'render.json'
manifest.unlink(missing_ok=True)
frames=json.loads(sc['sample_frames']) if clip else [0]
if stage=='d':frames=[frames[i] for i in [0,2,5,9]]
if stage=='b':frames=[0,0,0]
rendered={}
if stage=='b':
 clay=bpy.data.materials.new('GEO-plain-review-clay');clay.diffuse_color=(.55,.49,.38,1);clay.use_nodes=True
 clay.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.55,.49,.38,1)
 sc.view_layers[0].material_override=clay
assert sc.camera is not None,'Missing camera'
for i,f in enumerate(frames):
 destination=out/f'{i:02}.png'
 if stage=='b' and i>0:
  sc.camera.location=((-10,0,3.2),(0,-10,3.2))[i-1];sc.camera.rotation_euler=(Vector((0,0,1.26))-sc.camera.location).to_track_quat('-Z','Y').to_euler()
 if f in rendered and stage!='b':shutil.copyfile(rendered[f],destination)
 else:
  sc.frame_set(f);sc.render.filepath=str(destination);bpy.ops.render.render(write_still=True);rendered[f]=destination
(out/'render.json').write_text(json.dumps({'engine':sc.render.engine,'resolution':sc.render.resolution_x,'samples':sc.cycles.samples,'device':sc.cycles.device if sc.render.engine=='CYCLES' else 'Metal','blend_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'frames':frames,'held_samples_reused':True},indent=2))
