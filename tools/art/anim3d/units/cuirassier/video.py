"""Eight seconds, five reconstructed 160 px clips at 2x, cream H.264 yuv420p."""
from pathlib import Path
from PIL import Image,ImageDraw
import os,json,subprocess
R=Path(os.environ['ANIM_ROOT']);path=Path('app/src/assets/units/anim/cuirassier.webp');atlas=Image.open(path).convert('RGBA');meta=json.loads(path.with_suffix('.json').read_text());clips=[]
sheet=Image.new('RGBA',(1600,900),(233,207,160,255));labels=ImageDraw.Draw(sheet)
for name,c in meta['clips'].items():
 frames=[]
 row=len(clips);labels.text((8,row*180+3),name+' / decoded 160px atlas',fill='#30281e')
 for index,r in enumerate(c['rects']):
  im=Image.new('RGBA',(160,160));im.paste(atlas.crop((r['x'],r['y'],r['x']+r['w'],r['y']+r['h'])),(r['ox'],r['oy']));sheet.alpha_composite(im,(index*160,row*180+20));frames.append(im.resize((320,320),Image.Resampling.LANCZOS))
 clips.append((name,c,frames))
sheet.convert('RGB').save(R/'review/3d-v2/cuirassier-g-decoded-atlas.png')
out=R/'review/3d-v2'/f'cuirassier-round{os.environ.get("ROUND","1")}.mp4';fps=24
proc=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgba','-s','1600x348','-r',str(fps),'-i','-','-an','-c:v','libx264','-threads','2','-pix_fmt','yuv420p','-crf','20','-movflags','+faststart',str(out)],stdin=subprocess.PIPE)
for t in range(fps*8):
 canvas=Image.new('RGBA',(1600,348),(233,207,160,255));d=ImageDraw.Draw(canvas)
 for k,(name,c,frames) in enumerate(clips):
  i=int(t/fps*c['fps'])%len(frames) if c['loop'] else min(int((t%(2*fps))/fps*c['fps']),len(frames)-1)
  canvas.alpha_composite(frames[i],(k*320,28));d.text((k*320+8,8),name,fill='#30281e')
 proc.stdin.write(canvas.tobytes())
proc.stdin.close();assert proc.wait()==0
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=codec_name,pix_fmt,width,height,nb_frames,duration','-of','json',str(out)]))['streams'][0]
assert probe['codec_name']=='h264' and probe['pix_fmt']=='yuv420p'
assert (probe['width'],probe['height'],int(probe['nb_frames']))==(1600,348,192)
assert abs(float(probe['duration'])-8)<.01
out.with_suffix('.json').write_text(json.dumps(probe,indent=2))
print(out)
