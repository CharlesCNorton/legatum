"""Prepare and pin original painting and existing generated hidden-surface fill."""
from pathlib import Path
import hashlib,json,os,shutil
from PIL import Image
R=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')))
A=R/'assets/landship';M=R/'masters/landship';M.mkdir(parents=True,exist_ok=True)
(M/'textures').mkdir(exist_ok=True)
source=A/'landship-source.png'
im=Image.open(source).convert('RGBA');im=im.crop(im.getchannel('A').getbbox());k=928/max(im.size)
im=im.resize((round(im.width*k),round(im.height*k)),Image.Resampling.LANCZOS)
out=Image.new('RGBA',(1024,1024));out.alpha_composite(im,((1024-im.width)//2,(1024-im.height)//2));out.save(M/'textures/painting.png')
shutil.copyfile(R/'assets/artillery/painted-olive.png',A/'painted-olive.png')
lock={'files':[{'path':str(p.relative_to(R)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in (source,A/'painted-olive.png',M/'textures/painting.png')]}
Path('tools/art/anim3d/units/landship/assets.lock.json').write_text(json.dumps(lock,indent=2)+'\n')
