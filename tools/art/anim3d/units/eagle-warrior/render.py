"""Sequential CPU previews / GPU finals with source hashes and immediate reviews."""
import bpy,os,json,hashlib,shutil,subprocess
from pathlib import Path
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/eagle-warrior';V=R/'review/3d-v2';stages=os.environ.get('STAGES','b-plain,c-textured-lit').split(',');resolution=int(os.environ.get('RESOLUTION','256'))
for stage in stages:
 clip=stage[2:] if stage.startswith('e-') else 'attack' if stage=='d-rig-poses' else None
 path=M/'clips'/f'{clip}.blend' if clip else M/('plain.blend' if stage=='b-plain' else 'eagle-warrior.blend')
 bpy.ops.wm.open_mainfile(filepath=str(path));sc=bpy.context.scene;sc.render.engine=os.environ.get('RENDER_ENGINE','CYCLES');device=os.environ.get('CYCLES_DEVICE','CPU')
 if sc.render.engine=='CYCLES':
  sc.cycles.device=device;sc.cycles.samples=int(os.environ.get('SAMPLES','8'));sc.cycles.use_denoising=True;sc.cycles.max_bounces=4
  if device=='GPU':
   prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices();found=False
   for d in prefs.devices:d.use=d.type=='METAL';found=found or d.use
   assert found,'Metal unavailable; no CPU fallback'
 sc.render.resolution_x=sc.render.resolution_y=resolution;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8';sc.render.use_file_extension=True
 out=M/'renders'/str(resolution)/stage;out.mkdir(parents=True,exist_ok=True);(out/'render.json').unlink(missing_ok=True);frames=list(range(1,json.loads(sc['clip_info'])['frames']+1)) if clip else [1]
 if stage=='d-rig-poses':frames=[1,3,5,8]
 base=bpy.data.objects['GEO-cream-stone-base'];base_matrix=[list(r) for r in base.matrix_world]
 for i,frame in enumerate(frames):
  sc.frame_set(frame);bpy.context.view_layer.update();assert [list(r) for r in base.matrix_world]==base_matrix;assert all(min(abs(v) for v in o.scale)>.0001 for o in sc.objects),'Unsafe zero scale'
  if stage=='e-death' and i==len(frames)-1:shutil.copyfile(out/f'{i-1:02}.png',out/f'{i:02}.png')
  else:sc.render.filepath=str(out/f'{i:02}.png');bpy.ops.render.render(write_still=True)
  if not clip:shutil.copyfile(out/f'{i:02}.png',V/f'eagle-warrior-{stage}.png')
 manifest={'stage':stage,'engine':sc.render.engine,'device':device,'samples':sc.cycles.samples,'resolution':resolution,'blend_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'frames':len(frames),'stationary_base':True,'nonzero_scales':True};(out/'render.json').write_text(json.dumps(manifest,indent=2));print('RENDER_OK',stage,flush=True)
 rest_manifest=M/'renders'/str(resolution)/'c-textured-lit/render.json'
 if rest_manifest.exists() and json.loads(rest_manifest.read_text())['blend_sha256']==hashlib.sha256((M/'eagle-warrior.blend').read_bytes()).hexdigest():subprocess.run([str(R/'venv/bin/python'),'tools/art/anim3d/units/eagle-warrior/deliver.py','--resolution',str(resolution),'--review-only'],check=True)
