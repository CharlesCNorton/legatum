"""Prepare external painting and generated material fills; retain pinned inputs."""
import os, json, hashlib
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
ROOT=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'))
A=ROOT/'assets/legionary'; M=ROOT/'masters/legionary'; M.mkdir(parents=True,exist_ok=True)
lock=json.loads((Path(__file__).parent/'assets.lock.json').read_text())
for name,record in lock.items():
    assert (A/name).exists(),f'Missing external input: {A/name}'
    assert hashlib.sha256((A/name).read_bytes()).hexdigest()==record['sha256'],f'Changed pinned input: {name}'
ref=Image.open('app/src/assets/units/legionary-256.png').convert('RGBA')
src=Image.open(A/'painting-source.png').convert('RGBA')
# Some historical masters use magenta; this source must never project it.
pix=list(src.get_flattened_data()); src.putdata([(r,g,b,0 if r>g*1.5 and b>g*1.5 and r>120 and b>100 else a) for r,g,b,a in pix])
box=ref.getchannel('A').getbbox(); patch=src.crop(src.getchannel('A').getbbox())
out=Image.new('RGBA',(1024,1024)); out.paste(patch.resize(((box[2]-box[0])*4,(box[3]-box[1])*4),Image.Resampling.LANCZOS),(box[0]*4,box[1]*4));out.save(A/'painting-aligned.png')
im=Image.open(A/'painted-fills.png'); w,h=im.size
for kind,box in [('cloth',(0,0,w//2,h//2)),('leather',(w//2,0,w,h//2)),('iron',(0,h//2,w//2,h)),('bronze',(w//2,h//2,w,h))]:im.crop(box).save(A/f'fill-{kind}.png')
# Skin masking stops shield/metal colours spilling onto the anatomical mesh.
mask=Image.new('L',out.size); d=ImageDraw.Draw(mask)
for poly in [[(114,31),(137,31),(143,51),(127,60),(112,48)],[(66,65),(81,65),(93,88),(108,77),(113,87),(95,103),(78,98),(67,82)],[(105,150),(123,150),(121,198),(115,219),(104,220),(108,192)],[(128,150),(147,149),(151,217),(137,221),(132,195)]]:d.polygon([(x*4,y*4) for x,y in poly],fill=255)
mask=mask.filter(ImageFilter.GaussianBlur(3)); skin=out.copy();skin.putalpha(mask);skin.save(A/'projection-skin.png')
(M/'inputs.json').write_text(json.dumps({str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [A/'painting-source.png',A/'painted-fills.png']},indent=2))
print('PREPARED legionary inputs',src.size)
