"""Trim 160px frames into five compact rows; preserve full alpha and timing."""
from pathlib import Path
import os, json, hashlib, io, sys, shutil
from PIL import Image

R=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')))
M=R/'masters/barbarian-spearman';O=Path('app/src/assets/units/anim');O.mkdir(parents=True,exist_ok=True)
CLIPS={'idle':(8,10,True),'move':(8,12,True),'attack':(10,14,False),'hit':(4,12,False),'death':(10,10,False)}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
preview='--preview' in sys.argv
source=sha(M/'barbarian-spearman.blend');grade=sha(M/'grade.json')
rest=json.loads((M/'renders/c/render.json').read_text())
assert rest['blend_sha256']==source and rest['grade_sha256']==grade,'Stale rest/grade'
settings=tuple(rest[k] for k in ['engine','device','resolution','samples'])
meta={'version':2,'unit':'barbarian-spearman','frame':{'w':160,'h':160,'ax':80,'ay':137},'clips':{}}
report={'source_sha256':source,'grade_sha256':grade,'frames':{},'renders':{},'preview':preview,'resampler':'BICUBIC','alpha':'lossless 8-bit'}
placements=[];y=2;atlas_width=0
for row,(clip,(count,fps,loop)) in enumerate(CLIPS.items()):
 folder=M/'renders'/f'e-{clip}';manifest=json.loads((folder/'render.json').read_text())
 assert manifest['blend_sha256']==sha(M/'clips'/f'{clip}.blend'),'Stale clip render'
 assert manifest['source_sha256']==source and manifest['grade_sha256']==grade,'Stale source/grade'
 assert tuple(manifest[k] for k in ['engine','device','resolution','samples'])==settings,'Mixed render settings'
 assert manifest['resolution'] in ([256,512] if preview else [512]),'Final masters must be rendered at 512'
 paths=sorted(folder.glob('[0-9][0-9].png'));assert len(paths)==count
 report['renders'][clip]=manifest;rects=[];x=2;height=0;unique={}
 for i,p in enumerate(paths):
  im=Image.open(p).convert('RGBA');assert im.size==(manifest['resolution'],)*2
  bounds=im.getchannel('A').point(lambda a:255 if a>8 else 0).getbbox()
  assert bounds and min(bounds[:2])>0 and max(bounds[2:])<im.width,f'Clipped frame: {clip}/{i}: {bounds}'
  for size in [n for n in [512,256] if n<=im.width]:
   dest=M/str(size)/clip;dest.mkdir(parents=True,exist_ok=True);im.resize((size,size),Image.Resampling.LANCZOS).save(dest/f'{i:02}.png')
  small=im.resize((160,160),Image.Resampling.BICUBIC);box=small.getchannel('A').getbbox();assert box
  ox,oy,x1,y1=box;w=x1-ox;h=y1-oy;digest=hashlib.sha256(small.tobytes()).hexdigest()
  if digest in unique:rect=unique[digest].copy()
  else:
   rect={'x':x,'y':y,'w':w,'h':h,'ox':ox,'oy':oy};unique[digest]=rect
   placements.append((small.crop(box),(x,y)));x+=w+4;height=max(height,h)
  rects.append(rect);report['frames'][f'{clip}/{i:02}']=sha(p)
 meta['clips'][clip]={'row':row,'frames':count,'fps':fps,'loop':loop,'rects':rects}
 y+=height+4;atlas_width=max(atlas_width,x)
atlas=Image.new('RGBA',(atlas_width,y));meta['atlas']={'w':atlas.width,'h':atlas.height}
for crop,position in placements:atlas.paste(crop,position)
for stage in ['b','c','c-details','d']:
 for p in sorted((M/'renders'/stage).glob('[0-9][0-9].png')):
  im=Image.open(p).convert('RGBA');assert preview or im.size==(512,512)
  for size in [n for n in [512,256] if n<=im.width]:
   dest=M/str(size)/stage;dest.mkdir(parents=True,exist_ok=True);im.resize((size,size),Image.Resampling.LANCZOS).save(dest/p.name)
attempts={}
for quality in [90,85,80,75]:
 buf=io.BytesIO();atlas.save(buf,format='WEBP',quality=quality,method=6,exact=True);attempts[quality]=len(buf.getvalue())
 if len(buf.getvalue())<=200000:break
else:raise RuntimeError(f'Atlas exceeds 200000 bytes; no quality/frame reduction: {attempts}')
path=O/'barbarian-spearman.webp';path.write_bytes(buf.getvalue());path.with_suffix('.json').write_text(json.dumps(meta,indent=2)+'\n')
report.update(quality=quality,bytes=path.stat().st_size,atlas_sha256=sha(path),metadata_sha256=sha(path.with_suffix('.json')),attempts=attempts,unique_rectangles=len(placements))
(M/'pack.json').write_text(json.dumps(report,indent=2)+'\n')
print('PACK_READY',report['bytes'],'bytes, quality',quality,'preview',preview)
