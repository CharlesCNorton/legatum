"""Register full-resolution project painting to the shipped miniature field."""
from pathlib import Path
from PIL import Image,ImageOps,ImageEnhance
import os,json,hashlib,shutil
R=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'))
A=R/'assets/stealth-fighter';M=R/'masters/stealth-fighter';M.mkdir(parents=True,exist_ok=True)
im=Image.open(A/'stealth-fighter-source.png').convert('RGBA');box=im.getchannel('A').getbbox()
fig=im.crop(box);k=928/max(fig.size);size=tuple(round(v*k) for v in fig.size);offset=((1024-size[0])//2,(1024-size[1])//2)
out=Image.new('RGBA',(1024,1024));out.alpha_composite(fig.resize(size,Image.Resampling.LANCZOS),offset);out.save(A/'projection.png')
Image.new('L',(1024,1024),255).save(A/'projection-mask.png')
# Reuse licensed original generated painted-metal grain; grey pigment is unit-specific.
fill=Image.open(R/'assets/bomber/painted-fill.png').convert('RGB')
fill=ImageOps.colorize(ImageOps.grayscale(fill),'#333638','#91928d');fill.save(A/'painted-fill.png')
# Reuse the licensed generated clean limestone disc as occlusion fill. Fit its
# texture footprint to this painting, retaining this unit's original lower rim.
# This is pigment for a closed 3D cylinder, never a rendered background/card.
stone=Image.open(A/'stone-fill-source.png').convert('RGBA')
stone=stone.crop(stone.getchannel('A').point(lambda a:255 if a>8 else 0).getbbox()).resize((362,150),Image.Resampling.LANCZOS)
plate=Image.new('RGBA',(1024,1024));plate.alpha_composite(stone,(341,737))
plate.paste(out.crop((341,850,703,887)),(341,850))
plate.save(A/'stone-pigment.png')
record={'box':box,'scale':k,'offset':offset,'sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in A.glob('*.png')}}
(M/'registration.json').write_text(json.dumps(record,indent=2))
Path(__file__).with_name('inputs.json').write_text(json.dumps(record,indent=2)+'\n')
