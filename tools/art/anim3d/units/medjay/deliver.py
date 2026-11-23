"""Grade, review, trim, validate and encode Medjay. Python + Pillow, no Blender."""
import os, sys, json, hashlib, subprocess, tempfile, math
from pathlib import Path
from PIL import Image, ImageDraw, ImageChops
ROOT=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')));M=ROOT/'masters/medjay';R=ROOT/'review/3d-v2';OUT=Path('app/src/assets/units/anim');OUT.mkdir(parents=True,exist_ok=True)
CLIPS={'idle':(8,10,True),'move':(8,12,True),'attack':(10,14,False),'hit':(4,12,False),'death':(10,10,False)};CREAM=(233,207,160,255)
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def log(s):
 with (R/'medjay-log.md').open('a') as f:f.write(s+'\n')
 print(s)
def read(p):return Image.open(p).convert('RGBA')
def ref():return read(Path('app/src/assets/units/medjay-256.png'))
def over(im):
 out=Image.new('RGBA',im.size,CREAM);out.alpha_composite(im);return out

def histq(im,c):
 h=im.getchannel(c).histogram(mask=im.getchannel('A').point(lambda x:255 if x>128 else 0));total=sum(h);out=[]
 for q in [.02+i*.96/16 for i in range(17)]:
  acc=0
  for v,n in enumerate(h):
   acc+=n
   if acc>=total*q:out.append(v);break
 return out

def calibrate(im):
 tables=[];stats={}
 for c in 'RGB':
  a=histq(im,c);b=histq(ref(),c);lut=[]
  for x in range(256):
   if x<=a[0]:target=x+b[0]-a[0]
   elif x>=a[-1]:target=x+b[-1]-a[-1]
   else:
    k=next(i for i in range(16) if a[i]<=x<=a[i+1]);t=(x-a[k])/max(1,a[k+1]-a[k]);target=b[k]+t*(b[k+1]-b[k])
   lut.append(round(max(0,min(255,x+max(-24,min(24,(target-x)*.55))))))
  tables.append(lut);stats[c]={'render':a,'painting':b}
 (M/'grade.json').write_text(json.dumps({'method':'17 foreground quantiles; frozen bounded 55% transfer','luts':tables,'quantiles':stats},indent=2));return tables

def sheet(images,labels,path,cell=256):
 canvas=Image.new('RGBA',(cell*len(images),cell+108),CREAM);d=ImageDraw.Draw(canvas)
 for i,(im,label) in enumerate(zip(images,labels)):
  canvas.alpha_composite(im.resize((cell,cell),Image.Resampling.LANCZOS),(i*cell,24));d.text((i*cell+8,5),label,fill='#493723');canvas.alpha_composite(im.resize((64,64),Image.Resampling.LANCZOS),(i*cell+96,cell+38))
 canvas.convert('RGB').save(path)

def review(stage):
 folder=M/'renders'/stage;meta=json.loads((folder/'render.json').read_text());paths=[folder/f'{i:02d}.png' for i in range(len(meta['frames']))]
 for p in paths:assert digest(p)==meta['sha256'][p.name],'Raw frame changed: '+str(p)
 ims=[read(p) for p in paths]
 if stage!='b':
  tables=calibrate(ims[0]) if stage=='c' else json.loads((M/'grade.json').read_text())['luts'];ims=[Image.merge('RGBA',[im.getchannel(c).point(lut) for c,lut in zip('RGB',tables)]+[im.getchannel('A')]) for im in ims]
 graded=folder/'graded';graded.mkdir(exist_ok=True)
 for i,im in enumerate(ims):
  im.save(graded/f'{i:02d}.png')
  size=im.width
  for resolution in [256,512]:
   if size>=resolution:
    dest=M/str(resolution)/stage;dest.mkdir(parents=True,exist_ok=True);im.resize((resolution,resolution),Image.Resampling.LANCZOS).save(dest/f'{i:02d}.png')
 (folder/'review.json').write_text(json.dumps({'grade_sha256':None if stage=='b' else digest(M/'grade.json'),'raw_manifest_sha256':digest(folder/'render.json'),'graded_sha256':{f'{i:02d}.png':digest(graded/f'{i:02d}.png') for i in range(len(ims))}},indent=2))
 kind={'b':'b-plain','c':'c-textured-lit','d':'d-rig-poses','c-details':'c-details'}.get(stage,stage+'-strip')
 if stage=='c-details':
  crops=[(105,24,153,73),(105,59,155,111),(143,53,194,158),(104,93,158,154)];images=[];labels=[]
  for n,box in zip(['face','torso','shield','linen'],crops):
   for label,im in [('painting',ref()),('3D',ims[0].resize((256,256),Image.Resampling.LANCZOS))]:images.append(im.crop(box).resize((256,256),Image.Resampling.LANCZOS));labels.append(n+' '+label)
  sheet(images,labels,R/f'medjay-{kind}.png')
 else:sheet([ref()]+ims,['painting']+[stage+f' {i+1}' for i in range(len(ims))],R/f'medjay-{kind}.png')
 if stage=='c':
  actual=ims[0].resize((256,256),Image.Resampling.LANCZOS);painting=ref();half=painting.copy();half.paste(actual.crop((128,0,256,256)),(128,0));cross=Image.blend(over(painting),over(actual),.5)
  sheet([painting,actual,half,cross],['painting','3D rest','half split','50/50 crossfade'],R/'medjay-f-restpose-compare.png')
 if stage.startswith('e-'):
  clip=stage[2:];n,fps,_=CLIPS[clip];frames=[over(im.resize((256,256),Image.Resampling.LANCZOS)) for im in ims];frames[0].save(R/f'medjay-{stage}.webp',save_all=True,append_images=frames[1:],duration=round(1000/fps),loop=0,quality=85,method=6)
 log(f'Published {kind} review immediately; source {meta["engine"]}/{meta["device"]}, {meta["resolution"]}px.')

