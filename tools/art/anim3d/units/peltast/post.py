"""Review native sizes, frozen histogram grade, masters and side-by-side evidence."""
import os,sys,json,hashlib
from pathlib import Path
from PIL import Image,ImageDraw,ImageStat
R=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'));M=R/'masters/peltast';V=R/'review/3d-v2';stage=sys.argv[1]
BG=(240,232,214,255);ref=Image.open('app/src/assets/units/peltast-256.png').convert('RGBA');raw=M/'raw'/stage;manifest=json.loads((raw/'render.json').read_text());frames=[Image.open(raw/f'{n}.png').convert('RGBA') for n in manifest['frames']]
def bounds_stats(im):
 im=im.resize((256,256));mask=im.getchannel('A').point(lambda x:255 if x>180 else 0);mask.paste(0,(0,199,256,256));hist=im.convert('RGB').histogram(mask)
 out=[]
 for k in range(3):
  h=hist[k*256:(k+1)*256];total=sum(h);percent=[]
  for q in [.1,.5,.9]:
   acc=0
   for i,n in enumerate(h):
    acc+=n
    if acc>=total*q:percent.append(i);break
  out.append(percent)
 return out
def base_stats(im):
 im=im.resize((256,256));vals=[[],[],[]]
 for y in range(207,240):
  for x in range(32,203):
   r,g,b,a=im.getpixel((x,y))
   if a>220 and r>110 and g>95 and 0<r-g<45 and g-b>12:
    for k,v in enumerate((r,g,b)):vals[k].append(v)
 return [sorted(v)[len(v)//2] for v in vals]
def grade(im):
 if stage=='b':return im
 g=json.loads((M/'grade.json').read_text());bands=list(im.split())
 for i in range(3):bands[i]=bands[i].point(lambda x:max(0,min(255,round((x-g['source'][i][1])*g['gains'][i]+g['source'][i][1]+g['shifts'][i]))))
 out=Image.merge('RGBA',bands)
 # Separate stationary limestone grade prevents cloth calibration greying the base.
 mask=Image.new('L',im.size);px=im.load();mp=mask.load()
 for y in range(round(im.height*202/256),im.height):
  for x in range(im.width):
   r,gg,b,a=px[x,y]
   if a>0 and r>110 and gg>95 and 0<r-gg<45 and gg-b>12:mp[x,y]=255
 base=list(im.split())
 for k in range(3):base[k]=base[k].point(lambda x:max(0,min(255,x+g['base_shifts'][k])))
 return Image.composite(Image.merge('RGBA',base),out,mask)
if stage=='c':
 src=bounds_stats(frames[0]);dst=bounds_stats(ref);gains=[max(.88,min(1.18,(b[2]-b[0])/max(1,a[2]-a[0]))) for a,b in zip(src,dst)];shifts=[max(-12,min(12,b[1]-a[1])) for a,b in zip(src,dst)]
 (M/'grade.json').write_text(json.dumps({'source':src,'target':dst,'gains':gains,'shifts':shifts,'base_shifts':[b-a for a,b in zip(base_stats(frames[0]),base_stats(ref))],'method':'Reference RGB percentiles, bounded, frozen for every clip; alpha unchanged'},indent=2))
frames=[grade(im) for im in frames]
for n,im in zip(manifest['frames'],frames):
 for s in [256,512]:
  if s>im.width:continue
  d=M/str(s)/stage;d.mkdir(exist_ok=True,parents=True);im.resize((s,s),Image.Resampling.LANCZOS).save(d/f'{n}.png')
manifest['grade_sha256']=hashlib.sha256((M/'grade.json').read_bytes()).hexdigest() if stage!='b' else None
(M/'raw'/stage/'delivery.json').write_text(json.dumps(manifest,indent=2))
f256=[im.resize((256,256),Image.Resampling.LANCZOS) for im in frames]
def sheet(ims,labels,name,small=True):
 w=len(ims)*256;out=Image.new('RGBA',(w,360 if small else 286),BG);d=ImageDraw.Draw(out)
 for i,(im,label) in enumerate(zip(ims,labels)):
  d.text((i*256+9,8),label,fill=(55,43,32));out.alpha_composite(im,(i*256,28))
  if small:out.alpha_composite(im.resize((64,64),Image.Resampling.LANCZOS),(i*256+96,292))
 out.save(V/f'peltast-{name}.png')
if stage=='b':sheet([ref]+f256,['Painting','Plain rest','Plain side'],'b-plain')
elif stage=='c':
 sheet([ref,f256[0]],['Painting',f"{manifest['engine']} {manifest['device']}"],'c-textured-lit')
 blend=Image.blend(ref,f256[0],.5);sheet([ref,f256[0],blend],['Painting','Rest render','50/50 crossfade'],'f-restpose-compare')
 crops=[];labels=[]
 for label,box in [('Head / cap',(83,10,140,65)),('Cloth',(77,62,148,142)),('Pelta',(147,35,210,128))]:
  for typ,im in [('painting',ref),('render',f256[0])]:crops.append(im.crop(box).resize((256,256),Image.Resampling.LANCZOS));labels.append(label+' '+typ)
 sheet(crops,labels,'c-details',False)
elif stage=='d':sheet(f256,['Windup','Coil','Release','Recovery'],'d-rig-poses')
else:
 clip=stage[2:];sheet(f256,[f'{clip} {i+1}' for i in range(len(frames))],f'e-{clip}-strip')
 fps={'idle':10,'move':12,'attack':14,'hit':12,'death':10}[clip]
 f256[0].save(V/f'peltast-e-{clip}.webp',save_all=True,append_images=f256[1:],duration=round(1000/fps),loop=0,quality=80,method=2)
with (V/'peltast-log.md').open('a') as f:f.write(f'- Published {stage} review immediately: {manifest["engine"]}/{manifest["device"]}, {manifest["resolution"]} px, {len(frames)} frame(s).\n')
print('REVIEW',stage)
