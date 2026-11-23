"""Eight-second review of all five decoded, offset-restored atlas clips."""
import json,os,subprocess,hashlib
from pathlib import Path
from PIL import Image,ImageDraw
R=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')));M=R/'masters/settler';V=R/'review/3d-v2'
path=Path('app/src/assets/units/anim/settler.webp');atlas=Image.open(path).convert('RGBA');meta=json.loads(path.with_suffix('.json').read_text())
clips={}
for name,c in meta['clips'].items():
    clips[name]=[]
    for t in c['trim']:
        im=Image.new('RGBA',(160,160));im.paste(atlas.crop((t['x'],t['y'],t['x']+t['w'],t['y']+t['h'])),(t['dx'],t['dy']))
        clips[name].append(im.resize((320,320),Image.Resampling.NEAREST))
out=V/f'settler-round{os.environ.get("ROUND","2")}.mp4'
cmd=['ffmpeg','-v','error','-y','-f','rawvideo','-pixel_format','rgb24','-video_size','1600x352','-framerate','24','-i','pipe:0','-an','-c:v','libx264','-threads','3','-pix_fmt','yuv420p','-crf','18','-movflags','+faststart',str(out)]
proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
try:
    for frame in range(192):
        canvas=Image.new('RGB',(1600,352),(224,215,191));draw=ImageDraw.Draw(canvas);time=frame/24
        for col,(name,c) in enumerate(meta['clips'].items()):
            index=int(time*c['fps'])%c['frames'] if c['loop'] else min(int((time%2)*c['fps']),c['frames']-1)
            im=clips[name][index];canvas.paste(im,(col*320,32),im);draw.text((col*320+12,10),name,fill=(40,34,27))
        proc.stdin.write(canvas.tobytes())
finally:proc.stdin.close()
assert proc.wait()==0,'FFmpeg failed'
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(out)]));s=probe['streams'][0]
assert (s['codec_name'],s['pix_fmt'],s['width'],s['height'],int(s['nb_frames']))==('h264','yuv420p',1600,352,192)
assert abs(float(probe['format']['duration'])-8)<.05
report={'file':str(out),'codec':'h264','pixel_format':'yuv420p','width':1600,'height':352,'frames':192,'seconds':8,'atlas_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
(M/'video.json').write_text(json.dumps(report,indent=2));print('VIDEO_PASS',json.dumps(report))
