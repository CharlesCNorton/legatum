"""Register the licensed full master into the token field; preserve source pixels."""
import hashlib, json, os
from pathlib import Path
from PIL import Image
ROOT=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'))
A=ROOT/'assets/fighter'; M=ROOT/'masters/fighter'
A.mkdir(parents=True,exist_ok=True);M.mkdir(parents=True,exist_ok=True)
src=A/'painting-source.png'
im=Image.open(src).convert('RGBA'); fig=im.crop(im.getchannel('A').getbbox())
k=928/max(fig.size); fig=fig.resize(tuple(round(v*k) for v in fig.size),Image.Resampling.LANCZOS)
out=Image.new('RGBA',(1024,1024));out.alpha_composite(fig,((1024-fig.width)//2,(1024-fig.height)//2));out.save(A/'projection.png')
record={'url':'https://pub-fb5c281dd12d4ea4bbd38d657cdeb907.r2.dev/app/src/assets/units/fighter-source.png','license':'CC BY 4.0','registration':'alpha bbox, 232/256 field, centered, no warp','files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [src,A/'projection.png',A/'painted-fill.png']}}
Path('tools/art/anim3d/units/fighter/assets.lock.json').write_text(json.dumps(record,indent=2)+'\n')
