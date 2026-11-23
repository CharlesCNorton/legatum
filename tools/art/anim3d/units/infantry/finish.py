"""Review, measured grade, trim/pack, decoded validation and driver MP4."""
import os,sys,json,hashlib,io,subprocess
from pathlib import Path
from PIL import Image,ImageDraw,ImageStat
R=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'));M=R/'masters/infantry';V=R/'review/3d-v2';OUT=Path('app/src/assets/units/anim')
CLIPS={'idle':(8,4,True),'move':(8,6,True),'attack':(10,14,False),'hit':(4,8,False),'death':(10,5,False)}
CREAM=(233,207,160,255)
ref=Image.open('app/src/assets/units/infantry-256.png').convert('RGBA')
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canvas(im,size=256):
 out=Image.new('RGBA',(size,size),CREAM);out.alpha_composite(im.resize((size,size),Image.Resampling.LANCZOS));return out

def grade_params(im):
 # Alpha-masked, monotone quantile matching, calibrated once at rest.
 def quantiles(img,c):
  hist=img.getchannel(c).histogram(mask=img.getchannel('A').point(lambda v:255 if v>200 else 0));total=sum(hist);result=[]
  for q in (0,.01,.05,.25,.5,.75,.95,.99,1):
   acc=0
   for i,count in enumerate(hist):
    acc+=count
    if acc>=q*total:result.append(i);break
  return result
 luts=[]
 for c in 'RGB':
  src=quantiles(ref,c);dst=quantiles(im,c);pairs={0:0,255:255}
  for x,y in zip(dst[1:-1],src[1:-1]):pairs[x]=max(0,min(255,x+max(-20,min(20,y-x))))
  knots=sorted(pairs.items());ys=[];last=0
  for x,y in knots:last=max(last,y);ys.append((x,last))
  lut=[]
  for v in range(256):
   j=next((j for j in range(len(ys)-1) if ys[j][0]<=v<=ys[j+1][0]),len(ys)-2);x0,y0=ys[j];x1,y1=ys[j+1];lut.append(round(y0+(y1-y0)*(v-x0)/max(1,x1-x0)))
  luts.append(lut)
 return {'luts':luts,'method':'bounded monotone opaque-pixel RGB quantiles, frozen across clips','source_sha256':digest(Path('app/src/assets/units/infantry-256.png')),'master_sha256':digest(M/'infantry.blend'),'rest_sha256':digest(M/'renders/c-textured-lit/00.png')}
def grade(im,p):
 if 'luts' not in p:return im.copy()
 return Image.merge('RGBA',(*(c.point(lut) for c,lut in zip(im.convert('RGB').split(),p['luts'])),im.getchannel('A')))
