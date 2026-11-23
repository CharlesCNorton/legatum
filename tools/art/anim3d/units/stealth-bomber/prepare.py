"""Register the archived painting; retain transparent margins and pin inputs."""
from pathlib import Path
from PIL import Image, ImageOps
import os,json,hashlib
R=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'))
A=R/'assets/stealth-bomber';M=R/'masters/stealth-bomber';M.mkdir(parents=True,exist_ok=True)
im=Image.open(A/'stealth-bomber-source.png').convert('RGBA');box=im.getchannel('A').getbbox()
fig=im.crop(box);k=928/max(fig.size);size=tuple(round(v*k) for v in fig.size);offset=((1024-size[0])//2,(1024-size[1])//2)
out=Image.new('RGBA',(1024,1024));out.alpha_composite(fig.resize(size,Image.Resampling.LANCZOS),offset);out.save(A/'projection.png')
Image.new('L',(1024,1024),255).save(A/'projection-mask.png')
# Reuse licensed generated brushwork, neutralised to the painting's composite grey.
fill=Image.open(R/'assets/bomber/painted-fill.png').convert('RGB')
ImageOps.colorize(ImageOps.grayscale(fill),(36,35,34),(111,109,106)).save(A/'painted-fill.png')
record={'box':box,'scale':k,'offset':offset,'sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in A.glob('*.png')}}
(M/'registration.json').write_text(json.dumps(record,indent=2))
Path(__file__).with_name('inputs.json').write_text(json.dumps(record,indent=2)+'\n')
