"""Review sheets, frozen histogram grade, trimmed atlas and eight-second video."""
import os,sys,json,hashlib,io,subprocess,tempfile
from pathlib import Path
from PIL import Image,ImageDraw,ImageStat,ImageEnhance
R=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'));M=R/'masters/barbarian-musketman';V=R/'review/3d-v2';SLUG='barbarian-musketman';HERE=Path(__file__).resolve().parent
CLIPS={'idle':(8,10,True),'move':(8,12,True),'attack':(10,14,False),'hit':(4,12,False),'death':(10,10,False)}
CREAM=(233,207,160,255)
def tile(im,size=256):
 canvas=Image.new('RGBA',(size,size),CREAM);canvas.alpha_composite(im.convert('RGBA').resize((size,size),Image.Resampling.LANCZOS));return canvas

def review(stage,graded=False):
 files=sorted((M/('256' if graded else 'renders')/stage).glob('[0-9][0-9].png'));ims=[Image.open(f).convert('RGBA').resize((256,256),Image.Resampling.LANCZOS) for f in files];ref=Image.open(f'app/src/assets/units/{SLUG}-256.png').convert('RGBA')
 if stage.startswith('e-'):
  name=stage[2:];sheet=Image.new('RGBA',(len(ims)*256,350),CREAM);d=ImageDraw.Draw(sheet)
  for i,im in enumerate(ims):sheet.paste(tile(im),(i*256,24));sheet.paste(tile(im,64),(i*256,282));d.text((i*256+5,5),f'{name} {i+1}',fill='black')
  sheet.save(V/f'{SLUG}-{stage}-strip.png');ims=[im.resize((256,256),Image.Resampling.LANCZOS) for im in ims];ims[0].save(V/f'{SLUG}-{stage}.webp',save_all=True,append_images=ims[1:],duration=round(1000/CLIPS[name][1]),loop=0,quality=85,method=4)
 else:
  allims=[ref]+ims;sheet=Image.new('RGBA',(len(allims)*256,370),CREAM);d=ImageDraw.Draw(sheet)
  for i,im in enumerate(allims):sheet.paste(tile(im),(i*256,24));sheet.paste(tile(im,64),(i*256,292));d.text((i*256+5,5),'Painting' if i==0 else stage,fill='black')
  sheet.save(V/f'{SLUG}-{stage}.png')
  if stage=='c-textured-lit':
   compare=Image.new('RGBA',(768,370),CREAM);draw=ImageDraw.Draw(compare)
   for i,im in enumerate([ref,ims[0],Image.blend(tile(ref),tile(ims[0]),.5)]):compare.paste(tile(im),(i*256,24));compare.paste(tile(im,64),(i*256,292));draw.text((i*256+6,5),['Painting','3D rest','50/50 crossfade'][i],fill='black')
   compare.save(V/f'{SLUG}-f-restpose-compare.png')
   detail=Image.new('RGBA',(768,536),CREAM)
   for i,box in enumerate([(37,30,98,87),(24,74,139,142),(30,124,148,205)]):
    for j,im in enumerate([ref,ims[0]]):detail.paste(tile(im.crop(box),256),(i*256,j*268))
   detail.save(V/f'{SLUG}-c-details.png')
 print('REVIEW',stage)
if __name__=='__main__':
 if sys.argv[1]=='review':
  review(sys.argv[2])
  stop=M/'stop-preview'
  if sys.argv[2].startswith('e-') and stop.exists():
   stop.unlink();raise SystemExit('Preview stopped between clips for model correction')

def percentile(im,channel,p):
 values=[v[channel] for v in im.getdata() if v[3]>200]
 values.sort();return values[round((len(values)-1)*p)]

