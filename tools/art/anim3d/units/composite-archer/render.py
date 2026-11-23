"""Render saved masters only. CPU previews or explicit fail-closed Metal finals."""
import bpy,os,sys,json,hashlib,subprocess
from pathlib import Path
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/composite-archer';HERE=Path(__file__).parent
CLIPS={'idle':(8,10),'move':(8,12),'attack':(10,14),'hit':(4,12),'death':(10,10)}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def configure(sc):
 sc.render.use_persistent_data=True
 sc.render.engine=os.environ.get('RENDER_ENGINE','CYCLES');device=os.environ.get('CYCLES_DEVICE','CPU')
 if sc.render.engine=='CYCLES':
  sc.cycles.device=device;sc.cycles.samples=int(os.environ.get('SAMPLES','8'));sc.cycles.use_denoising=True
  if device=='GPU':
   prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices();found=False
   for d in prefs.devices:d.use=d.type=='METAL';found|=d.type=='METAL'
   if not found:raise RuntimeError('Metal GPU requested but unavailable; no silent CPU fallback')
 sc.render.threads_mode='FIXED';sc.render.threads=3;sc.render.resolution_x=sc.render.resolution_y=int(os.environ.get('RESOLUTION','512'));sc.render.resolution_percentage=100;sc.render.film_transparent=True;sc.render.image_settings.color_mode='RGBA'
 return device
def render(stage):
 clip=stage[2:] if stage.startswith('e-') else None
 blend=M/'clips'/f'{clip}.blend' if clip else M/'composite-archer.blend'
 bpy.ops.wm.open_mainfile(filepath=str(blend));sc=bpy.context.scene
 assert sc.camera is not None,'Saved painting camera required'
 device=configure(sc)
 out=M/'renders'/stage;out.mkdir(parents=True,exist_ok=True);(out/'manifest.json').unlink(missing_ok=True)
 frames=range(1,CLIPS[clip][0]+1) if clip else [1]
 files=[]
 for i,f in enumerate(frames):
  sc.frame_set(f);path=out/f'{i:02d}.png'
  if clip=='death' and i==9:
   import shutil
   shutil.copyfile(out/'08.png',path)
  else:
   sc.render.filepath=str(path);bpy.ops.render.render(write_still=True)
  files.append({'path':str(path.relative_to(M)),'sha256':sha(path)})
 report={'stage':stage,'blend':str(blend.relative_to(M)),'blend_sha256':sha(blend),'engine':sc.render.engine,'device':device,'samples':sc.cycles.samples,'resolution':sc.render.resolution_x,'frames':files}
 (out/'manifest.json').write_text(json.dumps(report,indent=2))
 subprocess.run([str(R/'venv/bin/python'),str(HERE/'post.py'),stage],check=True)
 print('RENDER_READY',stage,flush=True)
if __name__=='__main__':
 stage=os.environ.get('STAGE','c');render(stage)
