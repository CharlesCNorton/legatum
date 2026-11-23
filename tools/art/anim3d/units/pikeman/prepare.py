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
canvas=Image.new('RGBA',(1024,1024));crop=src.crop(sb).resize(((rb[2]-rb[0])*4,(rb[3]-rb[1])*4),Image.Resampling.LANCZOS);canvas.alpha_composite(crop,(rb[0]*4,rb[1]*4));canvas.save(A/'painting-aligned.png')
for material in ['linen','bronze']:
 shutil.copyfile(R/f'assets/horseman/fill-{material}.png',A/f'fill-{material}.png')
inputs={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [A/'painting-source.png',A/'painting-aligned.png',A/'fill-linen.png',A/'fill-bronze.png']}
(M/'inputs.json').write_text(json.dumps({'sha256':inputs,'source_bbox':sb,'token_bbox':rb},indent=2))
print('Painting registered',src.size,sb,rb)