def pack():
 ref=Image.open(f'app/src/assets/units/{SLUG}-256.png').convert('RGBA');rest=Image.open(M/'renders/c-textured-lit/00.png').convert('RGBA').resize((256,256),Image.Resampling.LANCZOS)
 # One restrained affine grade from the rest pose, frozen across every frame.
 refbody=ref.crop((8,18,220,191));renderbody=rest.crop((8,18,220,191));gain=[];bias=[]
 for c in range(3):
  a,b=percentile(refbody,c,.12),percentile(refbody,c,.88);x,y=percentile(renderbody,c,.12),percentile(renderbody,c,.88)
  g=max(.85,min(1.18,(b-a)/max(1,y-x)));gain.append(1+.5*(g-1));bias.append(.5*max(-8,min(8,a-g*x)))
 grade={'gain':gain,'bias':bias,'method':'12/88 percentiles of opaque figure; half-strength bounded affine transform frozen across clips'}
 (M/'grade.json').write_text(json.dumps(grade,indent=2))
 def graded(im):
  channels=im.split();return Image.merge('RGBA',tuple(channels[c].point(lambda x,c=c:round(max(0,min(255,x*gain[c]+bias[c])))) for c in range(3))+(channels[3],))
 # Preserve genuine render masters. Never upscale a CPU preview and call it 512.
 for stage in ['b-plain','c-textured-lit','d-rig-poses']+['e-'+c for c in CLIPS]:
  data=json.loads((M/'renders'/stage/'render.json').read_text());size=data['resolution']
  for f in sorted((M/'renders'/stage).glob('[0-9][0-9].png')):
   im=Image.open(f).convert('RGBA');assert im.size==(size,size)
   for target in [512,256]:
    if size<target:continue
    dest=M/str(target)/stage;dest.mkdir(parents=True,exist_ok=True);graded(im).resize((target,target),Image.Resampling.LANCZOS).save(dest/f.name)
 frames={};renders={};hashes={}
 current=hashlib.sha256((M/f'{SLUG}.blend').read_bytes()).hexdigest()
 for clip,(n,fps,loop) in CLIPS.items():
  renders[clip]=json.loads((M/'renders'/('e-'+clip)/'render.json').read_text());meta=json.loads((M/'clips'/f'{clip}.json').read_text())
  assert meta['source_sha256']==current,f'Stale source {clip}'
  assert renders[clip]['blend_sha256']==hashlib.sha256((M/'clips'/f'{clip}.blend').read_bytes()).hexdigest(),f'Stale render {clip}'
  frames[clip]=[]
  for i in range(n):
   f=M/'renders'/('e-'+clip)/f'{i:02}.png';im=graded(Image.open(f).convert('RGBA')).resize((160,160),Image.Resampling.LANCZOS)
   a=im.getchannel('A').point(lambda x:round(round(x*31/255)*255/31));im.putalpha(a);im.paste((0,0,0,0),mask=a.point(lambda x:255 if x==0 else 0));bbox=a.getbbox();assert bbox
   assert bbox[0]>0 and bbox[1]>0 and bbox[2]<160 and bbox[3]<160,(clip,i,'clipped',bbox)
   box=(max(0,bbox[0]-1),max(0,bbox[1]-1),min(160,bbox[2]+1),min(160,bbox[3]+1));frames[clip].append((im.crop(box),box))
   hashes[f'{clip}/{i}']=hashlib.sha256(f.read_bytes()).hexdigest()
 assert len(set((r['engine'],r['device'],r['resolution'],r['samples']) for r in renders.values()))==1,'Mixed render settings'
 rowheights=[max(im.height for im,box in frames[c])+2 for c in CLIPS];width=max(sum(im.width+2 for im,box in frames[c]) for c in CLIPS);height=sum(rowheights)
 atlas=Image.new('RGBA',(width,height));meta={'version':2,'unit':SLUG,'frame':{'w':160,'h':160,'ax':54,'ay':134},'atlas':{'w':width,'h':height},'clips':{}};y=0
 for row,(clip,(n,fps,loop)) in enumerate(CLIPS.items()):
  rects=[];x=0
  for im,box in frames[clip]:
   atlas.paste(im,(x,y));rects.append({'x':x,'y':y,'w':im.width,'h':im.height,'ox':box[0],'oy':box[1]});x+=im.width+2
  meta['clips'][clip]={'row':row,'frames':n,'fps':fps,'loop':loop,'rects':rects};y+=rowheights[row]
 for quality in (90,85,80,75):
  output=io.BytesIO();atlas.save(output,format='WEBP',quality=quality,method=6,exact=True)
  print('ENCODE',quality,len(output.getvalue()),flush=True)
  if len(output.getvalue())<=200000:break
 else:raise RuntimeError('Atlas exceeds 200000 bytes at quality 75; frame count and quality floor retained')
 out=Path('app/src/assets/units/anim');out.mkdir(exist_ok=True,parents=True);(out/f'{SLUG}.webp').write_bytes(output.getvalue());(out/f'{SLUG}.json').write_text(json.dumps(meta,separators=(',',':'))+'\n')
 report={'bytes':len(output.getvalue()),'quality':quality,'frames':40,'alpha_levels':32,'atlas_sha256':hashlib.sha256(output.getvalue()).hexdigest(),'source_sha256':hashes,'renders':renders,'grade':grade,'approval':'round 1 candidate; no PASS'}
 (M/'pack.json').write_text(json.dumps(report,indent=2));(V/f'{SLUG}-pack.json').write_text(json.dumps(report,indent=2));print('PACK',len(output.getvalue()),'bytes quality',quality)
 # Regenerate review images from the graded masters, preserving raw render outputs.
 for stage in ['b-plain','c-textured-lit','d-rig-poses']+['e-'+c for c in CLIPS]:review(stage,True)
 validate();video()

