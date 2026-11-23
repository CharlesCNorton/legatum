import os,json
from pathlib import Path
from PIL import Image,ImageDraw
r=Path(os.environ['ANIM_ROOT']);m=r/'masters/pikeman/feet';audit=json.loads((m/'audit.json').read_text());out=Image.new('RGBA',(1024,316),(233,207,160,255));draw=ImageDraw.Draw(out)
for row,view in enumerate(['top','front']):
 draw.text((8,row*154+5),f'{view} / travel -Y / {audit["device"]} preview' if audit['device']=='CPU' else f'{view} / travel -Y / GPU',fill='#352619')
 for i in range(8):out.alpha_composite(Image.open(m/f'{view}-{i:02}.png').convert('RGBA'),(i*128,row*154+22))
out.save(r/'review/3d-v2/pikeman-g-feet-check.png')
print('FEET_REVIEW_OK',min(f['feet'][s]['forward_dot'] for f in audit['frames'] for s in ['l','r'] if f['feet'][s]['planted']))
