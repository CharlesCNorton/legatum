"""Immediate review publishing; restrained source-measured grade, never edits alpha."""
from pathlib import Path
import os, sys, json
from PIL import Image, ImageDraw, ImageEnhance, ImageStat
R=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'));M=R/'masters/howitzer';V=R/'review/3d-v2'
stage=sys.argv[1];cream=(233,207,160,255)
ref=Image.open('app/src/assets/units/howitzer-256.png').convert('RGBA')
def rgba(path):return Image.open(path).convert('RGBA')
def flat(im):
 out=Image.new('RGBA',im.size,cream);out.alpha_composite(im);return out

def stats(im):
 # Subject only: avoid the base dominating the match.
 im=im.crop((0,0,im.width,int(im.height*.69)));mask=im.getchannel('A').point(lambda a:255 if a>220 else 0)
 s=ImageStat.Stat(im.convert('RGB'),mask);return s.mean,s.stddev

def grade(im):
 p=M/'grade.json'
 if not p.exists():return im
 g=json.loads(p.read_text());a=im.getchannel('A');rgb=im.convert('RGB');channels=rgb.split();rgb=Image.merge('RGB',[ch.point(lambda x,k=k:int(max(0,min(255,(x-128)*g['contrast']+128))*g['gains'][k])) for k,ch in enumerate(channels)])
 rgb=ImageEnhance.Color(rgb).enhance(1.04);rgb.putalpha(a);return rgb

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
  rm,rs=stats(raw);tm,ts=stats(ref)
  gains=[max(.90,min(1.08,t/max(1,r))) for t,r in zip(tm,rm)];contrast=max(.96,min(1.08,sum(ts)/max(1,sum(rs))))
  (M/'grade.json').write_text(json.dumps({'gains':gains,'contrast':contrast,'source_mean':tm,'render_mean':rm,'alpha':'unchanged'},indent=2));im=grade(raw)
 else:im=raw
 keep256(im,stage+'.png')
 images=[ref,im];labels=['Painting',stage]
 if stage=='b-plain' and (M/'renders/b-side.png').exists():
  images += [rgba(M/'renders/b-side.png'),rgba(M/'renders/b-front.png')];labels += ['Side: true volume','Front: true volume']
 sheet(images,labels,V/f'howitzer-{stage}.png')
 if stage.startswith('c-'):
  cross=Image.blend(flat(ref),flat(im.resize((256,256),Image.Resampling.LANCZOS)),.5)
  sheet([ref,im,cross],['Painting','True 3D rest','50/50 crossfade'],V/'howitzer-f-restpose-compare.png')
elif stage=='c-details':
 im=grade(rgba(M/'renders/c-textured-lit.png')).resize((256,256),Image.Resampling.LANCZOS)
 boxes=[(88,58,211,142),(72,105,141,213),(135,16,242,115)];images=[];labels=[]
 for label,box in zip(['Shield','Wheel','Barrel'],boxes):
  images.extend([ref.crop(box),im.crop(box)]);labels.extend([label+' painting',label+' render'])
 sheet(images,labels,V/'howitzer-c-details.png',sizes=(192,))
elif stage.startswith('e-'):
 clip=stage[2:];frames=[grade(rgba(p)) for p in sorted((M/'renders'/clip).glob('[0-9][0-9].png'))]
 folder=M/'256'/clip;folder.mkdir(parents=True,exist_ok=True)
 for i,im in enumerate(frames):im.resize((256,256),Image.Resampling.LANCZOS).save(folder/f'{i:02}.png')
 sheet(frames,[f'{clip} {i+1}' for i in range(len(frames))],V/f'howitzer-{stage}-strip.png')
 frames=[flat(im.resize((256,256),Image.Resampling.LANCZOS)).convert('RGB') for im in frames]
 frames[0].save(V/f'howitzer-{stage}.webp',save_all=True,append_images=frames[1:],duration=round(1000/{'idle':10,'move':12,'attack':14,'hit':12,'death':10}[clip]),loop=0,quality=85)
elif stage=='d-rig-poses':
 frames=[grade(rgba(M/'renders'/f'pose-{i}.png')) for i in [0,2,3,6]]
 sheet(frames,['Rest','Anticipation','Recoil / flash','Recovery'],V/'howitzer-d-rig-poses.png')
elif stage=='g-feet-check':
 images=[rgba(M/'renders/contact'/f'{v}-{i:02}.png') for v in ['top','front'] for i in range(8)]
 out=Image.new('RGBA',(8*160,2*184),cream);d=ImageDraw.Draw(out)
 for k,im in enumerate(images):
  x=k%8*160;y=k//8*184
  out.alpha_composite(im.resize((160,160),Image.Resampling.LANCZOS),(x,y+24));d.text((x+4,y+5),('top' if k<8 else 'front')+f' move {k%8+1}',fill='#423b2d')
 out.convert('RGB').save(V/'howitzer-g-feet-check.png')
print('Published',stage,flush=True)
