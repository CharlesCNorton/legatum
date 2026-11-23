"""External texture preparation, preserving the committed token's framing."""
from pathlib import Path
from PIL import Image
import os,json,hashlib
R=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'));A=R/'assets/peltast';A.mkdir(parents=True,exist_ok=True)
source=Image.open(A/'painting-source.png').convert('RGBA')
# Source is already keyed, but retains a thin magenta fringe: exclude it from projection.
pixels=list(source.get_flattened_data());source.putdata([(r,g,b,0 if r>g*1.55 and b>g*1.55 and r>80 and b>70 else a) for r,g,b,a in pixels])
ref=Image.open('app/src/assets/units/peltast-256.png').convert('RGBA');box=ref.getchannel('A').getbbox()
patch=source.crop(source.getchannel('A').getbbox()).resize(((box[2]-box[0])*4,(box[3]-box[1])*4),Image.Resampling.LANCZOS)
out=Image.new('RGBA',(1024,1024));out.paste(patch,(box[0]*4,box[1]*4));out.save(A/'painting-aligned.png')
fills=Image.open(A/'painted-fills.png').convert('RGB');w,h=fills.size
for name,rect in [('red',(0,0,w//2,h//2)),('blue',(w//2,0,w,h//2)),('wicker',(0,h//2,w//2,h)),('leather',(w//2,h//2,w,h))]:fills.crop(rect).save(A/f'fill-{name}.png')
lock={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(A.glob('*.png'))}
Path(__file__).with_name('assets.lock.json').write_text(json.dumps(lock,indent=2)+'\n')
print('PREPARED',box,source.size)
