"""Review, stable histogram grade, trim-offset packing, validation and H.264 review."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops,ImageStat
import os,json,sys,hashlib,io,subprocess
R=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')));M=R/'masters/byzantine-heir';V=R/'review/3d-v2';V.mkdir(parents=True,exist_ok=True)
U='byzantine-heir';OUT=Path('app/src/assets/units/anim');CLIPS={'idle':(8,10,True),'move':(8,12,True),'attack':(10,14,False),'hit':(4,12,False),'death':(10,10,False)};CREAM=(233,207,160,255);REF=Image.open(f'app/src/assets/units/{U}-256.png').convert('RGBA')
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(stage):
 meta=json.loads((M/'renders'/stage/'render.json').read_text());paths=sorted((M/'renders'/stage).glob('[0-9][0-9].png'));assert len(paths)==meta['frames'];return [Image.open(p).convert('RGBA') for p in paths],meta

def grade_params():
 meta=json.loads((M/'renders/c/render.json').read_text())
 assert meta['source_sha256']==digest(M/'byzantine-heir.blend'),'Stale calibration render master'
 assert meta['frame_sha256']['00.png']==digest(M/'renders/c/00.png'),'Modified calibration render'
 raw=Image.open(M/'renders/c/00.png').convert('RGBA').resize((256,256),Image.Resampling.LANCZOS)
 def stats(im):
  mask=im.getchannel('A').point(lambda x:255 if x>240 else 0);s=ImageStat.Stat(im.convert('RGB'),mask);return s.mean,s.stddev
 rm,rs=stats(REF);sm,ss=stats(raw);gain=[min(1.16,max(.86,a/max(1,b))) for a,b in zip(rs,ss)];offset=[min(10,max(-10,a-g*b)) for a,b,g in zip(rm,sm,gain)];d={'gain':gain,'offset':offset,'reference_mean':rm,'render_mean':sm,'reference_std':rs,'render_std':ss,'source_sha256':digest(M/'byzantine-heir.blend'),'rest_sha256':digest(M/'renders/c/00.png'),'reference_sha256':digest(Path(f'app/src/assets/units/{U}-256.png')),'method':'Bounded per-channel mean/variance transfer from rest; identical transform for every clip'};(M/'grade.json').write_text(json.dumps(d,indent=2));return d

def grade(im,d):
 channels=im.split();return Image.merge('RGBA',tuple(channels[i].point([min(255,max(0,round(x*d['gain'][i]+d['offset'][i]))) for x in range(256)]) for i in range(3))+(channels[3],))
def bg(im,size=None):
 if size:im=im.resize(size,Image.Resampling.LANCZOS)
 out=Image.new('RGBA',im.size,CREAM);out.alpha_composite(im);return out

def compare(render,path,title):
 render=render.resize((256,256),Image.Resampling.LANCZOS);sheet=Image.new('RGBA',(768,360),CREAM);d=ImageDraw.Draw(sheet)
 for i,(im,label) in enumerate([(REF,'Painting'),(render,title),(Image.blend(REF,render,.5),'50/50 crossfade')]):
  sheet.alpha_composite(im,(i*256,24));sheet.alpha_composite(im.resize((64,64),Image.Resampling.LANCZOS),(i*256+96,290));d.text((i*256+8,7),label,fill='#443626')
 sheet.convert('RGB').save(path)

def review(stage):
 ims,meta=load(stage);tag=f"{meta['device']} {meta['resolution']}px {meta['samples']} samples"
 if stage=='b':
  side=M/'renders/b/side.png';quarter=M/'renders/b/three-quarter.png'
  if side.exists() and quarter.exists():
   sheet=Image.new('RGBA',(1024,360),CREAM);d=ImageDraw.Draw(sheet)
   for k,(im,label) in enumerate([(REF,'Painting'),(ims[0],'Plain '+tag),(Image.open(quarter).convert('RGBA'),'Three-quarter geometry'),(Image.open(side).convert('RGBA'),'Side geometry')]):
    im=im.resize((256,256),Image.Resampling.LANCZOS);sheet.alpha_composite(im,(k*256,24));sheet.alpha_composite(im.resize((64,64),Image.Resampling.LANCZOS),(k*256+96,290));d.text((k*256+8,7),label,fill='#443626')
   sheet.convert('RGB').save(V/f'{U}-b-plain.png')
  else:compare(ims[0],V/f'{U}-b-plain.png','Plain '+tag)
  return
 gp=grade_params() if stage=='c' else json.loads((M/'grade.json').read_text());ims=[grade(im,gp) for im in ims]
 # Masters are never synthesized at a higher resolution than the render.
 for size in [512,256]:
  if meta['resolution']<size:continue
  dest=M/str(size)/stage;dest.mkdir(parents=True,exist_ok=True)
  for i,im in enumerate(ims):im.resize((size,size),Image.Resampling.LANCZOS).save(dest/f'{i:02}.png')
 if stage=='g-feet':
  sheet=Image.new('RGBA',(2048,568),CREAM);draw=ImageDraw.Draw(sheet)
  for i,im in enumerate(ims):
   row=i//8;col=i%8;sheet.alpha_composite(im.resize((256,256),Image.Resampling.LANCZOS),(col*256,row*284+24))
   draw.text((col*256+5,row*284+5),f"{'Top' if row==0 else 'Front'} move {col+1} {tag}",fill='#443626')
  sheet.convert('RGB').save(V/f'{U}-g-feet-check.png');print('FEET_REVIEW',tag);return
 if stage=='c':
  compare(ims[0],V/f'{U}-c-textured-lit.png',tag);compare(ims[0],V/f'{U}-f-restpose-compare.png',tag)
  full=ims[0].resize((256,256),Image.Resampling.LANCZOS);sheet=Image.new('RGBA',(768,540),CREAM);d=ImageDraw.Draw(sheet)
  for k,(name,box) in enumerate([('Face and crown',(100,20,139,60)),('Armour and mantle',(89,58,168,146)),('Boots and train',(88,164,189,230))]):
   for row,im in enumerate([REF,full]):sheet.alpha_composite(im.crop(box).resize((256,256),Image.Resampling.LANCZOS),(k*256,row*270+14))
   d.text((k*256+8,0),name,fill='#443626')
  sheet.convert('RGB').save(V/f'{U}-c-details.png')
 else:
  clip=stage[2:];small=[im.resize((256,256),Image.Resampling.LANCZOS) for im in ims];sheet=Image.new('RGBA',(256*len(ims),350),CREAM);d=ImageDraw.Draw(sheet)
  for i,im in enumerate(small):sheet.alpha_composite(im,(i*256,24));sheet.alpha_composite(im.resize((64,64),Image.Resampling.LANCZOS),(i*256+96,283));d.text((i*256+8,7),f'{clip} {i+1} {tag}',fill='#443626')
  sheet.convert('RGB').save(V/f'{U}-e-{clip}-strip.png');small[0].save(V/f'{U}-e-{clip}.webp',save_all=True,append_images=small[1:],duration=round(1000/CLIPS[clip][1]),loop=0,quality=90,method=6)
  if clip=='attack':
   poses=Image.new('RGBA',(1024,280),CREAM)
   for k,i in enumerate([0,2,5,9]):poses.alpha_composite(small[i],(k*256,24))
   ImageDraw.Draw(poses).text((8,7),'Staff guard / preparation / thrust / recovery',fill='#443626');poses.convert('RGB').save(V/f'{U}-d-rig-poses.png')
 print('REVIEW',stage,tag)

def verify_gpu():
 source=digest(M/'byzantine-heir.blend')
 for stage in ['b','c','g-feet']+['e-'+n for n in CLIPS]:
  ims,meta=load(stage)
  assert (meta['device'],meta['resolution'],meta['samples'])==('GPU',512,48),(stage,'Not GPU512/48')
  assert meta['source_sha256']==source,(stage,'Stale master')
  blend=M/'clips'/('move' if stage=='g-feet' else stage[2:])/'clip.blend' if stage.startswith('e-') or stage=='g-feet' else M/('plain.blend' if stage=='b' else 'byzantine-heir.blend')
  assert meta['blend_sha256']==digest(blend),(stage,'Stale render blend')
  for filename,h in meta['frame_sha256'].items():assert digest(M/'renders'/stage/filename)==h
  if stage!='b':
   for size in [512,256]:
    for i in range(len(ims)):
     saved=Image.open(M/str(size)/stage/f'{i:02}.png').convert('RGBA');assert saved.size==(size,size)
     expected=grade(ims[i],json.loads((M/'grade.json').read_text())).resize((size,size),Image.Resampling.LANCZOS)
     assert saved.tobytes()==expected.tobytes(),(stage,size,i,'Stale exported master')
 print('GPU_MASTERS_OK')

def check_grade(gp):
 assert gp['source_sha256']==digest(M/'byzantine-heir.blend'),'Stale grade master'
 assert gp['rest_sha256']==digest(M/'renders/c/00.png'),'Stale grade rest render'
 assert gp['reference_sha256']==digest(Path(f'app/src/assets/units/{U}-256.png')),'Stale grade reference'

def pack():
 data={};rows=[];source=digest(M/'byzantine-heir.blend');gp=json.loads((M/'grade.json').read_text());check_grade(gp);audit={};rest=json.loads((M/'renders/c/render.json').read_text())
 for row,(clip,(count,fps,loop)) in enumerate(CLIPS.items()):
  images,meta=load('e-'+clip);assert meta['source_sha256']==source,'Stale master';assert len(images)==count
  assert all(meta[k]==rest[k] for k in ['engine','device','resolution','samples']),'Mixed render settings'
  assert meta['blend_sha256']==digest(M/'clips'/clip/'clip.blend'),'Stale clip render'
  for file,h in meta['frame_sha256'].items():assert digest(M/'renders'/('e-'+clip)/file)==h,'Modified rendered frame'
  cm=json.loads((M/'clips'/clip/'clip.json').read_text());assert cm['source_sha256']==source,'Stale animation'
  x=2;entries=[];tiles=[];seen={}
  for i,im in enumerate(images):
   im=grade(im,gp).resize((160,160),Image.Resampling.BICUBIC);box=im.getbbox();assert box,'Empty frame';l,t,r,b=box
   assert l>0 and t>0 and r<160 and b<160,(clip,i,'clipped',box)
   tile=im.crop(box);key=hashlib.sha256(im.tobytes()).hexdigest()
   if key in seen:entries.append(dict(seen[key]));continue
   rect={'x':x,'y':row*160+2,'w':r-l,'h':b-t,'ox':l,'oy':t};seen[key]=rect
   tiles.append((x,tile));entries.append(rect);x+=r-l+4
  data[clip]={'row':row,'frames':count,'fps':fps,'loop':loop,'rects':entries}
  if clip=='move':data[clip]['root_motion_m']=[sample['root_motion_m'] for sample in cm['motion']['samples'][:count]]
  rows.append((x,tiles));audit[clip]=meta
 atlas=Image.new('RGBA',(max(w for w,_ in rows),800))
 for row,(_,tiles) in enumerate(rows):
  for x,tile in tiles:atlas.alpha_composite(tile,(x,row*160+2))
 chosen=None
 for quality in [90,85,80,75]:
  stream=io.BytesIO();atlas.save(stream,format='WEBP',quality=quality,method=6,exact=True)
  if len(stream.getvalue())<=200000:chosen=stream.getvalue();break
 assert chosen,'Atlas exceeds 200000 bytes at minimum quality 75; preserve all frames'
 OUT.mkdir(parents=True,exist_ok=True);(OUT/f'{U}.webp').write_bytes(chosen);metadata={'version':2,'layout':'trimmed-rows','resampler':'bicubic','gutter':2,'atlas':{'w':atlas.width,'h':atlas.height},'frame':{'w':160,'h':160,'ax':76,'ay':144},'clips':data,'quality':quality};(OUT/f'{U}.json').write_text(json.dumps(metadata,indent=2)+'\n');(M/'pack.json').write_text(json.dumps({'bytes':len(chosen),'quality':quality,'source_sha256':source,'atlas_sha256':digest(OUT/f'{U}.webp'),'grade_sha256':digest(M/'grade.json'),'renders':audit},indent=2));print('PACKED',len(chosen),'bytes, quality',quality)

def decoded():
 meta=json.loads((OUT/f'{U}.json').read_text());atlas=Image.open(OUT/f'{U}.webp').convert('RGBA');frames={}
 for name,clip in meta['clips'].items():
  frames[name]=[]
  for q in clip['rects']:
   im=Image.new('RGBA',(160,160));im.alpha_composite(atlas.crop((q['x'],q['y'],q['x']+q['w'],q['y']+q['h'])),(q['ox'],q['oy']));frames[name].append(im)
 return meta,atlas,frames

def validate():
 check_grade(json.loads((M/'grade.json').read_text()));assert json.loads((M/'pack.json').read_text())['grade_sha256']==digest(M/'grade.json'),'Grade changed after packing'
 meta,atlas,frames=decoded();assert digest(OUT/f'{U}.webp')==json.loads((M/'pack.json').read_text())['atlas_sha256'];assert (OUT/f'{U}.webp').stat().st_size<=200000;assert meta['quality']>=75;assert meta['frame']=={'w':160,'h':160,'ax':76,'ay':144};assert list(meta['clips'])==list(CLIPS);checks=[]
 for clip,(count,fps,loop) in CLIPS.items():
  c=meta['clips'][clip];assert (c['frames'],c['fps'],c['loop'])==(count,fps,loop);assert len(frames[clip])==count;hashes=[]
  for im,q in zip(frames[clip],c['rects']):
   assert 0<=q['x']<q['x']+q['w']<=atlas.width;assert 0<=q['y']<q['y']+q['h']<=atlas.height;assert 0<q['ox']<q['ox']+q['w']<160;assert 0<q['oy']<q['oy']+q['h']<160;assert im.getchannel('A').getextrema()[0]==0;hashes.append(hashlib.sha256(im.tobytes()).hexdigest())
  assert len(set(hashes))>1,clip+' has no motion'
  gp=json.loads((M/'grade.json').read_text())
  for i,decoded_frame in enumerate(frames[clip]):
   source=grade(Image.open(M/'renders'/('e-'+clip)/f'{i:02}.png').convert('RGBA'),gp).resize((160,160),Image.Resampling.BICUBIC)
   assert decoded_frame.getchannel('A').tobytes()==source.getchannel('A').tobytes(),(clip,i,'Alpha changed')
   diff=ImageChops.difference(decoded_frame.convert('RGB'),source.convert('RGB'));error=ImageStat.Stat(diff,source.getchannel('A').point(lambda a:255 if a>240 else 0)).mean;assert max(error)<22,(clip,i,'trim reconstruction error',error)
  checks.append(clip+': frame count, alpha, padding, bounds and motion OK')
 assert frames['death'][-1].tobytes()==frames['death'][-2].tobytes(),'Decoded death changed'
 sheet=Image.new('RGBA',(1600,840),CREAM)
 for row,(name,images) in enumerate(frames.items()):
  ImageDraw.Draw(sheet).text((4,row*168),name,fill='#443626')
  for i,im in enumerate(images):sheet.alpha_composite(im,(i*160,row*168+8))
 sheet.convert('RGB').save(V/f'{U}-g-decoded-atlas.png')
 # Compare raw terminal frames, avoiding WebP block context differences.
 a=Image.open(M/'renders/e-death/08.png');b=Image.open(M/'renders/e-death/09.png');assert a.tobytes()==b.tobytes(),'Death must settle identically'
 result={'checks':checks+['Held death identical','Atlas <=200000 bytes and quality >=75'],'bytes':(OUT/f'{U}.webp').stat().st_size,'quality':meta['quality'],'art_approval':False};(M/'validation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))

def video():
 meta,atlas,frames=decoded();frames={n:[bg(im.resize((320,320),Image.Resampling.LANCZOS)) for im in fr] for n,fr in frames.items()};out=V/f"{U}-round{os.environ.get('ROUND','1')}.mp4"
 command=['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s','1600x348','-r','30','-i','-','-an','-c:v','libx264','-threads','3','-pix_fmt','yuv420p','-crf','20','-movflags','+faststart',str(out)]
 p=subprocess.Popen(command,stdin=subprocess.PIPE)
 for t in range(240):
  canvas=Image.new('RGB',(1600,348),CREAM[:3]);d=ImageDraw.Draw(canvas)
  for k,(n,c) in enumerate(meta['clips'].items()):
   i=int(t/30*c['fps'])%c['frames'] if c['loop'] else min(int((t%60)/30*c['fps']),c['frames']-1);canvas.paste(frames[n][i].convert('RGB'),(k*320,28));d.text((k*320+10,8),n,fill='#443626')
  p.stdin.write(canvas.tobytes())
 p.stdin.close();assert p.wait()==0
 probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(out)]));stream=probe['streams'][0];assert stream['codec_name']=='h264' and stream['pix_fmt']=='yuv420p';assert (stream['width'],stream['height'],int(stream['nb_frames']))==(1600,348,240);assert abs(float(probe['format']['duration'])-8)<.05;(M/'video.json').write_text(json.dumps(probe,indent=2));print('VIDEO',out,'H.264 yuv420p 1600x348, 240 frames, 8 seconds')

if __name__=='__main__':
 mode=sys.argv[1]
 if mode=='review':review(sys.argv[2])
 else:{'pack':pack,'validate':validate,'video':video,'verify-gpu':verify_gpu}[mode]()
