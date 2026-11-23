"""Review sheets, frozen histogram grade, trimmed atlas and eight-second video."""
import os,sys,json,hashlib,io,subprocess,tempfile
from pathlib import Path
from PIL import Image,ImageDraw,ImageStat,ImageEnhance
R=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'));M=R/'masters/musketman';V=R/'review/3d-v2';SLUG='musketman';HERE=Path(__file__).resolve().parent
CLIPS={'idle':(8,4,True),'move':(8,8,True),'attack':(10,14,False),'hit':(4,8,False),'death':(10,8,False)}
CREAM=(233,207,160,255)
def tile(im,size=256):
 canvas=Image.new('RGBA',(size,size),CREAM);canvas.alpha_composite(im.convert('RGBA').resize((size,size),Image.Resampling.LANCZOS));return canvas

def review(stage,graded=False):
 files=sorted((M/('256' if graded else 'renders')/stage).glob('[0-9][0-9].png'));ims=[Image.open(f).convert('RGBA').resize((256,256),Image.Resampling.LANCZOS) for f in files];ref=Image.open(f'app/src/assets/units/{SLUG}-256.png').convert('RGBA')
 if stage.startswith('g-feet-'):
  sheet=Image.new('RGBA',(8*160,2*186),CREAM);d=ImageDraw.Draw(sheet)
  for row,view in enumerate(('top','front')):
   files=sorted((M/('256' if graded else 'renders')/('g-feet-'+view)).glob('[0-9][0-9].png'))
   for i,file in enumerate(files):sheet.paste(tile(Image.open(file),160),(i*160,row*186+24));d.text((i*160+4,row*186+4),f'{view} {i+1}; travel +X',fill='black')
  sheet.save(V/f'{SLUG}-g-feet-check.png');return
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
   for i,box in enumerate([(58,12,142,71),(28,58,146,142),(18,123,155,221)]):
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

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def stage_blend(stage):
 return M/('plain.blend' if stage=='b-plain' else f'{SLUG}.blend' if stage=='c-textured-lit' else 'clips/move.blend' if stage.startswith('g-feet-') else 'clips/attack.blend' if stage=='d-rig-poses' else f'clips/{stage[2:]}.blend')

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
 for stage in ['b-plain','c-textured-lit','d-rig-poses','g-feet-top','g-feet-front']+['e-'+c for c in CLIPS]:
  data=json.loads((M/'renders'/stage/'render.json').read_text());size=data['resolution']
  assert data['blend_sha256']==sha(stage_blend(stage)),f'Stale stage {stage}'
  restdata=json.loads((M/'renders/c-textured-lit/render.json').read_text())
  assert all(data[k]==restdata[k] for k in ('engine','device','resolution','samples')),f'Mixed stage settings {stage}'
  if size<512 and (M/'512'/stage).exists():
   import shutil;shutil.rmtree(M/'512'/stage)
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
 atlas=Image.new('RGBA',(width,height));meta={'version':2,'unit':SLUG,'frame':{'w':160,'h':160,'ax':54,'ay':141},'atlas':{'w':width,'h':height},'clips':{}};y=0
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
 report={'bytes':len(output.getvalue()),'quality':quality,'frames':40,'alpha_levels':32,'atlas_sha256':hashlib.sha256(output.getvalue()).hexdigest(),'source_sha256':hashes,'renders':renders,'grade':grade,'master_sha256':current,'rest_sha256':sha(M/'renders/c-textured-lit/00.png'),'metadata_sha256':sha(out/f'{SLUG}.json'),'approval':'round 1 candidate; no PASS'}
 (M/'pack.json').write_text(json.dumps(report,indent=2));(V/f'{SLUG}-pack.json').write_text(json.dumps(report,indent=2));print('PACK',len(output.getvalue()),'bytes quality',quality)
 # Regenerate review images from the graded masters, preserving raw render outputs.
 for stage in ['b-plain','c-textured-lit','d-rig-poses','g-feet-top','g-feet-front']+['e-'+c for c in CLIPS]:review(stage,True)
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
 assert sha(p)==report['atlas_sha256'],'Atlas changed after packing'
 assert sha(p.with_suffix('.json'))==report['metadata_sha256'],'Metadata changed after packing'
 assert sha(M/f'{SLUG}.blend')==report['master_sha256'],'Master changed after packing'
 assert sha(M/'renders/c-textured-lit/00.png')==report['rest_sha256'],'Rest changed after packing'
 assert json.loads((M/'grade.json').read_text())==report['grade'],'Grade changed after packing'
 for name,render in report['renders'].items():
  assert sha(M/'clips'/f'{name}.blend')==render['blend_sha256'],'Clip changed after render'
  assert json.loads((M/'clips'/f'{name}.json').read_text())['source_sha256']==report['master_sha256']
 for frame,digest in report['source_sha256'].items():
  name,index=frame.split('/');assert sha(M/'renders'/f'e-{name}'/f'{int(index):02}.png')==digest,'Frame changed after packing'
 assert im.size==(meta['atlas']['w'],meta['atlas']['h']) and im.getchannel('A').getextrema()==(0,255)
 assert meta['frame']=={'w':160,'h':160,'ax':54,'ay':141}
 for row,(name,(n,fps,loop)) in enumerate(CLIPS.items()):
  c=meta['clips'][name];assert c['row']==row and c['frames']==n and c['fps']==fps and c['loop']==loop and len(c['rects'])==n
  assert len({f.tobytes() for f in clips[name]})>1,(name,'no animation')
  for index,r in enumerate(c['rects']):
   source=Image.open(M/'renders'/f'e-{name}'/f'{index:02}.png').convert('RGBA').resize((160,160),Image.Resampling.LANCZOS)
   alpha=source.getchannel('A').point(lambda x:round(round(x*31/255)*255/31))
   assert clips[name][index].getchannel('A').tobytes()==alpha.tobytes(),(name,index,'alpha/offset mismatch')
   assert 0<=r['ox']<160 and 0<=r['oy']<160 and r['ox']+r['w']<=160 and r['oy']+r['h']<=160
   assert r['x']+r['w']<=im.width and r['y']+r['h']<=im.height
 assert (M/'renders/e-death/08.png').read_bytes()==(M/'renders/e-death/09.png').read_bytes(),'Death must hold'
 result={'status':'pass','frames':sum(len(f) for f in clips.values()),'bytes':p.stat().st_size,'quality':report['quality'],'checks':['trim reconstruction','40 frames','clip fps and loops','alpha','motion','terminal death hold','source and render hashes at pack'],'visual_approval':False}
 sheet=Image.new('RGBA',(10*160,5*184),CREAM);draw=ImageDraw.Draw(sheet)
 for row,(name,frames) in enumerate(clips.items()):
  for index,frame in enumerate(frames):sheet.paste(tile(frame,160),(index*160,row*184+20));draw.text((index*160+4,row*184+3),f'{name} {index+1}',fill='black')
 sheet.save(V/f'{SLUG}-g-decoded-atlas.png')
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
 probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','stream=codec_name,pix_fmt,width,height,nb_frames:format=duration','-of','json',str(out)]));assert (probe['streams'][0]['width'],probe['streams'][0]['height'])==(1600,348)
 assert probe['streams'][0]['codec_name']=='h264' and probe['streams'][0]['pix_fmt']=='yuv420p' and int(probe['streams'][0]['nb_frames'])==240 and abs(float(probe['format']['duration'])-8)<.05
 (V/f'{SLUG}-video.json').write_text(json.dumps(probe,indent=2));print('VIDEO',out)

