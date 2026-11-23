"""Sequential Cycles CPU previews or explicit Metal GPU finals, fixed camera."""
import sys,hashlib,shutil
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
stage=sys.argv[sys.argv.index('--')+1];clip=stage[2:] if stage.startswith('e-') else 'attack' if stage=='d' else None
path=M/'clips'/f'{clip}.blend' if clip else M/('peltast-unpainted.blend' if stage=='b' else 'peltast.blend')
bpy.ops.wm.open_mainfile(filepath=str(path));sc=bpy.context.scene
sc.render.engine=os.environ.get('RENDER_ENGINE','CYCLES');device=os.environ.get('CYCLES_DEVICE','CPU');size=int(os.environ.get('RESOLUTION','256'))
if sc.render.engine=='CYCLES':
 sc.cycles.device=device;sc.cycles.samples=int(os.environ.get('SAMPLES','8'));sc.cycles.use_denoising=True
 if device=='GPU':
  prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices();gpu=[d for d in prefs.devices if d.type=='METAL'];assert gpu,'Metal device unavailable; no silent CPU fallback'
  for d in prefs.devices:d.use=d.type=='METAL'
sc.render.resolution_x=sc.render.resolution_y=size;sc.render.resolution_percentage=100
sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.film_transparent=True
assert sc.camera is not None
out=M/'raw'/stage;out.mkdir(parents=True,exist_ok=True);(out/'render.json').unlink(missing_ok=True)
if stage=='b':
 plain=material('Plain clay review',(.38,.38,.38),rough=.8);sc.view_layers[0].material_override=plain
 frames=[('rest',1),('side',1)]
elif clip:frames=[(f'{i:02}',i+1) for i in ([0,2,4,8] if stage=='d' else range(CLIPS[clip][0]))]
else:frames=[('rest',1)]
if stage=='e-death':frames=[(name,min(f,CLIPS['death'][0]-1)) for name,f in frames]
rendered={}
for name,f in frames:
 if f in rendered and stage=='e-death':
  shutil.copyfile(rendered[f],out/f'{name}.png');continue
 sc.frame_set(f)
 if name=='side':sc.camera.location=TARGET+Vector((7,-3,2));aim(sc.camera,TARGET)
 sc.render.filepath=str(out/f'{name}.png');bpy.ops.render.render(write_still=True);rendered[f]=out/f'{name}.png'
report={'stage':stage,'engine':sc.render.engine,'device':device if sc.render.engine=='CYCLES' else 'METAL','resolution':size,'samples':sc.cycles.samples if sc.render.engine=='CYCLES' else None,'blend_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'frames':[n for n,f in frames],'timeline_frames':[f for n,f in frames],'blender':bpy.app.version_string}
(out/'render.json').write_text(json.dumps(report,indent=2));print('RENDERED',report)
