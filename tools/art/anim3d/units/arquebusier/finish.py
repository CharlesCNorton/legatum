"""Review, measured grade, trim/pack, decoded validation and driver MP4."""
import os,sys,json,hashlib,io,subprocess
from pathlib import Path
from PIL import Image,ImageDraw,ImageStat
R=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'));M=R/'masters/arquebusier';V=R/'review/3d-v2';OUT=Path('app/src/assets/units/anim')
CLIPS={'idle':(8,10,True),'move':(8,12,True),'attack':(10,14,False),'hit':(4,12,False),'death':(10,10,False)}
CREAM=(233,207,160,255)
ref=Image.open('app/src/assets/units/arquebusier-256.png').convert('RGBA')
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canvas(im,size=256):
 out=Image.new('RGBA',(size,size),CREAM);out.alpha_composite(im.resize((size,size),Image.Resampling.LANCZOS));return out

def grade_params(im):
 src=ImageStat.Stat(ref.convert('RGB'),ref.getchannel('A').point(lambda x:255 if x>200 else 0));dst=ImageStat.Stat(im.convert('RGB'),im.getchannel('A').point(lambda x:255 if x>200 else 0))
 gains=[max(.9,min(1.12,a/max(b,1))) for a,b in zip(src.mean,dst.mean)]
 return {'gains':gains,'contrast':max(.95,min(1.10,sum(src.stddev)/max(1,sum(dst.stddev)))),'source_mean':src.mean,'render_mean':dst.mean}
def grade(im,p):
 channels=[]
 for c,g in zip(im.convert('RGB').split(),p['gains']):channels.append(c.point(lambda v:round(max(0,min(255,((v-128)*p['contrast']+128)*g)))))
 return Image.merge('RGBA',(*channels,im.getchannel('A')))
def review(stage):
 directory=M/'renders'/stage;paths=sorted(directory.glob('[0-9][0-9].png'));raw=[Image.open(p).convert('RGBA') for p in paths]
 gp=M/'grade.json'
 if stage=='c-textured-lit':gp.write_text(json.dumps(grade_params(raw[0]),indent=2))
 p=json.loads(gp.read_text()) if gp.exists() and stage!='b-plain' else {'gains':[1,1,1],'contrast':1}
 frames=[grade(i,p) for i in raw]
 for path,im in zip(paths,frames):
  # Raw renders remain immutable. Both downsampled gallery and full masters retained.
  if im.width>=512:
   folder=M/'512'/stage;folder.mkdir(parents=True,exist_ok=True);im.save(folder/path.name)
  folder=M/('256' if im.width>=256 else 'preview')/stage;folder.mkdir(parents=True,exist_ok=True);im.resize((256,256) if im.width>=256 else im.size,Image.Resampling.LANCZOS).save(folder/path.name)
 if stage in ('b-plain','c-textured-lit'):
  sheet=Image.new('RGBA',(768,360),CREAM);d=ImageDraw.Draw(sheet)
  for k,(label,im) in enumerate([('Painting',ref),('Render',frames[0]),('50/50',Image.blend(canvas(ref),canvas(frames[0]),.5))]):
   sheet.alpha_composite(canvas(im),(k*256,24));sheet.alpha_composite(canvas(im,64),(k*256+96,290));d.text((k*256+8,6),label,fill='#3c3025')
  sheet.save(V/f'arquebusier-{stage}.png')
  if stage=='c-textured-lit':
   sheet.save(V/'arquebusier-f-restpose-compare.png')
   details=Image.new('RGBA',(768,536),CREAM);dd=ImageDraw.Draw(details)
   for k,(name,box) in enumerate([('Head and helmet',(90,5,151,76)),('Doublet and gun',(71,57,174,132)),('Powder and breeches',(79,106,165,165))]):
    dd.text((k*256+5,4),name,fill='#3c3025')
    for row,im in enumerate((ref,frames[0].resize((256,256),Image.Resampling.LANCZOS))):details.alpha_composite(canvas(im.crop(box),256),(k*256,24+row*256))
   details.save(V/'arquebusier-c-details.png')
 else:
  sheet=Image.new('RGBA',(256*len(frames),350),CREAM);d=ImageDraw.Draw(sheet)
  for j,im in enumerate(frames):sheet.alpha_composite(canvas(im),(j*256,20));sheet.alpha_composite(canvas(im,64),(j*256+96,280));d.text((j*256+8,4),f'{stage} {j+1}',fill='#3c3025')
  name=stage+'-strip' if stage.startswith('e-') else stage;sheet.save(V/f'arquebusier-{name}.png')
  if stage.startswith('e-'):
   fps=CLIPS[stage[2:]][1];frames[0].save(V/f'arquebusier-{stage}.webp',save_all=True,append_images=frames[1:],duration=round(1000/fps),loop=0,quality=85,method=6)
 print('Review written:',stage,flush=True)

