"""One temporal grade, review sheets, 512/256 masters and trimmed 160 px delivery."""
import argparse,hashlib,io,json,os
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops
R=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')));M=R/'masters/pikeman';V=R/'review/3d-v2';SLUG='pikeman'
CLIPS={'idle':(8,10,True),'move':(8,12,True),'attack':(10,14,False),'hit':(4,12,False),'death':(10,10,False)}
CREAM=(233,207,160,255)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def quantiles(im,c):
 h=im.getchannel(c).histogram(mask=im.getchannel('A').point(lambda x:255 if x>100 else 0));total=sum(h);out=[]
 for k in range(17):
  target=total*(.01+.98*k/16);acc=0
  for i,n in enumerate(h):
   acc+=n
   if acc>=target:out.append(i);break
 return out

def grade_lut(src,target):
 tables=[]
 for c in ['R','G','B']:
  a=quantiles(src,c);b=quantiles(target,c);lut=[]
  for x in range(256):
   j=next((i for i in range(15,-1,-1) if x>=a[i]),0);t=max(0,min(1,(x-a[j])/max(1,a[j+1]-a[j])));y=b[j]+t*(b[j+1]-b[j]);lut.append(round(.50*x+.50*y))
  tables.append(lut)
 return tables

def grade(im,luts):
 return Image.merge('RGBA',tuple(im.getchannel(c).point(lut) for c,lut in zip(['R','G','B'],luts))+(im.getchannel('A'),))
