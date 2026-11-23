"""Trim every 160 px virtual cell and pack clip rows without dropping samples."""
from pathlib import Path
from PIL import Image
import os,json,hashlib,io
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/cuirassier';V=R/'review/3d-v2';OUT=Path('app/src/assets/units/anim');OUT.mkdir(parents=True,exist_ok=True)
CLIPS={'idle':(8,10,True),'move':(8,12,True),'attack':(10,14,False),'hit':(4,12,False),'death':(10,10,False)}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
master=sha(M/'cuirassier.blend');grade=sha(M/'grade.json');meta={'version':2,'format':'trimmed-rows','frame':{'w':160,'h':160,'ax':103,'ay':140},'clips':{}};tiles=[];y=0;maxwidth=0;sources={}
for row,(clip,(count,fps,loop)) in enumerate(CLIPS.items()):
 folder=M/'renders'/f'e-{clip}';manifest=json.loads((folder/'render.json').read_text())
 assert manifest['blend_sha256']==sha(M/'clips'/f'{clip}.blend'),f'Stale {clip} blend'
 assert manifest['source_master_sha256']==master,f'Stale {clip} source'
 assert manifest['grade_sha256']==grade,f'Stale {clip} grade'
 x=0;rowheight=0;rects=[];sources[clip]={'render':manifest,'frames':{}}
 for i in range(count):
  p=folder/f'{i:02}.png';im=Image.open(p).convert('RGBA').resize((160,160),Image.Resampling.LANCZOS)
  # Discard only almost-transparent reconstruction ringing before trim.
  alpha=im.getchannel('A').point(lambda a:0 if a<3 else a);im.putalpha(alpha);box=alpha.getbbox();assert box
  ox,oy,right,bottom=box;w,h=right-ox,bottom-oy;crop=im.crop(box)
  tiles.append((crop,x+2,y+2));rects.append({'x':x+2,'y':y+2,'w':w,'h':h,'ox':ox,'oy':oy});x+=w+4;rowheight=max(rowheight,h+4);sources[clip]['frames'][str(i)]=sha(p)
 meta['clips'][clip]={'row':row,'frames':count,'fps':fps,'loop':loop,'rects':rects};y+=rowheight;maxwidth=max(maxwidth,x)
atlas=Image.new('RGBA',(maxwidth,y))
for crop,x,y0 in tiles:atlas.paste(crop,(x,y0))
for quality in [90,85,80,75]:
 buffer=io.BytesIO();atlas.save(buffer,format='WEBP',quality=quality,method=6,exact=True)
 if len(buffer.getvalue())<=200000:break
else:raise RuntimeError('Atlas exceeds 200 KB at quality 75; keep masters and report.')
meta['atlas']={'w':atlas.width,'h':atlas.height,'quality':quality};(OUT/'cuirassier.webp').write_bytes(buffer.getvalue());(OUT/'cuirassier.json').write_text(json.dumps(meta,separators=(',',':'))+'\n')
report={'bytes':len(buffer.getvalue()),'quality':quality,'frames':40,'atlas_sha256':sha(OUT/'cuirassier.webp'),'master_sha256':master,'sources':sources}
(V/'cuirassier-pack.json').write_text(json.dumps(report,indent=2));print(f'PACK: 40 frames, {atlas.size}, quality {quality}, {report["bytes"]} bytes')
