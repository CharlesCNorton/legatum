"""Normalize source to the shipped token's exact framing and split generated fills."""
from pathlib import Path
from PIL import Image
import os,hashlib,json
root=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'))
a=root/'assets/barbarian-archer'
pinned=json.loads(Path(__file__).with_name('inputs.json').read_text())
for name in ('painting-source.png','painted-fills.png','stone-fill-source.png'):
    assert hashlib.sha256((a/name).read_bytes()).hexdigest()==pinned[name],('source changed',name)
src=Image.open(a/'painting-source.png').convert('RGBA')
ref=Image.open('app/src/assets/units/barbarian-archer-256.png').convert('RGBA')
bbox=ref.getchannel('A').point(lambda x:255 if x>32 else 0).getbbox()
sbox=src.getchannel('A').point(lambda x:255 if x>32 else 0).getbbox()
out=Image.new('RGBA',(1024,1024));box=tuple(v*4 for v in bbox)
out.paste(src.crop(sbox).resize((box[2]-box[0],box[3]-box[1]),Image.Resampling.LANCZOS),(box[0],box[1]));out.save(a/'painting-registered.png')
f=Image.open(a/'painted-fills.png').convert('RGB');w,h=f.size
for name,b in [('fur',(0,0,w//2,h//2)),('linen',(w//2,0,w,h//2)),('leather',(0,h//2,w//2,h)),('hair',(w//2,h//2,w,h))]:f.crop(b).save(a/f'fill-{name}.png')
print('Registered source',sbox,'to token',bbox)
# Register the generated clean disc; retain the original unoccluded front rim.
# Texture alpha never cuts the mesh. Extend colors beyond its footprint so the
# bevel cannot sample transparent black at the silhouette.
generated=Image.open(a/'stone-fill-source.png').convert('RGBA')
gbox=generated.getchannel('A').point(lambda x:255 if x>220 else 0).getbbox()
stone=generated.crop(gbox).resize((488,144),Image.Resampling.LANCZOS).convert('RGB')
original=out.crop((236,832,724,976)).convert('RGB')
from PIL import ImageDraw,ImageFilter
mask=Image.new('L',stone.size)
draw=ImageDraw.Draw(mask);draw.rectangle((0,98,488,144),fill=255)
mask=mask.filter(ImageFilter.GaussianBlur(2))
Image.composite(original,stone,mask).save(a/'stone-pigment.png')
(a/'inputs.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in a.glob('*.png')},indent=2))
