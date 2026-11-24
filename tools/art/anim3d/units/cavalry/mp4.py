"""Decode trimmed delivery frames and render all clips, 2x on cream, 8 seconds."""
import json,os,subprocess
from pathlib import Path
from PIL import Image,ImageDraw
R=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')));V=R/'review/3d-v2';O=Path('app/src/assets/units/anim');meta=json.loads((O/'cavalry.json').read_text());atlas=Image.open(O/'cavalry.webp').convert('RGBA');clips={}
for name,c in meta['clips'].items():
 frames=[]
 for r in c['rects']:
  im=Image.new('RGBA',(160,160));im.paste(atlas.crop((r['x'],r['y'],r['x']+r['w'],r['y']+r['h'])),(r['ox'],r['oy']));frames.append(im.resize((320,320),Image.Resampling.LANCZOS))
 clips[name]=frames
out=V/f'cavalry-round{os.environ.get("ROUND","1")}.mp4'
cmd=['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s','1600x352','-r','24','-i','-','-an','-c:v','libx264','-threads','3','-preset','fast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(out)]
p=subprocess.Popen(cmd,stdin=subprocess.PIPE)
for f in range(192):
 im=Image.new('RGB',(1600,352),'#E9CFA0');d=ImageDraw.Draw(im)
 for i,(name,c) in enumerate(meta['clips'].items()):
  frame=clips[name][int(f/24*c['fps'])%c['frames']];im.paste(frame,(i*320,32),frame);d.text((i*320+12,10),name,fill='#332b20')
 p.stdin.write(im.tobytes())
p.stdin.close();assert p.wait()==0
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(out)]));s=probe['streams'][0];assert s['codec_name']=='h264' and s['pix_fmt']=='yuv420p' and int(s['nb_frames'])==192 and float(probe['format']['duration'])==8
check_sheet=V/f'cavalry-round{os.environ.get("ROUND","1")}-video-check.png'
subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(out),'-vf','fps=1,scale=800:176,tile=2x4:nb_frames=8','-frames:v','1','-threads','3','-update','1',str(check_sheet)],check=True)
assert Image.open(check_sheet).size==(1600,704)
(V/'cavalry-video-validation.json').write_text(json.dumps({'file':str(out),'frames':192,'seconds':8,'size':[1600,352],'codec':'h264','pixel_format':'yuv420p','decoded_check_sheet':str(check_sheet)},indent=2)+'\n');print('VIDEO',out)
