"""Native-size reviews and painting comparison; one temporal-stable colour grade."""
from pathlib import Path
from PIL import Image,ImageDraw
import os,sys,json,hashlib
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/cuirassier';V=R/'review/3d-v2';stage=sys.argv[1];folder=M/'renders'/stage
painting=Image.open('app/src/assets/units/cuirassier-256.png').convert('RGBA');cream=(233,207,160,255)
def quantile(im,c):
 h=im.getchannel(c).histogram(mask=im.getchannel('A').point(lambda x:255 if x>128 else 0));total=sum(h);result=[]
 for i in range(17):
  acc=0
  for x,n in enumerate(h):
   acc+=n
   if acc>=total*(.02+.96*i/16):result.append(x);break
 return result
if stage=='c':
 raw=Image.open(folder/'raw/00.png').convert('RGBA');luts=[]
 for c in 'RGB':
  a,b=quantile(raw,c),quantile(painting,c);lut=[]
  for x in range(256):
   if x<=a[0]:target=x+b[0]-a[0]
   elif x>=a[-1]:target=x+b[-1]-a[-1]
   else:
    k=next(i for i in range(16) if a[i]<=x<=a[i+1]);target=b[k]+(b[k+1]-b[k])*(x-a[k])/max(1,a[k+1]-a[k])
   lut.append(round(max(0,min(255,.65*x+.35*target))))
  luts.append(lut)
 (M/'grade.json').write_text(json.dumps({'luts':luts,'method':'35% rest foreground quantile transfer, fixed for all frames','master_sha256':hashlib.sha256((M/'cuirassier.blend').read_bytes()).hexdigest(),'raw_sha256':hashlib.sha256((folder/'raw/00.png').read_bytes()).hexdigest()}))
files=sorted((folder/'raw').glob('*.png'));images=[]
for p in files:
 im=Image.open(p).convert('RGBA')
 if stage!='b':
  lut=json.loads((M/'grade.json').read_text())['luts'];im=Image.merge('RGBA',[im.getchannel(c).point(l) for c,l in zip('RGB',lut)]+[im.getchannel('A')]);im.save(folder/p.name)
 if stage=='b':im.save(folder/p.name)
 for size in [512,256]:
  if im.width>=size:
   dest=M/str(size)/stage;dest.mkdir(parents=True,exist_ok=True);im.resize((size,size),Image.Resampling.LANCZOS).save(dest/p.name)
 images.append(im.resize((256,256),Image.Resampling.LANCZOS))
manifest=json.loads((folder/'render.json').read_text())
if stage!='b':manifest['grade_sha256']=hashlib.sha256((M/'grade.json').read_bytes()).hexdigest()
(folder/'render.json').write_text(json.dumps(manifest,indent=2))
def sheet(imgs,labels,path):
 out=Image.new('RGBA',(256*len(imgs),350),cream);d=ImageDraw.Draw(out)
 for i,(im,label) in enumerate(zip(imgs,labels)):
  d.text((i*256+8,5),label,fill='#30281e');out.alpha_composite(im,(i*256,24));out.alpha_composite(im.resize((64,64),Image.Resampling.LANCZOS),(i*256+96,282))
 out.convert('RGB').save(path)
name={'b':'b-plain','c':'c-textured-lit','c-details':'c-details','d':'d-rig-poses'}.get(stage,stage+'-strip')
sheet([painting]+images,['painting']+[f'{stage} {i} / {manifest["device"]}' for i in range(len(images))],V/f'cuirassier-{name}.png')
if stage=='c-details':
 # Match anatomical regions rather than presenting a second full-frame rest image.
 full=Image.open(folder/'00.png').convert('RGBA');reference=Image.open(R/'assets/cuirassier/painting-aligned.png').convert('RGBA')
 out=Image.new('RGBA',(768,550),cream);d=ImageDraw.Draw(out)
 for j,(label,box) in enumerate([('helmet and breastplate',(132,8,183,100)),('horse and tack',(139,65,235,181)),('pistol and arm',(27,20,154,83))]):
  d.text((j*256+8,5),label+f' / painting above, {manifest["device"]}{manifest["resolution"]} below',fill='#30281e')
  for row,im in enumerate([reference,full]):
   scale=im.width/256;region=im.crop(tuple(round(v*scale) for v in box));factor=min(248/region.width,248/region.height);region=region.resize((round(region.width*factor),round(region.height*factor)),Image.Resampling.LANCZOS);out.alpha_composite(region,(j*256+(256-region.width)//2,24+row*260))
 out.convert('RGB').save(V/'cuirassier-c-details.png')
if stage=='c':
 render=images[0];split=painting.copy();split.paste(render.crop((128,0,256,256)),(128,0));cross=Image.blend(painting,render,.5)
 sheet([painting,render,split,cross],['painting','3D rest','half split','50% crossfade'],V/'cuirassier-f-restpose-compare.png')
if stage.startswith('e-'):
 fps={'idle':10,'move':12,'attack':14,'hit':12,'death':10}[stage[2:]];images[0].save(V/f'cuirassier-{stage}.webp',save_all=True,append_images=images[1:],duration=round(1000/fps),loop=0,quality=85,method=6)
with (V/'cuirassier-log.md').open('a') as f:f.write(f'- Emitted {stage}: {len(images)} frames, {manifest["resolution"]} px {manifest["engine"]}/{manifest["device"]}, {manifest["samples"]} samples.\n')
