"""Native-size comparisons, fixed histogram grade and transparent clip previews."""
import os,sys,json,hashlib
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops
R=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')));M=R/'masters/archer';review=R/'review/3d-v2';stage=sys.argv[1];folder=M/'renders'/stage
painting=Image.open('app/src/assets/units/archer-256.png').convert('RGBA')
def quantiles(im,c):
 h=im.getchannel(c).histogram(mask=im.getchannel('A').point(lambda a:255 if a>128 else 0));total=sum(h);vals=[]
 for k in range(17):
  threshold=total*(.02+.96*k/16);acc=0
  for j,n in enumerate(h):
   acc+=n
   if acc>=threshold:vals.append(j);break
 return vals
def fit_grade(im):
 luts=[];stats={}
 for c in 'RGB':
  a=quantiles(im,c);b=quantiles(painting,c);lut=[]
  for x in range(256):
   if x<=a[0]:target=x+b[0]-a[0]
   elif x>=a[-1]:target=x+b[-1]-a[-1]
   else:
    k=next(k for k in range(16) if a[k]<=x<=a[k+1]);t=(x-a[k])/max(1,a[k+1]-a[k]);target=b[k]+t*(b[k+1]-b[k])
   lut.append(round(max(0,min(255,.65*x+.35*target))))
  luts.append(lut);stats[c]={'render':a,'painting':b}
 return {'method':'Fixed rest-calibrated 17-quantile RGB LUT, 35 percent transfer','luts':luts,'quantiles':stats}
raw=folder/'raw';raw.mkdir(exist_ok=True)
existing_meta=json.loads((folder/'render.json').read_text())
already_graded=bool(existing_meta.get('grade_sha256'))
def input_path(p):return raw/p.name if already_graded else p
paths=sorted(folder.glob('*.png'))
if stage=='c':(M/'grade.json').write_text(json.dumps(fit_grade(Image.open(input_path(paths[0])).convert('RGBA')),indent=2))
luts=json.loads((M/'grade.json').read_text())['luts'] if stage!='b' and (M/'grade.json').exists() else None
frames=[]
for p in paths:
 im=Image.open(input_path(p)).convert('RGBA');im.save(raw/p.name)
 if luts:im=Image.merge('RGBA',[im.getchannel(c).point(lut) for c,lut in zip('RGB',luts)]+[im.getchannel('A')])
 im.save(p)
 for size in [256,512]:
  # 512 masters only exist when actually rendered at 512 or above: never upscale.
  if im.width>=size:
   dest=M/f'frames-{size}'/stage;dest.mkdir(parents=True,exist_ok=True);im.resize((size,size),Image.Resampling.LANCZOS).save(dest/p.name)
 frames.append(im.resize((256,256),Image.Resampling.LANCZOS))
meta=json.loads((folder/'render.json').read_text());meta['grade_sha256']=hashlib.sha256((M/'grade.json').read_bytes()).hexdigest() if luts else None;(folder/'render.json').write_text(json.dumps(meta,indent=2))
def panel(images,labels,name):
 w=len(images)*256;sheet=Image.new('RGB',(w,370),'#eee4d2');d=ImageDraw.Draw(sheet)
 for i,(im,label) in enumerate(zip(images,labels)):
  d.text((i*256+8,8),label,fill='#3c3023');sheet.paste(im,(i*256,30),im);small=im.resize((64,64),Image.Resampling.LANCZOS);sheet.paste(small,(i*256+96,295),small)
 sheet.save(review/name)
if stage.startswith('e-'):
 clip=stage[2:];panel(frames,[f'{clip} {i+1}' for i in range(len(frames))],f'archer-{stage}-strip.png')
 fps={'idle':10,'move':12,'attack':14,'hit':12,'death':10}[clip];frames[0].save(review/f'archer-{stage}.webp',save_all=True,append_images=frames[1:],duration=round(1000/fps),loop=0,lossless=True)
elif stage=='g-feet-check':
 sheet=Image.new('RGB',(8*256,2*286),'#eee4d2');d=ImageDraw.Draw(sheet)
 for i,im in enumerate(frames):
  x=(i%8)*256;y=(i//8)*286
  d.text((x+8,y+8),f'{"front" if i<8 else "top"} move {i%8+1}',fill='#3c3023');sheet.paste(im,(x,y+30),im)
 sheet.save(review/'archer-g-feet-check.png')
elif stage=='b':panel([painting]+frames,['painting','front - plain','three-quarter','side'],'archer-b-plain.png')
elif stage=='d':panel(frames,['draw','full draw','release','guard'],'archer-d-rig-poses.png')
elif stage=='c-details':
 source=Image.open(R/'assets/archer/painting-aligned.png').convert('RGBA');render=Image.open(paths[0]).convert('RGBA');images=[];labels=[]
 for name,box in [('head',(75,25,125,85)),('chest',(60,70,155,145)),('legs/base',(50,145,175,250))]:
  for label,im in [('painting',source),('3D',render)]:
   crop=im.crop(tuple(round(v*im.width/256) for v in box));scale=min(256/crop.width,256/crop.height);crop=crop.resize((round(crop.width*scale),round(crop.height*scale)),Image.Resampling.LANCZOS);tile=Image.new('RGBA',(256,256));tile.paste(crop,((256-crop.width)//2,(256-crop.height)//2));images.append(tile);labels.append(f'{name} {label} ({im.width}px source)')
 panel(images,labels,'archer-c-details.png')
else:
 panel([painting]+frames,['painting','3D CPU' if meta['device']=='CPU' else '3D GPU'],'archer-c-textured-lit.png')
 split=painting.copy();split.paste(frames[0].crop((128,0,256,256)),(128,0));fade=Image.blend(painting,frames[0],.5)
 panel([painting,frames[0],split,fade],['painting','3D rest','half split','50 percent crossfade'],'archer-f-restpose-compare.png')
 a=painting.getchannel('A').point(lambda x:255 if x>128 else 0)
 b=frames[0].getchannel('A').point(lambda x:255 if x>128 else 0)
 intersection=sum(ImageChops.multiply(a,b).histogram()[1:]);union=sum(ImageChops.lighter(a,b).histogram()[1:])
 (review/'archer-comparison.json').write_text(json.dumps({'alpha_silhouette_iou':intersection/union,'render':meta,'limitation':'Silhouette overlap is a diagnostic, not art approval.'},indent=2))
with (review/'archer-log.md').open('a') as f:f.write(f'- Published {stage} native 256/64 comparison; render device {meta["device"]}.\n')
