"""Grade once, retain masters, build reviews, trim 160px frames and validate delivery."""
import os,json,hashlib,io,subprocess,tempfile,sys
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops
R=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')));M=R/'masters/keshig';Q=R/'review/3d-v2'
CLIPS={'idle':(8,10,True),'move':(8,12,True),'attack':(10,14,False),'hit':(4,12,False),'death':(10,10,False)}
CREAM=(233,207,160,255);ref=Image.open('app/src/assets/units/keshig-256.png').convert('RGBA')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def quantiles(im,c):
 mask=im.getchannel('A').point(lambda a:255 if a>128 else 0);hist=im.getchannel(c).histogram(mask);total=sum(hist);out=[];cum=0;idx=0
 for q in range(17):
  target=q/16*max(0,total-1)
  while idx<255 and cum+hist[idx]<=target:cum+=hist[idx];idx+=1
  out.append(idx)
 return out
def lut_for(raw):
 lut=[]
 for c in range(3):
  a=quantiles(raw,c);b=quantiles(ref,c);tab=[]
  for v in range(256):
   j=next((j for j in range(15) if v<a[j+1]),15)
   t=max(0,min(1,(v-a[j])/max(1,a[j+1]-a[j])));mapped=b[j]+t*(b[j+1]-b[j]);tab.append(round(.65*v+.35*mapped))
  lut.extend(tab)
 return lut
rest=M/'renders/c-textured-lit/000.png'
if not rest.exists():raise SystemExit('Render textured rest first')
raw=Image.open(rest).convert('RGBA');lut=lut_for(raw)
(M/'grade.json').write_text(json.dumps({'method':'35 percent 17-quantile RGB monotonic transfer, one rest LUT for every clip','lut':lut,'rest_sha256':sha(rest)},indent=2))
def grade(im):
 alpha=im.getchannel('A');im=im.convert('RGB').point(lut).convert('RGBA');im.putalpha(alpha);return im
def load(p,size=256):return grade(Image.open(p).convert('RGBA')).resize((size,size),Image.Resampling.LANCZOS)
def tile(im,size=256):
 bg=Image.new('RGBA',(size,size),CREAM);bg.alpha_composite(im.resize((size,size),Image.Resampling.LANCZOS));return bg
render=load(rest)
rest_manifest=json.loads((rest.parent/'manifest.json').read_text())
render_label=f"3D / {rest_manifest['device']} {rest_manifest['resolution']}px"
# Painting/render, half split and 50 percent crossfade at both review sizes.
split=ref.copy();split.paste(render.crop((128,0,256,256)),(128,0))
fade=Image.blend(ref,render,.5)
sheet=Image.new('RGBA',(1024,364),CREAM);d=ImageDraw.Draw(sheet)
for i,(name,im) in enumerate([('Painting',ref),(render_label,render),('Half split',split),('50% crossfade',fade)]):
 d.text((i*256+8,8),name,fill=(55,42,25));sheet.alpha_composite(im,(i*256,28));sheet.alpha_composite(im.resize((64,64),Image.Resampling.LANCZOS),(i*256+96,292))
sheet.convert('RGB').save(Q/'keshig-f-restpose-compare.png')
sheet.crop((0,0,512,364)).save(Q/'keshig-c-textured-lit.png')
# Plain geometry evidence: material override render has no projection.
bpath=M/'renders/b-plain/000.png'
if bpath.exists():
 b=Image.open(bpath).convert('RGBA').resize((256,256),Image.Resampling.LANCZOS);s=Image.new('RGBA',(512,284),CREAM);s.alpha_composite(ref,(0,28));s.alpha_composite(b,(256,28));ImageDraw.Draw(s).text((8,8),'Painting / plain 3D',fill=(55,42,25));s.save(Q/'keshig-b-plain.png')
# Export actual stage masters; never upscale CPU previews into a 512px claim.
for stage in ['b-plain','c-textured-lit','d-rig-poses']:
 for p in sorted((M/'renders'/stage).glob('*.png')):
  original=Image.open(p).convert('RGBA')
  if stage!='b-plain':original=grade(original)
  for size in [256]+([512] if original.width>=512 else []):
   dest=M/str(size)/stage;dest.mkdir(parents=True,exist_ok=True);original.resize((size,size),Image.Resampling.LANCZOS).save(dest/p.name)
# Close details, same native pixel scale on each side.
boxes=[('Face / bow',(75,16,182,99)),('Coat / saddle',(106,70,181,174)),('Horse head',(178,99,244,161))]
detail=Image.new('RGBA',(768,280),CREAM);d=ImageDraw.Draw(detail)
for i,(name,box) in enumerate(boxes):
 d.text((i*256+5,8),name,fill=(55,42,25))
 for j,im in enumerate([ref,render]):
  crop=im.crop(box);crop.thumbnail((60,110));detail.alpha_composite(crop.resize((crop.width*2,crop.height*2),Image.Resampling.NEAREST),(i*256+j*128,32))