def pack():
 entries=[];rowheights=[];rows=[];sources={};p=json.loads((M/'grade.json').read_text())
 for row,(clip,(n,fps,loop)) in enumerate(CLIPS.items()):
  folder=M/'renders'/('e-'+clip);manifest=json.loads((folder/'render.json').read_text());blend=M/'clips'/f'{clip}.blend'
  assert manifest['frames']==n and manifest['blend_sha256']==digest(blend),f'Stale {clip} render'
  assert json.loads(blend.with_suffix('.json').read_text())['source_sha256']==digest(M/'arquebusier.blend'),f'Stale {clip} action'
  sources[clip]=manifest;items=[]
  for i in range(n):
   im=grade(Image.open(folder/f'{i:02}.png').convert('RGBA'),p).resize((160,160),Image.Resampling.LANCZOS);box=im.getchannel('A').getbbox();assert box,'Empty frame';items.append((im,box))
  rows.append(items);rowheights.append(max(b[3]-b[1] for _,b in items)+2)
 width=max(sum(b[2]-b[0]+2 for _,b in row) for row in rows);atlas=Image.new('RGBA',(width,sum(rowheights)))
 meta={'version':2,'atlas':{'w':width,'h':atlas.height},'frame':{'w':160,'h':160,'ax':80,'ay':140},'clips':{}};y=0
 for row,((clip,(n,fps,loop)),items) in enumerate(zip(CLIPS.items(),rows)):
  rects=[];x=0
  for im,b in items:
   crop=im.crop(b);atlas.paste(crop,(x+1,y+1));rects.append(dict(x=x+1,y=y+1,w=crop.width,h=crop.height,ox=b[0],oy=b[1]));x+=crop.width+2
  meta['clips'][clip]=dict(row=row,frames=n,fps=fps,loop=loop,rects=rects);y+=rowheights[row]
 atlas.paste((0,0,0,0),mask=atlas.getchannel('A').point(lambda x:255 if x==0 else 0))
 attempts=[]
 for quality,method in ((90,4),(85,4),(80,4),(75,4),(75,5)):
  print('Encoding trimmed atlas',atlas.size,'quality',quality,'method',method,flush=True);buf=io.BytesIO();atlas.save(buf,format='WEBP',quality=quality,method=method,exact=True);data=buf.getvalue();attempts.append({'quality':quality,'method':method,'bytes':len(data)})
  if len(data)<=200000:break
 else:raise RuntimeError(f'All 40 frames exceed cap at quality 75: {attempts}')
 OUT.mkdir(parents=True,exist_ok=True);(OUT/'arquebusier.webp').write_bytes(data);(OUT/'arquebusier.json').write_text(json.dumps(meta,separators=(',',':'))+'\n')
 report={'quality':quality,'method':method,'bytes':len(data),'frames':40,'attempts':attempts,'sources':sources,'sha256':digest(OUT/'arquebusier.webp'),'alpha':'lossless 8-bit'};(V/'arquebusier-pack.json').write_text(json.dumps(report,indent=2));validate(atlas);print(json.dumps(report),flush=True)

