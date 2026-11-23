"""Grade, review, pack trimmed frames, validate and encode the knight round.

Raw renders are immutable inputs. One mild rest-fitted LUT is shared across the
whole round. Every decoded atlas rectangle reconstructs into a 160px canvas.
"""
import os,json,hashlib,io,subprocess,tempfile,argparse
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops
R=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')));M=R/'masters/knight';V=R/'review/3d-v2';OUT=Path('app/src/assets/units/anim')
CLIPS={'idle':(8,10,True),'move':(8,12,True),'attack':(10,14,False),'hit':(4,12,False),'death':(10,10,False)}
CREAM=(240,232,214,255)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return Image.open(p).convert('RGBA')
def label_sheet(images,labels,size=256):
 canvas=Image.new('RGBA',(len(images)*size,size+24),CREAM);d=ImageDraw.Draw(canvas)
 for i,(im,label) in enumerate(zip(images,labels)):
  canvas.alpha_composite(im.resize((size,size),Image.Resampling.LANCZOS),(i*size,24));d.text((i*size+5,5),label,fill=(60,50,40))
 return canvas

def grade(resolution):
 folder=M/'renders'/str(resolution);ref=load('app/src/assets/units/knight-256.png');rest=load(folder/'c/hero-00.png');luts=[];stats={}
 for c in 'RGB':
  def quant(im):
   hist=im.getchannel(c).histogram(mask=im.getchannel('A').point(lambda a:255 if a>128 else 0));total=sum(hist);vals=[]
   for i in range(17):
    threshold=total*(.02+.96*i/16);acc=0
    for x,n in enumerate(hist):
     acc+=n
     if acc>=threshold:vals.append(x);break
   return vals
  a,b=quant(rest),quant(ref);lut=[]
  for x in range(256):
   if x<=a[0]:y=x+b[0]-a[0]
   elif x>=a[-1]:y=x+b[-1]-a[-1]
   else:
    k=next(k for k in range(16) if a[k]<=x<=a[k+1]);t=(x-a[k])/max(1,a[k+1]-a[k]);y=b[k]+t*(b[k+1]-b[k])
   lut.append(round(max(0,min(255,x*.85+y*.15))))
  luts.append(lut);stats[c]={'render':a,'painting':b}
 (M/'grade.json').write_text(json.dumps({'method':'17 foreground quantiles, 15% transfer, same LUT for all frames','luts':luts,'quantiles':stats},indent=2))
 for stage in ['b','c','d','g']+[f'e-{c}' for c in CLIPS]:
  source=folder/stage;manifest=json.loads((source/'manifest.json').read_text())
  assert manifest['resolution']==resolution
  assert sha(manifest['blend'])==manifest['blend_sha256'],f'Stale blend: {stage}'
  if os.environ.get('REQUIRE_GPU')=='1':assert manifest['device']=='GPU' and resolution==512 and manifest['samples']>=64
  for record in manifest['frames']:
   p=source/record['file'];assert sha(p)==record['sha256'],f'Stale frame {p}'
   im=load(p);assert im.size==(resolution,resolution)
   if stage!='b':im=Image.merge('RGBA',[im.getchannel(c).point(lut) for c,lut in zip('RGB',luts)]+[im.getchannel('A')])
   for size in sorted(set([256,resolution])):
    dest=M/str(size)/stage;dest.mkdir(parents=True,exist_ok=True);im.resize((size,size),Image.Resampling.LANCZOS).save(dest/p.name)
  dest=M/str(resolution)/stage;(dest/'manifest.json').write_text(json.dumps(manifest,indent=2))

