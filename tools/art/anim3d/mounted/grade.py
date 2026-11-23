"""Apply one painting-derived colour LUT to every clip, preserving original alpha.

Calibrate once from the rest render. Never fit a separate histogram per animation
frame: that would cause visible temporal pumping. Raw renders remain external.
"""
import os,sys,json,hashlib
from pathlib import Path
from PIL import Image
R=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')));M=R/'masters/horseman-3d';stage=sys.argv[1];folder=M/'renders'/stage
if stage=='b':
 for p in sorted(folder.glob('*.png')):
  im=Image.open(p).convert('RGBA')
  for size in (512,256):
   if size>im.width:continue
   archive=R/'masters/horseman'/str(size)/stage;archive.mkdir(parents=True,exist_ok=True)
   im.resize((size,size),Image.Resampling.LANCZOS).save(archive/p.name)
 raise SystemExit(0)
def hist(im,channel):
 mask=im.getchannel('A').point(lambda x:255 if x>128 else 0)
 return im.getchannel(channel).histogram(mask=mask)
def quantiles(h):
 total=sum(h);vals=[]
 for i in range(17):
  threshold=total*(.02+.96*i/16);acc=0
  for j,n in enumerate(h):
   acc+=n
   if acc>=threshold:vals.append(j);break
 return vals
if stage=='c' and os.environ.get('GRADE_REUSE')!='1':
 source=Image.open('app/src/assets/units/horseman-256.png').convert('RGBA');render=Image.open(folder/'00.png').convert('RGBA');luts=[];stats={}
 for channel in 'RGB':
  a=quantiles(hist(render,channel));b=quantiles(hist(source,channel));lut=[]
  for x in range(256):
   if x<=a[0]:target=x+(b[0]-a[0])
   elif x>=a[-1]:target=x+(b[-1]-a[-1])
   else:
    k=next(i for i in range(16) if a[i]<=x<=a[i+1]);t=(x-a[k])/max(1,a[k+1]-a[k]);target=b[k]+(b[k+1]-b[k])*t
   lut.append(round(max(0,min(255,x*.55+target*.45))))
  luts.append(lut);stats[channel]={'render':a,'painting':b}
 (M/'grade.json').write_text(json.dumps({'method':'17 foreground quantiles per channel, 45 percent transfer','luts':luts,'quantiles':stats},indent=2))
else:luts=json.loads((M/'grade.json').read_text())['luts']
raw=folder/'raw';raw.mkdir(exist_ok=True)
for p in sorted(folder.glob('*.png')):
 im=Image.open(p).convert('RGBA');im.save(raw/p.name)
 channels=[im.getchannel(c).point(lut) for c,lut in zip('RGB',luts)]+[im.getchannel('A')]
 Image.merge('RGBA',channels).save(p)
meta=json.loads((folder/'render.json').read_text());meta['grade_sha256']=hashlib.sha256((M/'grade.json').read_bytes()).hexdigest();meta['raw_preserved']=True;(folder/'render.json').write_text(json.dumps(meta,indent=2))
print('GRADED',stage)

# Keep canonical 512 masters and a separately downsampled 256 gallery set.
size=int(meta['resolution'])
if size in (256,512):
 archive=R/'masters/horseman'/str(size)/stage;archive.mkdir(parents=True,exist_ok=True)
 for p in sorted(folder.glob('*.png')):
  im=Image.open(p).convert('RGBA');im.save(archive/p.name)
  if size==512:
   small=R/'masters/horseman/256'/stage;small.mkdir(parents=True,exist_ok=True)
   im.resize((256,256),Image.Resampling.LANCZOS).save(small/p.name)
 (archive/'render.json').write_text((folder/'render.json').read_text())
