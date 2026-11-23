"""Immediate review publishing; restrained source-measured grade, never edits alpha."""
from pathlib import Path
import os, sys, json
from PIL import Image, ImageDraw
R=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'));M=R/'masters/artillery';V=R/'review/3d-v2'
stage=sys.argv[1];cream=(233,207,160,255)
ref=Image.open('app/src/assets/units/artillery-256.png').convert('RGBA')
def rgba(path):return Image.open(path).convert('RGBA')
def flat(im):
 out=Image.new('RGBA',im.size,cream);out.alpha_composite(im);return out

def histogram_grade(raw):
 # Source-measured monotone channel curves, fixed once at rest. The cream stone
 # must not inherit the gun's contrast/saturation correction. No per-frame fit.
 raw=raw.resize((256,256),Image.Resampling.LANCZOS)
 regions={}
 for name,(lo,hi) in {'gun':(0,174),'stone':(184,211)}.items():
  samples=[]
  for im in [raw,ref]:
   crop=im.crop((0,lo,256,hi));mask=crop.getchannel('A').point(lambda a:255 if a>240 else 0)
   hist=crop.convert('RGB').histogram(mask)
   quantiles=[]
   for k in range(3):
    h=hist[k*256:(k+1)*256];total=sum(h);values=[]
    for fraction in [0,.02,.10,.25,.5,.75,.90,.98,1]:
     cumulative=0
     for value,n in enumerate(h):
      cumulative+=n
      if cumulative>=total*fraction:break
     values.append(value)
    quantiles.append(values)
   samples.append(quantiles)
  curves=[]
  for source,target in zip(*samples):
   lut=[]
   contrast=max(.8,min(1.6 if name=='stone' else 1.2,(target[6]-target[2])/max(1,source[6]-source[2])))
   for value in range(256):
    match=(value-source[4])*contrast+target[4]
    lut.append(round(max(0,min(255,value+max(-28,min(28,match-value))*.85))))
   curves.append(lut)
  regions[name]={'curves':curves,'render_quantiles':samples[0],'painting_quantiles':samples[1]}
 return {'method':'bounded RGB median and 10/90-percentile contrast match, separate gun and stone; fixed at rest','regions':regions,'alpha':'unchanged'}

def grade(im):
 p=M/'grade.json'
 if not p.exists():return im
 g=json.loads(p.read_text());a=im.getchannel('A');channels=im.convert('RGB').split()
 corrected={name:Image.merge('RGB',[ch.point(curve) for ch,curve in zip(channels,region['curves'])]) for name,region in g['regions'].items()}
 mask=Image.new('L',(1,im.height));mask.putdata([round(max(0,min(1,(y/im.height*256-177)/9))*255) for y in range(im.height)])
 rgb=Image.composite(corrected['stone'],corrected['gun'],mask.resize(im.size));rgb.putalpha(a);return rgb

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
 keep256(im,stage+'.png');sheet([ref,im],['Painting',stage],V/f'artillery-{stage}.png')
 if stage.startswith('c-'):
  cross=Image.blend(flat(ref),flat(im.resize((256,256),Image.Resampling.LANCZOS)),.5)
  sheet([ref,im,cross],['Painting','True 3D rest','50/50 crossfade'],V/'artillery-f-restpose-compare.png')
elif stage=='c-details':
 im=grade(rgba(M/'renders/c-textured-lit.png')).resize((256,256),Image.Resampling.LANCZOS)
 boxes=[(90,55,205,130),(85,100,145,190),(140,40,242,114)];images=[];labels=[]
 for label,box in zip(['Shield','Wheel','Barrel'],boxes):
  images.extend([ref.crop(box),im.crop(box)]);labels.extend([label+' painting',label+' render'])
 sheet(images,labels,V/'artillery-c-details.png',sizes=(192,))
elif stage.startswith('e-'):
 clip=stage[2:];frames=[grade(rgba(p)) for p in sorted((M/'renders'/clip).glob('[0-9][0-9].png'))]
 folder=M/'256'/clip;folder.mkdir(parents=True,exist_ok=True)
 for i,im in enumerate(frames):im.resize((256,256),Image.Resampling.LANCZOS).save(folder/f'{i:02}.png')
 sheet(frames,[f'{clip} {i+1}' for i in range(len(frames))],V/f'artillery-{stage}-strip.png')
 frames=[flat(im.resize((256,256),Image.Resampling.LANCZOS)).convert('RGB') for im in frames]
 frames[0].save(V/f'artillery-{stage}.webp',save_all=True,append_images=frames[1:],duration=round(1000/{'idle':10,'move':12,'attack':14,'hit':12,'death':10}[clip]),loop=0,quality=85)
elif stage=='d-rig-poses':
 frames=[grade(rgba(M/'renders'/f'pose-{i}.png')) for i in [0,2,3,6]]
 sheet(frames,['Rest','Anticipation','Recoil / flash','Recovery'],V/'artillery-d-rig-poses.png')
elif stage=='g-feet-check':
 out=Image.new('RGBA',(8*160,2*185),cream);draw=ImageDraw.Draw(out)
 for row,label in enumerate(['front','top']):
  for i in range(8):
   im=rgba(M/'contact-views'/f'{label}-{i:02}.png').resize((160,160),Image.Resampling.LANCZOS)
   out.alpha_composite(im,(i*160,row*185+25));draw.text((i*160+5,row*185+6),f'{label} move {i+1}',fill='#423b2d')
 out.convert('RGB').save(V/'artillery-g-feet-check.png')
print('Published',stage,flush=True)
