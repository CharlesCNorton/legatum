"""Serial render stages, explicit CPU/GPU selection and immediate review output."""
import bpy,os,json,hashlib,shutil,subprocess
from pathlib import Path
from mathutils import Vector
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/cuirassier';U=Path('tools/art/anim3d/units/cuirassier')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for stage in os.environ.get('STAGES','b,c,c-details,d,e-idle,e-move,e-attack,e-hit,e-death').split(','):
 clip=stage[2:] if stage.startswith('e-') else 'attack' if stage=='d' else None
 path=M/'clips'/f'{clip}.blend' if clip else M/('cuirassier-plain.blend' if stage=='b' else 'cuirassier.blend')
 bpy.ops.wm.open_mainfile(filepath=str(path));sc=bpy.context.scene;assert sc.camera
 sc.render.engine=os.environ.get('RENDER_ENGINE','CYCLES');device=os.environ.get('CYCLES_DEVICE','CPU')
 if sc.render.engine=='CYCLES':
  sc.cycles.device=device;sc.cycles.samples=int(os.environ.get('SAMPLES','8'));sc.cycles.use_denoising=True;sc.cycles.max_bounces=6
  if device=='GPU':
   prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices();assert any(d.type=='METAL' for d in prefs.devices),'Metal required'
   for d in prefs.devices:d.use=d.type=='METAL'
 size=int(os.environ.get('RESOLUTION','256'));sc.render.resolution_x=sc.render.resolution_y=size;sc.render.resolution_percentage=100
 sc.render.threads_mode='FIXED';sc.render.threads=3;sc.render.film_transparent=True
 if stage=='b':
  clay=bpy.data.materials.new('Review clay');clay.diffuse_color=(.50,.45,.36,1);clay.use_nodes=True;clay.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.50,.45,.36,1)
  sc.view_layers[0].material_override=clay
 frames=json.loads(sc['sample_frames']) if clip else [0]
 if stage=='d':frames=[1,3,5,8]
 if stage=='b':frames=[0,0,0]
 out=M/'renders'/stage;out.mkdir(parents=True,exist_ok=True);(out/'render.json').unlink(missing_ok=True);used={};camera=sc.camera.matrix_world.copy()
 for i,f in enumerate(frames):
  dst=out/f'{i:02}.png'
  if f in used and stage!='b':shutil.copyfile(used[f],dst)
  else:
   sc.frame_set(f)
   if stage=='b' and i:
    sc.camera.location=Vector((0,-10,3.7)) if i==1 else Vector((-10,0,3.7));sc.camera.rotation_euler=(Vector((0,0,1.35))-sc.camera.location).to_track_quat('-Z','Y').to_euler()
   sc.render.filepath=str(dst);bpy.ops.render.render(write_still=True);used[f]=dst
 manifest={'engine':sc.render.engine,'device':device,'resolution':size,'samples':sc.cycles.samples,'blend_sha256':sha(path),'frames':frames,'source_master_sha256':sc.get('source_master_sha256',sha(path))}
 (out/'render.json').write_text(json.dumps(manifest,indent=2))
 subprocess.run([str(R/'venv/bin/python'),str(U/'post.py'),stage],check=True)
 print('REVIEW_READY',stage,flush=True)
