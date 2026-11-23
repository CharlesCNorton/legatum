"""Decode trimmed frames and encode the driver's eight-second five-clip review."""
import json, os, subprocess, hashlib
from pathlib import Path
from PIL import Image, ImageDraw

R=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')))
O=R/'review/3d-v2';M=R/'masters/barbarian-spearman';atlas_path=Path('app/src/assets/units/anim/barbarian-spearman.webp')
meta=json.loads(atlas_path.with_suffix('.json').read_text());atlas=Image.open(atlas_path).convert('RGBA')
order=['idle','move','attack','hit','death'];clips=[]
for name in order:
 info=meta['clips'][name];frames=[]
 for rect in info['rects']:
  x,y,w,h,ox,oy=[rect[k] for k in ['x','y','w','h','ox','oy']]
  frame=Image.new('RGBA',(160,160));frame.paste(atlas.crop((x,y,x+w,y+h)),(ox,oy))
  frames.append(frame.resize((320,320),Image.Resampling.LANCZOS))
 clips.append(frames)
round_number=os.environ.get('ROUND','2');assert round_number.isdigit(),'ROUND must be a nonnegative integer'
output=O/f'barbarian-spearman-round{round_number}.mp4';temp=output.with_suffix('.pending.mp4')
command=['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pixel_format','rgb24','-video_size','1600x348','-framerate','30','-i','pipe:0','-an','-c:v','libx264','-threads','3','-pix_fmt','yuv420p','-crf','20','-movflags','+faststart',str(temp)]
with subprocess.Popen(command,stdin=subprocess.PIPE) as proc:
 for t in range(240):
  canvas=Image.new('RGBA',(1600,348),(240,232,214,255));draw=ImageDraw.Draw(canvas)
  for k,name in enumerate(order):
   c=meta['clips'][name];i=int(t/30*c['fps'])%c['frames'] if c['loop'] else min(int((t%60)/30*c['fps']),c['frames']-1)
   canvas.alpha_composite(clips[k][i],(k*320,28));draw.text((k*320+8,6),name,fill=(60,50,40,255))
  if t in [0,10,20,30,45]:canvas.convert('RGB').save(M/f'video-check-{t:02}.png')
  proc.stdin.write(canvas.convert('RGB').tobytes())
 proc.stdin.close();assert proc.wait()==0,'FFmpeg failed'
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=codec_name,pix_fmt,width,height,nb_read_frames,duration','-of','json',str(temp)]))['streams'][0]
assert (probe['codec_name'],probe['pix_fmt'],probe['width'],probe['height'],int(probe['nb_read_frames']))==('h264','yuv420p',1600,348,240),probe
assert abs(float(probe['duration'])-8)<.01,probe
temp.replace(output)
(M/'video.json').write_text(json.dumps({'path':str(output),'probe':probe,'atlas_sha256':hashlib.sha256(atlas_path.read_bytes()).hexdigest()},indent=2)+'\n')
print('VIDEO_READY',output,probe)
