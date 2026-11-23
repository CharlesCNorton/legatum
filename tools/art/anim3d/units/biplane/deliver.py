"""Trimmed 160 px atlas, verified reconstruction, and five-clip H.264 review.
No runtime registration: these files remain an art candidate until lead approval.
"""
from pathlib import Path
import os,json,hashlib,subprocess,io,sys
from PIL import Image,ImageDraw,ImageChops
R=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'));M=R/'masters/biplane';D=R/'review/3d-v2';OUT=Path('app/src/assets/units/anim');OUT.mkdir(exist_ok=True,parents=True)
order=['idle','move','attack','hit','death'];counts=[8,8,10,4,10];cream=(233,207,160,255)
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
masterhash=digest(M/'biplane.blend');metadata={'schema':'legatum-trimmed-atlas-v1','frame':{'w':160,'h':160,'ax':73,'ay':140},'clips':{}};allims={};source_reports={};rows=[];height=0;unique={}
for row,(clip,n) in enumerate(zip(order,counts)):
 config=json.loads((M/(clip+'.json')).read_text());assert config['source_sha256']==masterhash,('stale animation',clip)
 report=json.loads((M/'raw'/('e-'+clip)/'render.json').read_text());assert report['frames']==n
 assert report['blend_sha256']==digest(M/(clip+'.blend')),('stale render',clip)
 processed=json.loads((M/'256'/('e-'+clip)/'processed.json').read_text())
 assert processed['blend_sha256']==report['blend_sha256'] and processed['grade_sha256']==digest(M/'grade.json'),('stale processing',clip)
 assert processed['raw_sha256']==[digest(M/'raw'/('e-'+clip)/f'{i:02}.png') for i in range(n)],('stale raw frames',clip)
 assert processed['processed_sha256']==[digest(M/'256'/('e-'+clip)/f'{i:02}.png') for i in range(n)],('modified processed frames',clip)
 if os.environ.get('REQUIRE_GPU')=='1':assert report['device']=='GPU' and report['resolution']==512,report
 ims=[Image.open(M/'256'/('e-'+clip)/f'{i:02}.png').convert('RGBA').resize((160,160),Image.Resampling.LANCZOS) for i in range(n)]
 # 32-level alpha, as in the family pipeline; <=3/255 ringing becomes zero.
 # Native 512/256 masters retain full alpha. Max quantization error is 4/255.
 for im in ims:im.putalpha(im.getchannel('A').point([round(round(a*31/255)*255/31) for a in range(256)]))
 rects=[];x=0;rowh=0
 for im in ims:
  b=im.getchannel('A').getbbox();assert b and b[0]>0 and b[1]>0 and b[2]<160 and b[3]<160,('clipped',clip,b)
  l,t,r,bottom=b;w,h=r-l,bottom-t;key=hashlib.sha256(im.tobytes()).hexdigest()
  if key in unique:rects.append(dict(unique[key]));continue
  rect={'x':x+1,'y':height+1,'w':w,'h':h,'ox':l,'oy':t};rects.append(rect);unique[key]=rect;x+=w+2;rowh=max(rowh,h+2)
 metadata['clips'][clip]={'row':row,'frames':n,'fps':config['fps'],'loop':config['loop'],'rects':rects};rows.append((x,rowh));height+=rowh;allims[clip]=ims;source_reports[clip]=report
atlas=Image.new('RGBA',(max(w for w,h in rows),height))
for clip in order:
 for im,r in zip(allims[clip],metadata['clips'][clip]['rects']):atlas.paste(im.crop((r['ox'],r['oy'],r['ox']+r['w'],r['oy']+r['h'])),(r['x'],r['y']))
for q in [90,85,80,75]:
 buf=io.BytesIO();atlas.save(buf,format='WEBP',quality=q,method=6,exact=False)
 print('ENCODE',q,buf.tell(),flush=True)
 (M/f'atlas-q{q}-candidate.webp').write_bytes(buf.getvalue())
 if buf.tell()<=200000:break
