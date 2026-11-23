"""Sequential renders with provenance; never silently falls back from GPU."""
import bpy,os,json,hashlib,sys
from pathlib import Path
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/barbarian-pikeman';V=R/'review/3d-v2';V.mkdir(exist_ok=True,parents=True)
stages=os.environ.get('STAGES','b-plain,c-textured-lit').split(',');resolution=int(os.environ.get('RESOLUTION','256'))
for stage in stages:
 clip=stage[2:] if stage.startswith('e-') else 'attack' if stage=='d-rig-poses' else 'move' if stage=='g-feet-check' else None
 path=M/'clips'/f'{clip}.blend' if clip else M/('plain.blend' if stage=='b-plain' else 'barbarian-pikeman.blend')
 bpy.ops.wm.open_mainfile(filepath=str(path));sc=bpy.context.scene;sc.render.engine=os.environ.get('RENDER_ENGINE','CYCLES')
 if sc.render.engine=='CYCLES':
  device=os.environ.get('CYCLES_DEVICE','CPU');sc.cycles.device=device;sc.cycles.samples=int(os.environ.get('SAMPLES','8'));sc.cycles.use_denoising=True;sc.cycles.max_bounces=4
  if device=='GPU':
   prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices();found=False
   for d in prefs.devices:d.use=d.type=='METAL';found=found or d.use
   assert found,'Metal GPU unavailable; no CPU fallback'
 sc.render.resolution_x=sc.render.resolution_y=resolution;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8';sc.render.use_file_extension=True
 out=M/'renders'/str(resolution)/stage;out.mkdir(parents=True,exist_ok=True);(out/'render.json').unlink(missing_ok=True)
 frames=list(range(1,json.loads(sc['clip_info'])['frames']+1)) if clip else [1]
 if stage=='d-rig-poses':frames=[1,3,5,8]
 if stage=='g-feet-check':frames=list(range(1,9))*2
 if stage=='e-death':frames[-1]=frames[-2]
 audit=[]
 base_matrix=[list(r) for r in bpy.data.objects['GEO-cream-stone-base'].matrix_world]
 for i,frame in enumerate(frames):
  if i and frame==frames[i-1]:
   import shutil
   shutil.copyfile(out/f'{i-1:02}.png',out/f'{i:02}.png')
   continue
  sc.frame_set(frame);bpy.context.view_layer.update()
  if stage=='g-feet-check':
   from mathutils import Vector
   target=Vector((-.14,0,.30)) if i<8 else Vector((-.14,0,0))
   sc.camera.location=(-.14,-8,.30) if i<8 else (-.14,0,8)
   sc.camera.rotation_euler=(target-sc.camera.location).to_track_quat('-Z','Y').to_euler()
   sc.camera.data.ortho_scale=1.35;sc.camera.data.clip_start=.1 if i<8 else 7.4
  assert [list(r) for r in bpy.data.objects['GEO-cream-stone-base'].matrix_world]==base_matrix,'Base moved'
  assert all(min(abs(v) for v in o.scale)>.0001 for o in sc.objects),'Unsafe near-zero scale'
  if clip and clip!='death':
   from mathutils import Vector,Matrix
   rig=bpy.data.objects['RIG-pikeman'];pike=bpy.data.objects['CTRL-pike'];inv=Matrix.Translation(Vector((-.24,-.26,1.06))).inverted();a=pike.matrix_world @ (inv @ Vector((-1.17,-.26,.20)));b=pike.matrix_world @ (inv @ Vector((1.17,-.26,2.34)));axis=(b-a).normalized();distances={}
   for side in ['r','l']:
    hand=rig.matrix_world @ rig.pose.bones['hand_'+side].head;delta=hand-a;distance=(delta-axis*delta.dot(axis)).length;distances[side]=distance;assert distance<.13,(clip,frame,side,'hand too far from shaft',distance)
   audit.append({'frame':frame,'wrist_to_shaft':distances})
  sc.render.filepath=str(out/f'{i:02}.png');bpy.ops.render.render(write_still=True)
  if not clip:
   # Immediate unpolished interim; review.py replaces with labelled comparison later.
   import shutil;shutil.copyfile(out/f'{i:02}.png',V/f'barbarian-pikeman-{stage}.png')
 manifest={'stage':stage,'engine':sc.render.engine,'device':os.environ.get('CYCLES_DEVICE','CPU'),'samples':sc.cycles.samples,'resolution':resolution,'blend_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'frames':len(frames),'sample_frames':frames,'audit':audit,'stationary_base':True,'nonzero_scales':True}
 (out/'render.json').write_text(json.dumps(manifest,indent=2));print('RENDER_OK',stage,flush=True)

 # Publish complete interim strips immediately after each stage; no Blender subprocess.
 if (M/'renders'/str(resolution)/'c-textured-lit/render.json').exists():
  import subprocess
  subprocess.run([str(R/'venv/bin/python'),'tools/art/anim3d/units/barbarian-pikeman/deliver.py','--resolution',str(resolution),'--review-only'],check=True)
