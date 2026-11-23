"""Immediate review publication, fixed rest grade, 512/256 masters."""
import os,sys,json,hashlib
from pathlib import Path
from PIL import Image,ImageDraw,ImageStat,ImageEnhance
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/scout';V=R/'review/3d-v2';stage=sys.argv[1];out=M/'renders'/stage
ref=Image.open('app/src/assets/units/scout-256.png').convert('RGBA')
def opaque(im,bg=(39,35,31)):
 b=Image.new('RGBA',im.size,(*bg,255));b.alpha_composite(im);return b.convert('RGB')
def tile(im,size=256):return opaque(im.resize((size,size),Image.Resampling.LANCZOS))
raw=[Image.open(p).convert('RGBA') for p in sorted((out/'raw').glob('*.png'))]
if stage=='c':
 def quant(im):
  pix=[p[:3] for p in im.getdata() if p[3]>230];return [[sorted(p[c] for p in pix)[int((len(pix)-1)*q)] for q in [.1,.5,.9]] for c in range(3)]
 a,b=quant(raw[0]),quant(ref);lut=[]
 for c in range(3):
  gain=max(.88,min(1.14,(b[c][2]-b[c][0])/max(1,a[c][2]-a[c][0])));offset=max(-14,min(14,b[c][1]-a[c][1]*gain));lut.append([max(0,min(255,round(v*gain+offset*.6))) for v in range(256)])
 (M/'grade.json').write_text(json.dumps({'lut':lut,'reference_quantiles':b,'raw_quantiles':a}))
frames=[]
for i,im in enumerate(raw):
 if stage!='b':
  lut=json.loads((M/'grade.json').read_text())['lut'];alpha=im.getchannel('A');im=Image.merge('RGB',[im.getchannel(c).point(lut[k]) for k,c in enumerate('RGB')]);im=ImageEnhance.Color(im).enhance(1.05).convert('RGBA');im.putalpha(alpha)
 im.save(out/f'{i:02}.png');small=im.resize((256,256),Image.Resampling.LANCZOS);d=M/'256'/stage;d.mkdir(parents=True,exist_ok=True);small.save(d/f'{i:02}.png');frames.append(small)
manifest=json.loads((out/'render.json').read_text());manifest['grade_sha256']=hashlib.sha256((M/'grade.json').read_bytes()).hexdigest() if stage!='b' else None;(out/'render.json').write_text(json.dumps(manifest,indent=2))
if stage.startswith('e-'):
 clip=stage[2:];sheet=Image.new('RGB',(len(frames)*256,356),(39,35,31));d=ImageDraw.Draw(sheet);d.text((8,4),'Scout / '+clip+' / CPU preview' if manifest['device']=='CPU' else 'Scout / '+clip+' / GPU',(240,220,180))
 for i,im in enumerate(frames):sheet.paste(tile(im),(i*256,24));sheet.paste(tile(im,64),(i*256+96,284))
 sheet.save(V/f'scout-e-{clip}-strip.png');frames[0].save(V/f'scout-e-{clip}.webp',save_all=True,append_images=frames[1:],duration=round(1000/{'idle':10,'move':12,'attack':14,'hit':12,'death':10}[clip]),loop=0,quality=85)
elif stage=='b' and len(frames)==3:
 sheet=Image.new('RGB',(1024,370),(39,35,31));d=ImageDraw.Draw(sheet)
 for i,(label,im) in enumerate(zip(['Painting','Rest geometry','Front geometry','Side geometry'],[ref]+frames)):
  d.text((i*256+8,6),label,(240,220,180));sheet.paste(tile(im),(i*256,28));sheet.paste(tile(im,64),(i*256+96,294))
 sheet.save(V/'scout-b-plain.png')
elif stage=='d':
 sheet=Image.new('RGB',(1024,288),(39,35,31))
 for i,im in enumerate(frames):sheet.paste(tile(im),(i*256,24))
 ImageDraw.Draw(sheet).text((8,4),'Scout rig: anticipation / windup / staff strike / recovery',(240,220,180));sheet.save(V/'scout-d-rig-poses.png')
else:
 sheet=Image.new('RGB',(768,370),(39,35,31));d=ImageDraw.Draw(sheet)
 for i,(name,im) in enumerate([('Painting',ref),('3D '+manifest['engine']+'/'+manifest['device'],frames[0]),('50/50 crossfade',Image.blend(ref,frames[0],.5))]):
  d.text((i*256+8,6),name,(240,220,180));sheet.paste(tile(im),(i*256,28));sheet.paste(tile(im,64),(i*256+96,294))
 name={'b':'b-plain','c':'c-textured-lit','c-details':'c-details'}[stage];sheet.save(V/f'scout-{name}.png')
 if stage=='c':sheet.save(V/'scout-f-restpose-compare.png')
 if stage=='c-details':
  detail=Image.new('RGB',(1024,858),(39,35,31));source=Image.open(R/'assets/scout/projection.png').convert('RGBA');render=Image.open(out/'00.png').convert('RGBA')
  for i,(box,label) in enumerate([((105,15,225,110),'Face / shoulders'),((70,75,190,170),'Straps / tunic')]):
   for j,im in enumerate([source,render]):
    scale=im.width/256;crop=im.crop(tuple(round(v*scale) for v in box));detail.paste(opaque(crop.resize((512,405),Image.Resampling.LANCZOS)),(j*512,i*429+24))
   ImageDraw.Draw(detail).text((8,i*429+4),label+' / full painting left, '+str(render.width)+' px render right',(240,220,180))
  detail.save(V/'scout-c-details.png')
print('Published scout '+stage)
