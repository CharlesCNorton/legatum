"""Trim 160px logical frames into five atlas rows; validate and encode review MP4.
Quality never below 75. Refuse partial/stale frames. No atlas runtime changes.
"""
from pathlib import Path
import hashlib, io, json, os, subprocess, tempfile
from PIL import Image, ImageChops, ImageDraw
R=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'));M=R/'masters/artillery';V=R/'review/3d-v2'
OUT=Path('app/src/assets/units/anim');OUT.mkdir(parents=True,exist_ok=True)
CLIPS={'idle':(8,10,True),'move':(8,12,True),'attack':(10,14,False),'hit':(4,12,False),'death':(10,10,False)}
man=json.loads((M/'render-manifest.json').read_text());assert man['source_sha256']==hashlib.sha256((M/'artillery.blend').read_bytes()).hexdigest(),'stale model'
assert man['script_sha256']==hashlib.sha256((Path(__file__).parent/'scene.py').read_bytes()).hexdigest(),'scene changed since render'
frames={};rects={};rows=[];y=0
meta={'version':2,'layout':'trimmed-rows','frame':{'w':160,'h':160,'ax':80,'ay':124},'clips':{}}
for row,(clip,(count,fps,loop)) in enumerate(CLIPS.items()):
 frames[clip]=[];rects[clip]=[];x=0;rh=0
 for i in range(count):
  raw=M/'renders'/clip/f'{i:02}.png';assert hashlib.sha256(raw.read_bytes()).hexdigest()==man['clips'][clip]['hashes'][i],'stale frame'
  p=M/'256'/clip/f'{i:02}.png';im=Image.open(p).convert('RGBA');assert im.size==(256,256)
  im=im.resize((160,160),Image.Resampling.LANCZOS);alpha=im.getchannel('A');box=alpha.point(lambda a:255 if a>12 else 0).getbbox();assert box
  assert box[0]>=1 and box[1]>=1 and box[2]<=159 and box[3]<=159,(clip,i,'clipped',box)
  box=alpha.getbbox();crop=im.crop(box);w,h=crop.size
  rects[clip].append({'x':x,'y':y,'w':w,'h':h,'ox':box[0],'oy':box[1]});frames[clip].append(im);x+=w+2;rh=max(rh,h)
 meta['clips'][clip]={'row':row,'frames':count,'fps':fps,'loop':loop,'sprites':rects[clip]};rows.append((x,rh));y+=rh+2
atlas=Image.new('RGBA',(max(w for w,h in rows),y))
for clip in CLIPS:
 for im,d in zip(frames[clip],rects[clip]):atlas.paste(im.crop((d['ox'],d['oy'],d['ox']+d['w'],d['oy']+d['h'])),(d['x'],d['y']))
for quality in [90,85,80,78,75]:
 buf=io.BytesIO();atlas.save(buf,format='WEBP',quality=quality,method=6,exact=True,alpha_quality=100)
 print('WebP',quality,len(buf.getvalue()))
 if len(buf.getvalue())<=200000:break
else:raise RuntimeError('160px atlas exceeds 200KB at quality 75; do not lower quality or delete frames')
(OUT/'artillery.webp').write_bytes(buf.getvalue());(OUT/'artillery.json').write_text(json.dumps(meta,separators=(',',':'))+'\n')
# Validate decoded metadata and reconstruct logical cells with their original anchors.
decoded=Image.open(OUT/'artillery.webp').convert('RGBA');assert decoded.size==atlas.size
restored={}
for clip,(count,fps,loop) in CLIPS.items():
 restored[clip]=[]
 for d in rects[clip]:
  assert 0<=d['x']<decoded.width and d['x']+d['w']<=decoded.width
  assert 0<=d['y']<decoded.height and d['y']+d['h']<=decoded.height
  assert d['ox']+d['w']<=160 and d['oy']+d['h']<=160
  im=Image.new('RGBA',(160,160));im.alpha_composite(decoded.crop((d['x'],d['y'],d['x']+d['w'],d['y']+d['h'])),(d['ox'],d['oy']));restored[clip].append(im)
 assert any(ImageChops.difference(restored[clip][0],im).getbbox(alpha_only=False) for im in restored[clip][1:]),clip+' no motion'
 assert all(a.getchannel('A').tobytes()==b.getchannel('A').tobytes() for a,b in zip(frames[clip],restored[clip])),clip+' trim offsets changed alpha'
assert frames['death'][-1].tobytes()==frames['death'][-2].tobytes(),'death not held'
report={'status':'technical PASS, not art approval','bytes':len(buf.getvalue()),'quality':quality,'logical_cell':160,'frames':40,'atlas_size':atlas.size,'decoded_offsets':'all 40 alpha masks reconstruct exactly','held_death':True,'provenance':man}
(V/'artillery-validation.json').write_text(json.dumps(report,indent=2))
# 8 seconds, all clips together, decoded trimmed atlas, 2x logical scale on cream.
mp4=V/f'artillery-round{os.environ.get("ROUND","1")}.mp4'
with tempfile.TemporaryDirectory(prefix='artillery-video-',dir=R/'tmp') as tmp:
 for tick in range(240):
  canvas=Image.new('RGBA',(1600,348),(233,207,160,255));draw=ImageDraw.Draw(canvas)
  for k,(clip,(count,fps,loop)) in enumerate(CLIPS.items()):
   i=int(tick/30*fps)%count if loop else min(int((tick%60)/30*fps),count-1)
   canvas.alpha_composite(restored[clip][i].resize((320,320),Image.Resampling.LANCZOS),(k*320,28));draw.text((k*320+10,7),clip,fill='#423b2d')
  canvas.convert('RGB').save(Path(tmp)/f'{tick:04}.png')
 subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate','30','-i',tmp+'/%04d.png','-c:v','libx264','-pix_fmt','yuv420p','-crf','20','-movflags','+faststart',str(mp4)],check=True)
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','stream=codec_name,pix_fmt,width,height,nb_frames:format=duration','-of','json',str(mp4)]));stream=probe['streams'][0]
assert stream['codec_name']=='h264' and stream['pix_fmt']=='yuv420p' and int(stream['nb_frames'])==240
assert float(probe['format']['duration'])==8
(V/'artillery-video-validation.json').write_text(json.dumps(probe,indent=2))
print('PASS: 40 frames, >=75 quality, <=200KB, exact trim offsets, all clips move, held death, 240-frame 8s H264 yuv420p MP4',mp4)
