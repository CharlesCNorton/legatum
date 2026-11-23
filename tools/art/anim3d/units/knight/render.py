"""Render knight stages, transparent source frames and gait inspection serially."""
import bpy,os,json,hashlib,sys,subprocess
from pathlib import Path
from mathutils import Vector
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/knight'
resolution=int(os.environ.get('RESOLUTION','256'));samples=int(os.environ.get('SAMPLES','8'));device=os.environ.get('CYCLES_DEVICE','CPU')
stages=os.environ.get('STAGES','c').split(',')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def setup(path):
 bpy.ops.wm.open_mainfile(filepath=str(path));s=bpy.context.scene
 s.render.engine='CYCLES';s.cycles.device=device;s.cycles.samples=samples;s.cycles.use_denoising=True;s.cycles.max_bounces=4
 if device=='GPU':
  pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='METAL';pref.get_devices()
  assert any(d.type=='METAL' for d in pref.devices),'Metal GPU unavailable; no CPU fallback'
  for d in pref.devices:d.use=d.type=='METAL'
 s.render.resolution_x=s.render.resolution_y=resolution;s.render.resolution_percentage=100;s.render.film_transparent=True
 s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA';s.render.image_settings.color_depth='8';s.render.use_persistent_data=True
 assert s.camera is not None
 return s
for stage in stages:
 path=M/('knight-base.blend' if stage=='base' else 'knight-plain.blend' if stage=='b' else 'clips/attack.blend' if stage=='d' else 'clips/move.blend' if stage=='g' else f'clips/{stage[2:]}.blend' if stage.startswith('e-') else 'knight.blend')
 s=setup(path);out=M/'renders'/str(resolution)/stage;out.mkdir(parents=True,exist_ok=True)
 manifest=out/'manifest.json';manifest.unlink(missing_ok=True)
 frames=json.loads(s.get('sample_frames','[0]')) if stage.startswith('e-') or stage=='g' else [1,4,7,10] if stage=='d' else [0]
 if stage=='g':
  # Diagnostic only: expose the actual skinned lower legs so the top view can
  # judge hoof axes instead of looking at the caparison's opaque roof.
  import bmesh
  s.frame_set(frames[0]);bpy.context.view_layer.update();horse=bpy.data.objects['Horse']
  ev=horse.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
  assert len(me.vertices)==len(horse.data.vertices)
  remove={v.index for v in me.vertices if (ev.matrix_world@v.co).z>.85};ev.to_mesh_clear()
  horse.data=horse.data.copy();bm=bmesh.new();bm.from_mesh(horse.data);bm.verts.ensure_lookup_table();bmesh.ops.delete(bm,geom=[v for v in bm.verts if v.index in remove],context='VERTS');bm.to_mesh(horse.data);bm.free()
  for ob in s.objects:
   if ob.type in {'MESH','CURVE'} and ob not in {horse,bpy.data.objects['Stationary cream stone']}:ob.hide_render=True
 records=[]
 if stage=='b':
  clay=bpy.data.materials.new('Review clay');clay.diffuse_color=(.5,.5,.5,1);clay.use_nodes=True;clay.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.5,.5,.5,1);s.view_layers[0].material_override=clay
 for view in (['front','top'] if stage=='g' else ['hero']):
  if view=='front':s.camera.location=(0,-8,.9);target=Vector((0,0,.4));s.camera.data.ortho_scale=2.2
  elif view=='top':s.camera.location=(0,0,8);target=Vector((0,0,0));s.camera.data.ortho_scale=2.7
  if view!='hero':s.camera.rotation_euler=(target-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.shift_x=s.camera.data.shift_y=0
  for i,frame in enumerate(frames):
   s.frame_set(frame);s.render.filepath=str(out/f'{view}-{i:02d}.png');bpy.ops.render.render(write_still=True)
   records.append({'file':Path(s.render.filepath).name,'frame':frame,'sha256':sha(Path(s.render.filepath))})
 manifest.write_text(json.dumps({'stage':stage,'resolution':resolution,'device':device,'samples':samples,'blend':str(path),'blend_sha256':sha(path),'frames':records},indent=2))
 print('KNIGHT_RENDER_READY',stage,flush=True)
 if stage!='base' and stage!='g':subprocess.run([str(R/'venv/bin/python'),'tools/art/anim3d/units/knight/interim.py',stage,str(resolution)],check=True)
