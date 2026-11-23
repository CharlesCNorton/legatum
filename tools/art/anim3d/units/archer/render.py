"""Resumable archer previews and 512 px host masters, no silent GPU fallback."""
import sys,hashlib,shutil
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
stage=sys.argv[sys.argv.index('--')+1];clip=stage[2:] if stage.startswith('e-') else 'attack' if stage=='d' else 'move' if stage=='g-feet-check' else None
path=MASTER/'clips'/f'{clip}.blend' if clip else MASTER/'archer.blend'
out=MASTER/'renders'/stage;out.mkdir(parents=True,exist_ok=True);(out/'render.json').unlink(missing_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(path));sc=bpy.context.scene;sc.render.engine=os.environ.get('RENDER_ENGINE','CYCLES');device=os.environ.get('CYCLES_DEVICE','CPU')
if sc.render.engine=='BLENDER_EEVEE':device='GPU'
if sc.render.engine=='CYCLES':
 sc.cycles.device=device;sc.cycles.samples=int(os.environ.get('SAMPLES','8'));sc.cycles.use_denoising=True
 if device=='GPU':
  pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='METAL';pref.get_devices();devices=[d for d in pref.devices if d.type=='METAL'];assert devices,'No Metal devices; refusing CPU fallback'
  for d in pref.devices:d.use=d.type=='METAL'
res=int(os.environ.get('RESOLUTION','256'));sc.render.resolution_x=sc.render.resolution_y=res;sc.render.threads_mode='FIXED';sc.render.threads=3
frames=list(range(CLIPS[clip][0])) if clip else [0]
if stage=='d':frames=[0,3,5,9]
if stage=='b':frames=[0,1,2]
if stage=='g-feet-check':frames=list(range(8))*2
if stage=='b':
 clay=mat('MAT-review-clay',(.5,.43,.33),rough=.8);sc.view_layers[0].material_override=clay
seen={}
for i,f in enumerate(frames):
 sc.frame_set(f)
 if stage=='g-feet-check':
  target=Vector((0,0,.32)) if i<8 else Vector((0,0,0))
  sc.camera.location=(0,-8,.32) if i<8 else (0,0,8)
  sc.camera.rotation_euler=(target-sc.camera.location).to_track_quat('-Z','Y').to_euler()
  sc.camera.data.ortho_scale=1.35
  sc.camera.data.clip_start=.1 if i<8 else 7.35
 if stage=='b':
  sc.camera.location=[(.15,-8,3.2),(3,-7,3.2),(8,-.5,3.2)][i];sc.camera.rotation_euler=(Vector((.15,0,1.04))-sc.camera.location).to_track_quat('-Z','Y').to_euler()
 actual=i if stage=='g-feet-check' else 8 if clip=='death' and f==9 else f
 if actual in seen:shutil.copyfile(seen[actual],out/f'{i:02}.png');continue
 sc.render.filepath=str(out/f'{i:02}.png');bpy.ops.render.render(write_still=True);seen[actual]=out/f'{i:02}.png'
meta={'engine':sc.render.engine,'device':device,'resolution':res,'samples':sc.cycles.samples,'blend_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'source_sha256':sc.get('source_sha256',hashlib.sha256(path.read_bytes()).hexdigest()),'frames':frames,'stage':stage}
(out/'render.json').write_text(json.dumps(meta,indent=2));log(f'- Rendered {stage}: {res}px {sc.render.engine} {device}, {sc.cycles.samples} samples.')
