"""Register the archived painting to the shipped token; never use it as geometry."""
import hashlib,json,os,shutil
from pathlib import Path
from PIL import Image,ImageChops,ImageFilter
R=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')));A=R/'assets/pikeman';M=R/'masters/pikeman'
src=Image.open(A/'painting-source.png').convert('RGBA')
pixels=[]
for r,g,b,a in src.getdata():
    pixels.append((r,g,b,0 if r>100 and b>90 and g<r*.6 and g<b*.65 else a))
src.putdata(pixels)
ref=Image.open('app/src/assets/units/pikeman-256.png').convert('RGBA');rb=ref.getbbox();sb=src.getbbox()
# Body-only silhouette for bounded full-depth contour fitting. Opening removes
# the one-pixel shaft; the image is never used for opacity or replacement geometry.
mask=ref.getchannel('A').point(lambda x:255 if x>160 else 0).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(3))
mask.save(A/'body-fit-mask.png')
canvas=Image.new('RGBA',(1024,1024));crop=src.crop(sb).resize(((rb[2]-rb[0])*4,(rb[3]-rb[1])*4),Image.Resampling.LANCZOS);canvas.alpha_composite(crop,(rb[0]*4,rb[1]*4));canvas.save(A/'painting-aligned.png')
for material in ['linen','bronze']:
 shutil.copyfile(R/f'assets/horseman/fill-{material}.png',A/f'fill-{material}.png')
for material in ['steel','leather']:
 shutil.copyfile(R/f'assets/tagmatic-soldier/fill-{material}.png',A/f'fill-{material}.png')
shutil.copyfile(R/'assets/medjay/fill-skin.png',A/'fill-skin.png')
# Generated clean disc has no baked feet/shadows. Register its opaque bounds to
# the painting's actual disc, independent of the generator's canvas resolution.
stone=Image.open(A/'stone-fill-source.png').convert('RGBA')
box=stone.getchannel('A').point(lambda x:255 if x>180 else 0).getbbox()
plate=Image.new('RGBA',(1024,1024));plate.alpha_composite(stone.crop(box).resize((488,120),Image.Resampling.LANCZOS),(204,834));plate.save(A/'stone-fill-aligned.png')
inputs={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in A.glob('*.png')}
(M/'inputs.json').write_text(json.dumps({'sha256':inputs,'source_bbox':sb,'token_bbox':rb},indent=2))
print('Painting registered',src.size,sb,rb)
