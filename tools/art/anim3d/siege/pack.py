"""Pack all 40 frames into the agreed WebP grid, without reducing frame counts."""
import os,json,io,hashlib
from pathlib import Path
from PIL import Image
ROOT=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')))
M=ROOT/'masters/field-cannon';R=ROOT/'review/3d-v2'
CLIPS={'idle':(8,10,True),'move':(8,12,True),'attack':(10,14,False),'hit':(4,12,False),'death':(10,10,False)}
out=Path('app/src/assets/units/anim');out.mkdir(parents=True,exist_ok=True)
atlas=Image.new('RGBA',(2560,1280));meta={'frame':{'w':256,'h':256,'ax':127,'ay':221},'clips':{}};hashes={};render_sources={}
for row,(clip,(n,fps,loop)) in enumerate(CLIPS.items()):
 meta['clips'][clip]={'row':row,'frames':n,'fps':fps,'loop':loop}
 render_dir=M/'renders'/('e-'+clip)
 rendered=json.loads((render_dir/'render.json').read_text())
 blend=M/'clips'/(clip+'.blend')
 assert rendered['blend_sha256']==hashlib.sha256(blend.read_bytes()).hexdigest(),f'{clip}: render is stale'
 clip_info=json.loads((blend.with_suffix('.json')).read_text())
 assert clip_info['source_master_sha256']==hashlib.sha256((M/'field-cannon.blend').read_bytes()).hexdigest(),f'{clip}: clip is stale'
 render_sources[clip]=rendered
 files=[M/'renders'/('e-'+clip)/(f'{i:02}.png') for i in range(n)]
 assert all(p.exists() for p in files),f'Missing frames for {clip}'
 for i,p in enumerate(files):
  im=Image.open(p).convert('RGBA').resize((256,256),Image.Resampling.LANCZOS)
  # Quantize alpha only within the contract tolerance; retain every source frame.
  a=im.getchannel('A').point(lambda x:round(round(x*31/255)*255/31));im.putalpha(a)
  im.paste((0,0,0,0),mask=a.point(lambda x:255 if x==0 else 0))
  atlas.paste(im,(i*256,row*256));hashes[f'{clip}/{i}']=hashlib.sha256(p.read_bytes()).hexdigest()
attempts={}
for quality in [85,80,75,70,65,60,55,50,45,40]:
 b=io.BytesIO();atlas.save(b,format='WEBP',quality=quality,method=6,exact=True)
 attempts[quality]=len(b.getvalue())
 if len(b.getvalue())<=200000:break
else:raise RuntimeError('40-frame atlas exceeds 200 KB at quality 40; do not silently degrade')
(out/'field-cannon.webp').write_bytes(b.getvalue());(out/'field-cannon.json').write_text(json.dumps(meta,separators=(',',':'))+'\n')
report={'bytes':len(b.getvalue()),'quality':quality,'quality_search_bytes':attempts,'frames':40,'engines':sorted({r['engine'] for r in render_sources.values()}),'render_sources':render_sources,'source_sha256':hashes,'atlas_sha256':hashlib.sha256(b.getvalue()).hexdigest()}
(R/'field-cannon-pack.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k not in ['source_sha256','render_sources']},indent=2))
