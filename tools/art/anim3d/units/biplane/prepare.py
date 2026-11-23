"""Register the archived painting using the same alpha bounds as the unit token."""
from pathlib import Path
import json, hashlib, os
from PIL import Image
R=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot')); A=R/'assets/biplane'; M=R/'masters/biplane'
M.mkdir(parents=True,exist_ok=True)
im=Image.open(A/'painting-source.png').convert('RGBA'); bbox=im.getchannel('A').getbbox(); fig=im.crop(bbox)
k=min(928/fig.width,928/fig.height);fig=fig.resize((round(fig.width*k),round(fig.height*k)),Image.Resampling.LANCZOS)
out=Image.new('RGBA',(1024,1024));out.alpha_composite(fig,((1024-fig.width)//2,(1024-fig.height)//2));out.save(A/'projection.png')
im=Image.open(A/'painted-fills.png'); w,h=im.size
for name,box in zip(('linen','olive','wood','rubber'),((0,0,w//2,h//2),(w//2,0,w,h//2),(0,h//2,w//2,h),(w//2,h//2,w,h))):
    im.crop(box).save(A/f'{name}.png')
(M/'inputs.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in A.glob('*.png')},indent=2))