def reduced(im,p):
 return grade(im,p).convert('RGBa').resize((160,160),Image.Resampling.BICUBIC).convert('RGBA')
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
  device=json.loads((directory/'render.json').read_text())['device']
  for k,(label,im) in enumerate([('Painting',ref),(device+' render',frames[0]),('50/50',Image.blend(canvas(ref),canvas(frames[0]),.5))]):
   sheet.alpha_composite(canvas(im),(k*256,24));sheet.alpha_composite(canvas(im,64),(k*256+96,290));d.text((k*256+8,6),label,fill='#3c3025')
  sheet.save(V/f'infantry-{stage}.png')
  if stage=='c-textured-lit':
   split=canvas(ref);split.paste(canvas(frames[0]).crop((128,0,256,256)),(128,0))
   split_sheet=Image.new('RGBA',(1024,360),CREAM);split_sheet.alpha_composite(sheet,(0,0));split_sheet.alpha_composite(split,(768,24));split_sheet.alpha_composite(split.resize((64,64)),(864,290));ImageDraw.Draw(split_sheet).text((776,6),'Split at center',fill='#3c3025');split_sheet.save(V/'infantry-f-restpose-compare.png')
   details=Image.new('RGBA',(768,536),CREAM);dd=ImageDraw.Draw(details)
   for k,(name,box) in enumerate([('Face, helmet and grenade',(81,10,143,78)),('Jacket and webbing',(89,74,156,145)),('Gaiters and boots',(83,180,161,228))]):
    dd.text((k*256+5,4),name,fill='#3c3025')
    for row,im in enumerate((ref,frames[0].resize((256,256),Image.Resampling.LANCZOS))):details.alpha_composite(canvas(im.crop(box),256),(k*256,24+row*256))
   details.save(V/'infantry-c-details.png')
 else:
  sheet=Image.new('RGBA',(256*len(frames),350),CREAM);d=ImageDraw.Draw(sheet)
  for j,im in enumerate(frames):sheet.alpha_composite(canvas(im),(j*256,20));sheet.alpha_composite(canvas(im,64),(j*256+96,280));d.text((j*256+8,4),f'{stage} {j+1}',fill='#3c3025')
  name=stage+'-strip' if stage.startswith('e-') else stage;sheet.save(V/f'infantry-{name}.png')
  if stage.startswith('e-'):
   fps=CLIPS[stage[2:]][1];frames=[i.resize((256,256),Image.Resampling.LANCZOS) for i in frames];frames[0].save(V/f'infantry-{stage}.webp',save_all=True,append_images=frames[1:],duration=round(1000/fps),loop=0,quality=85,method=6)
 print('Review written:',stage,flush=True)

def pack():
 (V/'infantry-validation.json').unlink(missing_ok=True)
 entries=[];rowheights=[];rows=[];sources={};p=json.loads((M/'grade.json').read_text())
 assert p['master_sha256']==digest(M/'infantry.blend'),'Stale grade'
 rest=json.loads((M/'renders/c-textured-lit/render.json').read_text())
 for row,(clip,(n,fps,loop)) in enumerate(CLIPS.items()):
  folder=M/'renders'/('e-'+clip);manifest=json.loads((folder/'render.json').read_text());blend=M/'clips'/f'{clip}.blend'
  assert manifest['frames']==n and manifest['blend_sha256']==digest(blend),f'Stale {clip} render'
  assert json.loads(blend.with_suffix('.json').read_text())['source_sha256']==digest(M/'infantry.blend'),f'Stale {clip} action'
  assert all(manifest[k]==rest[k] for k in ('engine','device','samples','resolution')),'Mixed render settings'
  sources[clip]=dict(manifest,png_sha256=[digest(folder/f'{i:02}.png') for i in range(n)]);items=[]
  for i in range(n):
   im=reduced(Image.open(folder/f'{i:02}.png').convert('RGBA'),p);box=im.getchannel('A').getbbox();assert box,'Empty frame'
   visible=im.getchannel('A').point(lambda v:255 if v>8 else 0).getbbox()
   assert visible and min(visible[0],visible[1],160-visible[2],160-visible[3])>=1,(clip,i,'Visible clipping; delivery not replaced')
   items.append((im,box))
  rows.append(items);rowheights.append(max(b[3]-b[1] for _,b in items)+2)
 width=max(sum(b[2]-b[0]+2 for _,b in row) for row in rows);atlas=Image.new('RGBA',(width,sum(rowheights)))
 meta={'version':2,'atlas':{'w':width,'h':atlas.height},'frame':{'w':160,'h':160,'ax':80,'ay':140},'clips':{}};y=0
 for row,((clip,(n,fps,loop)),items) in enumerate(zip(CLIPS.items(),rows)):
  rects=[];x=0;seen={}
  for im,b in items:
   key=hashlib.sha256(im.tobytes()).hexdigest()
   if key in seen:rects.append(seen[key]);continue
   crop=im.crop(b);atlas.paste(crop,(x+1,y+1));r=dict(x=x+1,y=y+1,w=crop.width,h=crop.height,ox=b[0],oy=b[1]);rects.append(r);seen[key]=r;x+=crop.width+2
  meta['clips'][clip]=dict(row=row,frames=n,fps=fps,loop=loop,rects=rects);y+=rowheights[row]
 atlas.paste((0,0,0,0),mask=atlas.getchannel('A').point(lambda x:255 if x==0 else 0))
 attempts=[]
 for quality,method in ((90,4),(85,4),(80,4),(75,4),(75,5)):
  print('Encoding trimmed atlas',atlas.size,'quality',quality,'method',method,flush=True);buf=io.BytesIO();atlas.save(buf,format='WEBP',quality=quality,method=method,exact=True);data=buf.getvalue();attempts.append({'quality':quality,'method':method,'bytes':len(data)})
  if len(data)<=200000:break
 else:raise RuntimeError(f'All 40 frames exceed cap at quality 75: {attempts}')
 OUT.mkdir(parents=True,exist_ok=True);(OUT/'infantry.webp').write_bytes(data);(OUT/'infantry.json').write_text(json.dumps(meta,separators=(',',':'))+'\n')
 report={'quality':quality,'method':method,'bytes':len(data),'frames':40,'attempts':attempts,'sources':sources,'sha256':digest(OUT/'infantry.webp'),'preview':rest['device']!='GPU','alpha':'lossless 8-bit','resampler':'premultiplied bicubic','grade_sha256':digest(M/'grade.json')};(V/'infantry-pack.json').write_text(json.dumps(report,indent=2));validate(atlas);print('PACK',report['bytes'],'bytes, quality',quality,', 40 frames; preview:',report['preview'],flush=True)