def panel(ims,labels,size=256):
 out=Image.new('RGBA',(len(ims)*size,size+26),CREAM);d=ImageDraw.Draw(out)
 for i,(im,label) in enumerate(zip(ims,labels)):
  out.alpha_composite(im.resize((size,size),Image.Resampling.LANCZOS),(i*size,26));d.text((i*size+6,7),label,fill='#3e3025')
 return out

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--resolution',type=int,default=256);ap.add_argument('--review-only',action='store_true');args=ap.parse_args();raw=M/'renders'/str(args.resolution)
 ref=Image.open('app/src/assets/units/pikeman-256.png').convert('RGBA');rest=Image.open(raw/'c-textured-lit/00.png').convert('RGBA');luts=grade_lut(rest.resize((256,256)),ref)
 rest_manifest=json.loads((raw/'c-textured-lit/render.json').read_text())
 if args.review_only and rest_manifest['blend_sha256']!=sha(M/f'{SLUG}.blend'):return
 assert rest_manifest['blend_sha256']==sha(M/f'{SLUG}.blend'),'stale rest calibration'
 (M/'grade.json').write_text(json.dumps({'method':'50 percent monotonic 17-quantile foreground RGB transfer; fixed for all clips','rest_sha256':sha(raw/'c-textured-lit/00.png'),'reference_sha256':sha(Path('app/src/assets/units/pikeman-256.png')),'master_sha256':sha(M/f'{SLUG}.blend'),'lut':luts},indent=2))
 graded={};sources={}
 for folder in sorted(raw.iterdir()):
  if not (folder/'render.json').exists():continue
  manifest=json.loads((folder/'render.json').read_text());stage=folder.name
  source=M/'clips'/f'{stage[2:]}.blend' if stage.startswith('e-') else M/'clips/attack.blend' if stage=='d-rig-poses' else M/('plain.blend' if stage=='b-plain' else SLUG+'.blend')
  if args.review_only and manifest['blend_sha256']!=sha(source):continue
  if args.review_only and any(manifest[k]!=rest_manifest[k] for k in ['engine','device','samples','resolution']):continue
  if source.parent.name=='clips':
   info=json.loads(source.with_suffix('.json').read_text())
   if args.review_only and info['source_master_sha256']!=sha(M/f'{SLUG}.blend'):continue
   assert info['source_master_sha256']==sha(M/f'{SLUG}.blend'),(stage,'stale clip')
  assert manifest['blend_sha256']==sha(source),(stage,'stale render')
  assert all(manifest[k]==rest_manifest[k] for k in ['engine','device','samples','resolution']),(stage,'mixed render settings')
  sources[stage]=manifest;ims=[]
  for i in range(manifest['frames']):
   im=Image.open(folder/f'{i:02}.png').convert('RGBA');im=im if stage=='b-plain' else grade(im,luts)
   for sz in sorted({256,args.resolution}):
    target=M/'graded'/str(sz)/stage;target.mkdir(parents=True,exist_ok=True);im.resize((sz,sz),Image.Resampling.LANCZOS).save(target/f'{i:02}.png')
   ims.append(im.resize((256,256),Image.Resampling.LANCZOS))
  graded[stage]=ims
  if stage.startswith('e-'):
   clip=stage[2:];n,fps,loop=CLIPS[clip];assert len(ims)==n
   top=panel(ims,[f'{clip} {i+1}' for i in range(n)]);sheet=Image.new('RGBA',(top.width,top.height+88),CREAM);sheet.alpha_composite(top)
   for i,im in enumerate(ims):sheet.alpha_composite(im.resize((64,64),Image.Resampling.LANCZOS),(i*256+96,top.height+12))
   sheet.save(V/f'{SLUG}-{stage}-strip.png');ims[0].save(V/f'{SLUG}-{stage}.webp',save_all=True,append_images=ims[1:],duration=round(1000/fps),loop=0,lossless=True)
  elif stage=='d-rig-poses':panel(ims,['guard','anticipation','thrust','recover']).save(V/f'{SLUG}-{stage}.png')
  elif stage!='c-details':
   top=panel([ref,ims[0]],['painting','3D '+manifest['device']]);sheet=Image.new('RGBA',(512,370),CREAM);sheet.alpha_composite(top);sheet.alpha_composite(ref.resize((64,64)),(96,294));sheet.alpha_composite(ims[0].resize((64,64)),(352,294));sheet.save(V/f'{SLUG}-{stage}.png')
 if 'c-textured-lit' in graded:
  rest=graded['c-textured-lit'][0];half=ref.copy();half.paste(rest.crop((128,0,256,256)),(128,0));cross=Image.blend(ref,rest,.5)
  comparison=panel([ref,rest,half,cross],['painting','3D rest','half split','50/50 crossfade'])
  sheet=Image.new('RGBA',(comparison.width,370),CREAM);sheet.alpha_composite(comparison)
  for i,im in enumerate([ref,rest,half,cross]):sheet.alpha_composite(im.resize((64,64),Image.Resampling.LANCZOS),(i*256+96,294))
  sheet.save(V/f'{SLUG}-f-restpose-compare.png')
  boxes=[(82,64,130,111),(66,94,143,173),(65,170,166,228)]
  details=[];labels=[]
  detail=graded.get('c-details',[rest])[0]
  for name,box in zip(['helmet / face','armour / grips','greaves / boots'],boxes):details.extend([ref.crop(box),detail.crop(box)]);labels.extend([name+' painting',name+' 3D'])
  panel(details,labels,256).save(V/f'{SLUG}-c-details.png')
 if args.review_only:return
 frames={};rows=[];rects={};y=1;maxw=0
 for row,(clip,(n,fps,loop)) in enumerate(CLIPS.items()):
  info=json.loads((M/'clips'/f'{clip}.json').read_text());assert info['source_master_sha256']==sha(M/f'{SLUG}.blend'),'stale animation'
  x=1;height=0;rowitems=[];unique={}
  for i,im in enumerate(graded['e-'+clip]):
   im=im.resize((160,160),Image.Resampling.BICUBIC);alpha=im.getchannel('A');im.paste((0,0,0,0),mask=alpha.point(lambda a:255 if a==0 else 0));box=alpha.getbbox();assert box
   key=hashlib.sha256(im.tobytes()).hexdigest()
   if key in unique:
    rects[clip,i]=unique[key];frames[clip,i]=im;continue
   crop=im.crop(box);rects[clip,i]={'x':x,'y':y,'w':crop.width,'h':crop.height,'ox':box[0],'oy':box[1]};rowitems.append((crop,x,y));x+=crop.width+2;height=max(height,crop.height);frames[clip,i]=im
   unique[key]=rects[clip,i]
  rows+=rowitems;maxw=max(maxw,x);y+=height+2
 atlas=Image.new('RGBA',(maxw,y))
 for crop,x,y in rows:atlas.paste(crop,(x,y))
 attempts=[]
 for quality in [90,85,80,75]:
  out=io.BytesIO();atlas.save(out,format='WEBP',quality=quality,method=6,exact=True);data=out.getvalue();attempts.append({'quality':quality,'bytes':len(data)})
  if len(data)<=200000:break
 else:raise RuntimeError('Atlas too large at quality 75; no frame or quality reduction allowed')
 decoded=Image.open(io.BytesIO(data)).convert('RGBA');assert decoded.getchannel('A').tobytes()==atlas.getchannel('A').tobytes(),'Alpha changed'
 meta={'version':2,'atlas':{'w':atlas.width,'h':atlas.height},'frame':{'w':160,'h':160,'ax':70,'ay':140},'clips':{}}
 for row,(clip,(n,fps,loop)) in enumerate(CLIPS.items()):meta['clips'][clip]={'row':row,'frames':n,'fps':fps,'loop':loop,'rects':[rects[clip,i] for i in range(n)]}
 target=Path('app/src/assets/units/anim');target.mkdir(parents=True,exist_ok=True);(target/f'{SLUG}.webp').write_bytes(data);(target/f'{SLUG}.json').write_text(json.dumps(meta,separators=(',',':'))+'\n')
 report={'bytes':len(data),'quality':quality,'frames':40,'logical_size':160,'alpha':'lossless 8-bit','source_resolution':args.resolution,'attempts':attempts,'render_sources':sources,'atlas_sha256':sha(target/f'{SLUG}.webp'),'master_sha256':sha(M/f'{SLUG}.blend'),'grade_sha256':sha(M/'grade.json'),'frames_sha256':{f'{c}/{i}':sha(M/'graded/256'/('e-'+c)/f'{i:02}.png') for c,i in frames}}
 (V/f'{SLUG}-pack.json').write_text(json.dumps(report,indent=2));print('PACK_OK',len(data),'bytes','quality',quality,'40 frames')
if __name__=='__main__':main()