def review():
 ref=load('app/src/assets/units/knight-256.png');rest=load(M/'256/c/hero-00.png')
 label_sheet([ref,load(M/'256/b/hero-00.png')],['Painting','Plain geometry']).save(V/'knight-b-plain.png')
 label_sheet([ref,rest],['Painting','Round '+os.environ.get('ROUND','2')+' painted 3D']).save(V/'knight-c-textured-lit.png')
 split=ref.copy();split.paste(rest.crop((128,0,256,256)),(128,0));blend=Image.blend(ref,rest,.5)
 big=label_sheet([ref,rest,split,blend],['Painting','3D rest','Split 50/50','Crossfade 50/50']);small=label_sheet([ref,rest,split,blend],['Art','3D','Split','Blend'],64)
 sheet=Image.new('RGBA',(1024,368),CREAM);sheet.alpha_composite(big,(0,0));sheet.alpha_composite(small,(0,280));sheet.save(V/'knight-f-restpose-compare.png')
 boxes=[(108,55,140,89),(132,86,165,149),(73,142,125,204)];detail=[];labels=[]
 for box,name in zip(boxes,['Helmet','Shield','Caparison']):
  detail.extend([ref.crop(box),rest.crop(box)]);labels.extend([name+' painting',name+' 3D'])
 label_sheet(detail,labels,192).save(V/'knight-c-details.png')
 poses=[load(p) for p in sorted((M/'256/d').glob('hero-*.png'))];label_sheet(poses,['Attack '+str(i) for i in range(len(poses))]).save(V/'knight-d-rig-poses.png')
 for name,(count,fps,_) in CLIPS.items():
  frames=[load(M/f'256/e-{name}/hero-{i:02d}.png') for i in range(count)]
  strip=label_sheet(frames,[f'{name} {i+1}' for i in range(count)]);small=label_sheet(frames,['']*count,64)
  sheet=Image.new('RGBA',(count*256,368),CREAM);sheet.alpha_composite(strip);sheet.alpha_composite(small,(0,280));sheet.save(V/f'knight-e-{name}-strip.png')
  frames[0].save(V/f'knight-e-{name}.webp',save_all=True,append_images=frames[1:],duration=round(1000/fps),loop=0,quality=85,method=6)
 rows=[]
 for view in ['front','top']:
  rows.append(label_sheet([load(M/f'256/g/{view}-{i:02d}.png') for i in range(8)],[f'{view} move {i+1}' for i in range(8)],192))
 check=Image.new('RGBA',(1536,432),CREAM);check.alpha_composite(rows[0]);check.alpha_composite(rows[1],(0,216));check.save(V/'knight-g-feet-check.png')

