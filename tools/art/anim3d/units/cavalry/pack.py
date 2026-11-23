"""40 frames, 160px logical cells, per-frame trim rectangles and anchor offsets."""
import os,json,hashlib,io
from pathlib import Path
from PIL import Image
R=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')));M=R/'masters/cavalry';V=R/'review/3d-v2';O=Path('app/src/assets/units/anim');O.mkdir(parents=True,exist_ok=True)
CLIPS={'idle':(8,10,True),'move':(8,12,True),'attack':(10,14,False),'hit':(4,12,False),'death':(10,10,False)}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
meta={'version':2,'frame':{'w':160,'h':160,'ax':87,'ay':141},'clips':{},'trimmed':True};rows=[];sources={};source_hashes={};y=0
for row,(clip,(count,fps,loop)) in enumerate(CLIPS.items()):
 folder=M/'renders'/f'e-{clip}';info=json.loads((folder/'render.json').read_text());blend=M/'clips'/f'{clip}.blend';clipinfo=json.loads((M/'clips'/f'{clip}.json').read_text())
 assert info['blend_sha256']==sha(blend),f'Stale {clip} render'
 assert clipinfo['source_master_sha256']==sha(M/'cavalry.blend'),f'Stale {clip} rig'
 assert info['grade_sha256']==sha(M/'grade.json'),f'Stale {clip} grade'
 assert len(info['frames'])==count
 if os.environ.get('REQUIRE_MASTERS')=='1':assert info['resolution']==512,f'{clip} must be genuine 512px GPU masters'
 x=0;height=0;images=[];rects=[]
 for i in range(count):
  p=folder/f'{i:02}.png';im=Image.open(p).convert('RGBA');source_hashes[f'{clip}/{i}']=sha(p)
  # Keep actual native master resolution, never claim an upsample is a master.
  native=M/str(im.width)/clip;native.mkdir(parents=True,exist_ok=True);im.save(native/f'{i:02}.png')
  smaller=M/'256'/clip;smaller.mkdir(parents=True,exist_ok=True);im.resize((256,256),Image.Resampling.LANCZOS).save(smaller/f'{i:02}.png')
  im=im.resize((160,160),Image.Resampling.LANCZOS)
  a=im.getchannel('A').point(lambda a:round(round(a*31/255)*255/31));im.putalpha(a);im.paste((0,0,0,0),mask=a.point(lambda a:255 if a==0 else 0))
  b=a.getbbox();assert b,f'Empty {clip}/{i}'
  assert b[0]>0 and b[1]>0 and b[2]<160 and b[3]<160,f'Clipped frame {clip}/{i}: {b}'
  crop=im.crop(b);rects.append({'x':x,'y':y,'w':crop.width,'h':crop.height,'ox':b[0],'oy':b[1]});images.append((x,y,crop));x+=crop.width+2;height=max(height,crop.height)
 meta['clips'][clip]={'row':row,'frames':count,'fps':fps,'loop':loop,'rects':rects};rows.append((x,images));y+=height+2;sources[clip]=info
atlas=Image.new('RGBA',(max(w for w,_ in rows),y))
for _,imgs in rows:
 for x,y,im in imgs:atlas.paste(im,(x,y))
for quality in [90,85,80,75]:
 b=io.BytesIO();atlas.save(b,format='WEBP',quality=quality,method=6,exact=True)
 if len(b.getvalue())<=200000:break
else:raise RuntimeError('Atlas exceeds 200,000 bytes at q75; keep frames and report, never silently reduce quality.')
(O/'cavalry.webp').write_bytes(b.getvalue());(O/'cavalry.json').write_text(json.dumps(meta,separators=(',',':'))+'\n')
report={'quality':quality,'bytes':len(b.getvalue()),'frames':40,'dimensions':atlas.size,'logical_cell':160,'atlas_sha256':sha(O/'cavalry.webp'),'json_sha256':sha(O/'cavalry.json'),'sources':sources,'source_sha256':source_hashes}
(V/'cavalry-pack.json').write_text(json.dumps(report,indent=2)+'\n');print('PACK',report['bytes'],'bytes, quality',quality)
