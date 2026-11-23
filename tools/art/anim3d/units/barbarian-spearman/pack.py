"""160px trimmed-per-frame atlas; 512 and 256 masters are retained externally."""
from pathlib import Path
import os,json,hashlib,io
from PIL import Image,ImageChops
R=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')));M=R/'masters/barbarian-spearman';O=Path('app/src/assets/units/anim');O.mkdir(parents=True,exist_ok=True)
CLIPS={'idle':(8,10,True),'move':(8,12,True),'attack':(10,14,False),'hit':(4,12,False),'death':(10,10,False)}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
source=sha(M/'barbarian-spearman.blend');grade=sha(M/'grade.json');atlas=Image.new('RGBA',(1600,800));meta={'version':2,'unit':'barbarian-spearman','frame':{'w':160,'h':160,'ax':80,'ay':137},'clips':{}};report={'source_sha256':source,'grade_sha256':grade,'frames':{},'renders':{}}
for row,(clip,(count,fps,loop)) in enumerate(CLIPS.items()):
 folder=M/'renders'/f'e-{clip}';manifest=json.loads((folder/'render.json').read_text());assert manifest['blend_sha256']==sha(M/'clips'/f'{clip}.blend'),'Stale clip render';assert manifest['source_sha256']==source,'Stale source model';assert manifest['grade_sha256']==grade,'Mixed grade';assert manifest['resolution']==512,'Master must be rendered at 512'
 paths=sorted(folder.glob('[0-9][0-9].png'));assert len(paths)==count
 report['renders'][clip]=manifest;offsets=[]
 for i,p in enumerate(paths):
  im=Image.open(p).convert('RGBA');assert im.size==(512,512)
  bounds=im.getchannel('A').point(lambda a:255 if a>8 else 0).getbbox()
  assert bounds and min(bounds[:2])>0 and max(bounds[2:])<512,f'Clipped frame: {p.name} in {clip}'
  for size in [512,256]:
   dest=M/str(size)/clip;dest.mkdir(parents=True,exist_ok=True);im.resize((size,size),Image.Resampling.LANCZOS).save(dest/f'{i:02}.png')
  small=im.resize((160,160),Image.Resampling.LANCZOS);alpha=small.getchannel('A').point(lambda a:round(a/8)*8 if a<248 else 255);small.putalpha(alpha)
  box=alpha.getbbox();assert box; x,y,x1,y1=box;w=x1-x;h=y1-y
  atlas.paste(small.crop(box),(i*160,row*160));offsets.append({'x':i*160,'y':row*160,'w':w,'h':h,'ox':x,'oy':y})
  report['frames'][f'{clip}/{i:02}']=sha(p)
 meta['clips'][clip]={'row':row,'frames':count,'fps':fps,'loop':loop,'rects':offsets}
# Keep review-stage masters at both sizes as well as every clip.
for stage in ['b','c','c-details','d']:
 for p in sorted((M/'renders'/stage).glob('[0-9][0-9].png')):
  im=Image.open(p).convert('RGBA');assert im.size==(512,512)
  for size in [512,256]:
   dest=M/str(size)/stage;dest.mkdir(parents=True,exist_ok=True);im.resize((size,size),Image.Resampling.LANCZOS).save(dest/p.name)
for quality in [90,85,80,75]:
 buf=io.BytesIO();atlas.save(buf,format='WEBP',quality=quality,method=6,exact=True)
 if len(buf.getvalue())<=200000:break
else:raise RuntimeError('Atlas exceeds 200000 bytes at quality 75; frames and quality were preserved')
path=O/'barbarian-spearman.webp';path.write_bytes(buf.getvalue());(O/'barbarian-spearman.json').write_text(json.dumps(meta,indent=2)+'\n')
report.update(quality=quality,bytes=path.stat().st_size,atlas_sha256=sha(path));(M/'pack.json').write_text(json.dumps(report,indent=2)+'\n')
print('PACK_READY',report['bytes'],'bytes, quality',quality)