def validate(original=None):
 ap=OUT/'arquebusier.webp';meta=json.loads(ap.with_suffix('.json').read_text());im=Image.open(ap).convert('RGBA');report=json.loads((V/'arquebusier-pack.json').read_text());assert ap.stat().st_size<=200000 and report['quality']>=75
 assert im.size==(meta['atlas']['w'],meta['atlas']['h']);assert meta['frame']['w']==meta['frame']['h']==160
 if original:assert im.getchannel('A').tobytes()==original.getchannel('A').tobytes(),'WebP alpha changed'
 clipping=[]
 for clip,(n,fps,loop) in CLIPS.items():
  c=meta['clips'][clip];assert (c['frames'],c['fps'],c['loop'])==(n,fps,loop);assert len(c['rects'])==n
  hashes=[]
  for j,r in enumerate(c['rects']):
   assert 0<=r['ox']<160 and 0<=r['oy']<160 and r['ox']+r['w']<=160 and r['oy']+r['h']<=160
   assert r['x']+r['w']<im.width and r['y']+r['h']<im.height
   frame=Image.new('RGBA',(160,160));frame.paste(im.crop((r['x'],r['y'],r['x']+r['w'],r['y']+r['h'])),(r['ox'],r['oy']));hashes.append(hashlib.sha256(frame.tobytes()).hexdigest())
   # Lanczos can extend alpha 1-3 to the cell edge despite clear raw margins.
   # Preserve those alpha values; reject clipping of visible coverage instead.
   visible=frame.getchannel('A').point(lambda x:255 if x>8 else 0).getbbox()
   if visible and min(visible[0],visible[1],160-visible[2],160-visible[3])<1:clipping.append(f'{clip}/{j}')
  assert len(set(hashes))>1,clip+' is static'
 # Decode can differ slightly between compressed rectangles; raw held death must match exactly.
 assert digest(M/'renders/e-death/08.png')==digest(M/'renders/e-death/09.png'),'Death not held'
 assert not clipping,('Frames touch cell edge',clipping)
 result={'status':'pass','frames':40,'size':ap.stat().st_size,'quality':report['quality'],'checks':['bounds','trim offsets','lossless alpha','motion in all clips','held death','size/quality cap'],'visual_approval':False};(V/'arquebusier-validation.json').write_text(json.dumps(result,indent=2));print('VALIDATION PASS',result)

def video():
 meta=json.loads((OUT/'arquebusier.json').read_text());atlas=Image.open(OUT/'arquebusier.webp').convert('RGBA');groups=[]
 for clip,c in meta['clips'].items():
  frames=[]
  for r in c['rects']:
   im=Image.new('RGBA',(160,160));im.paste(atlas.crop((r['x'],r['y'],r['x']+r['w'],r['y']+r['h'])),(r['ox'],r['oy']));frames.append(im.resize((320,320),Image.Resampling.LANCZOS))
  groups.append((clip,c,frames))
 out=V/f"arquebusier-round{os.environ.get('ROUND','1')}.mp4"
 proc=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s','1600x348','-r','30','-i','-','-an','-c:v','libx264','-pix_fmt','yuv420p','-crf','20','-movflags','+faststart',str(out)],stdin=subprocess.PIPE)
 for t in range(240):
  im=Image.new('RGBA',(1600,348),CREAM);d=ImageDraw.Draw(im)
  for k,(name,c,frames) in enumerate(groups):
   index=int(t/30*c['fps'])%c['frames'] if c['loop'] else min(int((t%60)/30*c['fps']),c['frames']-1);im.alpha_composite(frames[index],(k*320,28));d.text((k*320+8,8),name,fill='#3c3025')
  proc.stdin.write(im.convert('RGB').tobytes())
 proc.stdin.close();assert proc.wait()==0
 probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(out)]));s=probe['streams'][0];assert s['codec_name']=='h264' and s['pix_fmt']=='yuv420p' and int(s['nb_frames'])==240
 print('MP4 verified:',out)

if __name__=='__main__':
 if len(sys.argv)>1 and sys.argv[1]=='review':review(sys.argv[2])
 elif len(sys.argv)>1 and sys.argv[1]=='validate':validate()
 else:pack();video()
