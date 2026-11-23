"""Pack all 40 frames into the agreed WebP grid, without reducing frame counts."""
import os,json,io,hashlib
from pathlib import Path
from PIL import Image
ROOT=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')))
M=ROOT/'masters/spearman-3d-v2';R=ROOT/'review/3d-v2'
CLIPS={'idle':(8,10,True),'move':(8,12,True),'attack':(10,14,False),'hit':(4,12,False),'death':(10,10,False)}
out=Path('app/src/assets/units/anim');out.mkdir(parents=True,exist_ok=True)
atlas=Image.new('RGBA',(2560,1280));meta={'frame':{'w':256,'h':256,'ax':127,'ay':221},'clips':{}};hashes={}
for row,(clip,(n,fps,loop)) in enumerate(CLIPS.items()):
 meta['clips'][clip]={'row':row,'frames':n,'fps':fps,'loop':loop}
 files=[M/'renders'/('e-'+clip)/(f'{i:02}.png') for i in range(n)]
 assert all(p.exists() for p in files),f'Missing frames for {clip}'
 for i,p in enumerate(files):
  im=Image.open(p).convert('RGBA').resize((256,256),Image.Resampling.LANCZOS)
  # Quantize alpha only within the contract tolerance; retain every source frame.
  a=im.getchannel('A').point(lambda x:round(round(x*31/255)*255/31));im.putalpha(a)
  im.paste((0,0,0,0),mask=a.point(lambda x:255 if x==0 else 0))
  atlas.paste(im,(i*256,row*256));hashes[f'{clip}/{i}']=hashlib.sha256(p.read_bytes()).hexdigest()
for quality in [85,80,75,70,65,60]:
 b=io.BytesIO();atlas.save(b,format='WEBP',quality=quality,method=6,exact=True)
 if len(b.getvalue())<=200000:break
else:raise RuntimeError('40-frame atlas exceeds 200 KB at quality 60; do not silently degrade')
(out/'spearman.webp').write_bytes(b.getvalue());(out/'spearman.json').write_text(json.dumps(meta,separators=(',',':'))+'\n')
report={'bytes':len(b.getvalue()),'quality':quality,'frames':40,'engine':os.environ.get('RENDER_ENGINE','CYCLES CPU preview'),'source_sha256':hashes,'atlas_sha256':hashlib.sha256(b.getvalue()).hexdigest()}
(R/'pack.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='source_sha256'},indent=2))