def validate(original=None):
 ap=OUT/'infantry.webp';meta=json.loads(ap.with_suffix('.json').read_text());im=Image.open(ap).convert('RGBA');report=json.loads((V/'infantry-pack.json').read_text());assert ap.stat().st_size<=200000 and report['quality']>=75
 assert im.size==(meta['atlas']['w'],meta['atlas']['h']);assert meta['frame']['w']==meta['frame']['h']==160
 if original:assert im.getchannel('A').tobytes()==original.getchannel('A').tobytes(),'WebP alpha changed'
 assert report['sha256']==digest(ap),'Atlas hash mismatch'
 assert report['grade_sha256']==digest(M/'grade.json'),'Grade hash mismatch'
 p=json.loads((M/'grade.json').read_text());clipping=[]
 assert p['source_sha256']==digest(Path('app/src/assets/units/infantry-256.png')),'Changed painting reference'
 assert p['master_sha256']==digest(M/'infantry.blend'),'Stale grade master'
 assert p['rest_sha256']==digest(M/'renders/c-textured-lit/00.png'),'Stale grade calibration'
 for clip,(n,fps,loop) in CLIPS.items():
  source=report['sources'][clip];blend=M/'clips'/f'{clip}.blend'
  assert source['blend_sha256']==digest(blend),'Stale rendered clip'
  assert json.loads(blend.with_suffix('.json').read_text())['source_sha256']==digest(M/'infantry.blend'),'Stale action master'
  assert source['png_sha256']==[digest(M/'renders'/('e-'+clip)/f'{i:02}.png') for i in range(n)],'Stale frame bytes'
  c=meta['clips'][clip];assert (c['frames'],c['fps'],c['loop'])==(n,fps,loop);assert len(c['rects'])==n
  hashes=[]
  for j,r in enumerate(c['rects']):
   assert 0<=r['ox']<160 and 0<=r['oy']<160 and r['ox']+r['w']<=160 and r['oy']+r['h']<=160
   assert r['x']+r['w']<im.width and r['y']+r['h']<im.height
   frame=Image.new('RGBA',(160,160));frame.paste(im.crop((r['x'],r['y'],r['x']+r['w'],r['y']+r['h'])),(r['ox'],r['oy']));hashes.append(hashlib.sha256(frame.tobytes()).hexdigest())
   expected=reduced(Image.open(M/'renders'/('e-'+clip)/f'{j:02}.png').convert('RGBA'),p)
   assert frame.getchannel('A').tobytes()==expected.getchannel('A').tobytes(),(clip,j,'decoded alpha mismatch')
   # Preserve low-opacity perimeter samples; visible coverage must retain a margin.
   # Preserve those alpha values; reject clipping of visible coverage instead.
   visible=frame.getchannel('A').point(lambda x:255 if x>8 else 0).getbbox()
   if visible and min(visible[0],visible[1],160-visible[2],160-visible[3])<1:clipping.append(f'{clip}/{j}')
  assert len(set(hashes))>1,clip+' is static'
 if clip=='death':assert hashes[-1]==hashes[-2],'Decoded death hold changed'
 # Raw held death must match exactly too.
 assert digest(M/'renders/e-death/08.png')==digest(M/'renders/e-death/09.png'),'Death not held'
 assert not clipping,('Frames touch cell edge',clipping)
 result={'status':'pass','frames':40,'size':ap.stat().st_size,'quality':report['quality'],'checks':['bounds','trim offsets','lossless alpha','motion in all clips','held death','size/quality cap'],'preview':report['preview'],'visual_approval':False};(V/'infantry-validation.json').write_text(json.dumps(result,indent=2));print('VALIDATION PASS',result)

