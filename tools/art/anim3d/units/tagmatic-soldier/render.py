"""Sequential Cycles CPU previews / Metal GPU masters; manifest on completion only."""
import bpy, os, sys, json, hashlib, shutil
from pathlib import Path
from mathutils import Vector, Matrix
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/tagmatic-soldier'
stage=sys.argv[sys.argv.index('--')+1];clip=stage[2:] if stage.startswith('e-') else 'attack' if stage=='d' else 'move' if stage=='g' else None
path=M/'clips'/f'{clip}.blend' if clip else M/('unpainted.blend' if stage=='b' else 'tagmatic-soldier.blend')
bpy.ops.wm.open_mainfile(filepath=str(path));sc=bpy.context.scene
sc.render.engine=os.environ.get('RENDER_ENGINE','CYCLES');device=os.environ.get('CYCLES_DEVICE','CPU')
if sc.render.engine=='CYCLES':
 sc.cycles.device=device;sc.cycles.samples=int(os.environ.get('SAMPLES','8'));sc.cycles.use_denoising=True
 if device=='GPU':
  prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices()
  devices=[d for d in prefs.devices if d.type=='METAL'];assert devices,'Metal requested but no Metal device found'
  for d in prefs.devices:d.use=d.type=='METAL'
res=int(os.environ.get('RESOLUTION','256'));sc.render.resolution_x=sc.render.resolution_y=res
sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.file_format='PNG';sc.render.film_transparent=True
out=M/'renders'/stage;out.mkdir(parents=True,exist_ok=True);(out/'render.json').unlink(missing_ok=True)
if stage=='b':
 plain=bpy.data.materials.new('MAT-neutral clay');plain.use_nodes=True;plain.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.42,.36,.28,1)
 sc.view_layers[0].material_override=plain
views=[0,0,0] if stage=='b' else [0]
original_camera=sc.camera.matrix_world.copy()
if clip:
 views=json.loads(sc['sample_frames'])
 if stage=='d':views=[views[i] for i in [0,2,4,7]]
if stage=='g':
 views=views+views
 for o in sc.objects:
  if o.type=='MESH':o.hide_render=not o.name.startswith(('GEO-closed leather shoe','GEO-stitched boot sole','GEO-leather wrapped boot','GEO-boot winding'))
 sc.camera.data.ortho_scale=1.45
for i,frame in enumerate(views):
 if stage=='e-death' and i==len(views)-1:
  shutil.copyfile(out/f'{i-1:02}.png',out/f'{i:02}.png');continue
 sc.frame_set(frame)
 if stage=='b' and i:
  pivot=Vector((0,0,1.08));sc.camera.matrix_world=Matrix.Translation(pivot)@Matrix.Rotation(i*1.0472,4,'Z')@Matrix.Translation(-pivot)@original_camera
 if stage=='g':
  target=Vector((-.13,0,.28));sc.camera.location=target+Vector((0,0,6) if i<8 else (0,-6,.2));sc.camera.rotation_euler=(target-sc.camera.location).to_track_quat('-Z','Y').to_euler()
 sc.render.filepath=str(out/f'{i:02}.png');assert sc.camera is not None;bpy.ops.render.render(write_still=True)
(out/'render.json').write_text(json.dumps({'stage':stage,'held_terminal_frame':len(views)-2 if stage=='e-death' else None,'frames':len(views),'resolution':res,'engine':sc.render.engine,'device':device,'samples':sc.cycles.samples if sc.render.engine=='CYCLES' else None,'blend_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'blender':bpy.app.version_string},indent=2))
print('RENDER_READY',stage)
