"""Serial GPU/CPU renders. No subprocess Blender and no silent GPU fallback."""
import bpy,os,sys,json,hashlib,shutil,subprocess
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/keshig';Q=R/'review/3d-v2';Q.mkdir(parents=True,exist_ok=True)
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['all']
stage=args[0];res=int(os.environ.get('RESOLUTION','256'));samples=int(os.environ.get('SAMPLES','8'))
clips={'idle':8,'move':8,'attack':10,'hit':4,'death':10}
def log(msg):
 with (Q/'keshig-log.md').open('a') as f:f.write(msg+'\n')
def open_scene(file):
 bpy.ops.wm.open_mainfile(filepath=str(file));sc=bpy.context.scene
 sc.render.engine=os.environ.get('RENDER_ENGINE','CYCLES');sc.cycles.device=os.environ.get('CYCLES_DEVICE','CPU')
 if sc.render.engine=='CYCLES' and sc.cycles.device=='GPU':
  pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='METAL';pref.get_devices()
  gpu=[d for d in pref.devices if d.type=='METAL'];assert gpu,'Metal GPU required; no CPU fallback'
  for d in pref.devices:d.use=d.type=='METAL'
 sc.cycles.samples=samples;sc.cycles.use_denoising=True;sc.cycles.max_bounces=6
 sc.render.resolution_x=sc.render.resolution_y=res;sc.render.resolution_percentage=100
 sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8'
 sc.render.use_persistent_data=True
 assert sc.camera is not None
 return sc
def save_frame(sc,path,frame):
 path.parent.mkdir(parents=True,exist_ok=True);sc.frame_set(frame);sc.render.filepath=str(path);bpy.ops.render.render(write_still=True)
def render_rest(name,file):
 sc=open_scene(file)
 if name=='b-plain':
  mat=bpy.data.materials.new('Neutral clay review');mat.use_nodes=True;mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.42,.42,.42,1);mat.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.8;sc.view_layers[0].material_override=mat
 (M/'renders'/name).mkdir(parents=True,exist_ok=True)
 (M/'renders'/name/'manifest.json').unlink(missing_ok=True)
 save_frame(sc,M/'renders'/name/'000.png',sc.get('rest_frame',3))
 # Every stage gets immediately visible review evidence, even before deliver.py.
 shutil.copyfile(M/'renders'/name/'000.png',Q/f'keshig-{name}.png');log(f'Rendered {name}: {res}px {sc.render.engine} {sc.cycles.device}, {samples} samples.')
 base=bpy.data.objects['Stationary cream stone'];anchor=world_to_camera_view(sc,sc.camera,base.matrix_world@Vector((0,0,.05)))
 manifest={'anchor_160':[round(anchor.x*160),round((1-anchor.y)*160)],'engine':sc.render.engine,'device':sc.cycles.device,'resolution':res,'samples':samples,'blend_sha256':hashlib.sha256(file.read_bytes()).hexdigest()}
 (M/'renders'/name/'manifest.json').write_text(json.dumps(manifest,indent=2))
if stage in ['all','b']:
 render_rest('b-plain',(M/'plain.blend') if (M/'plain.blend').exists() else (M/'unpainted.blend'))
if stage in ['all','c']:
 render_rest('c-textured-lit',M/'keshig.blend')
 sc=bpy.context.scene
 # Same full-scene frame preserves framing; deliver.py makes detail crops.
 shutil.copyfile(M/'renders/c-textured-lit/000.png',Q/'keshig-c-details.png')
if stage in ['all','d']:
 file=M/'clips/attack.blend';sc=open_scene(file)
 assert sc['source_master_sha256']==hashlib.sha256((M/'keshig.blend').read_bytes()).hexdigest()
 (M/'renders/d-rig-poses').mkdir(parents=True,exist_ok=True)
 (M/'renders/d-rig-poses/manifest.json').unlink(missing_ok=True)
 for i,frame in enumerate([1,3,5,8]):save_frame(sc,M/'renders/d-rig-poses'/f'{i:03}.png',frame)
 (M/'renders/d-rig-poses/manifest.json').write_text(json.dumps({'engine':sc.render.engine,'device':sc.cycles.device,'resolution':res,'samples':samples,'blend_sha256':hashlib.sha256(file.read_bytes()).hexdigest()}))
 log('Rendered four keyed attack rig poses.')
for clip,count in clips.items():
 if stage not in ['all','e-'+clip]:continue
 file=M/'clips'/f'{clip}.blend';sc=open_scene(file)
 assert sc.get('source_master_sha256')==hashlib.sha256((M/'keshig.blend').read_bytes()).hexdigest(), 'Stale clip master'
 out=M/'renders'/('e-'+clip);out.mkdir(parents=True,exist_ok=True)
 manifest=out/'manifest.json';manifest.unlink(missing_ok=True)
 for i in range(count):
  if clip=='death' and i==count-1:shutil.copyfile(out/f'{i-1:03}.png',out/f'{i:03}.png')
  else:save_frame(sc,out/f'{i:03}.png',i+1)
 manifest.write_text(json.dumps({'clip':clip,'frames':count,'engine':sc.render.engine,'device':sc.cycles.device,'resolution':res,'samples':samples,'blend_sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'master_sha256':hashlib.sha256((M/'keshig.blend').read_bytes()).hexdigest()},indent=2))
 log(f'Rendered {clip}: {count} frames, {res}px, {samples} samples, {sc.cycles.device}.')
 subprocess.run([str(R/'venv/bin/python'),'tools/art/anim3d/units/keshig/deliver.py','--reviews'],check=True)
if stage in ['all','feet']:
 file=M/'clips/move.blend';sc=open_scene(file);cam=sc.camera
 sc.render.resolution_x=sc.render.resolution_y=min(res,256)
 # All eight native-gallop samples; camera and rig's -Y forward axis are fixed.
 for view,loc,target in [('top',(0,0,8),(0,0,0)),('front',(0,-8,1.3),(0,0,.8))]:
  cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=4.2
  for i in range(8):save_frame(sc,M/'feet'/view/f'{i:03}.png',i+1)
 (M/'feet/manifest.json').write_text(json.dumps({'engine':sc.render.engine,'device':sc.cycles.device,'resolution':sc.render.resolution_x,'samples':samples,'blend_sha256':hashlib.sha256(file.read_bytes()).hexdigest()}))
 subprocess.run([str(R/'venv/bin/python'),'tools/art/anim3d/units/keshig/feet_review.py'],check=True)
 log('Rendered top/front views for all eight move samples; native -Y travel axis, no post-retarget foot rotation.')
