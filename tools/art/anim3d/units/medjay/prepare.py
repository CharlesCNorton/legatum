"""Prepare CC BY painting and generated back-surface texture tiles outside git."""
import hashlib, json, os
from pathlib import Path
from PIL import Image
ROOT = Path(os.environ.get('ANIM_ROOT', str(Path.home()/'LegatumRuns/anim-pilot')))
A = ROOT/'assets/medjay'; A.mkdir(parents=True, exist_ok=True)
lock=json.loads(Path(__file__).with_name('assets.lock.json').read_text())
for name,expected in lock['sha256'].items():
 assert hashlib.sha256((A/name).read_bytes()).hexdigest()==expected, 'Source asset changed: '+name
src = Image.open(A/'painting-source.png').convert('RGBA')
ref = Image.open('app/src/assets/units/medjay-256.png').convert('RGBA')
b = ref.getchannel('A').getbbox()
patch = src.crop(src.getchannel('A').getbbox()).resize(((b[2]-b[0])*4,(b[3]-b[1])*4),Image.Resampling.LANCZOS)
out = Image.new('RGBA',(1024,1024)); out.paste(patch,(b[0]*4,b[1]*4)); out.save(A/'painting-aligned.png')
im = Image.open(A/'painted-fills.png').convert('RGB'); w,h=im.size
for name,box in [('skin',(0,0,w//2,h//2)),('linen',(w//2,0,w,h//2)),('hide',(0,h//2,w//2,h)),('wood',(w//2,h//2,w,h))]:
 im.crop(box).save(A/f'fill-{name}.png')
print('Prepared painting and four generated fills:', A)

# Restrict skin projection to skin pigment; never project white linen or the base onto ankles.
pixels=list(out.get_flattened_data());alpha=[]
for i,(r,g,b,a) in enumerate(pixels):
 x,y=(i%1024)/4,(i//1024)/4
 region=(y<99 and x<153) or (145<y<219 and 108<x<162)
 valid=region and r>g*1.18 and g>max(1,b)*1.16
 alpha.append(a if valid else 0)
mask=Image.new('L',out.size);mask.putdata(alpha)
skin=out.copy();skin.putalpha(mask);skin.save(A/'projection-skin.png')

(A/'sources-sha256.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in A.glob('*.png')},indent=2))
