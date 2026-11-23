"""Register the full painting to the shipped token's alpha bounds; pin inputs."""
import hashlib, json, os, shutil
from pathlib import Path
from PIL import Image
ROOT=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'))
A=ROOT/'assets/gaesatae'; A.mkdir(parents=True,exist_ok=True)
source=A/'painting-source.png'
im=Image.open(source).convert('RGBA')
# Source still carries magenta anti-alias fringe from its historical key.
pix=im.load()
for y in range(im.height):
    for x in range(im.width):
        r,g,b,a=pix[x,y]
        if r>g*1.35 and b>g*1.30 and r>120 and b>100:
            pix[x,y]=(r,g,b,0)
ref=Image.open('app/src/assets/units/gaesatae-256.png').convert('RGBA')
b=ref.getchannel('A').point(lambda x:255 if x>30 else 0).getbbox()
s=im.getchannel('A').point(lambda x:255 if x>30 else 0).getbbox()
canvas=Image.new('RGBA',(1024,1024)); box=tuple(v*4 for v in b)
canvas.alpha_composite(im.crop(s).resize((box[2]-box[0],box[3]-box[1]),Image.Resampling.LANCZOS),box[:2])
canvas.save(A/'painting-aligned.png')
# Existing original generated texture fills, with provenance in central SOURCES.md.
for kind,src in {'skin':'medjay/fill-skin.png','wood':'medjay/fill-wood.png','linen':'horseman/fill-linen.png','hair':'horseman/fill-hair.png'}.items():
    p=ROOT/'assets'/src
    if p.exists(): shutil.copyfile(p,A/f'fill-{kind}.png')
lock={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(A.glob('*.png'))}
(A/'inputs.json').write_text(json.dumps({'sha256':lock,'source_bounds':s,'token_bounds':b},indent=2)+'\n')
print('Registered source',s,'to',b)
