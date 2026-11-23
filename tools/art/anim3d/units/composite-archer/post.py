"""One frozen painting-derived grade; retain raw 512 and graded 512/256 sets."""
import os,sys,json,hashlib
from pathlib import Path
from PIL import Image,ImageStat,ImageDraw
from review import sheet,REF,R,M,OUT
CLIPS={'idle':(8,10),'move':(8,12),'attack':(10,14),'hit':(4,12),'death':(10,10)}
def quantiles(im):
 mask=im.getchannel('A').point(lambda v:255 if v>200 else 0);vals=[]
 for band in im.convert('RGB').split():
  h=band.histogram(mask);n=sum(h);qs=[]
  for q in [.1,.3,.5,.7,.9]:
   target=n*q;acc=0
   for v,count in enumerate(h):
    acc+=count
    if acc>=target:qs.append(v);break
  vals.append(qs)
 return vals
stage=sys.argv[1];folder=M/'renders'/stage;manifest=json.loads((folder/'manifest.json').read_text());raw=[Image.open(M/f['path']).convert('RGBA') for f in manifest['frames']]
if stage=='c':
 src=quantiles(raw[0]);dst=quantiles(REF);luts=[]
 for a,b in zip(src,dst):
  points=[(0,0)]+[(x,max(0,min(255,x+max(-22,min(22,(y-x)*.45))))) for x,y in zip(a,b)]+[(255,255)]
  points=sorted(dict(points).items());lut=[]
  for v in range(256):
   j=next((i for i in range(len(points)-1) if points[i][0]<=v<=points[i+1][0]),len(points)-2);x,y=points[j];xx,yy=points[j+1];lut.append(round(y+(yy-y)*(v-x)/max(1,xx-x)))
  luts.append(lut)
 (M/'grade.json').write_text(json.dumps({'source':src,'target':dst,'luts':luts,'method':'45% opaque RGB quantile matching, max 22 levels; frozen for all clips'},indent=2))
grade=json.loads((M/'grade.json').read_text());ims=[]
for i,im in enumerate(raw):
 alpha=im.getchannel('A');bands=[c.point(lut) for c,lut in zip(im.convert('RGB').split(),grade['luts'])];im=Image.merge('RGBA',(*bands,alpha))
 for size in [512,256]:
  p=M/f'{size}'/stage;p.mkdir(parents=True,exist_ok=True);im.resize((size,size),Image.Resampling.LANCZOS).save(p/f'{i:02d}.png')
 ims.append(im.resize((256,256),Image.Resampling.LANCZOS))
manifest['grade_sha256']=hashlib.sha256((M/'grade.json').read_bytes()).hexdigest();(folder/'manifest.json').write_text(json.dumps(manifest,indent=2))
label=f"{manifest['engine']} {manifest['device']} {manifest['samples']} samples"
if stage=='c':
 sheet('c-textured-lit',ims,[label]);blend=Image.blend(REF,ims[0],.5);split=REF.copy();split.paste(ims[0].crop((128,0,256,256)),(128,0));sheet('f-restpose-compare',[ims[0],split,blend],[label,'Half split','50/50 crossfade'])
 # Unscaled 512 master crops make surface failures visible.
 source=Image.open(R/'assets/composite-archer/painting-aligned.png').convert('RGBA').resize((512,512),Image.Resampling.LANCZOS)
 cooked=Image.open(M/'512/c/00.png')
 crops=[(130,65,255,215),(95,160,295,350),(105,290,355,440)]
 canvas=Image.new('RGB',(768,560),(38,34,30));d=ImageDraw.Draw(canvas)
 for i,box in enumerate(crops):
  for j,img in enumerate([source,cooked]):
   part=img.crop(box);part.thumbnail((250,250));canvas.paste(part,(i*256,30+j*275),part)
  d.text((i*256+5,7),['Face / draw hand','Cloth / leather','Trousers / folds'][i],fill=(240,220,190))
 canvas.save(OUT/'composite-archer-c-details.png')
elif stage.startswith('e-'):
 clip=stage[2:];sheet(f'e-{clip}-strip',ims,[f'{clip} {i+1}' for i in range(len(ims))])
 ims[0].save(OUT/f'composite-archer-e-{clip}.webp',save_all=True,append_images=ims[1:],duration=round(1000/CLIPS[clip][1]),loop=0,quality=88,method=6)
 if clip=='attack':sheet('d-rig-poses',[ims[i] for i in [0,2,4,7]],['Draw','Aim','Release','Recover'])
with (OUT/'composite-archer-log.md').open('a') as f:f.write(f'- Saved {stage} review, raw {manifest["resolution"]} px and graded 512/256 sets; {label}.\n')
