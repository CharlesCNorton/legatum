"""Review, fixed rest-derived grade, trimmed 160 atlas, validation and MP4.

Frame offsets are measured in the original 160-square coordinate system.
The anchor stays common to all frames and is never inferred from their trim.
"""
from pathlib import Path
import os,sys,json,hashlib,io,subprocess,tempfile
from PIL import Image,ImageDraw
R=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')));M=R/'masters/tagmatic-soldier';REV=R/'review/3d-v2';SLUG='tagmatic-soldier';OUT=Path('app/src/assets/units/anim')
CLIPS={'idle':(8,10,True),'move':(8,12,True),'attack':(10,14,False),'hit':(4,12,False),'death':(10,10,False)}
CREAM=(233,207,160,255);BG=(240,232,214,255)
def read(p):return Image.open(p).convert('RGBA')
def shrink(im,n):return im.resize((n,n),Image.Resampling.LANCZOS)
def paste(canvas,im,x,y):canvas.alpha_composite(im,(x,y))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def quant(im,ch):
 h=im.getchannel(ch).histogram(mask=im.getchannel('A').point(lambda x:255 if x>192 else 0));tot=sum(h);q=[]
 for k in range(17):
  target=tot*(.02+.96*k/16);n=0
  for j,v in enumerate(h):
   n+=v
   if n>=target:q.append(j);break
 return q

def grade_fit():
 ref=read(f'app/src/assets/units/{SLUG}-256.png');raw=read(M/'renders/c/00.png');luts=[];stats={}
 for ch in 'RGB':
  a=quant(raw,ch);b=quant(ref,ch);lut=[]
  for x in range(256):
   if x<=a[0]:target=x+b[0]-a[0]
   elif x>=a[-1]:target=x+b[-1]-a[-1]
   else:
    k=next(k for k in range(16) if a[k]<=x<=a[k+1]);t=(x-a[k])/max(1,a[k+1]-a[k]);target=b[k]+t*(b[k+1]-b[k])
   lut.append(round(max(0,min(255,x*.55+target*.45))))
  stats[ch]={'painting':b,'render':a};luts.append(lut)
 (M/'grade.json').write_text(json.dumps({'method':'one rest-derived 17-quantile LUT, 45% transfer; identical across every clip','luts':luts,'stats':stats},indent=2))

def graded(im):
 luts=json.loads((M/'grade.json').read_text())['luts'];return Image.merge('RGBA',[im.getchannel(c).point(l) for c,l in zip('RGB',luts)]+[im.getchannel('A')])
def review(stage):
 folder=M/'renders'/stage;manifest=json.loads((folder/'render.json').read_text());ims=[read(folder/f'{i:02}.png') for i in range(manifest['frames'])]
 if stage=='c':grade_fit()
 if stage!='b':ims=[graded(im) for im in ims]
 for i,im in enumerate(ims):
  if im.width==512:
   d=M/'512'/stage;d.mkdir(parents=True,exist_ok=True);im.save(d/f'{i:02}.png')
  d=M/'256'/stage;d.mkdir(parents=True,exist_ok=True);shrink(im,256).save(d/f'{i:02}.png')
 ims=[shrink(im,256) for im in ims];ref=read(f'app/src/assets/units/{SLUG}-256.png')
 label=f'{SLUG} | {stage} | {manifest["engine"]} {manifest["device"]} {manifest["resolution"]}px'
 if stage=='b':
  sheet=Image.new('RGBA',(1024,370),BG);dr=ImageDraw.Draw(sheet);dr.text((8,8),label,fill='black')
  for k,(name,im) in enumerate(zip(['Painting','Matched camera / clay','60 degree orbit / clay','120 degree orbit / clay'],[ref]+ims)):
   paste(sheet,im,k*256,30);dr.text((k*256+8,288),name,fill='black');paste(sheet,shrink(im,64),k*256+96,306)
  sheet.save(REV/f'{SLUG}-b-plain.png')
 elif stage=='c':
  sheet=Image.new('RGBA',(768,384),BG);dr=ImageDraw.Draw(sheet);dr.text((12,8),label,fill='black')
  for i,im in enumerate([ref,ims[0],Image.blend(ref,ims[0],.5)]):paste(sheet,im,256*i,32);paste(sheet,shrink(im,64),256*i+96,300)
  dr.text((12,280),'Painting',fill='black');dr.text((268,280),'3D rest',fill='black');dr.text((524,280),'50/50 crossfade',fill='black')
  sheet.save(REV/f'{SLUG}-{"b-plain" if stage=="b" else "c-textured-lit"}.png')
  if stage=='c':
   sheet.save(REV/f'{SLUG}-f-restpose-compare.png')
   detail=Image.new('RGBA',(768,322),BG);dr=ImageDraw.Draw(detail)
   for k,(name,box) in enumerate([('Helmet / face',(96,13,140,70)),('Lamellar / sleeve',(62,47,111,126)),('Shield',(106,51,170,220))]):
    dr.text((k*256+5,5),name,fill='black')
    for j,im in enumerate([ref,ims[0]]):
     patch=im.crop(box);scale=min(124/patch.width,280/patch.height);patch=patch.resize((round(patch.width*scale),round(patch.height*scale)),Image.Resampling.LANCZOS);paste(detail,patch,k*256+j*128,30)
   detail.save(REV/f'{SLUG}-c-details.png')
 else:
  sheet=Image.new('RGBA',(256*len(ims),370),BG);dr=ImageDraw.Draw(sheet);dr.text((8,8),label,fill='black')
  for i,im in enumerate(ims):paste(sheet,im,i*256,30);paste(sheet,shrink(im,64),i*256+96,296)
  sheet.save(REV/f'{SLUG}-{"d-rig-poses" if stage=="d" else stage+"-strip"}.png')
  if stage.startswith('e-'):
   fps=CLIPS[stage[2:]][1];ims[0].save(REV/f'{SLUG}-{stage}.webp',save_all=True,append_images=ims[1:],duration=round(1000/fps),loop=0,quality=85,method=6)
 review_manifest={'render_sha256':sha(folder/'render.json'),'grade_sha256':sha(M/'grade.json') if stage!='b' else None,'frames256':{f'{i:02}.png':sha(M/'256'/stage/f'{i:02}.png') for i in range(len(ims))}}
 (folder/'review.json').write_text(json.dumps(review_manifest,indent=2))
 print('REVIEW_READY',stage)