def decoded():
 out=Path('app/src/assets/units/anim');meta=json.loads((out/f'{SLUG}.json').read_text());im=Image.open(out/f'{SLUG}.webp').convert('RGBA');clips={}
 for name,c in meta['clips'].items():
  frames=[]
  for r in c['rects']:
   canvas=Image.new('RGBA',(160,160));canvas.paste(im.crop((r['x'],r['y'],r['x']+r['w'],r['y']+r['h'])),(r['ox'],r['oy']));frames.append(canvas)
  clips[name]=frames
 return meta,im,clips

def validate():
 meta,im,clips=decoded();p=Path(f'app/src/assets/units/anim/{SLUG}.webp');report=json.loads((M/'pack.json').read_text())
 assert p.stat().st_size<=200000 and report['quality']>=75
 assert im.size==(meta['atlas']['w'],meta['atlas']['h']) and im.getchannel('A').getextrema()==(0,255)
 assert meta['frame']=={'w':160,'h':160,'ax':54,'ay':134}
 for row,(name,(n,fps,loop)) in enumerate(CLIPS.items()):
  c=meta['clips'][name];assert c['row']==row and c['frames']==n and c['fps']==fps and c['loop']==loop and len(c['rects'])==n
  assert len({f.tobytes() for f in clips[name]})>1,(name,'no animation')
  for r in c['rects']:
   assert 0<=r['ox']<160 and 0<=r['oy']<160 and r['ox']+r['w']<=160 and r['oy']+r['h']<=160
   assert r['x']+r['w']<=im.width and r['y']+r['h']<=im.height
 assert (M/'renders/e-death/08.png').read_bytes()==(M/'renders/e-death/09.png').read_bytes(),'Death must hold'
 result={'status':'pass','frames':sum(len(f) for f in clips.values()),'bytes':p.stat().st_size,'quality':report['quality'],'checks':['trim reconstruction','40 frames','clip fps and loops','alpha','motion','terminal death hold','source and render hashes at pack'],'visual_approval':False}
 (V/f'{SLUG}-validation.json').write_text(json.dumps(result,indent=2));print('VALIDATE',json.dumps(result))

def video():
 meta,atlas,clips=decoded();frames={name:[tile(im,320).convert('RGB') for im in ims] for name,ims in clips.items()};out=V/f'{SLUG}-round{os.environ.get("ROUND","1")}.mp4'
 # Stream raw frames to avoid 240 temporary PNG files. Reconstruct trims first.
 process=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pixel_format','rgb24','-video_size','1600x348','-framerate','30','-i','-','-c:v','libx264','-pix_fmt','yuv420p','-crf','20','-movflags','+faststart',str(out)],stdin=subprocess.PIPE)
 for tick in range(240):
  canvas=Image.new('RGB',(1600,348),CREAM[:3]);d=ImageDraw.Draw(canvas)
  for k,(name,(n,fps,loop)) in enumerate(CLIPS.items()):
   idx=int(tick/30*fps)%n if loop else min(int((tick%60)/30*fps),n-1);canvas.paste(frames[name][idx],(k*320,28));d.text((k*320+10,8),name,fill=(60,45,25))
  process.stdin.write(canvas.tobytes())
 process.stdin.close();assert process.wait()==0
 probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','stream=codec_name,pix_fmt,width,height,nb_frames:format=duration','-of','json',str(out)]));assert probe['streams'][0]['codec_name']=='h264' and probe['streams'][0]['pix_fmt']=='yuv420p' and int(probe['streams'][0]['nb_frames'])==240 and abs(float(probe['format']['duration'])-8)<.05
 (V/f'{SLUG}-video.json').write_text(json.dumps(probe,indent=2));print('VIDEO',out)

if __name__=='__main__' and sys.argv[1]!='review':
 {'pack':pack,'validate':validate,'video':video}[sys.argv[1]]()