else:raise RuntimeError('Atlas exceeds 200 KB even at quality 75; retain all frames and report')
metadata['atlas']={'w':atlas.width,'h':atlas.height,'quality':q,'bytes':buf.tell()}
(OUT/'biplane.webp').write_bytes(buf.getvalue());(OUT/'biplane.json').write_text(json.dumps(metadata,indent=2)+'\n')
# Verify the actual decoded artifact, including every offset and all transparent margins.
decoded=Image.open(OUT/'biplane.webp').convert('RGBA');assert decoded.size==atlas.size
reconstructed={}
for clip in order:
 frames=[]
 for expected,r in zip(allims[clip],metadata['clips'][clip]['rects']):
  im=Image.new('RGBA',(160,160));im.alpha_composite(decoded.crop((r['x'],r['y'],r['x']+r['w'],r['y']+r['h'])),(r['ox'],r['oy']));frames.append(im)
  assert ImageChops.difference(im.getchannel('A'),expected.getchannel('A')).getbbox() is None,('alpha trim reconstruction',clip)
 reconstructed[clip]=frames
 assert len({im.tobytes() for im in frames})>1,('no motion',clip)
assert reconstructed['death'][-1].tobytes()==reconstructed['death'][-2].tobytes(),'death is not held'
report={'bytes':buf.tell(),'quality':q,'frames':sum(counts),'dimensions':decoded.size,'alpha_offsets':'all 40 reconstruct exactly','death':'last two frames identical','source_master_sha256':masterhash,'renders':source_reports,'atlas_sha256':digest(OUT/'biplane.webp'),'json_sha256':digest(OUT/'biplane.json')}
(M/'validation.json').write_text(json.dumps(report,indent=2))
# Feed RGB frames directly to ffmpeg: no enormous temporary PNG sequence.
mp4=D/f"biplane-round{os.environ.get('ROUND','1')}.mp4";fps=30;w,h=1600,348
proc=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pixel_format','rgb24','-video_size',f'{w}x{h}','-framerate',str(fps),'-i','-','-an','-c:v','libx264','-threads','2','-pix_fmt','yuv420p','-crf','20','-movflags','+faststart',str(mp4)],stdin=subprocess.PIPE)
large={clip:[im.resize((320,320),Image.Resampling.LANCZOS) for im in reconstructed[clip]] for clip in order}
try:
 for t in range(fps*8):
  canvas=Image.new('RGBA',(w,h),cream);draw=ImageDraw.Draw(canvas)
  for k,clip in enumerate(order):
   c=metadata['clips'][clip];i=int(t/fps*c['fps'])%c['frames'] if c['loop'] else min(int((t%(2*fps))/fps*c['fps']),c['frames']-1)
   canvas.alpha_composite(large[clip][i],(k*320,28));draw.text((k*320+12,8),clip,fill='#403329')
  proc.stdin.write(canvas.convert('RGB').tobytes())
finally:proc.stdin.close()
assert proc.wait()==0,'ffmpeg failed'
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(mp4)]));s=probe['streams'][0]
assert s['codec_name']=='h264' and s['pix_fmt']=='yuv420p' and s['width']==w and s['height']==h and int(s['nb_frames'])==240 and abs(float(probe['format']['duration'])-8)<.05
(M/'video-validation.json').write_text(json.dumps({'path':str(mp4),'codec':s['codec_name'],'pixel_format':s['pix_fmt'],'frames':s['nb_frames'],'duration':probe['format']['duration']},indent=2))
with (D/'biplane-log.md').open('a') as f:f.write(f'- Packed/decoded/validated 40 trimmed 160 px frames: {buf.tell()} bytes, WebP q{q}; exact alpha offsets and held death. Encoded and ffprobe-verified 240-frame 8 s H.264 yuv420p MP4.\n')
print(json.dumps(report,indent=2));print(mp4)