def pack():
 frames={};manifest={};packed=[];rowheights=[]
 for row,(clip,(n,fps,loop)) in enumerate(CLIPS.items()):
  stage='e-'+clip;meta=json.loads((M/'renders'/stage/'render.json').read_text());assert meta['frames']==n;assert meta['blend_sha256']==sha(M/'clips'/f'{clip}.blend'),'Stale clip render'
  cm=json.loads((M/'clips'/f'{clip}.json').read_text());assert cm['source_sha256']==sha(M/f'{SLUG}.blend'),'Stale animation master'
  review_meta=json.loads((M/'renders'/stage/'review.json').read_text());assert review_meta['render_sha256']==sha(M/'renders'/stage/'render.json'),'Stale review';assert review_meta['grade_sha256']==sha(M/'grade.json'),'Stale grade'
  for filename,digest in review_meta['frames256'].items():assert digest==sha(M/'256'/stage/filename),'Changed frame'
  entries=[];x=0;height=0
  for i in range(n):
   p=M/'256'/stage/f'{i:02}.png';im=shrink(read(p),160);box=im.getchannel('A').getbbox();assert box,'Empty frame'
   # Preserve antialiasing and all alpha, with one-pixel trim gutter.
   l,t,r,b=box;l=max(0,l-1);t=max(0,t-1);r=min(160,r+1);b=min(160,b+1);patch=im.crop((l,t,r,b));w,h=patch.size
   entries.append({'x':x,'y':0,'w':w,'h':h,'ox':l,'oy':t});packed.append((row,patch,x));x+=w+2;height=max(height,h)
  frames[clip]={'row':row,'frames':n,'fps':fps,'loop':loop,'rects':entries};rowheights.append(height+2);manifest[clip]=meta
 width=max(sum(e['w']+2 for e in v['rects']) for v in frames.values());height=sum(rowheights);atlas=Image.new('RGBA',(width,height));yoffset=[sum(rowheights[:r]) for r in range(5)]
 for row,patch,x in packed:paste(atlas,patch,x,yoffset[row])
 for clip,v in frames.items():
  for e in v['rects']:e['y']=yoffset[v['row']]
 chosen=None
 for quality in [90,85,80,75]:
  buf=io.BytesIO();atlas.save(buf,format='WEBP',quality=quality,method=6,exact=True)
  if len(buf.getvalue())<=200000:chosen=(quality,buf.getvalue());break
 assert chosen,'Atlas exceeds 200 KB at quality 75; do not silently reduce quality'
 meta={'version':2,'unit':SLUG,'layout':'trimmed-rows','frame':{'w':160,'h':160,'ax':74,'ay':142},'clips':frames,'quality':chosen[0]}
 OUT.mkdir(exist_ok=True,parents=True);(OUT/f'{SLUG}.webp').write_bytes(chosen[1]);(OUT/f'{SLUG}.json').write_text(json.dumps(meta,indent=2)+'\n')
 (M/'pack.json').write_text(json.dumps({'bytes':len(chosen[1]),'quality':chosen[0],'atlas_sha256':sha(OUT/f'{SLUG}.webp'),'renders':manifest,'grade_sha256':sha(M/'grade.json')},indent=2))
 print('PACKED',len(chosen[1]),'bytes, quality',chosen[0])