def pack():
 meta={'version':2,'layout':'trimmed-rows','frame':{'w':160,'h':160,'ax':79,'ay':144},'atlas':{},'clips':{}}
 allrows=[];y=1;maxwidth=0;hashes={}
 for row,(name,(count,fps,loop)) in enumerate(CLIPS.items()):
  frames=[];rects=[];x=1;maxheight=0
  for i in range(count):
   p=M/f'256/e-{name}/hero-{i:02d}.png';im=load(p).resize((160,160),Image.Resampling.LANCZOS);im.putalpha(im.getchannel('A').point(lambda v:round(v/255*31)*255//31));box=im.getchannel('A').getbbox();assert box,f'Blank {name} {i}'
   ox,oy,ex,ey=box;patch=im.crop(box);w,h=patch.size
   if name=='death' and i==count-1 and frames and patch.tobytes()==frames[-1].tobytes() and (ox,oy)==(rects[-1]['ox'],rects[-1]['oy']):
    rects.append(dict(rects[-1]));frames.append(patch);hashes[str(p)]=sha(p);continue
   rects.append({'x':x,'y':y,'w':w,'h':h,'ox':ox,'oy':oy});frames.append(patch);hashes[str(p)]=sha(p);x+=w+2;maxheight=max(maxheight,h)
  meta['clips'][name]={'row':row,'frames':count,'fps':fps,'loop':loop,'rects':rects};allrows.append(frames);y+=maxheight+2;maxwidth=max(maxwidth,x)
 atlas=Image.new('RGBA',(maxwidth,y));meta['atlas']={'w':maxwidth,'h':y}
 for (name,c),frames in zip(meta['clips'].items(),allrows):
  for rect,im in zip(c['rects'],frames):atlas.paste(im,(rect['x'],rect['y']))
 for quality in [90,85,80,75]:
  buffer=io.BytesIO();atlas.save(buffer,format='WEBP',quality=quality,method=6,exact=True);data=buffer.getvalue()
  if len(data)<=200000:break
 assert len(data)<=200000,'Cannot meet byte budget at quality >=75'
 OUT.mkdir(parents=True,exist_ok=True);(OUT/'knight.webp').write_bytes(data);(OUT/'knight.json').write_text(json.dumps(meta,indent=2)+'\n')
 (M/'pack.json').write_text(json.dumps({'quality':quality,'bytes':len(data),'atlas_sha256':sha(OUT/'knight.webp'),'metadata_sha256':sha(OUT/'knight.json'),'frames':hashes,'grade_sha256':sha(M/'grade.json'),'blend_sha256':sha(M/'knight.blend')},indent=2));print('PACK',len(data),'bytes quality',quality)

def reconstruct(atlas,rect):
 im=Image.new('RGBA',(160,160));x,y,w,h=(rect[n] for n in ['x','y','w','h']);im.paste(atlas.crop((x,y,x+w,y+h)),(rect['ox'],rect['oy']));return im

def validate():
 report=json.loads((M/'pack.json').read_text());meta=json.loads((OUT/'knight.json').read_text());atlas=load(OUT/'knight.webp')
 assert report['bytes']==(OUT/'knight.webp').stat().st_size<=200000 and report['quality']>=75
 assert report['atlas_sha256']==sha(OUT/'knight.webp') and report['metadata_sha256']==sha(OUT/'knight.json')
 assert report['blend_sha256']==sha(M/'knight.blend') and report['grade_sha256']==sha(M/'grade.json')
 assert atlas.size==(meta['atlas']['w'],meta['atlas']['h']);assert atlas.getchannel('A').getextrema()==(0,255)
 occupied=[];warnings=[]
 for name,(count,fps,loop) in CLIPS.items():
  c=meta['clips'][name];assert (c['frames'],c['fps'],c['loop'])==(count,fps,loop);assert len(c['rects'])==count;decoded=[]
  for i,r in enumerate(c['rects']):
   assert all(isinstance(v,int) for v in r.values());x,y,w,h=(r[k] for k in ['x','y','w','h']);assert w>0 and h>0 and x>=0 and y>=0 and x+w<=atlas.width and y+h<=atlas.height
   assert 0<=r['ox']<=160-w and 0<=r['oy']<=160-h
   box=(x,y,x+w,y+h)
   assert not any(x<b[2] and x+w>b[0] and y<b[3] and y+h>b[1] for b in occupied if b!=box);occupied.append(box)
   p=M/f'256/e-{name}/hero-{i:02d}.png';assert report['frames'][str(p)]==sha(p);source=load(p).resize((160,160),Image.Resampling.LANCZOS)
   quant=source.getchannel('A').point(lambda v:round(v/255*31)*255//31);im=reconstruct(atlas,r)
   assert ImageChops.difference(quant,im.getchannel('A')).getbbox() is None
   assert ImageChops.difference(source.getchannel('A'),quant).getextrema()[1]<=5
   b=im.getchannel('A').point(lambda v:255 if v>32 else 0).getbbox();assert b and min(b[0],b[1],160-b[2],160-b[3])>=1,f'Clipping {name} {i}'
   decoded.append(im.tobytes())
  assert len(set(decoded))>1,f'Static clip {name}'
  if name=='death':assert decoded[-1]==decoded[-2],'Death must hold'
 result={'passed':True,'frames':40,'bytes':report['bytes'],'quality':report['quality'],'alpha_max_error':5,'checks':['hash provenance','counts and timing','bounds and no overlap','trim reconstruction','transparent alpha','clipping margin','motion present','death held'],'art_approved':False}
 (M/'validation.json').write_text(json.dumps(result,indent=2));print('VALIDATED',json.dumps(result))

def movie():
 meta=json.loads((OUT/'knight.json').read_text());atlas=load(OUT/'knight.webp');clips={n:[reconstruct(atlas,r).resize((320,320),Image.Resampling.LANCZOS) for r in c['rects']] for n,c in meta['clips'].items()};path=V/f"knight-round{os.environ.get('ROUND','1')}.mp4"
 with tempfile.TemporaryDirectory(prefix='knight-movie-',dir=R/'tmp') as tmp:
  for t in range(240):
   canvas=Image.new('RGBA',(1600,348),CREAM);d=ImageDraw.Draw(canvas)
   for col,(name,c) in enumerate(meta['clips'].items()):
    i=int(t/30*c['fps'])%c['frames'] if c['loop'] else min(int((t%60)/30*c['fps']),c['frames']-1)
    canvas.alpha_composite(clips[name][i],(col*320,28));d.text((col*320+8,7),name,fill=(60,50,40))
   canvas.convert('RGB').save(Path(tmp)/f'{t:04d}.png')
  subprocess.run(['ffmpeg','-y','-loglevel','error','-threads','2','-framerate','30','-i',str(Path(tmp)/'%04d.png'),'-c:v','libx264','-threads','2','-pix_fmt','yuv420p','-crf','20','-movflags','+faststart',str(path)],check=True)
 probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=codec_name,pix_fmt,nb_read_frames,width,height:format=duration','-of','json',str(path)]));s=probe['streams'][0]
 assert s['codec_name']=='h264' and s['pix_fmt']=='yuv420p' and int(s['nb_read_frames'])==240 and float(probe['format']['duration'])==8
 (M/'movie.json').write_text(json.dumps(probe,indent=2));print('MOVIE_VALIDATED',path)

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('task',choices=['all','review','validate','movie']);parser.add_argument('--resolution',type=int,default=256);a=parser.parse_args()
 if a.task=='all':grade(a.resolution);review();pack();validate();movie()
 elif a.task=='review':review()
 elif a.task=='validate':validate()
 else:movie()
