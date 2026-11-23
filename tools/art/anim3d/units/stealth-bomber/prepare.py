"""Register the archived painting; retain transparent margins and pin inputs."""
from pathlib import Path
from PIL import Image, ImageOps, ImageFilter
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
# Register the generated clean disc to the painting's original disc footprint.
# Only colour is transferred; the Blender disc supplies the actual silhouette.
clean=Image.open(A/'stone-fill-source.png').convert('RGBA')
cb=clean.getchannel('A').point(lambda a:255 if a>128 else 0).getbbox()
clean=clean.crop(cb).resize((326,114),Image.Resampling.LANCZOS)
stone=Image.new('RGBA',(1024,1024));stone.alpha_composite(clean,(371,752))
# Preserve the painted lower rim; blend gradually below the former support.
mask=Image.new('L',(1024,1024));mask.paste(255,(350,838,715,880));mask=mask.filter(ImageFilter.GaussianBlur(3))
stone=Image.composite(out,stone,mask)
stone.save(A/'stone-projection.png')
record={'box':box,'scale':k,'offset':offset,'sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in A.glob('*.png')}}
(M/'registration.json').write_text(json.dumps(record,indent=2))
Path(__file__).with_name('inputs.json').write_text(json.dumps(record,indent=2)+'\n')
