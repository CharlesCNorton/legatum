"""Reconstruct trimmed frames, then encode the driver's eight-second review."""
import json,os,subprocess,tempfile
from pathlib import Path
from PIL import Image,ImageDraw
R=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')));slug='pikeman';p=Path('app/src/assets/units/anim')/slug;meta=json.loads(p.with_suffix('.json').read_text());atlas=Image.open(p.with_suffix('.webp')).convert('RGBA');frames={}
for name,c in meta['clips'].items():
 frames[name]=[]
 for r in c['rects']:
  im=Image.new('RGBA',(160,160));im.paste(atlas.crop((r['x'],r['y'],r['x']+r['w'],r['y']+r['h'])),(r['ox'],r['oy']));frames[name].append(im.resize((320,320),Image.Resampling.LANCZOS))
report=json.loads((R/'review/3d-v2'/f'{slug}-pack.json').read_text());label='GPU' if all(x['device']=='GPU' for x in report['render_sources'].values()) else 'CPU preview'
out=R/'review/3d-v2'/f'{slug}-round{os.environ.get("ROUND","1")}.mp4'
# Pipe raw RGB: bounded memory and no 240-frame temp directory.
proc=subprocess.Popen(['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s','1600x348','-r','30','-i','-','-an','-c:v','libx264','-threads','3','-pix_fmt','yuv420p','-crf','20','-movflags','+faststart',str(out)],stdin=subprocess.PIPE)
for t in range(240):
 canvas=Image.new('RGBA',(1600,348),(233,207,160,255));d=ImageDraw.Draw(canvas)
 for col,(name,c) in enumerate(meta['clips'].items()):
  i=int(t/30*c['fps'])%c['frames'] if c['loop'] else min(int((t%60)/30*c['fps']),c['frames']-1);canvas.alpha_composite(frames[name][i],(col*320,28));d.text((col*320+8,7),name+' / '+label,fill='#3e3025')
 proc.stdin.write(canvas.convert('RGB').tobytes())
proc.stdin.close();assert proc.wait()==0;info=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height,codec_name,pix_fmt,nb_frames:format=duration','-of','json',str(out)]));stream=info['streams'][0];assert stream['codec_name']=='h264' and stream['pix_fmt']=='yuv420p';assert stream['width']==1600 and stream['height']==348;assert int(stream['nb_frames'])==240 and abs(float(info['format']['duration'])-8)<.05;out.with_suffix('.json').write_text(json.dumps(info,indent=2));print('MP4_OK',out)
