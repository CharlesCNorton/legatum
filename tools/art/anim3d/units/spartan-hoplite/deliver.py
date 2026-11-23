"""Painting preparation, review sheets, 160px trim metadata and source-bound validation."""
import os,sys,json,hashlib,io
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops,ImageStat
R=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')));M=Path(os.environ.get('ANIM_MASTER',str(R/'masters/spartan-hoplite/round4-3d')));A=R/'assets/spartan-hoplite';REV=R/'review/3d-v2';SLUG='spartan-hoplite'
CLIPS={'idle':(8,4,True),'move':(8,6,True),'attack':(10,14,False),'hit':(4,8,False),'death':(10,5,False)}
REF=Path('app/src/assets/units/spartan-hoplite-256.png');OUT=Path('app/src/assets/units/anim')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def log(s):
 with (REV/(SLUG+'-log.md')).open('a') as f:f.write(s+'\n')
def prepare():
 source=Image.open(A/'painting-source.png').convert('RGBA');token=Image.open(REF).convert('RGBA');box=token.getchannel('A').getbbox();crop=source.crop(source.getchannel('A').getbbox());aligned=Image.new('RGBA',(1024,1024));aligned.alpha_composite(crop.resize(((box[2]-box[0])*4,(box[3]-box[1])*4),Image.Resampling.LANCZOS),(box[0]*4,box[1]*4));aligned.save(A/'painting-aligned.png')
 # Restrict projections by pigment; prevents cloak red bleeding onto linen/skin.
 for kind in ['linen','red','bronze','skin']:
  im=aligned.copy();px=list(im.getdata());out=[]
  for r,g,b,a in px:
   accept={'linen':g>r*.69 and b>r*.47 and r>90,'red':r>g*1.45 and r>b*1.5,'bronze':r>g*1.12 and g>b*1.12,'skin':r>g*1.16 and g>b*1.1}[kind]
   out.append((r,g,b,a if accept else 0))
  im.putdata(out);im.save(A/f'projection-{kind}.png')
 (A/'sources.json').write_text(json.dumps({'painting_sha256':sha(A/'painting-source.png'),'aligned_sha256':sha(A/'painting-aligned.png'),'token_sha256':sha(REF),'licence':'Project CC BY 4.0'},indent=2))
def quantiles(im,ch):
 h=im.getchannel(ch).histogram(mask=im.getchannel('A').point(lambda x:255 if x>160 else 0));n=sum(h);out=[]
 for j in range(17):
  threshold=n*(.02+.96*j/16);acc=0
  for x,v in enumerate(h):
   acc+=v
   if acc>=threshold:out.append(x);break
 return out
def grade(stage,images):
 if stage=='b':return images
 path=M/'grade.json'
 if stage=='c':
  ref=Image.open(REF).convert('RGBA');luts=[];stats={}
  for ch in 'RGB':
   a=quantiles(images[0],ch);b=quantiles(ref,ch);lut=[]
   for x in range(256):
    if x<=a[0]:y=x+b[0]-a[0]
    elif x>=a[-1]:y=x+b[-1]-a[-1]
    else:
     k=next(i for i in range(16) if a[i]<=x<=a[i+1]);t=(x-a[k])/max(1,a[k+1]-a[k]);y=b[k]+t*(b[k+1]-b[k])
    lut.append(round(max(0,min(255,x*.65+y*.35))))
   luts.append(lut);stats[ch]={'painting':b,'render':a}
  path.write_text(json.dumps({'luts':luts,'quantiles':stats,'method':'35 percent transfer; one rest-derived monotonic LUT across all frames'},indent=2))
 luts=json.loads(path.read_text())['luts']
 return [Image.merge('RGBA',[im.getchannel(ch).point(lut) for ch,lut in zip('RGB',luts)]+[im.getchannel('A')]) for im in images]
