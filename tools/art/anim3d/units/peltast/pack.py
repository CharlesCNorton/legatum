"""160px logical cells, per-frame trims and bounded alpha quantization for delivery."""
import os,json,io,hashlib
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'));M=ROOT/'masters/peltast';R=ROOT/'review/3d-v2';OUT=Path('app/src/assets/units/anim');OUT.mkdir(exist_ok=True,parents=True)
CLIPS={'idle':(8,10,True),'move':(8,12,True),'attack':(10,14,False),'hit':(4,12,False),'death':(10,10,False)}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
frames={};sources={};hashes={}
for clip,(n,fps,loop) in CLIPS.items():
 source=json.loads((M/'raw'/f'e-{clip}'/'delivery.json').read_text());assert source['blend_sha256']==sha(M/'clips'/f'{clip}.blend'),f'{clip}: stale render'
 assert json.loads((M/'clips'/f'{clip}.json').read_text())['source_sha256']==sha(M/'peltast.blend'),f'{clip}: stale animation'
 assert source['grade_sha256']==sha(M/'grade.json'),f'{clip}: stale grade'
 for i in range(n):
  path=M/'256'/f'e-{clip}'/f'{i:02}.png';frames[clip,i]=Image.open(path).convert('RGBA').resize((160,160),Image.Resampling.LANCZOS);hashes[f'{clip}/{i}']=sha(path)
 sources[clip]=source
assert len({(s['engine'],s['device'],s['resolution']) for s in sources.values()})==1,'Mixed render settings'
def compose(levels):
 meta={'version':2,'atlas':{},'frame':{'w':160,'h':160,'ax':72.5,'ay':139.375},'clips':{}};items=[];y=0;maxw=0
 for row,(clip,(n,fps,loop)) in enumerate(CLIPS.items()):
  x=0;height=0;rects=[]
  for i in range(n):
   im=frames[clip,i].copy();a=im.getchannel('A')
   if levels<256:a=a.point(lambda v:round(round(v*(levels-1)/255)*255/(levels-1)))
   im.putalpha(a);im.paste((0,0,0,0),mask=a.point(lambda v:255 if v==0 else 0));box=a.getbbox();assert box
   crop=im.crop(box);r={'x':x+1,'y':y+1,'w':crop.width,'h':crop.height,'ox':box[0],'oy':box[1]};rects.append(r);items.append((crop,r));x+=crop.width+2;height=max(height,crop.height+2)
  meta['clips'][clip]={'row':row,'frames':n,'fps':fps,'loop':loop,'rects':rects};maxw=max(maxw,x);y+=height
 atlas=Image.new('RGBA',(maxw,y));meta['atlas']={'w':maxw,'h':y}
 for im,r in items:atlas.paste(im,(r['x'],r['y']))
 return atlas,meta
attempts=[];quality=75
for levels in [256,64,32]:
 atlas,meta=compose(levels);data=io.BytesIO();atlas.save(data,format='WEBP',quality=quality,method=6,exact=True);payload=data.getvalue();attempts.append({'quality':quality,'alpha_levels':levels,'bytes':len(payload)});print('ATTEMPT',attempts[-1],flush=True)
 (M/'atlas-attempts.json').write_text(json.dumps(attempts,indent=2))
 if len(payload)<=200000:break
else:
 (M/'peltast-oversize.webp').write_bytes(payload);(M/'peltast-oversize.json').write_text(json.dumps(meta))
 raise RuntimeError(f'All40/160px exceeds 200KB at RGB quality75 and at most 4/255 alpha error; report, do not degrade further: {attempts}')
assert Image.open(io.BytesIO(payload)).convert('RGBA').getchannel('A').tobytes()==atlas.getchannel('A').tobytes(),'Additional encoding alpha loss'
(OUT/'peltast.webp').write_bytes(payload);(OUT/'peltast.json').write_text(json.dumps(meta,separators=(',',':'))+'\n')
report={'bytes':len(payload),'quality':quality,'frames':40,'alpha_levels':levels,'alpha_max_error':max(abs(v-round(round(v*(levels-1)/255)*255/(levels-1))) for v in range(256)),'alpha':'Bounded quantization, then lossless WebP alpha encoding','atlas_sha256':sha(OUT/'peltast.webp'),'source_sha256':hashes,'render_sources':sources,'attempts':attempts}
(R/'peltast-pack.json').write_text(json.dumps(report,indent=2));print('PACK',len(payload),'bytes, quality',quality,atlas.size,'40 frames')

# Review the decoded delivery, not just the larger render masters.
decoded=Image.open(io.BytesIO(payload)).convert('RGBA');r=meta['clips']['idle']['rects'][0];sprite=Image.new('RGBA',(160,160));sprite.paste(decoded.crop((r['x'],r['y'],r['x']+r['w'],r['y']+r['h'])),(r['ox'],r['oy']))
ref=Image.open('app/src/assets/units/peltast-256.png').convert('RGBA').resize((160,160),Image.Resampling.LANCZOS);preview=Image.new('RGBA',(320,260),(240,232,214,255));draw=ImageDraw.Draw(preview)
for i,(im,label) in enumerate([(ref,'Painting'),(sprite,'Shipped 160 px')]):
 preview.alpha_composite(im,(i*160,24));preview.alpha_composite(im.resize((64,64),Image.Resampling.LANCZOS),(i*160+48,190));draw.text((i*160+8,6),label,fill=(60,45,25))
preview.save(R/'peltast-f-atlas-compare.png')