def video():
 meta=json.loads((OUT/'infantry.json').read_text());atlas=Image.open(OUT/'infantry.webp').convert('RGBA');groups=[]
 for clip,c in meta['clips'].items():
  frames=[]
  for r in c['rects']:
   im=Image.new('RGBA',(160,160));im.paste(atlas.crop((r['x'],r['y'],r['x']+r['w'],r['y']+r['h'])),(r['ox'],r['oy']));frames.append(im.resize((320,320),Image.Resampling.LANCZOS))
  groups.append((clip,c,frames))
 out=V/f"infantry-round{os.environ.get('ROUND','1')}.mp4"
 proc=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s','1600x348','-r','30','-i','-','-an','-c:v','libx264','-threads','3','-pix_fmt','yuv420p','-crf','20','-movflags','+faststart',str(out)],stdin=subprocess.PIPE)
 for t in range(240):
  im=Image.new('RGBA',(1600,348),CREAM);d=ImageDraw.Draw(im)
  for k,(name,c,frames) in enumerate(groups):
   index=int(t/30*c['fps'])%c['frames'] if c['loop'] else min(int((t%60)/30*c['fps']),c['frames']-1);im.alpha_composite(frames[index],(k*320,28));d.text((k*320+8,8),name+(' / CPU preview' if json.loads((V/'infantry-pack.json').read_text())['preview'] else ' / GPU'),fill='#3c3025')
  proc.stdin.write(im.convert('RGB').tobytes())
 proc.stdin.close();assert proc.wait()==0
 probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(out)]));s=probe['streams'][0];assert s['codec_name']=='h264' and s['pix_fmt']=='yuv420p' and int(s['nb_frames'])==240 and (s['width'],s['height'])==(1600,348) and abs(float(s['duration'])-8)<.01
 print('MP4 verified:',out)

def feet_sheet():
 sheet=Image.new('RGBA',(1280,360),CREAM);draw=ImageDraw.Draw(sheet)
 for row,view in enumerate(('top','front')):
  draw.text((4,row*180+3),view+' / forward -Y; eight samples of one open walk cycle',fill='#3c3025')
  for i in range(8):sheet.alpha_composite(Image.open(M/'renders/feet'/f'{view}-{i:02}.png').convert('RGBA'),(i*160,row*180+20))
 sheet.save(V/'infantry-g-feet-check.png')

if __name__=='__main__':
 if len(sys.argv)>1 and sys.argv[1]=='feet':feet_sheet()
 elif len(sys.argv)>1 and sys.argv[1]=='review':review(sys.argv[2])
 elif len(sys.argv)>1 and sys.argv[1]=='validate':validate()
 else:pack();video()
