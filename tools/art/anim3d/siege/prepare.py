"""Material-selective projection masks from the project's licensed source painting."""
from pathlib import Path
import os,json,hashlib
from PIL import Image, ImageDraw
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
   # The gunner's pale leg is visible through the near wheel in the source.
   # Newly sampled spoke faces must not carry it away when the wheel turns.
   trouser_gap=(96<tx<128 and 120<ty<188 and min(red,green,blue)>105
                and max(red,green,blue)>145 and max(red,green,blue)-min(red,green,blue)<65)
   excluded|=kind=='machine' and trouser_gap
   excluded|=kind=='base' and ty<214
   if excluded:px[x,y]=(red,green,blue,0)
 result.save(A/f'projection-{kind}.png')
# Ivory trousers have deep warm painted shadows. A brightness-only mask discards
# those folds; use their actual source silhouette and exclude the separate rammer.
mask=Image.new('L',im.size);draw=ImageDraw.Draw(mask)
outline=[(64,109),(105,109),(101,123),(94,144),(90,167),(80,169),(80,145),(65,149),(55,167),(44,163),(53,133)]
def source_point(p):return (81+(p[0]-26)*(1172-81)/(230-26),7+(p[1]-12)*(1247-7)/(244-12))
draw.polygon([source_point(p) for p in outline],fill=255)
draw.line([source_point((54,58)),source_point((83,201))],fill=0,width=25)
draw.line([source_point((63,105)),source_point((55,148))],fill=0,width=40)
trousers=im.copy()
from PIL import ImageChops
# Reject almost-black neighbouring equipment while retaining midtone creases.
pigment=Image.new('L',im.size)
pigment.putdata([round(255*clamp((min(r,g,b)-65)/35)*clamp((75-(max(r,g,b)-min(r,g,b)))/25)) for r,g,b,a in im.getdata()])
trousers.putalpha(ImageChops.multiply(ImageChops.multiply(mask,pigment),im.getchannel('A')))
trousers.save(A/'projection-trousers.png')
(A/'manifest.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in A.glob('*.png')},indent=2))
