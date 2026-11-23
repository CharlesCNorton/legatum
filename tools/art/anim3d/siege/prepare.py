"""Material-selective projection masks from the project's licensed source painting."""
from pathlib import Path
import os,json,hashlib
from PIL import Image
R=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')));A=R/'assets/field-cannon';im=Image.open(A/'painting-source.png').convert('RGBA')
def clamp(x):return max(0,min(1,x))
for material in ['navy','ivory','leather']:
 result=im.copy();pixels=[]
 for r,g,b,a in im.getdata():
  if material=='navy':weight=clamp((b-r-3)/16)*clamp((b-g+7)/12)*clamp((165-r)/35)
  elif material=='leather':weight=clamp((135-max(r,g,b))/40)
  else:weight=clamp((min(r,g,b)-110)/45)*clamp((.22-(max(r,g,b)-min(r,g,b))/max(1,r,g,b))/.08)
  pixels.append((r,g,b,round(a*weight)))
 result.putdata(pixels);result.save(A/f'projection-{material}.png')
# The source hand and boot must not become permanent paint on articulated gun/base surfaces.
# Coordinates are measured on the shipped 256px token, using the same source registration.
for kind in ['machine','base','coat']:
 result=im.copy();px=result.load()
 for y in range(im.height):
  ty=12+(y-7)*(244-12)/(1247-7)
  for x in range(im.width):
   tx=26+(x-81)*(230-26)/(1172-81)
   red,green,blue,alpha=px[x,y]
   rammer=abs(tx-(54+(ty-58)*29/143))<3.1
   hand=48<tx<64 and 77<ty<94
   ivory=min(red,green,blue)>110 and max(red,green,blue)-min(red,green,blue)<55
   excluded=(kind=='coat' and (rammer or hand or ivory))
   excluded|=kind=='machine' and 123<tx<156 and 100<ty<132
   excluded|=kind=='base' and ty<214
   if excluded:px[x,y]=(red,green,blue,0)
 result.save(A/f'projection-{kind}.png')
(A/'manifest.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in A.glob('*.png')},indent=2))
