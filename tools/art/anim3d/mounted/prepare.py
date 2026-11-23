"""Prepare original painting and generated fill quadrants in the external root."""
from pathlib import Path
import os,json,hashlib
from PIL import Image
r=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')))/'assets/horseman'
lock=json.loads(Path(__file__).with_name('assets.lock.json').read_text())
for file,sha in lock.get('paint_assets_sha256',{}).items():
 assert (r/file).exists(),f'Missing external art master {r/file}; see Mounted PLAYBOOK chapter'
 assert hashlib.sha256((r/file).read_bytes()).hexdigest()==sha,f'Changed source {file}'
im=Image.open(r/'painted-fills.png');w,h=im.size
for name,box in [('coat',(0,0,w//2,h//2)),('linen',(w//2,0,w,h//2)),('bronze',(0,h//2,w//2,h)),('hair',(w//2,h//2,w,h))]:im.crop(box).save(r/f'fill-{name}.png')
src=Image.open(r/'painting-source.png').convert('RGBA');ref=Image.open('app/src/assets/units/horseman-256.png').convert('RGBA');box=ref.getchannel('A').getbbox();patch=src.crop(src.getchannel('A').getbbox());patch=patch.resize(((box[2]-box[0])*4,(box[3]-box[1])*4),Image.Resampling.LANCZOS);out=Image.new('RGBA',(1024,1024));out.paste(patch,(box[0]*4,box[1]*4));out.save(r/'painting-aligned-1024.png')
print('PREPARED painting projection and four generated surface fills')
# Separate projection masks prevent cloth or skin from being painted onto the horse.
from PIL import ImageDraw,ImageFilter
coatmask=Image.new('L',(1024,1024));d=ImageDraw.Draw(coatmask)
# Broad ownership plus the source alpha preserves every pale sock and raised
# foreleg. The earlier narrow polygon cut out the raised foreleg's white hair.
poly=[(60,127),(84,120),(114,118),(138,120),(147,90),(166,78),
      (190,78),(199,122),(175,150),(187,224),(80,225),(55,195)]
d.polygon([(x*4,y*4) for x,y in poly],fill=255)
for poly in [[(91,127),(141,117),(139,149),(92,149)],[(116,114),(135,116),(130,147),(126,176),(115,174)],
             [(166,159),(185,166),(188,176),(171,177)]]:d.polygon([(x*4,y*4) for x,y in poly],fill=0)
skinmask=Image.new('L',(1024,1024));d=ImageDraw.Draw(skinmask)
# Spatial skin ownership retains warm highlights and dark creases equally.
# Hue thresholds incorrectly discarded the painting's palest skin pixels.
for poly in [[(116,45),(129,44),(138,57),(132,69),(120,63)],
             [(87,66),(99,64),(110,68),(114,81),(105,94),(99,88),(94,87),(89,79)],
             [(138,69),(146,75),(147,93),(141,108),(133,107),(138,92)],
             [(119,115),(133,118),(132,134),(127,151),(128,174),(119,176),(112,168),(115,146),(111,131)],
             [(164,159),(180,162),(187,173),(178,177),(168,170)]]:
 d.polygon([(x*4,y*4) for x,y in poly],fill=255)
linenmask=Image.new('L',(1024,1024));d=ImageDraw.Draw(linenmask)
for poly in [[(110,62),(122,65),(139,71),(140,96),(136,116),(128,119),(119,113),(109,128),(102,123),(107,97)],
             [(90,132),(111,129),(112,147),(90,147)]]:
 d.polygon([(x*4,y*4) for x,y in poly],fill=255)
for kind in ['coat','linen','skin']:
 im=out.copy();pixels=list(im.get_flattened_data());mask=[]
 for i,(rr,gg,bb,aa) in enumerate(pixels):
  if kind=='coat':valid=coatmask.getpixel((i%1024,i//1024))/255
  elif kind=='linen':valid=linenmask.getpixel((i%1024,i//1024))/255
  else:valid=skinmask.getpixel((i%1024,i//1024))/255
  mask.append(round(aa*valid))
 alpha=Image.new('L',im.size);alpha.putdata(mask);alpha=alpha.filter(ImageFilter.GaussianBlur(1.5));im.putalpha(alpha);im.save(r/f'projection-{kind}.png')
print('PREPARED separate coat, linen and skin projection masks')
