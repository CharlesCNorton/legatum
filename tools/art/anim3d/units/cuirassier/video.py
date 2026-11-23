"""Eight seconds, five reconstructed 160 px clips at 2x, cream H.264 yuv420p."""
from pathlib import Path
from PIL import Image,ImageDraw
import os,json,subprocess
R=Path(os.environ['ANIM_ROOT']);path=Path('app/src/assets/units/anim/cuirassier.webp');atlas=Image.open(path).convert('RGBA');meta=json.loads(path.with_suffix('.json').read_text());clips=[]
for name,c in meta['clips'].items():
 frames=[]
 for r in c['rects']:
  im=Image.new('RGBA',(160,160));im.paste(atlas.crop((r['x'],r['y'],r['x']+r['w'],r['y']+r['h'])),(r['ox'],r['oy']));frames.append(im.resize((320,320),Image.Resampling.LANCZOS))
 clips.append((name,c,frames))
out=R/'review/3d-v2'/f'cuirassier-round{os.environ.get("ROUND","1")}.mp4';fps=24
proc=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgba','-s','1600x348','-r',str(fps),'-i','-','-an','-c:v','libx264','-threads','2','-pix_fmt','yuv420p','-crf','20','-movflags','+faststart',str(out)],stdin=subprocess.PIPE)
for t in range(fps*8):
 canvas=Image.new('RGBA',(1600,348),(233,207,160,255));d=ImageDraw.Draw(canvas)
 for k,(name,c,frames) in enumerate(clips):
  i=int(t/fps*c['fps'])%len(frames) if c['loop'] else min(int((t%(2*fps))/fps*c['fps']),len(frames)-1)
  canvas.alpha_composite(frames[i],(k*320,28));d.text((k*320+8,8),name,fill='#30281e')
 proc.stdin.write(canvas.tobytes())
proc.stdin.close();assert proc.wait()==0
print(out)
