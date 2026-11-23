"""Immediate review publishing; restrained source-measured grade, never edits alpha."""
from pathlib import Path
import os, sys, json
from PIL import Image, ImageDraw, ImageStat
R=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'));M=R/'masters/rocket-artillery';V=R/'review/3d-v2'
stage=sys.argv[1];cream=(233,207,160,255)
ref=Image.open('app/src/assets/units/rocket-artillery-256.png').convert('RGBA')
def rgba(path):return Image.open(path).convert('RGBA')
def flat(im):
 out=Image.new('RGBA',im.size,cream);out.alpha_composite(im);return out

def subject(im):
 # Match at the same sampling scale; exclude cream stone and transparent pixels.
 im=im.resize((256,256),Image.Resampling.LANCZOS).crop((0,0,256,177))
 mask=im.getchannel('A').point(lambda a:255 if a>220 else 0)
 return im.convert('RGB'),mask

def histogram_grade(raw):
 source,sm=subject(raw);target,tm=subject(ref)
 quantiles=(.02,.10,.25,.50,.75,.90,.98)
 def quantile(hist,q):
  total=sum(hist);running=0
  for i,n in enumerate(hist):
   running+=n
   if running>=q*total:return i
  return 255
 tables=[];knots=[]
 for a,b in zip(source.split(),target.split()):
  ah=a.histogram(sm);bh=b.histogram(tm);pairs={0:0,255:255}
  for q in quantiles:
   x=quantile(ah,q);y=quantile(bh,q)
   pairs[x]=max(0,min(255,x+max(-12,min(12,y-x))))
  points=sorted(pairs.items());table=[]
  for x in range(256):
   j=next((i for i in range(1,len(points)) if points[i][0]>=x),len(points)-1)
   x0,y0=points[j-1];x1,y1=points[j]
   table.append(round(y0+(y1-y0)*(x-x0)/max(1,x1-x0)))
  tables.append(table);knots.append(points)
 return {'method':'bounded RGB quantile histogram match at native 256; frozen across all frames',
         'max_channel_delta':12,'quantiles':quantiles,'knots':knots,'luts':tables,'alpha':'unchanged'}

def grade(im):
 p=M/'grade.json'
 if not p.exists():return im
 g=json.loads(p.read_text());alpha=im.getchannel('A')
 rgb=Image.merge('RGB',[ch.point(lut) for ch,lut in zip(im.convert('RGB').split(),g['luts'])])
 rgb.putalpha(alpha);return rgb

def sheet(images,labels,path,sizes=(256,64)):
 width=max(sizes)*len(images);height=sum(sizes)+65;out=Image.new('RGBA',(width,height),cream);d=ImageDraw.Draw(out);y=25
 for size in sizes:
  for j,(im,label) in enumerate(zip(images,labels)):
   x=j*max(sizes);out.alpha_composite(im.resize((size,size),Image.Resampling.LANCZOS),(x,y))
   if size==max(sizes):d.text((x+7,7),label,fill='#423b2d')
  y+=size+16
 out.convert('RGB').save(path)

def keep256(im,name):
 folder=M/'256';folder.mkdir(exist_ok=True);im.resize((256,256),Image.Resampling.LANCZOS).save(folder/name)
if stage in ['b-plain','c-textured-lit']:
 raw=rgba(M/'renders'/f'{stage}.png')
 if stage.startswith('c-'):
  (M/'grade.json').write_text(json.dumps(histogram_grade(raw),indent=2));im=grade(raw)
 else:im=raw
 keep256(im,stage+'.png');sheet([ref,im],['Painting',stage],V/f'rocket-artillery-{stage}.png')
 if stage.startswith('c-'):
  cross=Image.blend(flat(ref),flat(im.resize((256,256),Image.Resampling.LANCZOS)),.5)
  sheet([ref,im,cross],['Painting','True 3D rest','50/50 crossfade'],V/'rocket-artillery-f-restpose-compare.png')
elif stage=='c-details':
 im=grade(rgba(M/'renders/c-textured-lit.png')).resize((256,256),Image.Resampling.LANCZOS)
 boxes=[(25,90,127,148),(60,142,111,190),(116,37,233,116)];images=[];labels=[]
 for label,box in zip(['Cab','Wheel','Launcher'],boxes):
  images.extend([ref.crop(box),im.crop(box)]);labels.extend([label+' painting',label+' render'])
 sheet(images,labels,V/'rocket-artillery-c-details.png',sizes=(192,))
elif stage.startswith('e-'):
 clip=stage[2:];frames=[grade(rgba(p)) for p in sorted((M/'renders'/clip).glob('[0-9][0-9].png'))]
 folder=M/'256'/clip;folder.mkdir(parents=True,exist_ok=True)
 for i,im in enumerate(frames):im.resize((256,256),Image.Resampling.LANCZOS).save(folder/f'{i:02}.png')
 sheet(frames,[f'{clip} {i+1}' for i in range(len(frames))],V/f'rocket-artillery-{stage}-strip.png')
 frames=[flat(im.resize((256,256),Image.Resampling.LANCZOS)).convert('RGB') for im in frames]
 frames[0].save(V/f'rocket-artillery-{stage}.webp',save_all=True,append_images=frames[1:],duration=round(1000/{'idle':10,'move':12,'attack':14,'hit':12,'death':10}[clip]),loop=0,quality=85)
elif stage=='d-rig-poses':
 frames=[grade(rgba(M/'renders'/f'pose-{i}.png')) for i in [0,2,3,6]]
 sheet(frames,['Rest','Elevation','First rocket','Second rocket'],V/'rocket-artillery-d-rig-poses.png')
elif stage=='b-multiview':
 sheet([ref,rgba(M/'renders/b-plain.png'),rgba(M/'renders/b-side.png'),rgba(M/'renders/b-rear.png')],['Painting','Plain fixed camera','Plain side','Plain rear'],V/'rocket-artillery-b-plain.png')
elif stage=='g-feet-check':
 images=[rgba(M/'renders/feet'/f'{v}-{i:02}.png') for v in ['top','front'] for i in range(8)]
 out=Image.new('RGBA',(8*160,2*184+30),cream);d=ImageDraw.Draw(out)
 d.text((8,5),'Mechanical unit: six wheels, top / front, all eight move samples. No feet or mocap.',fill='#423b2d')
 for j,im in enumerate(images):
  x=j%8*160;y=30+j//8*184;out.alpha_composite(im.resize((160,160),Image.Resampling.LANCZOS),(x,y))
  d.text((x+5,y+161),f'{"top" if j<8 else "front"} {j%8+1}',fill='#423b2d')
 out.convert('RGB').save(V/'rocket-artillery-g-feet-check.png')
print('Published',stage,flush=True)
