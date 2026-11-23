"""Trim all 40 160px frames, keep offsets/anchors, WebP >=75 and <=200000 bytes."""
import os,json,hashlib,io,sys
from pathlib import Path
from PIL import Image
R=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')));M=R/'masters/archer';D=Path('app/src/assets/units/anim');D.mkdir(parents=True,exist_ok=True)
CLIPS={'idle':(8,10,True),'move':(8,12,True),'attack':(10,14,False),'hit':(4,12,False),'death':(10,10,False)}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
preview='--preview' in sys.argv
source=sha(M/'archer.blend');grade=sha(M/'grade.json');rows=[];clips={};manifest={};y=0;maxwidth=0
for row,(clip,(count,fps,loop)) in enumerate(CLIPS.items()):
 folder=M/'renders'/f'e-{clip}';meta=json.loads((folder/'render.json').read_text());assert meta['source_sha256']==source,(clip,'stale source');assert meta['blend_sha256']==sha(M/'clips'/f'{clip}.blend'),(clip,'stale clip');assert meta['grade_sha256']==grade,(clip,'stale grade');assert meta['resolution']>=(256 if preview else 512),(clip,'512px masters required unless --preview');rest=json.loads((M/'renders/c/render.json').read_text());assert all(meta[k]==rest[k] for k in ['engine','device','resolution','samples']), (clip,'render settings differ from rest')
 xs=0;items=[];rects=[];height=0;checks=[]
 for i in range(count):
  path=folder/f'{i:02}.png';im=Image.open(path).convert('RGBa').resize((160,160),Image.Resampling.BICUBIC).convert('RGBA');box=im.getchannel('A').getbbox();assert box
  cut=im.crop(box);w,h=cut.size;rects.append({'x':xs+1,'y':y+1,'w':w,'h':h,'ox':box[0],'oy':box[1]});items.append((cut,xs+1,y+1));xs+=w+2;height=max(height,h+2);checks.append({'frame':i,'sha256':sha(path),'trim':list(box)})
 rows.extend(items);clips[clip]={'row':row,'frames':count,'fps':fps,'loop':loop,'rects':rects};y+=height;maxwidth=max(maxwidth,xs);manifest[clip]={'render':meta,'frames':checks}
atlas=Image.new('RGBA',(maxwidth,y))
for im,x,z in rows:atlas.paste(im,(x,z))
encoded=None
for quality in [90,85,80,75]:
 data=io.BytesIO();atlas.save(data,'WEBP',quality=quality,method=6,exact=True);blob=data.getvalue()
 if len(blob)<=200000:encoded=blob;break
assert encoded is not None,'Atlas exceeds cap at quality75; do not silently drop frames or quality'
meta={'format':'trimmed-v1','frame':{'w':160,'h':160,'ax':80,'ay':138},'clips':clips}
(D/'archer.webp').write_bytes(encoded);(D/'archer.json').write_text(json.dumps(meta,indent=2)+'\n')
report={'preview':preview,'resampler':'premultiplied bicubic','quality':quality,'bytes':len(encoded),'atlas_size':list(atlas.size),'source_sha256':source,'grade_sha256':grade,'atlas_sha256':sha(D/'archer.webp'),'json_sha256':sha(D/'archer.json'),'clips':manifest};(M/'pack.json').write_text(json.dumps(report,indent=2));(R/'review/3d-v2/archer-pack.json').write_text(json.dumps({k:v for k,v in report.items() if k!='clips'},indent=2))
print('PACKED',len(encoded),'bytes, quality',quality,atlas.size,'40 frames')
