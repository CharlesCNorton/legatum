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
poly=[(82,133),(92,124),(141,118),(154,92),(169,83),(184,87),(194,122),(176,133),(170,180),(178,216),(166,219),(154,190),(145,173),(126,181),(128,211),(117,215),(110,179),(99,183),(101,214),(91,214),(89,181)]
d.polygon([(x*4,y*4) for x,y in poly],fill=255)
for poly in [[(91,127),(141,117),(139,149),(92,149)],[(116,114),(135,116),(130,147),(126,176),(115,174)]]:d.polygon([(x*4,y*4) for x,y in poly],fill=0)
for kind in ['coat','linen','skin']:
 im=out.copy();pixels=list(im.get_flattened_data());mask=[]
 for i,(rr,gg,bb,aa) in enumerate(pixels):
  if kind=='coat':valid=coatmask.getpixel((i%1024,i//1024))/255
  elif kind=='linen':valid=float((rr>95 and gg>80 and rr<gg*1.29 and gg<max(bb,1)*1.65) or (bb>rr and gg>rr*.9))
  else:valid=float(rr>gg*1.24 and gg>max(bb,1)*1.26 and rr>70)
  mask.append(round(aa*valid))
 alpha=Image.new('L',im.size);alpha.putdata(mask);alpha=alpha.filter(ImageFilter.GaussianBlur(1.5));im.putalpha(alpha);im.save(r/f'projection-{kind}.png')
print('PREPARED separate coat, linen and skin projection masks')
