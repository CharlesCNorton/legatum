"""Arrange the actual feet-camera renders with their source sample numbers."""
import json,os
from pathlib import Path
from PIL import Image,ImageDraw
R=Path(os.environ['ANIM_ROOT']);M=Path(os.environ['ANIM_MASTER']);e=json.loads((M/'feet/evidence.json').read_text())
out=Image.new('RGB',(2048,560),(222,210,187));draw=ImageDraw.Draw(out)
for row,view in enumerate(['top','front']):
 for i,record in enumerate(e['records']):
  im=Image.open(M/f'feet/{view}-{i:02}.png').convert('RGBA');out.paste(im,(i*256,row*280+24),im)
  label=f'{view}'+(' ankle cut' if view=='top' else '')+f' frame {record["frame"]}'
  if view=='top':label+=' yaw '+','.join(f'{record["feet"][s]["yaw_deg"]:.0f}' for s in ['l','r'])
  draw.text((i*256+5,row*280+5),label,fill=(35,29,20))
out.save(R/'review/3d-v2/spartan-hoplite-g-feet-check.png')