def sheet(images,labels,path,size=256):
 out=Image.new('RGB',(size*len(images),size+100),(222,210,187));d=ImageDraw.Draw(out)
 for i,(im,label) in enumerate(zip(images,labels)):
  thumb=im.resize((size,size),Image.Resampling.LANCZOS);out.paste(thumb,(i*size,22),thumb);d.text((i*size+6,4),label,fill=(35,29,20));small=im.resize((64,64),Image.Resampling.LANCZOS);out.paste(small,(i*size+size//2-32,size+28),small)
 out.save(path)
def review(stage):
 folder=M/'renders'/stage;meta=json.loads((folder/'render.json').read_text());paths=sorted(folder.glob('[0-9][0-9].png'));raw=[Image.open(p).convert('RGBA') for p in paths];images=grade(stage,raw)
 for size in [512,256]:
  # Never claim an upscaled CPU preview is a 512px rendered master.
  if meta['resolution']<size:continue
  dest=M/str(size)/stage;dest.mkdir(parents=True,exist_ok=True)
  for i,im in enumerate(images):im.resize((size,size),Image.Resampling.LANCZOS).save(dest/f'{i:02}.png')
  (dest/'render.json').write_text(json.dumps(meta,indent=2))
 if stage!='b':meta['grade_sha256']=sha(M/'grade.json')
 meta['raw_preserved']=True;(folder/'render.json').write_text(json.dumps(meta,indent=2))
 # The 256 gallery carries the same render provenance and grade hash.
 for size in [512,256]:
  if size<=meta['resolution']:(M/str(size)/stage/'render.json').write_text(json.dumps(meta,indent=2))
 ref=Image.open(REF).convert('RGBA')
 if stage=='b':sheet([ref]+images,['Painting','Front plain','3/4 plain','Side plain'],REV/(SLUG+'-b-plain.png'))
 elif stage=='c':
  im=images[0].resize((256,256),Image.Resampling.LANCZOS);sheet([ref,im],['Painting',f'{meta["device"]} Cycles {meta["resolution"]} px / {meta["samples"]} samples'],REV/(SLUG+'-c-textured-lit.png'))
  split=ref.copy();split.paste(im.crop((128,0,256,256)),(128,0));fade=Image.blend(ref,im,.5);sheet([ref,im,split,fade],['Painting','3D rest','Half split','50% crossfade'],REV/(SLUG+'-f-restpose-compare.png'))
  crops=[(101,22,149,87),(92,68,149,139),(132,82,188,174)]
  details=[];labels=[]
  for name,box in zip(['Helmet','Torso','Shield'],crops):
   for label,img in [('painting',ref),('render',im)]:details.append(img.crop(box));labels.append(name+' '+label)
  sheet(details,labels,REV/(SLUG+'-c-details.png'),180)
 elif stage=='d':sheet(images,['Attack '+str(i) for i in range(len(images))],REV/(SLUG+'-d-rig-poses.png'))
 else:
  clip=stage[2:];sheet(images,[clip+' '+str(i+1) for i in range(len(images))],REV/(SLUG+'-'+stage+'-strip.png'))
  frames=[im.resize((256,256),Image.Resampling.LANCZOS) for im in images];frames[0].save(REV/(SLUG+'-'+stage+'.webp'),save_all=True,append_images=frames[1:],duration=round(1000/CLIPS[clip][1]),loop=0,quality=88,method=6)
 log('Review '+stage+f': {meta["resolution"]}px {meta["engine"]}/{meta["device"]}, {meta["samples"]} samples; '+str(len(images))+' actual frames.')
def pack():
 atlas=Image.new('RGBA',(1600,800));clips={};records={}
 for row,(clip,(count,fps,loop)) in enumerate(CLIPS.items()):
  folder=M/'256'/('e-'+clip);clipmeta=json.loads((M/'clips'/clip/'clip.json').read_text());assert clipmeta['source_master_sha256']==sha(M/'spearman.blend'),'invalid clip rebuild';meta=json.loads((folder/'render.json').read_text());assert meta['source_master_sha256']==sha(M/'spearman.blend'),'stale source master';assert meta['blend_sha256']==sha(M/'clips'/clip/(clip+'.blend')),'stale clip';assert meta['grade_sha256']==sha(M/'grade.json'),'stale grade'
  entries=[];records[clip]={'render':meta,'sha256':[]}
  for i in range(count):
   path=folder/f'{i:02}.png';im=Image.open(path).convert('RGBA').resize((160,160),Image.Resampling.LANCZOS);box=im.getchannel('A').getbbox();assert box
   x,y,x1,y1=box;crop=im.crop(box);atlas.paste(crop,(i*160,row*160));entries.append({'x':i*160,'y':row*160,'w':x1-x,'h':y1-y,'ox':x,'oy':y});records[clip]['sha256'].append(sha(path))
  clips[clip]={'row':row,'frames':count,'fps':fps,'loop':loop,'rects':entries}
 OUT.mkdir(parents=True,exist_ok=True)
 # Quantize only alpha, preserve RGB; quality floor is the owner's 75.
 atlas.putalpha(atlas.getchannel('A').point(lambda a:round(a/17)*17))
 for quality in [90,85,80,75]:
  buf=io.BytesIO();atlas.save(buf,'WEBP',quality=quality,method=6,exact=True)
  if len(buf.getvalue())<=200000:break
 else:raise RuntimeError('Atlas exceeds 200 KB at quality 75; retain all frames and report')
 (OUT/(SLUG+'.webp')).write_bytes(buf.getvalue());data={'frame':{'w':160,'h':160,'ax':80,'ay':145},'clips':clips,'format':'trimmed-grid-v1'};(OUT/(SLUG+'.json')).write_text(json.dumps(data,indent=2)+'\n')
 (M/'pack.json').write_text(json.dumps({'quality':quality,'bytes':len(buf.getvalue()),'atlas_sha256':sha(OUT/(SLUG+'.webp')),'json_sha256':sha(OUT/(SLUG+'.json')),'clips':records},indent=2));print('PACKED',quality,len(buf.getvalue()))
def validate():
 meta=json.loads((OUT/(SLUG+'.json')).read_text());report=json.loads((M/'pack.json').read_text());atlas=Image.open(OUT/(SLUG+'.webp')).convert('RGBA');assert atlas.size==(1600,800);assert (OUT/(SLUG+'.webp')).stat().st_size<=200000;assert report['quality']>=75;assert report['atlas_sha256']==sha(OUT/(SLUG+'.webp'));assert report['json_sha256']==sha(OUT/(SLUG+'.json'))
 checks={}
 for clip,(count,fps,loop) in CLIPS.items():
  c=meta['clips'][clip];assert (c['frames'],c['fps'],c['loop'])==(count,fps,loop);assert len(c['rects'])==count
  images=[]
  folder=M/'256'/('e-'+clip);render=json.loads((folder/'render.json').read_text())
  assert render==report['clips'][clip]['render'],'render changed after packing'
  assert render['source_master_sha256']==sha(M/'spearman.blend'),'stale master'
  assert render['blend_sha256']==sha(M/'clips'/clip/(clip+'.blend')),'stale clip'
  assert render['grade_sha256']==sha(M/'grade.json'),'stale grade'
  for i,r in enumerate(c['rects']):
   assert 0<=r['ox']<160 and 0<=r['oy']<160 and r['ox']+r['w']<=160 and r['oy']+r['h']<=160
   path=folder/f'{i:02}.png';assert sha(path)==report['clips'][clip]['sha256'][i],'frame changed after packing'
   im=Image.open(path).convert('RGBA');images.append(im)
   assert r['x']==i*160 and r['y']==c['row']*160
   restored=Image.new('RGBA',(160,160));restored.paste(atlas.crop((r['x'],r['y'],r['x']+r['w'],r['y']+r['h'])),(r['ox'],r['oy']))
   expected=im.resize((160,160),Image.Resampling.LANCZOS)
   alpha_error=ImageChops.difference(restored.getchannel('A'),expected.getchannel('A')).getextrema()[1];assert alpha_error<=9,(clip,i,'alpha reconstruction',alpha_error)
   mask=expected.getchannel('A').point(lambda x:255 if x>128 else 0)
   error=ImageStat.Stat(ImageChops.difference(restored.convert('RGB'),expected.convert('RGB')),mask=mask).mean
   assert max(error)<14,(clip,i,'trim reconstruction',error)
   box=im.getchannel('A').point(lambda a:255 if a>20 else 0).getbbox();assert box and min(box)>0 and box[2]<256 and box[3]<256,(clip,i,'clipping',box)
  differences=[ImageChops.difference(images[i],images[i+1]).convert('RGB').getbbox() is not None for i in range(count-1)];assert any(differences),clip+' no movement'
  if clip=='death':assert images[-1].tobytes()==images[-2].tobytes(),'death must hold'
  checks[clip]={'frames':count,'motion':True,'inside_canvas':True,'trim_offsets':True}
 result={'status':'passed','checks':checks,'bytes':report['bytes'],'quality':report['quality'],'limits':'Technical validation only; not art approval. Frozen projection is view-dependent.'};(REV/(SLUG+'-validation.json')).write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':
 mode=sys.argv[1]
 if mode=='prepare':prepare()
 elif mode=='review':
  review(sys.argv[2])
  stop=M/'stop-after-stage'
  if stop.exists():
   stop.unlink();raise SystemExit('Stopped after completed review stage for a master revision')
 elif mode=='pack':pack()
 elif mode=='validate':validate()
 elif mode in {'video','verify-gpu'}:
  import handoff
  handoff.video() if mode=='video' else handoff.verify_gpu()
