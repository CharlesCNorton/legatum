"""Register archived painting by alpha bounds; reuse licensed painted bronze fill."""
from pathlib import Path
from PIL import Image
import os,json,hashlib,shutil
R=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'));A=R/'assets/drone-swarm';M=R/'masters/drone-swarm'
A.mkdir(parents=True,exist_ok=True);M.mkdir(parents=True,exist_ok=True)
ref=Image.open('app/src/assets/units/drone-swarm-256.png').convert('RGBA');im=Image.open(A/'painting-source.png').convert('RGBA')
b=im.getchannel('A').getbbox();rb=ref.getchannel('A').getbbox();scale=(rb[3]-rb[1])/(b[3]-b[1]);off=(rb[0]-b[0]*scale,rb[1]-b[1]*scale)
out=Image.new('RGBA',(1024,1024));fig=im.crop(b);out.alpha_composite(fig.resize((round(fig.width*scale*4),round(fig.height*scale*4)),Image.Resampling.LANCZOS),(rb[0]*4,rb[1]*4));out.save(A/'projection.png')
shutil.copyfile(R/'assets/horseman/fill-bronze.png',A/'painted-fill.png')
(M/'registration.json').write_text(json.dumps({'source_box':b,'token_box':rb,'scale':scale,'offset':off,'sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in A.glob('*.png')}},indent=2))
