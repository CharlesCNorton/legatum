"""Pack all 40 frames into the agreed WebP grid, without reducing frame counts."""
import os,json,io,hashlib
from pathlib import Path
from PIL import Image
ROOT=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')))
M=ROOT/'masters/horseman-3d';R=ROOT/'review/3d-v2'
CLIPS={'idle':(8,10,True),'move':(8,12,True),'attack':(10,14,False),'hit':(4,12,False),'death':(10,10,False)}
out=Path('app/src/assets/units/anim');out.mkdir(parents=True,exist_ok=True)
atlas=Image.new('RGBA',(2560,1280));meta={'frame':{'w':256,'h':256,'ax':127,'ay':221},'clips':{}};hashes={};renders={}
for row,(clip,(n,fps,loop)) in enumerate(CLIPS.items()):
 meta['clips'][clip]={'row':row,'frames':n,'fps':fps,'loop':loop}
 renders[clip]=json.loads((M/'renders'/('e-'+clip)/'render.json').read_text())
 files=[M/'renders'/('e-'+clip)/(f'{i:02}.png') for i in range(n)]
 assert all(p.exists() for p in files),f'Missing frames for {clip}'
 for i,p in enumerate(files):
  im=Image.open(p).convert('RGBA').resize((256,256),Image.Resampling.LANCZOS)
  # Quantize alpha only within the contract tolerance; retain every source frame.
  a=im.getchannel('A').point(lambda x:round(round(x*15/255)*255/15));im.putalpha(a)
  im.paste((0,0,0,0),mask=a.point(lambda x:255 if x==0 else 0))
  atlas.paste(im,(i*256,row*256));hashes[f'{clip}/{i}']=hashlib.sha256(p.read_bytes()).hexdigest()
grade_hash=hashlib.sha256((M/'grade.json').read_bytes()).hexdigest()
assert all(r.get('grade_sha256')==grade_hash for r in renders.values()), 'Rerender every clip after changing the rest colour grade'
assert len(set(r['engine'] for r in renders.values()))==1, 'Mixed render engines in delivery'
for clip,r in renders.items():
 assert r['blend_sha256']==hashlib.sha256((M/'clips'/f'{clip}.blend').read_bytes()).hexdigest(),f'Stale clip render: {clip}'
for quality in [85,80,75,70,65,60,59,58,57,55]:
 b=io.BytesIO();atlas.save(b,format='WEBP',quality=quality,method=6,exact=True)
 if len(b.getvalue())<=200000:break
else:raise RuntimeError('40-frame atlas exceeds 200 KB at quality 55; do not silently degrade')
(out/'horseman.webp').write_bytes(b.getvalue());(out/'horseman.json').write_text(json.dumps(meta,separators=(',',':'))+'\n')
report={'bytes':len(b.getvalue()),'quality':quality,'alpha_levels':16,'frames':40,'engine':sorted(set(r['engine'] for r in renders.values())),'renders':renders,'source_sha256':hashes,'atlas_sha256':hashlib.sha256(b.getvalue()).hexdigest()}
(R/'horseman-pack.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='source_sha256'},indent=2))