def pack():
 grade_sha=digest(M/'grade.json');meta={'version':2,'format':'trimmed-rows','frame':{'w':160,'h':160,'ax':84,'ay':141},'clips':{}};allrows=[];report={'grade_sha256':grade_sha,'sources':{}};maxw=0;totalh=0
 for row,(clip,(count,fps,loop)) in enumerate(CLIPS.items()):
  folder=M/'renders'/('e-'+clip);manifest=json.loads((folder/'render.json').read_text());assert digest(Path(manifest['blend']))==manifest['blend_sha256'],'Stale clip render';clipdata=json.loads((M/f'{clip}.json').read_text());assert clipdata['master_sha256']==digest(M/'medjay.blend'),'Stale animation master';assert len(manifest['frames'])==count
  rest=json.loads((M/'renders/c/render.json').read_text());assert rest['blend_sha256']==digest(M/'medjay.blend'),'Stale rest calibration'
  assert all(manifest[k]==rest[k] for k in ('engine','device','resolution','samples')),'Mixed render settings'
  review_meta=json.loads((folder/'review.json').read_text());assert review_meta['grade_sha256']==grade_sha,'Stale clip grade';assert review_meta['raw_manifest_sha256']==digest(folder/'render.json'),'Stale review'
  entries=[];x=0;rowh=0;frames=[];unique={}
  for i in range(count):
   raw=folder/f'{i:02d}.png';assert digest(raw)==manifest['sha256'][raw.name]
   graded_path=folder/'graded'/f'{i:02d}.png';assert digest(graded_path)==review_meta['graded_sha256'][graded_path.name];im=read(graded_path);assert im.width>=256
   im=im.resize((160,160),Image.Resampling.BICUBIC);box=im.getchannel('A').getbbox();assert box;ox,oy,x1,y1=box;w=x1-ox;h=y1-oy;assert min(ox,oy)>=1 and x1<=159 and y1<=159,(clip,i,'clipped frame',box)
   tile=im.crop(box);key=im.tobytes()
   if key in unique:
    entries.append(unique[key].copy());frames.append(tile);continue
   entry={'x':x,'y':totalh,'w':w,'h':h,'ox':ox,'oy':oy};unique[key]=entry;entries.append(entry);frames.append(tile);x+=w+2;rowh=max(rowh,h)
  meta['clips'][clip]={'row':row,'frames':count,'fps':fps,'loop':loop,'rects':entries};allrows.append((frames,entries));maxw=max(maxw,x);totalh+=rowh+2;report['sources'][clip]=manifest
 atlas=Image.new('RGBA',(maxw,totalh))
 for frames,entries in allrows:
  for tile,e in zip(frames,entries):atlas.paste(tile,(e['x'],e['y']))
 path=OUT/'medjay.webp';temp=M/'candidate.webp'
 for q in [90,85,80,75]:
  atlas.save(temp,format='WEBP',quality=q,method=6)
  if temp.stat().st_size<=200000:break
 else:raise RuntimeError('Atlas exceeds 200 KB at quality 75; no frame dropping or further degradation')
 path.write_bytes(temp.read_bytes());(OUT/'medjay.json').write_text(json.dumps(meta,indent=2)+'\n');report.update(quality=q,bytes=path.stat().st_size,atlas_sha256=digest(path),atlas_size=atlas.size);(M/'pack.json').write_text(json.dumps(report,indent=2));log(f'Packed 40 trimmed 160px frames at quality {q}: {path.stat().st_size} bytes.');validate()

def reconstruct(atlas,clip,i):
 e=clip['rects'][i];tile=atlas.crop((e['x'],e['y'],e['x']+e['w'],e['y']+e['h']));im=Image.new('RGBA',(160,160));im.paste(tile,(e['ox'],e['oy']));return im

