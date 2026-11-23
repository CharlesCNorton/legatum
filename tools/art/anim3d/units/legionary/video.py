"""Eight-second review movie reconstructed from the actual trimmed WebP atlas."""
import json
import os
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw

root = Path(os.environ.get('ANIM_ROOT', Path.home() / 'LegatumRuns/anim-pilot'))
review = root / 'review/3d-v2'
atlas_path = Path('app/src/assets/units/anim/legionary.webp')
meta = json.loads(atlas_path.with_suffix('.json').read_text())
atlas = Image.open(atlas_path).convert('RGBA')
assert meta['format'] == 'trimmed-rows-v1'
clips = list(meta['clips'].items())
frames = {}
for name, clip in clips:
    frames[name] = []
    for r in clip['rects']:
        im = Image.new('RGBA', (160, 160))
        im.paste(atlas.crop((r['x'], r['y'], r['x'] + r['w'], r['y'] + r['h'])), (r['ox'], r['oy']))
        frames[name].append(im.resize((320, 320), Image.Resampling.LANCZOS))
out = review / f'legionary-round{os.environ.get("ROUND", "2")}.mp4'
cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pixel_format', 'rgb24',
       '-video_size', '1600x348', '-framerate', '30', '-i', '-', '-an', '-c:v', 'libx264',
       '-threads', '3', '-pix_fmt', 'yuv420p', '-crf', '20', '-movflags', '+faststart', str(out)]
process = subprocess.Popen(cmd, stdin=subprocess.PIPE)
try:
    for t in range(240):
        canvas = Image.new('RGBA', (1600, 348), (240, 232, 214, 255))
        draw = ImageDraw.Draw(canvas)
        for k, (name, clip) in enumerate(clips):
            i = int(t / 30 * clip['fps']) % clip['frames'] if clip['loop'] else min(int((t % 60) / 30 * clip['fps']), clip['frames'] - 1)
            canvas.alpha_composite(frames[name][i], (k * 320, 28))
            draw.text((k * 320 + 8, 6), name, fill=(60, 50, 40, 255))
        process.stdin.write(canvas.convert('RGB').tobytes())
finally:
    process.stdin.close()
assert process.wait() == 0, 'FFmpeg failed'
probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams', '-of', 'json', str(out)]))['streams'][0]
assert (probe['codec_name'], probe['pix_fmt'], probe['width'], probe['height']) == ('h264', 'yuv420p', 1600, 348)
assert int(probe['nb_frames']) == 240 and abs(float(probe['duration']) - 8) < .001
(review / 'legionary-video-validation.json').write_text(json.dumps({'status': 'PASS', 'path': str(out), 'stream': probe}, indent=2))
print('VIDEO_PASS', out)
