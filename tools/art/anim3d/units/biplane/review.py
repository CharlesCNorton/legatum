"""Immediate review sheets and one frozen, measured RGB grade for the whole round."""
from pathlib import Path
import os,sys,json,hashlib
from PIL import Image,ImageDraw
R=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'));M=R/'masters/biplane';D=R/'review/3d-v2';stage=sys.argv[1]
ref=Image.open('app/src/assets/units/biplane-256.png').convert('RGBA');cream=(240,232,214,255)
def tile(im,size=256):return im.resize((size,size),Image.Resampling.LANCZOS)
def quant(im):
 pix=[p for p in im.getdata() if p[3]>240];return [[sorted(p[c] for p in pix)[int((len(pix)-1)*q)] for q in (.1,.5,.9)] for c in range(3)]
raw=M/'raw'/stage; paths=sorted(raw.glob('*.png'));assert paths,stage
ims=[Image.open(p).convert('RGBA') for p in paths]
if stage=='c':
 src,dst=quant(ims[0]),quant(ref);luts=[]
 for a,b in zip(src,dst):
  pts=[(0,0)]+list(zip(a,b))+[(255,255)];lut=[]
  for v in range(256):
   lo,hi=next((lo,hi) for lo,hi in zip(pts,pts[1:]) if lo[0]<=v<=hi[0]);target=lo[1]+(hi[1]-lo[1])*(v-lo[0])/max(1,hi[0]-lo[0]);lut.append(round(max(0,min(255,max(v-24,min(v+24,target))))))
  luts.append(lut)
 (M/'grade.json').write_text(json.dumps({'source_quantiles':dst,'raw_quantiles':src,'max_delta':24,'luts':luts},indent=2))
if stage!='b':
 luts=json.loads((M/'grade.json').read_text())['luts'];ims=[Image.merge('RGBA',tuple(im.getchannel(c).point(luts[i]) for i,c in enumerate('RGB'))+(im.getchannel('A'),)) for im in ims]
for size in (512,256):
 if ims[0].width<size:continue # Never mislabel enlarged CPU previews as 512 masters.
 folder=M/str(size)/stage;folder.mkdir(parents=True,exist_ok=True)
 for i,im in enumerate(ims):tile(im,size).save(folder/f'{i:02}.png')
 manifest=json.loads((raw/'render.json').read_text());manifest['raw_sha256']=[hashlib.sha256(p.read_bytes()).hexdigest() for p in paths];manifest['processed_sha256']=[hashlib.sha256((folder/f'{i:02}.png').read_bytes()).hexdigest() for i in range(len(ims))];manifest['grade_sha256']=None if stage=='b' else hashlib.sha256((M/'grade.json').read_bytes()).hexdigest();(folder/'processed.json').write_text(json.dumps(manifest,indent=2))
ims=[tile(im) for im in ims]
def sheet(images,labels,path):
 out=Image.new('RGBA',(256*len(images),360),cream);d=ImageDraw.Draw(out)
 for i,(im,label) in enumerate(zip(images,labels)):
  d.text((i*256+8,6),label,fill='#4b3f32');out.alpha_composite(tile(im),(i*256,26));out.alpha_composite(tile(im,64),(i*256+96,288))
 out.convert('RGB').save(D/path)
if stage=='b':sheet([ref]+ims,['Painting','Plain geometry'], 'biplane-b-plain.png')
elif stage=='c':
 sheet([ref,ims[0]],['Painting','3D • textured / lit'],'biplane-c-textured-lit.png')
 sheet([ref,ims[0],Image.blend(ref,ims[0],.5)],['Painting','3D rest pose','50/50 crossfade'],'biplane-f-restpose-compare.png')
 out=Image.new('RGB',(768,540),cream[:3]);d=ImageDraw.Draw(out)
 for j,(name,box) in enumerate([('Cowling / cockpit',(25,55,150,125)),('Wing / struts',(95,35,230,145)),('Landing gear',(25,110,115,182))]):
  for i,im in enumerate([ref,ims[0]]):out.paste(im.crop(box).resize((256,240),Image.Resampling.LANCZOS),(j*256,20+i*260),im.crop(box).resize((256,240),Image.Resampling.LANCZOS))
  d.text((j*256+8,3),name,fill='#4b3f32')
 out.save(D/'biplane-c-details.png')
elif stage=='d':sheet(ims,['Attack pose '+str(i) for i in range(len(ims))],'biplane-d-rig-poses.png')
else:
 clip=stage[2:];sheet(ims,[clip+' '+str(i+1) for i in range(len(ims))],f'biplane-e-{clip}-strip.png')
 fps={'idle':10,'move':12,'attack':14,'hit':12,'death':10}[clip]
 ims[0].save(D/f'biplane-e-{clip}.webp',save_all=True,append_images=ims[1:],duration=round(1000/fps),loop=0,quality=85,method=4)
with (D/'biplane-log.md').open('a') as f:f.write(f'- Saved {stage} review immediately; {len(ims)} frames; raw render manifest: {raw}/render.json.\n')
print('REVIEW',stage)