detail.save(Q/'keshig-c-details.png')
if '--rest-only' in sys.argv:raise SystemExit(0)
poses=sorted((M/'renders/d-rig-poses').glob('*.png'))
if poses:
 strip=Image.new('RGBA',(len(poses)*256,284),CREAM)
 for i,p in enumerate(poses):strip.alpha_composite(load(p),(i*256,28))
 ImageDraw.Draw(strip).text((8,8),'Attack: ready / draw / release / recovery',fill=(55,42,25));strip.save(Q/'keshig-d-rig-poses.png')
frames={};sources={};hashes={}
for name,(count,fps,loop) in CLIPS.items():
 folder=M/'renders'/('e-'+name);paths=[folder/f'{i:03}.png' for i in range(count)]
 if not all(p.exists() for p in paths) or not (folder/'manifest.json').exists():continue
 manifest=json.loads((folder/'manifest.json').read_text())
 if manifest['master_sha256']!=sha(M/'keshig.blend') or manifest['blend_sha256']!=sha(M/'clips'/f'{name}.blend'):continue
 frames[name]=[load(p) for p in paths];sources[name]=manifest
 strip=Image.new('RGBA',(count*256,356),CREAM)
 for i,(p,im) in enumerate(zip(paths,frames[name])):
  strip.alpha_composite(im,(i*256,28));strip.alpha_composite(im.resize((64,64),Image.Resampling.LANCZOS),(i*256+96,288));hashes[f'{name}/{i}']=sha(p)
  # Never label enlarged previews as 512px masters. GPU pass supplies true 512px renders.
  original=grade(Image.open(p).convert('RGBA'));sizes=[256]+([512] if original.width>=512 else [])
  for size in sizes:
   dest=M/str(size)/name;dest.mkdir(parents=True,exist_ok=True);original.resize((size,size),Image.Resampling.LANCZOS).save(dest/f'{i:03}.png')
 ImageDraw.Draw(strip).text((8,8),f'{name} / {count} frames / {sources[name]["device"]} {sources[name]["resolution"]}px',fill=(55,42,25))
 strip.save(Q/f'keshig-e-{name}-strip.png')
 previews=[tile(im) for im in frames[name]];previews[0].save(Q/f'keshig-e-{name}.webp',save_all=True,append_images=previews[1:],duration=round(1000/fps),loop=0,quality=88,method=6)
if '--reviews' in sys.argv:raise SystemExit(0)
assert len(frames)==5,'All five complete render manifests required'
mastersha=sha(M/'keshig.blend')
assert json.loads((rest.parent/'manifest.json').read_text())['blend_sha256']==mastersha,'Stale rest render'
for name,report in sources.items():
 assert report['master_sha256']==mastersha,f'{name}: stale source master'
 assert report['blend_sha256']==sha(M/'clips'/f'{name}.blend'),f'{name}: stale clip render'
assert len({(x['engine'],x['device'],x['resolution'],x['samples']) for x in [*sources.values(),json.loads((rest.parent/'manifest.json').read_text())]})==1,'Mixed render settings'
# Each row is packed left-to-right; per-frame rects recover original 160x160 canvases.
anchor=json.loads((rest.parent/'manifest.json').read_text()).get('anchor_160',[75,143])
meta={'version':2,'layout':'trimmed-rows','frame':{'w':160,'h':160,'ax':anchor[0],'ay':anchor[1]},'clips':{}}
rows=[];y=1;maxwidth=1;trimmed={};bounds={}
for row,(name,(count,fps,loop)) in enumerate(CLIPS.items()):
 cells=[];x=1;height=1;rects=[];bounds[name]=[];seen={}
 for im in frames[name]:
  im=im.resize((160,160),Image.Resampling.BICUBIC);alpha=im.getchannel('A')
  box=alpha.getbbox();assert box,'Empty frame';bounds[name].append(box)
  key=hashlib.sha256(im.tobytes()).hexdigest()
  if key in seen:rects.append(dict(seen[key]));continue
  crop=im.crop(box);w,h=crop.size;cells.append((crop,x));rect={'x':x,'y':y,'w':w,'h':h,'ox':box[0],'oy':box[1]};rects.append(rect);seen[key]=rect;x+=w+2;height=max(height,h)
 meta['clips'][name]={'row':row,'frames':count,'fps':fps,'loop':loop,'rects':rects};rows.append((y,cells));maxwidth=max(maxwidth,x);y+=height+2