def gpu_receipt():
 stages=['b-plain','c-textured-lit','d-rig-poses','g-feet-top','g-feet-front']+['e-'+c for c in CLIPS]
 for stage in stages:
  data=json.loads((M/'renders'/stage/'render.json').read_text())
  assert data['device']=='GPU' and data['engine']=='CYCLES' and data['resolution']==512 and data['samples']>=48,(stage,'not final GPU output')
  assert data['blend_sha256']==sha(stage_blend(stage))
  for size in (512,256):
   files=list((M/str(size)/stage).glob('[0-9][0-9].png'));assert len(files)==data['frames']
   assert all(Image.open(f).size==(size,size) for f in files)
 validate()
 round_number=os.environ.get('ROUND','1')
 movie=V/f'{SLUG}-round{round_number}.mp4';assert movie.exists()
 receipt={'round':round_number,'master_sha256':sha(M/f'{SLUG}.blend'),'atlas_sha256':sha(Path(f'app/src/assets/units/anim/{SLUG}.webp')),'movie_sha256':sha(movie),'stages':stages,'device':'GPU','resolution':512,'visual_approval':False}
 (V/f'{SLUG}-round{round_number}-gpu.json').write_text(json.dumps(receipt,indent=2))
 print('GPU delivery verified; visual review pending')

if __name__=='__main__' and sys.argv[1]!='review':
 {'pack':pack,'validate':validate,'video':video,'gpu-receipt':gpu_receipt}[sys.argv[1]]()
