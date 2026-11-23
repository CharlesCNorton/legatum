"""Write interim evidence immediately; native 256 and 64 px, never claim approval."""
from pathlib import Path
import os,sys,json
from PIL import Image,ImageDraw
R=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')));M=R/'masters/barbarian-spearman';O=R/'review/3d-v2';O.mkdir(exist_ok=True)
stage=sys.argv[1];folder=M/'renders'/stage
ref=Image.open('app/src/assets/units/barbarian-spearman-256.png').convert('RGBA')
frames=[Image.open(p).convert('RGBA').resize((256,256),Image.Resampling.LANCZOS) for p in sorted(folder.glob('[0-9][0-9].png'))]
assert frames,folder
bg=(47,48,45)
def paste(canvas,im,xy):canvas.paste(im,xy,im)
def label(c,x,y,s):ImageDraw.Draw(c).text((x,y),s,fill=(235,219,190))
if stage=='g-feet':
 sheet=Image.new('RGB',(128*8,300),bg)
 for i,im in enumerate(frames):
  x=(i%8)*128;y=(i//8)*150
  paste(sheet,im.resize((128,128),Image.Resampling.LANCZOS),(x,y+20));label(sheet,x+4,y+3,('top' if i<8 else 'front')+f' {i%8+1}')
 sheet.save(O/'barbarian-spearman-g-feet-check.png')
elif stage.startswith('e-'):
 clip=stage[2:];sheet=Image.new('RGB',(256*len(frames),354),bg)
 for i,im in enumerate(frames):paste(sheet,im,(256*i,24));paste(sheet,im.resize((64,64),Image.Resampling.LANCZOS),(256*i+96,286));label(sheet,256*i+8,5,f'{clip} {i+1}')
 sheet.save(O/f'barbarian-spearman-e-{clip}-strip.png')
 fps=dict(idle=10,move=12,attack=14,hit=12,death=10)[clip]
 frames[0].save(O/f'barbarian-spearman-e-{clip}.webp',save_all=True,append_images=frames[1:],duration=round(1000/fps),loop=0,quality=85)
elif stage=='c-details':
 sheet=Image.new('RGB',(768,550),bg)
 fullref=Image.open(R/'assets/barbarian-spearman/painting-aligned.png').convert('RGBA')
 fullrender=Image.open(folder/'00.png').convert('RGBA')
 for j,(name,box) in enumerate([('face / fur',(91,12,162,86)),('tunic / leather',(83,70,151,145)),('shield / iron',(151,47,207,172))]):
  a=tuple(round(v*fullref.width/256) for v in box);b=tuple(round(v*fullrender.width/256) for v in box)
  paste(sheet,fullref.crop(a).resize((256,256)),(j*256,25));paste(sheet,fullrender.crop(b).resize((256,256)),(j*256,285));label(sheet,j*256+8,5,name+f' : painting / {fullrender.width}px render')
 sheet.save(O/'barbarian-spearman-c-details.png')
else:
 ims=[ref]+frames;sheet=Image.new('RGB',(256*len(ims),370),bg)
 for i,im in enumerate(ims):paste(sheet,im,(i*256,28));paste(sheet,im.resize((64,64),Image.Resampling.LANCZOS),(i*256+96,294));label(sheet,i*256+8,7,'Painting' if i==0 else f'{stage} view {i}')
 suffix={'b':'b-plain','c':'c-textured-lit','d':'d-rig-poses'}[stage];sheet.save(O/f'barbarian-spearman-{suffix}.png')
 if stage=='c':
  im=frames[0];split=ref.copy();split.paste(im.crop((128,0,256,256)),(128,0));cross=Image.blend(ref,im,.5)
  sheet=Image.new('RGB',(1024,370),bg)
  for i,(name,pic) in enumerate(zip(['Painting','3D render','Half split','50/50 crossfade'],[ref,im,split,cross])):
   paste(sheet,pic,(i*256,28));paste(sheet,pic.resize((64,64),Image.Resampling.LANCZOS),(i*256+96,294));label(sheet,i*256+8,7,name)
  sheet.save(O/'barbarian-spearman-f-restpose-compare.png')
with (O/'barbarian-spearman-log.md').open('a') as f:f.write(f'- Published {stage} review from {json.loads((folder/"render.json").read_text())["device"]} render.\n')
print('REVIEW_READY',stage)
