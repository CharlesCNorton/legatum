"""Round-1 targeted repair: correct flash's local transform, rerender only visible sample.
All other frame pixels are unaffected because the flash is keyed hidden. Keep the
editable clips consistent too. The main build now constructs this correctly.
"""
import bpy, os, math, json, hashlib, shutil, subprocess
from pathlib import Path
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/artillery';HERE=Path(__file__).resolve().parent
man=json.loads((M/'render-manifest.json').read_text());(M/'render-manifest.json').unlink()
for clip in ['idle','move','hit','death','attack']:
 bpy.ops.wm.open_mainfile(filepath=str(M/f'artillery-{clip}.blend'));sc=bpy.context.scene;sc.frame_set(1)
 flash=bpy.data.objects['GEO-Muzzle flash'];flash.location=(1.44,0,0);flash.rotation_euler=(0,math.pi/2,0)
 bpy.ops.wm.save_as_mainfile(filepath=str(M/f'artillery-{clip}.blend'))
 if clip=='attack':
  sc.frame_set(4);assert not flash.hide_render;assert sc.camera
  sc.cycles.device='CPU';sc.render.filepath=str(M/'renders/attack/03.png');bpy.ops.render.render(write_still=True)
  shutil.copyfile(M/'renders/attack/03.png',M/'512/attack/03.png');shutil.copyfile(M/'renders/attack/03.png',M/'renders/pose-3.png')
  man['clips']['attack']['hashes'][3]=hashlib.sha256((M/'renders/attack/03.png').read_bytes()).hexdigest()
man['script_sha256']=hashlib.sha256((HERE/'scene.py').read_bytes()).hexdigest()
man['repair']='Flash placed in recoil-local coordinates in every clip; only visible attack sample 03 rerendered. Main build fixed identically.'
(M/'render-manifest.json').write_text(json.dumps(man,indent=2))
for stage in ['e-attack','d-rig-poses']:subprocess.run([str(R/'venv/bin/python'),str(HERE/'review.py'),stage],check=True)
with (R/'review/3d-v2/artillery-log.md').open('a') as f:f.write('- Fixed flash parent-space bug in build and all saved clips; rerendered visible firing sample, republished attack/pose reviews.\n')
