"""Material-selective projection masks from the project's licensed source painting."""
from pathlib import Path
import os,json,hashlib
from PIL import Image
R=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')));A=R/'assets/field-cannon';im=Image.open(A/'painting-source.png').convert('RGBA')
def clamp(x):return max(0,min(1,x))
for material in ['navy','ivory']:
 result=im.copy();pixels=[]
 for r,g,b,a in im.getdata():
  if material=='navy':weight=clamp((b-r-3)/16)*clamp((b-g+7)/12)*clamp((165-r)/35)
  else:weight=clamp((min(r,g,b)-65)/40)*clamp((.30-(max(r,g,b)-min(r,g,b))/max(1,r,g,b))/.10)
  pixels.append((r,g,b,round(a*weight)))
 result.putdata(pixels);result.save(A/f'projection-{material}.png')
(A/'manifest.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in A.glob('*.png')},indent=2))
