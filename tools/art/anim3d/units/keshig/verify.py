"""Independent decoded-atlas, source provenance and encoded-movie checks."""
import hashlib,json,os,subprocess,sys
from pathlib import Path
from PIL import Image,ImageChops
R=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')))
M=R/'masters/keshig';Q=R/'review/3d-v2';out=Path('app/src/assets/units/anim/keshig.webp')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
report=json.loads((Q/'keshig-validation.json').read_text());meta=json.loads(out.with_suffix('.json').read_text());atlas=Image.open(out).convert('RGBA')
assert out.stat().st_size<=200000 and report['bytes']==out.stat().st_size
assert meta['quality']==report['quality']>=75
assert report['atlas_sha256']==sha(out) and report['master_sha256']==sha(M/'keshig.blend')
assert report['grade_sha256']==sha(M/'grade.json')
assert meta['frame']['w']==meta['frame']['h']==160 and meta['atlas']=={'w':atlas.width,'h':atlas.height}
assert list(meta['clips'])==['idle','move','attack','hit','death']
if '--gpu' in sys.argv:
 for stage,file in [('b-plain',M/'plain.blend'),('c-textured-lit',M/'keshig.blend'),('d-rig-poses',M/'clips/attack.blend')]+[(f'e-{n}',M/f'clips/{n}.blend') for n in meta['clips']]:
  s=json.loads((M/f'renders/{stage}/manifest.json').read_text())
  assert (s['engine'],s['device'],s['resolution'],s['samples'])==('CYCLES','GPU',512,64),(stage,'GPU512/64 required')
  assert s['blend_sha256']==sha(file),(stage,'stale render')
for lockname in ['assets.lock.json','motion.lock.json']:
 lock=json.loads((Path(__file__).parent/lockname).read_text())
 for path,digest in lock['files'].items():assert sha(R/path)==digest,(path,'source changed')
if '--gpu' in sys.argv:
 feet=json.loads((M/'feet/manifest.json').read_text());assert feet['device']=='GPU' and feet['engine']=='CYCLES' and feet['blend_sha256']==sha(M/'clips/move.blend')
 for stage,count in [('b-plain',1),('c-textured-lit',1),('d-rig-poses',4)]:
  for size in [512,256]:
   for i in range(count):assert Image.open(M/f'{size}/{stage}/{i:03}.png').size==(size,size)
checks=[]
for name,count in zip(meta['clips'],[8,8,10,4,10]):
 c=meta['clips'][name];assert c['frames']==count==len(c['rects']);frames=[]
 manifest=json.loads((M/f'renders/e-{name}/manifest.json').read_text())
 assert manifest['master_sha256']==sha(M/'keshig.blend') and manifest['blend_sha256']==sha(M/f'clips/{name}.blend')
 for i,r in enumerate(c['rects']):
  x,y,w,h,ox,oy=[r[k] for k in ['x','y','w','h','ox','oy']]
  assert 1<=x and 1<=y and x+w<atlas.width and y+h<atlas.height
  assert 1<=ox and 1<=oy and ox+w<160 and oy+h<160
  for box in [(x-1,y-1,x+w+1,y),(x-1,y+h,x+w+1,y+h+1),(x-1,y,x,y+h),(x+w,y,x+w+1,y+h)]:assert atlas.crop(box).getchannel('A').getbbox() is None
  im=Image.new('RGBA',(160,160));im.paste(atlas.crop((x,y,x+w,y+h)),(ox,oy));frames.append(im)
  raw=M/f'renders/e-{name}/{i:03}.png';assert report['source_frames'][f'{name}/{i}']==sha(raw)
  source=Image.open(raw).convert('RGBA').resize((256,256),Image.Resampling.LANCZOS).resize((160,160),Image.Resampling.BICUBIC)
  assert source.getchannel('A').tobytes()==im.getchannel('A').tobytes(),(name,i,'alpha reconstruction')
  assert Image.open(M/f'256/{name}/{i:03}.png').size==(256,256)
  if '--gpu' in sys.argv:assert Image.open(M/f'512/{name}/{i:03}.png').size==(512,512)
 assert any(ImageChops.difference(frames[0],f).convert('RGB').getbbox() for f in frames[1:]),name
 if name=='death':assert frames[-1].tobytes()==frames[-2].tobytes()
 checks.append(name)
round_id=os.environ.get('ROUND','1');movie=Q/f'keshig-round{round_id}.mp4'
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=codec_name,pix_fmt,width,height,nb_frames,duration','-of','json',str(movie)]))['streams'][0]
assert (probe['codec_name'],probe['pix_fmt'],probe['width'],probe['height'],int(probe['nb_frames']))==('h264','yuv420p',1600,348,240)
assert abs(float(probe['duration'])-8)<.01
result={'round':round_id,'checks':checks,'frames':40,'bytes':report['bytes'],'quality':report['quality'],'lossless_alpha':True,'held_death_exact':True,'movie':probe,'master_sha256':report['master_sha256'],'art_pass':False}
if '--gpu' in sys.argv:(Q/f'keshig-gpu-round{round_id}.json').write_text(json.dumps(result,indent=2)+'\n')
print('KESHIG_DELIVERY_VERIFIED',json.dumps(result))