atlas=Image.new('RGBA',(maxwidth,y))
for y,cells in rows:
 for im,x in cells:atlas.paste(im,(x,y))
for quality in [90,85,80,75]:
 buf=io.BytesIO();atlas.save(buf,format='WEBP',quality=quality,method=6,exact=True)
 if len(buf.getvalue())<=200000:break
else:raise RuntimeError('Atlas exceeds 200,000 bytes at quality 75. No quality/frame-count downgrade allowed.')
meta['atlas']={'w':atlas.width,'h':atlas.height};meta['quality']=quality
out=Path('app/src/assets/units/anim');out.mkdir(parents=True,exist_ok=True);dst=M/'candidate.webp';dst.write_bytes(buf.getvalue());dst.with_suffix('.json').write_text(json.dumps(meta,indent=2)+'\n')
# Validate the decoded product and reconstruction rather than only source arrays.
decoded=Image.open(dst).convert('RGBA');assert decoded.size==atlas.size;reconstructed={};warnings=[]
for name,c in meta['clips'].items():
 reconstructed[name]=[]
 for rect in c['rects']:
  x,y,w,h,ox,oy=[rect[k] for k in ['x','y','w','h','ox','oy']]
  assert 0<=x<x+w<=decoded.width and 0<=y<y+h<=decoded.height
  assert 0<=ox<ox+w<=160 and 0<=oy<oy+h<=160
  im=Image.new('RGBA',(160,160));im.paste(decoded.crop((x,y,x+w,y+h)),(ox,oy));reconstructed[name].append(im)
  if ox<1 or oy<1 or ox+w>159 or oy+h>159:warnings.append(f'{name}: silhouette reaches canvas edge')
 assert any(ImageChops.difference(reconstructed[name][0],im).convert('RGB').getbbox() for im in reconstructed[name][1:]),f'{name} has no motion'
assert ImageChops.difference(frames['death'][-1],frames['death'][-2]).convert('RGB').getbbox() is None,'Death must hold'
# Identical source samples share one encoded rectangle, preserving the exact hold.
assert ImageChops.difference(reconstructed['death'][-1],reconstructed['death'][-2]).convert('RGB').getbbox() is None,'Decoded death must hold exactly'
assert decoded.getchannel('A').tobytes()==atlas.getchannel('A').tobytes(),'Lossless alpha must survive WebP'
assert decoded.getchannel('A').getextrema()==(0,255)
assert not warnings, sorted(set(warnings))
# Publish only after every decoded frame passed; failed candidates stay external.
delivered=out/'keshig.webp';delivered.write_bytes(dst.read_bytes());delivered.with_suffix('.json').write_text(json.dumps(meta,indent=2)+'\n');dst=delivered
report={'bytes':dst.stat().st_size,'quality':quality,'frames':40,'canvas':160,'atlas_size':decoded.size,'warnings':sorted(set(warnings)),'source_frames':hashes,'render_sources':sources,'atlas_sha256':sha(dst),'master_sha256':mastersha,'grade_sha256':sha(M/'grade.json')}
(Q/'keshig-validation.json').write_text(json.dumps(report,indent=2)+'\n')
# 8-second five-clip H.264 review. Trim offsets are restored before scaling.
video=Q/f'keshig-round{os.environ.get("ROUND","1")}.mp4'
with tempfile.TemporaryDirectory(prefix='keshig-mp4-',dir=R/'tmp') as tmp:
 for t in range(240):
  canvas=Image.new('RGBA',(1600,348),CREAM);d=ImageDraw.Draw(canvas)
  for k,(name,c) in enumerate(meta['clips'].items()):
   idx=int(t/30*c['fps'])%c['frames'] if c['loop'] else min(int((t%60)/30*c['fps']),c['frames']-1)
   canvas.alpha_composite(reconstructed[name][idx].resize((320,320),Image.Resampling.LANCZOS),(k*320,28));d.text((k*320+8,8),name,fill=(55,42,25))
  canvas.convert('RGB').save(Path(tmp)/f'{t:04}.png')
 subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate','30','-i',str(Path(tmp)/'%04d.png'),'-c:v','libx264','-threads','3','-pix_fmt','yuv420p','-crf','20','-movflags','+faststart',str(video)],check=True)
with (Q/'keshig-log.md').open('a') as f:f.write(f'Packed and decoded 40 trimmed frames, quality {quality}, {dst.stat().st_size} bytes; wrote {video.name}. Warnings: {sorted(set(warnings))}\n')
print(json.dumps({k:v for k,v in report.items() if k not in ['source_frames','render_sources']},indent=2))
