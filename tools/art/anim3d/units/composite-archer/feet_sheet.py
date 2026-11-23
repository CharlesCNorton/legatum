import json,os
from pathlib import Path
from PIL import Image,ImageDraw
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/composite-archer';report=json.loads((M/'feet.json').read_text())
out=Image.new('RGB',(8*160,2*188),(240,231,209));d=ImageDraw.Draw(out)
for f in report['files']:
 x=(f['frame']-1)*160;y=0 if f['view']=='front' else 188
 im=Image.open(M/f['path']).convert('RGBA');im.thumbnail((160,160));out.paste(im,(x,y+25),im)
 d.text((x+3,y+5),f"{f['view']} {f['frame']}",fill=(50,40,30))
out.save(R/'review/3d-v2/composite-archer-g-feet-check.png')
