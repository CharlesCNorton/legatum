"""Decode trimmed frames before making the driver's 8-second comparison movie."""
import json, subprocess, sys, tempfile, pathlib, os
from PIL import Image, ImageDraw

root = pathlib.Path(os.environ.get('ANIM_ROOT', str(pathlib.Path.home() / 'LegatumRuns/anim-pilot')))
atlas_path = pathlib.Path('app/src/assets/units/anim/horseman.webp')
out = str(root / 'review/3d-v2' / ('horseman-round' + os.environ.get('ROUND', '3') + '.mp4'))
meta = json.loads(atlas_path.with_suffix('.json').read_text())
atlas = Image.open(atlas_path).convert('RGBA')
w, h = meta['frame']['w'], meta['frame']['h']
order = ['idle', 'move', 'attack', 'hit', 'death']
clips = [(n, meta['clips'][n]) for n in order if n in meta['clips']]
FPS, SECONDS, SCALE, LABEL = 30, 8, 2, 28
cream = (240, 232, 214, 255)
cw, ch = w * SCALE, h * SCALE
frames = []
for n, c in clips:
    decoded = []
    for r in c['rects']:
        frame = Image.new('RGBA', (w, h))
        frame.paste(atlas.crop((r['x'], r['y'], r['x']+r['w'], r['y']+r['h'])), (r['ox'], r['oy']))
        decoded.append(frame.resize((cw, ch), Image.Resampling.LANCZOS))
    frames.append(decoded)
with tempfile.TemporaryDirectory(prefix='movie-', dir=root/'masters/horseman') as tmp:
    for t in range(FPS * SECONDS):
        canvas = Image.new('RGBA', (cw * len(clips), ch + LABEL), cream)
        d = ImageDraw.Draw(canvas)
        for k, ((n, c), fr) in enumerate(zip(clips, frames)):
            # one-shot clips replay every 2 s, holding the last frame (death holds as in game)
            i = int(t / FPS * c['fps'])
            i = i % c['frames'] if c['loop'] else min(int((t % (2 * FPS)) / FPS * c['fps']), c['frames'] - 1)
            canvas.alpha_composite(fr[i], (k * cw, LABEL))
            d.text((k * cw + 8, 6), n, fill=(60, 50, 40, 255))
        canvas.convert('RGB').save(f'{tmp}/{t:04d}.png')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', f'{tmp}/%04d.png',
                    '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2', '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
                    '-threads', '3', '-crf', '20', '-movflags', '+faststart', out], check=True)
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=codec_name,pix_fmt,width,height,nb_frames,duration','-of','json',out]))
stream=probe['streams'][0]
assert stream['codec_name']=='h264' and stream['pix_fmt']=='yuv420p'
assert int(stream['nb_frames'])==240 and abs(float(stream['duration'])-8)<.05
pathlib.Path(out).with_suffix('.json').write_text(json.dumps(probe,indent=2))
print(out, 'VERIFIED 240 frames, 8 seconds, H.264 yuv420p')
