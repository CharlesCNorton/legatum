"""Register the archived alpha painting to the shipped token field."""
from pathlib import Path
from PIL import Image
import os,json,hashlib
R=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'))
A=R/'assets/jet-bomber'; M=R/'masters/jet-bomber'; M.mkdir(parents=True,exist_ok=True)
im=Image.open(A/'jet-bomber-source.png').convert('RGBA'); box=im.getchannel('A').getbbox()
fig=im.crop(box); k=928/max(fig.size); size=tuple(round(v*k) for v in fig.size); offset=((1024-size[0])//2,(1024-size[1])//2)
out=Image.new('RGBA',(1024,1024));out.alpha_composite(fig.resize(size,Image.Resampling.LANCZOS),offset);out.save(A/'projection.png')
(M/'registration.json').write_text(json.dumps({'box':box,'scale':k,'offset':offset,'sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in A.glob('*.png')}},indent=2))
