"""Decode trimmed frames and show all five clips at 2x on cream for eight seconds."""
import json, os, subprocess
from pathlib import Path
from PIL import Image, ImageDraw
from deliver import CLIPS, restore, OUT, REVIEW, R
meta=json.loads((OUT/'tank.json').read_text());atlas=Image.open(OUT/'tank.webp').convert('RGBA')
frames={n:[restore(atlas,r).resize((320,320),Image.Resampling.LANCZOS) for r in c['rects']] for n,c in meta['clips'].items()}
round_label=os.environ.get('ROUND','4-cpu')
assert all(c.isalnum() or c in '-_' for c in round_label)
out=REVIEW/f'tank-round{round_label}.mp4'
cmd=['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pixel_format','rgb24','-video_size','1600x348','-framerate','30','-i','pipe:0','-an','-c:v','libx264','-threads','3','-pix_fmt','yuv420p','-crf','18','-movflags','+faststart',str(out)]
p=subprocess.Popen(cmd,stdin=subprocess.PIPE)
try:
    for t in range(240):
        canvas=Image.new('RGBA',(1600,348),(240,232,214,255));d=ImageDraw.Draw(canvas)
        for k,(n,(_,fps,loop)) in enumerate(CLIPS.items()):
            count=len(frames[n]);i=int(t/30*fps)%count if loop else min(int((t%60)/30*fps),count-1)
            canvas.alpha_composite(frames[n][i],(k*320,28));d.text((k*320+8,7),n,fill=(60,50,40))
        p.stdin.write(canvas.convert('RGB').tobytes())
    p.stdin.close();assert p.wait()==0
except BaseException:
    p.kill();p.wait();raise
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=codec_name,pix_fmt,width,height,nb_frames,duration','-of','json',str(out)]))['streams'][0]
assert probe['codec_name']=='h264' and probe['pix_fmt']=='yuv420p'
assert int(probe['nb_frames'])==240 and float(probe['duration'])==8
assert (probe['width'],probe['height'])==(1600,348)
(out.with_suffix('.json')).write_text(json.dumps(probe,indent=2));print('VIDEO PASS',out,probe)
# Representative decoded video frames for inspection; the MP4 is always decoded, never assumed.
for t in (0,.3,.6,1.5):
    subprocess.run(['ffmpeg','-y','-loglevel','error','-ss',str(t),'-i',str(out),'-frames:v','1',str(REVIEW/f'tank-round{round_label}-frame-{t}.png')],check=True)
