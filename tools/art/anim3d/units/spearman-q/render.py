"""Render saved round-2 masters through the same CPU/GPU painted material path."""
import argparse,json,os,sys
from pathlib import Path
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
import look

root=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'))
lane=root/'lanes/spearman-q-r2'
p=argparse.ArgumentParser();p.add_argument('--gpu',action='store_true');p.add_argument('--clip',required=True)
p.add_argument('--resolution',type=int,default=160);p.add_argument('--samples',type=int,default=32)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
bpy.ops.wm.open_mainfile(filepath=str(lane/'masters'/f'{a.clip}.blend'))
s=bpy.context.scene
look.apply(s,lane/'input/look',gpu=a.gpu)
s.render.resolution_x=s.render.resolution_y=a.resolution;s.render.resolution_percentage=100
if not a.gpu:s.cycles.samples=a.samples
folder=(lane/'gpu' if a.gpu else lane)/'frames'/a.clip;folder.mkdir(parents=True,exist_ok=True)
for f in range(s.frame_start,s.frame_end+1):
    s.frame_set(f);look.update_contacts(s)
    s.render.filepath=str(folder/f'{f-1:02}.png');bpy.ops.render.render(write_still=True)
receipt=json.loads((lane/'frames'/a.clip/'receipt.json').read_text())
receipt.update(stage='Eevee GPU' if a.gpu else 'painted CPU proxy',master_resolution=a.resolution)
(folder/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
