"""One restrained foreground quantile transfer, shared by every animation frame."""
from pathlib import Path
import os,sys,json,hashlib
from PIL import Image
R=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')));M=R/'masters/barbarian-spearman';stage=sys.argv[1];folder=M/'renders'/stage
if stage=='b':raise SystemExit(0)
def quant(im,c):
 h=im.getchannel(c).histogram(mask=im.getchannel('A').point(lambda a:255 if a>160 else 0));total=sum(h);out=[]
 for q in range(17):
  accum=0
  for v,n in enumerate(h):
   accum+=n
   if accum>=total*(.02+.96*q/16):out.append(v);break
 return out
if stage=='c':
 ref=Image.open('app/src/assets/units/barbarian-spearman-256.png').convert('RGBA');im=Image.open(folder/'00.png').convert('RGBA');luts=[];stats={}
 for c in 'RGB':
  a=quant(im,c);b=quant(ref,c);lut=[]
  for v in range(256):
   if v<=a[0]:target=v+b[0]-a[0]
   elif v>=a[-1]:target=v+b[-1]-a[-1]
   else:
    k=next(k for k in range(16) if a[k]<=v<=a[k+1]);t=(v-a[k])/max(1,a[k+1]-a[k]);target=b[k]+t*(b[k+1]-b[k])
   lut.append(round(max(0,min(255,.60*v+.40*target))))
  luts.append(lut);stats[c]={'painting':b,'render':a}
 (M/'grade.json').write_text(json.dumps({'method':'40% monotonic 17-quantile foreground transfer, rest only','luts':luts,'quantiles':stats},indent=2))
luts=json.loads((M/'grade.json').read_text())['luts'];raw=folder/'raw';raw.mkdir(exist_ok=True)
for path in sorted(folder.glob('[0-9][0-9].png')):
 im=Image.open(path).convert('RGBA');im.save(raw/path.name);Image.merge('RGBA',[im.getchannel(c).point(lut) for c,lut in zip('RGB',luts)]+[im.getchannel('A')]).save(path)
meta=json.loads((folder/'render.json').read_text());meta['grade_sha256']=hashlib.sha256((M/'grade.json').read_bytes()).hexdigest();(folder/'render.json').write_text(json.dumps(meta,indent=2))
print('GRADE_READY',stage)