def validate():
 path=OUT/'medjay.webp';atlas=read(path);meta=json.loads(path.with_suffix('.json').read_text());report=json.loads((M/'pack.json').read_text());assert path.stat().st_size<=200000;assert atlas.getchannel('A').getextrema()==(0,255);assert report['quality']>=75;assert report['atlas_sha256']==digest(path);assert report['grade_sha256']==digest(M/'grade.json');assert meta['frame']=={'w':160,'h':160,'ax':84,'ay':141};checks={}
 for name,(n,fps,loop) in CLIPS.items():
  c=meta['clips'][name];assert (c['frames'],c['fps'],c['loop'])==(n,fps,loop);assert len(c['rects'])==n
  for e in c['rects']:
   assert 0<=e['x']<e['x']+e['w']<=atlas.width and 0<=e['y']<e['y']+e['h']<=atlas.height;assert 0<=e['ox']<e['ox']+e['w']<=160 and 0<=e['oy']<e['oy']+e['h']<=160
  source=M/'renders'/('e-'+name);m=report['sources'][name];assert digest(Path(m['blend']))==m['blend_sha256'];frames=[read(source/'graded'/f'{i:02d}.png') for i in range(n)];assert len({im.tobytes() for im in frames})>=3
  if name=='death':
   assert frames[-1].tobytes()==frames[-2].tobytes(),'Death not held'
   assert reconstruct(atlas,c,n-1).tobytes()==reconstruct(atlas,c,n-2).tobytes(),'Decoded death not held'
  for size in (size for size in (256,512) if size<=m['resolution']):
   retained=[M/str(size)/('e-'+name)/f'{i:02d}.png' for i in range(n)]
   assert all(p.exists() and Image.open(p).size==(size,size) for p in retained),'Missing master size'
   for p,frame in zip(retained,frames):assert read(p).tobytes()==frame.resize((size,size),Image.Resampling.LANCZOS).tobytes(),'Stale retained master'
  for i,frame in enumerate(frames):
   expected=frame.resize((160,160),Image.Resampling.BICUBIC)
   actual=reconstruct(atlas,c,i)
   assert actual.getchannel('A').tobytes()==expected.getchannel('A').tobytes(),(name,i,'decoded alpha differs')
   assert digest(source/'graded'/f'{i:02d}.png')==json.loads((source/'review.json').read_text())['graded_sha256'][f'{i:02d}.png']
  checks[name]={'frames':n,'moving':True,'trim_rectangles_valid':True,'lossless_alpha':True}
 (M/'validation.json').write_text(json.dumps({'status':'pass','bytes':path.stat().st_size,'quality':report['quality'],'clips':checks,'art_approved':False,'preview':any(x['device']!='GPU' for x in report['sources'].values())},indent=2));log('Validation passed: 40 frames, motion in five clips, held death, transparent trimmed geometry, >=75 quality and <=200 KB. Art parity remains a visual judgment.')

def video():
 atlas=read(OUT/'medjay.webp');meta=json.loads((OUT/'medjay.json').read_text());out=R/f'medjay-round{os.environ.get("ROUND","2")}.mp4';frames={name:[reconstruct(atlas,meta['clips'][name],i).resize((320,320),Image.Resampling.LANCZOS) for i in range(n)] for name,(n,_,_) in CLIPS.items()}
 with tempfile.TemporaryDirectory(dir=ROOT/'tmp',prefix='medjay-video-') as tmp:
  for t in range(240):
   canvas=Image.new('RGBA',(1600,348),CREAM);draw=ImageDraw.Draw(canvas)
   for k,(name,(n,fps,loop)) in enumerate(CLIPS.items()):
    i=int(t/30*fps)%n if loop else min(int((t%60)/30*fps),n-1);canvas.alpha_composite(frames[name][i],(k*320,28));draw.text((k*320+10,8),name,fill='#493723')
   canvas.convert('RGB').save(Path(tmp)/f'{t:04d}.png')
  subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate','30','-i',str(Path(tmp)/'%04d.png'),'-c:v','libx264','-threads','3','-pix_fmt','yuv420p','-crf','20','-movflags','+faststart',str(out)],check=True)
 probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(out)]));v=probe['streams'][0];assert v['codec_name']=='h264' and v['pix_fmt']=='yuv420p' and int(v['nb_frames'])==240;log(f'Encoded {out.name}: all five clips, 1600x348, H.264 yuv420p, 240 frames / 8 seconds.')
if __name__=='__main__':
 task=sys.argv[1]
 if task=='review':review(sys.argv[2])
 elif task=='pack':pack()
 elif task=='validate':validate()
 elif task=='video':video()
 else:raise SystemExit('Use review STAGE, pack, validate or video')
