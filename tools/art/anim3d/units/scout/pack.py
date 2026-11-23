"""Trim every 160px sample, preserve row order, enforce quality >=75 / 200000 bytes."""
import os,json,hashlib,io
from pathlib import Path
from PIL import Image
R=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'));M=R/'masters/scout';V=R/'review/3d-v2';OUT=Path('app/src/assets/units/anim');OUT.mkdir(parents=True,exist_ok=True)
CLIPS={'idle':(8,10,True),'move':(8,12,True),'attack':(10,14,False),'hit':(4,12,False),'death':(10,10,False)}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
grade=sha(M/'grade.json');source=sha(M/'scout.blend');meta={'formatVersion':2,'frame':{'w':160,'h':160,'ax':80,'ay':142},'clips':{},'trims':{}};rows=[];renders={};hashes={};y=0
for row,(clip,(count,fps,loop)) in enumerate(CLIPS.items()):
 folder=M/'renders'/('e-'+clip);render=json.loads((folder/'render.json').read_text());renders[clip]=render
 assert render['resolution']==512,'Keep real 512px masters; never upscale a preview'
 assert render['blend_sha256']==sha(M/'clips'/(clip+'.blend')),'Stale clip render '+clip
 assert render['grade_sha256']==grade,'Mixed colour grades'
 assert json.loads((M/'clip-sources.json').read_text())[clip]==source,'Rebuild clips after model/material change'
 meta['clips'][clip]={'row':row,'frames':count,'fps':fps,'loop':loop};meta['trims'][clip]=[];sprites=[];x=0;rowh=0
 for i in range(count):
  p=folder/f'{i:02}.png';im=Image.open(p).convert('RGBA');assert im.size==(512,512)
  hashes[f'{clip}/{i}']=sha(p);im=im.resize((160,160),Image.Resampling.LANCZOS)
  # Quantize only alpha to 32 levels; RGB and all 40 samples are retained.
  a=im.getchannel('A').point(lambda v:round(round(v*31/255)*255/31));im.putalpha(a);box=a.getbbox();assert box
  crop=im.crop(box);w,h=crop.size;sprites.append((crop,x,y));meta['trims'][clip].append({'x':x,'y':y,'w':w,'h':h,'ox':box[0],'oy':box[1]});x+=w+2;rowh=max(rowh,h)
 rows.append((sprites,x-2,rowh));y+=rowh+2
atlas=Image.new('RGBA',(max(r[1] for r in rows),y-2))
for sprites,_,_ in rows:
 for im,x,y in sprites:atlas.paste(im,(x,y))
assert len({(r['engine'],r['device']) for r in renders.values()})==1,'Mixed engines/devices'
for quality in [90,85,80,75]:
 stream=io.BytesIO();atlas.save(stream,format='WEBP',quality=quality,method=6,exact=True)
 if len(stream.getvalue())<=200000:break
else:raise RuntimeError('Scout exceeds 200 KB at quality 75; report instead of degrading')
(OUT/'scout.webp').write_bytes(stream.getvalue());(OUT/'scout.json').write_text(json.dumps(meta,separators=(',',':'))+'\n')
report={'frames':40,'bytes':len(stream.getvalue()),'quality':quality,'alpha_levels':32,'size':atlas.size,'source_sha256':source,'grade_sha256':grade,'atlas_sha256':sha(OUT/'scout.webp'),'renders':renders,'frame_sha256':hashes};(V/'scout-pack.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k not in ['renders','frame_sha256']},indent=2))
