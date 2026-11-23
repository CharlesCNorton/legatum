"""Render saved stage or clip; manifests bind raw pixels to the exact blend."""
import sys, json, hashlib, os, shutil
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
stage=sys.argv[sys.argv.index('--')+1];clip=stage[2:] if stage.startswith('e-') else None
blend=M/(f'medjay-{clip}.blend' if clip else 'medjay-attack.blend' if stage=='d' else 'medjay.blend')
bpy.ops.wm.open_mainfile(filepath=str(blend));sc=configure();out=M/'renders'/stage;out.mkdir(parents=True,exist_ok=True);manifest=out/'render.json';manifest.unlink(missing_ok=True)
if stage=='b':
 clay=material('Plain clay review',(.50,.45,.36),rough=.8);sc.view_layers[0].material_override=clay
frames=list(range(1,CLIPS[clip][0]+1)) if clip else [1,3,5,8] if stage=='d' else [0]
if clip=='death':frames[-1]=frames[-2]
for i,f in enumerate(frames):
 if i and f==frames[i-1]:
  shutil.copyfile(out/f'{i-1:02d}.png',out/f'{i:02d}.png');continue
 sc.frame_set(f);sc.render.filepath=str(out/f'{i:02d}.png');bpy.ops.render.render(write_still=True)
manifest.write_text(json.dumps({'stage':stage,'blend':str(blend),'blend_sha256':hashlib.sha256(blend.read_bytes()).hexdigest(),'engine':sc.render.engine,'device':os.environ.get('CYCLES_DEVICE','CPU'),'resolution':sc.render.resolution_x,'samples':sc.cycles.samples,'frames':frames,'held_frame_reused':clip=='death','sha256':{f'{i:02d}.png':hashlib.sha256((out/f'{i:02d}.png').read_bytes()).hexdigest() for i in range(len(frames))}},indent=2))
log(f'Rendered {stage}: {len(frames)} frames, {sc.render.resolution_x}px, {sc.render.engine}/{os.environ.get("CYCLES_DEVICE","CPU")}.')
