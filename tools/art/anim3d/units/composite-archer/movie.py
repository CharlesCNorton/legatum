"""Eight-second review from decoded trimmed cells, with original frame anchors."""
import json
import os
import subprocess
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(os.environ.get('ANIM_ROOT', Path.home() / 'LegatumRuns/anim-pilot'))
OUT = ROOT / 'review/3d-v2'
path = Path('app/src/assets/units/anim/composite-archer.webp')
meta = json.loads(path.with_suffix('.json').read_text())
atlas = Image.open(path).convert('RGBA')
frames = {}
for name, rects in meta['frames'].items():
    frames[name] = []
    for r in rects:
        cell = Image.new('RGBA', (160, 160))
        cell.paste(atlas.crop((r['x'], r['y'], r['x'] + r['w'], r['y'] + r['h'])), (r['ox'], r['oy']))
        frames[name].append(cell.resize((320, 320), Image.Resampling.LANCZOS))
target = OUT / f"composite-archer-round{os.environ.get('ROUND', '2')}.mp4"
with tempfile.TemporaryDirectory(dir=ROOT / 'tmp', prefix='composite-archer-movie-') as tmp:
    for tick in range(240):
        canvas = Image.new('RGBA', (1600, 348), (240, 232, 214, 255))
        draw = ImageDraw.Draw(canvas)
        for col, (name, clip) in enumerate(meta['clips'].items()):
            index = int(tick / 30 * clip['fps']) % clip['frames'] if clip['loop'] else min(int((tick % 60) / 30 * clip['fps']), clip['frames'] - 1)
            canvas.alpha_composite(frames[name][index], (col * 320, 28))
            draw.text((col * 320 + 8, 6), name, fill=(60, 50, 40, 255))
        canvas.convert('RGB').save(Path(tmp) / f'{tick:04d}.png')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', '30', '-i', f'{tmp}/%04d.png', '-c:v', 'libx264', '-threads', '3', '-pix_fmt', 'yuv420p', '-crf', '20', '-movflags', '+faststart', str(target)], check=True)
probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams', '-of', 'json', str(target)]))['streams'][0]
assert (probe['codec_name'], probe['pix_fmt'], probe['width'], probe['height'], int(probe['nb_frames'])) == ('h264', 'yuv420p', 1600, 348, 240)
assert abs(float(probe['duration']) - 8) < .01
(OUT / f"composite-archer-round{os.environ.get('ROUND', '2')}-video.json").write_text(json.dumps(probe, indent=2))
print(f'PASS video: {target}; H.264/yuv420p, 1600x348, 240 frames, 8 seconds')
