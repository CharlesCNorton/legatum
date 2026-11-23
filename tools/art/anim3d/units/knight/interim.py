"""Publish each raw stage immediately, before later stages or colour refinement."""
import os,sys
from pathlib import Path
from PIL import Image
from delivery import label_sheet,CLIPS,CREAM
R=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')));M=R/'masters/knight';V=R/'review/3d-v2';stage=sys.argv[1];res=sys.argv[2]
folder=M/'renders'/res/stage;paths=sorted(folder.glob('hero-*.png'));frames=[Image.open(p).convert('RGBA') for p in paths]
ref=Image.open('app/src/assets/units/knight-256.png').convert('RGBA')
if stage in ['b','c']:
 label_sheet([ref,frames[0]],['Painting','Raw '+stage]).save(V/f"knight-{'b-plain' if stage=='b' else 'c-textured-lit'}.png")
if stage=='c':
 rest=frames[0].resize((256,256),Image.Resampling.LANCZOS);pieces=[];labels=[]
 for box,name in [((108,55,140,89),'Helmet'),((132,86,165,149),'Shield'),((73,142,125,204),'Caparison')]:
  pieces.extend([ref.crop(box),rest.crop(box)]);labels.extend([name+' art',name+' 3D'])
 label_sheet(pieces,labels,192).save(V/'knight-c-details.png')
elif stage=='d':label_sheet(frames,['Attack '+str(i+1) for i in range(len(frames))]).save(V/'knight-d-rig-poses.png')
elif stage.startswith('e-'):
 name=stage[2:];label_sheet(frames,[f'{name} {i+1}' for i in range(len(frames))]).save(V/f'knight-{stage}-strip.png');frames=[im.resize((256,256),Image.Resampling.LANCZOS) for im in frames];frames[0].save(V/f'knight-{stage}.webp',save_all=True,append_images=frames[1:],duration=round(1000/CLIPS[name][1]),loop=0,quality=85)
print('INTERIM_PUBLISHED',stage)
