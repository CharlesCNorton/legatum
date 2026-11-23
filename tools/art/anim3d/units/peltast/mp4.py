"""Reconstruct trimmed frames, then render the required eight-second comparison."""
import io,json,os,subprocess
from pathlib import Path
from PIL import Image,ImageDraw
R=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'));V=R/'review/3d-v2';path=Path('app/src/assets/units/anim/peltast.webp');meta=json.loads(path.with_suffix('.json').read_text());atlas=Image.open(path).convert('RGBA');clips=list(meta['clips'].items());decoded=[]
for name,c in clips:
 frames=[]
 for r in c['rects']:
  im=Image.new('RGBA',(160,160));im.paste(atlas.crop((r['x'],r['y'],r['x']+r['w'],r['y']+r['h'])),(r['ox'],r['oy']));frames.append(im.resize((320,320),Image.Resampling.LANCZOS))
 decoded.append(frames)
out=V/f'peltast-round{os.environ.get("ROUND","2")}.mp4'
cmd=['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s','1600x348','-r','30','-i','pipe:0','-an','-c:v','libx264','-threads','3','-pix_fmt','yuv420p','-crf','20','-movflags','+faststart',str(out)]
p=subprocess.Popen(cmd,stdin=subprocess.PIPE)
try:
 for t in range(240):
  im=Image.new('RGBA',(1600,348),(240,232,214,255));d=ImageDraw.Draw(im)
  for k,((name,c),frames) in enumerate(zip(clips,decoded)):
   index=int(t/30*c['fps'])%c['frames'] if c['loop'] else min(int((t%60)/30*c['fps']),c['frames']-1);im.alpha_composite(frames[index],(k*320,28));d.text((k*320+10,7),name,fill=(60,46,30))
  p.stdin.write(im.convert('RGB').tobytes())
finally:p.stdin.close()
assert p.wait()==0,'ffmpeg failed'
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0',
 '-show_entries','stream=codec_name,pix_fmt,width,height,nb_frames,duration','-of','json',str(out)]))['streams'][0]
assert (probe['codec_name'],probe['pix_fmt'],probe['width'],probe['height'],int(probe['nb_frames']))==('h264','yuv420p',1600,348,240),probe
assert abs(float(probe['duration'])-8)<.01,probe
(V/f'peltast-round{os.environ.get("ROUND","2")}-video.json').write_text(json.dumps(probe,indent=2))
contact=Image.new('RGB',(1600,348*6),(240,232,214))
for i,t in enumerate([0,.2,.4,.6,.8,1.]):
 data=subprocess.check_output(['ffmpeg','-v','error','-ss',str(t),'-i',str(out),'-frames:v','1',
  '-f','image2pipe','-vcodec','png','-threads','3','pipe:1'])
 contact.paste(Image.open(io.BytesIO(data)).convert('RGB'),(0,i*348))
contact.save(V/'peltast-mp4-check.png')
print(out,probe)
