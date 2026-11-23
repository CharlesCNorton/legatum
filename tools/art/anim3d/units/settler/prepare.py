"""Source registration and per-material painting extension; no synthetic geometry."""
from pathlib import Path
import os,json,hashlib
from PIL import Image
R=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')));A=R/'assets/settler'
im=Image.open(A/'painting-source.png').convert('RGBA');box=im.getchannel('A').getbbox();fig=im.crop(box);k=928/fig.height;fig=fig.resize((round(fig.width*k),928),Image.Resampling.LANCZOS);canvas=Image.new('RGBA',(1024,1024));canvas.alpha_composite(fig,((1024-fig.width)//2,48));canvas.save(A/'projection.png')
fill=Image.open(A/'painted-fills.png').convert('RGB');w,h=fill.size
for name,rect in {'ivory':(0,0,w//2,h//2),'olive':(w//2,0,w,h//2),'rust':(0,h//2,w//2,h),'leather':(w//2,h//2,w,h)}.items():fill.crop(rect).save(A/f'fill-{name}.png')
(A/'source-manifest.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in A.glob('*.png')},indent=2))
