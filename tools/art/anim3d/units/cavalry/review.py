"""Immediate honest review sheets, native 256 and 64 beside the reference."""
import os,sys,json
from pathlib import Path
from PIL import Image,ImageDraw
R=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')));M=R/'masters/cavalry';V=R/'review/3d-v2';stage=sys.argv[1];folder=M/'renders'/stage
proof=json.loads((folder/'render.json').read_text())
render_label=f"{proof['device']} {proof['resolution']}px/{proof['samples']}s"
ref=Image.open('app/src/assets/units/cavalry-256.png').convert('RGBA');frames=[Image.open(p).convert('RGBA').resize((256,256),Image.Resampling.LANCZOS) for p in sorted(folder.glob('*.png'))]
# Preserve native stage masters and gallery copies, including plain/rest/details.
for p in sorted(folder.glob('*.png')):
 native=Image.open(p).convert('RGBA')
 for size in {native.width,256}:
  dest=M/str(size)/stage;dest.mkdir(parents=True,exist_ok=True)
  native.resize((size,size),Image.Resampling.LANCZOS).save(dest/p.name)
cream=(233,207,160,255)
def backed(im):
 out=Image.new('RGBA',im.size,cream);out.alpha_composite(im);return out
label={'b':'b-plain','c':'c-textured-lit','c-details':'c-details','d':'d-rig-poses'}.get(stage,stage+'-strip')
ims=[ref]+frames;sheet=Image.new('RGBA',(256*len(ims),360),cream);d=ImageDraw.Draw(sheet)
for i,im in enumerate(ims):
 sheet.alpha_composite(im,(i*256,25));sheet.alpha_composite(im.resize((64,64),Image.Resampling.LANCZOS),(i*256+96,290));d.text((i*256+8,6),'painting' if i==0 else f'{stage} {i-1} / {render_label}',fill='black')
sheet.convert('RGB').save(V/f'cavalry-{label}.png')
if stage=='c':
 a=backed(ref);b=backed(frames[0]);split=a.copy();split.paste(b.crop((128,0,256,256)),(128,0));blend=Image.blend(a,b,.5)
 out=Image.new('RGBA',(1024,350),cream);dr=ImageDraw.Draw(out)
 for i,(im,title) in enumerate(zip([a,b,split,blend],['Painting','3D rest / '+render_label,'Half split','50/50 crossfade'])):
  out.paste(im,(i*256,25));dr.text((i*256+10,6),title,fill='black');out.paste(im.resize((64,64),Image.Resampling.LANCZOS),(i*256+96,285))
 out.convert('RGB').save(V/'cavalry-f-restpose-compare.png')
if stage=='c-details':
 raw=Image.open(folder/'00.png').convert('RGBA');r=Image.open(R/'assets/cavalry/painting-aligned-1024.png').convert('RGBA').resize(raw.size,Image.Resampling.LANCZOS);detail=Image.new('RGBA',(1536,300),cream);d=ImageDraw.Draw(detail)
 for j,(name,box) in enumerate([('face / cap',(105,25,164,80)),('uniform / hand',(65,45,162,126)),('horse / tack',(138,69,213,151))]):
  scale=raw.width/256;bb=tuple(round(x*scale) for x in box)
  for i,im in enumerate([r,raw]):detail.alpha_composite(im.crop(bb).resize((256,256),Image.Resampling.LANCZOS),(j*512+i*256,30))
  d.text((j*512+8,8),name+' : painting / render',fill='black')
 detail.convert('RGB').save(V/'cavalry-c-details.png')
if stage.startswith('e-'):
 clip=stage[2:];fps={'idle':10,'move':12,'attack':14,'hit':12,'death':10}[clip]
 frames[0].save(V/f'cavalry-{stage}.webp',save_all=True,append_images=frames[1:],duration=round(1000/fps),loop=0,quality=85,method=6)
with (V/'cavalry-log.md').open('a') as f:f.write(f'{stage}: review emitted from {json.loads((folder/"render.json").read_text())["engine"]} frames; no art-pass claim.\n')
print('REVIEW',V/f'cavalry-{label}.png')
