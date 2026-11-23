"""Prepare and pin original painting and existing generated hidden-surface fill."""
from pathlib import Path
import hashlib,json,os,shutil
from PIL import Image,ImageDraw,ImageFilter
R=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')))
A=R/'assets/landship';M=R/'masters/landship';M.mkdir(parents=True,exist_ok=True)
(M/'textures').mkdir(exist_ok=True)
source=A/'landship-source.png'
lock_path=Path('tools/art/anim3d/units/landship/assets.lock.json')
for entry in json.loads(lock_path.read_text())['files']:
    if entry['path'].startswith('assets/'):
        assert hashlib.sha256((R/entry['path']).read_bytes()).hexdigest()==entry['sha256'], entry['path']
(M/'build-inputs.json').unlink(missing_ok=True)
im=Image.open(source).convert('RGBA');im=im.crop(im.getchannel('A').getbbox());k=928/max(im.size)
im=im.resize((round(im.width*k),round(im.height*k)),Image.Resampling.LANCZOS)
out=Image.new('RGBA',(1024,1024));out.alpha_composite(im,((1024-im.width)//2,(1024-im.height)//2));out.save(M/'textures/painting.png')
# Generated clean stone is used only on the physical disc; preserve original lower rim.
stone=Image.open(A/'stone-fill-source.png').convert('RGBA').resize((1024,1024),Image.Resampling.LANCZOS)
mask=Image.new('L',(1024,1024));draw=ImageDraw.Draw(mask)
for y in range(1024):draw.line((0,y,1024,y),fill=round(255*max(0,min(1,(y/4-182)/3))))
stone=Image.composite(out,stone,mask);stone.save(M/'textures/stone.png')
patch=Image.open(A/'gun-fill-source.png').convert('RGBA').resize((1024,1024),Image.Resampling.LANCZOS)
mask=Image.new('L',(1024,1024));ImageDraw.Draw(mask).ellipse((98*4,102*4,119*4,117*4),fill=255)
mask=mask.filter(ImageFilter.GaussianBlur(2))
Image.composite(patch,out,mask).save(M/'textures/sponson.png')
shutil.copyfile(R/'assets/artillery/painted-olive.png',A/'painted-olive.png')
lock={'files':[{'path':str(p.relative_to(R)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in (source,A/'painted-olive.png',A/'stone-fill-source.png',A/'gun-fill-source.png',M/'textures/sponson.png',M/'textures/painting.png',M/'textures/stone.png')]}
Path('tools/art/anim3d/units/landship/assets.lock.json').write_text(json.dumps(lock,indent=2)+'\n')