def unpack(meta,atlas,clip):
 result=[]
 for e in meta['clips'][clip]['rects']:
  im=Image.new('RGBA',(160,160));im.alpha_composite(atlas.crop((e['x'],e['y'],e['x']+e['w'],e['y']+e['h'])),(e['ox'],e['oy']));result.append(im)
 return result

def validate():
 p=OUT/f'{SLUG}.webp';meta=json.loads(p.with_suffix('.json').read_text());atlas=read(p);assert p.stat().st_size<=200000;assert meta['quality']>=75;assert meta['frame']['w']==meta['frame']['h']==160
 report={'bytes':p.stat().st_size,'quality':meta['quality'],'clips':{}}
 for name,(n,fps,loop) in CLIPS.items():
  c=meta['clips'][name];assert c['frames']==n and len(c['rects'])==n and c['fps']==fps and c['loop']==loop
  for e in c['rects']:
   assert e['x']>=0 and e['y']>=0 and e['x']+e['w']<=atlas.width and e['y']+e['h']<=atlas.height
   assert 0<=e['ox'] and 0<=e['oy'] and e['ox']+e['w']<=160 and e['oy']+e['h']<=160
  ims=unpack(meta,atlas,name);assert all(im.getchannel('A').getextrema()==(0,255) for im in ims);assert len({im.tobytes() for im in ims})>1,'No motion'
  # Offset/sign errors are caught by exact alpha reconstruction, not only bounds.
  for i,im in enumerate(ims):
   expected=shrink(read(M/'256'/('e-'+name)/f'{i:02}.png'),160)
   assert im.getchannel('A').tobytes()==expected.getchannel('A').tobytes(),(name,i,'trim offset/alpha mismatch')
  margins=[]
  for im in ims:
   box=im.getchannel('A').point(lambda x:255 if x>32 else 0).getbbox();margins.append(min(box[0],box[1],160-box[2],160-box[3]))
  assert min(margins)>=1,(name,'frame clipping',margins)
  if name=='death':
   # Compare lossless masters because separate lossy atlas regions need not decode identically.
   assert read(M/'256/e-death/08.png').tobytes()==read(M/'256/e-death/09.png').tobytes(),'Death not held'
  report['clips'][name]={'frames':n,'minimum_margin':min(margins),'motion':True}
 (M/'validation.json').write_text(json.dumps(report,indent=2));print('VALIDATED',json.dumps(report))

def video():
 meta=json.loads((OUT/f'{SLUG}.json').read_text());atlas=read(OUT/f'{SLUG}.webp');frames={c:[shrink(im,320) for im in unpack(meta,atlas,c)] for c in CLIPS}
 out=REV/f'{SLUG}-round{os.environ.get("ROUND","1")}.mp4'
 proc=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s','1600x348','-r','30','-i','-','-an','-c:v','libx264','-threads','2','-pix_fmt','yuv420p','-crf','20','-movflags','+faststart',str(out)],stdin=subprocess.PIPE)
 for t in range(240):
  canvas=Image.new('RGBA',(1600,348),CREAM);d=ImageDraw.Draw(canvas)
  for k,(name,(n,fps,loop)) in enumerate(CLIPS.items()):
   i=int(t/30*fps)%n if loop else min(int((t%60)/30*fps),n-1);paste(canvas,frames[name][i],k*320,28);d.text((k*320+8,8),name,fill=(60,45,25,255))
  proc.stdin.write(canvas.convert('RGB').tobytes())
 proc.stdin.close();assert proc.wait()==0
 print('VIDEO_READY',out)
if __name__=='__main__':
 command=sys.argv[1]
 if command=='review':review(sys.argv[2])
 elif command=='pack':pack()
 elif command=='validate':validate()
 elif command=='video':video()
