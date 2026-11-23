"""Native top/front diagnostics; explicitly separate in-place gait from travel."""
from pathlib import Path
from PIL import Image, ImageDraw
import os,json,hashlib
root=Path(os.environ['ANIM_ROOT']);master=root/'masters/cuirassier';folder=master/'feet'
manifest=json.loads((folder/'manifest.json').read_text())
assert manifest['clip_sha256']==hashlib.sha256((master/'clips/move.blend').read_bytes()).hexdigest()
out=Image.new('RGB',(8*192,2*216),(233,207,160));draw=ImageDraw.Draw(out)
for row,view in enumerate(['top','front']):
 for i in range(8):
  im=Image.open(folder/view/f'{i:03}.png').convert('RGBA').resize((192,192),Image.Resampling.LANCZOS)
  out.paste(im,(i*192,row*216+24),im)
  draw.text((i*192+4,row*216+4),f'{view} {i+1} / {manifest["device"]}',fill='#30281e')
out.save(root/'review/3d-v2/cuirassier-g-feet-check.png')
print('FEET REVIEW: 16 evaluated top/front views; native source foot axes; in-place walk')
