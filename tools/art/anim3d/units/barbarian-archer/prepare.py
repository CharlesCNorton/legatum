"""Normalize source to the shipped token's exact framing and split generated fills."""
from pathlib import Path
from PIL import Image
import os,hashlib,json
root=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'))
a=root/'assets/barbarian-archer'
src=Image.open(a/'painting-source.png').convert('RGBA')
ref=Image.open('app/src/assets/units/barbarian-archer-256.png').convert('RGBA')
bbox=ref.getchannel('A').point(lambda x:255 if x>32 else 0).getbbox()
sbox=src.getchannel('A').point(lambda x:255 if x>32 else 0).getbbox()
out=Image.new('RGBA',(1024,1024));box=tuple(v*4 for v in bbox)
out.paste(src.crop(sbox).resize((box[2]-box[0],box[3]-box[1]),Image.Resampling.LANCZOS),(box[0],box[1]));out.save(a/'painting-registered.png')
f=Image.open(a/'painted-fills.png').convert('RGB');w,h=f.size
for name,b in [('fur',(0,0,w//2,h//2)),('linen',(w//2,0,w,h//2)),('leather',(0,h//2,w//2,h)),('hair',(w//2,h//2,w,h))]:f.crop(b).save(a/f'fill-{name}.png')
(a/'inputs.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in a.glob('*.png')},indent=2))
print('Registered source',sbox,'to token',bbox)
