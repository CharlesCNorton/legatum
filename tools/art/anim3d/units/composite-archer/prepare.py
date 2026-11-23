"""Align the full painting to its committed token; retain immutable inputs."""
import os, json, hashlib
from pathlib import Path
from PIL import Image
ROOT=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'))
A=ROOT/'assets/composite-archer'; M=ROOT/'masters/composite-archer'
M.mkdir(parents=True,exist_ok=True)
source=Image.open(A/'painting-source.png').convert('RGBA')
ref=Image.open('app/src/assets/units/composite-archer-256.png').convert('RGBA')
sbox=source.getchannel('A').point(lambda v:255 if v>32 else 0).getbbox()
tbox=ref.getchannel('A').point(lambda v:255 if v>32 else 0).getbbox()
canvas=Image.new('RGBA',(1024,1024)); box=tuple(v*4 for v in tbox)
canvas.paste(source.crop(sbox).resize((box[2]-box[0],box[3]-box[1]),Image.Resampling.LANCZOS),box[:2])
canvas.save(A/'painting-aligned.png')
f=Image.open(A/'painted-fills.png');w,h=f.size
for name,box in {'red':(0,0,w//2,h//2),'trousers':(w//2,0,w,h//2),'leather':(0,h//2,w//2,h),'gold':(w//2,h//2,w,h)}.items():
 f.crop(box).resize((512,512)).save(A/f'fill-{name}.png')
report={'source_bbox':sbox,'token_bbox':tbox,'sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(A.glob('*.png'))}}
(M/'inputs.json').write_text(json.dumps(report,indent=2))
print(report)
