"""Decode trim offsets before creating the driver movie; probe the encoded result."""
import json
import hashlib
import os
from pathlib import Path
import subprocess
from PIL import Image, ImageDraw

ROOT = Path(os.environ.get('ANIM_ROOT', Path.home() / 'LegatumRuns/anim-pilot'))
OUT = ROOT / 'review/3d-v2' / f"scout-round{os.environ.get('ROUND', '2')}.mp4"
ATLAS = Path('app/src/assets/units/anim/scout.webp')
meta = json.loads(ATLAS.with_suffix('.json').read_text())
atlas = Image.open(ATLAS).convert('RGBA')
assert meta['formatVersion'] == 2
frames = {}
for clip, info in meta['clips'].items():
    frames[clip] = []
    for trim in meta['trims'][clip]:
        x, y, w, h, ox, oy = (trim[k] for k in ('x', 'y', 'w', 'h', 'ox', 'oy'))
        im = Image.new('RGBA', (160, 160))
        im.paste(atlas.crop((x, y, x+w, y+h)), (ox, oy))
        frames[clip].append(im.resize((320, 320), Image.Resampling.LANCZOS))
encoder = subprocess.Popen([
    'ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pixel_format', 'rgb24',
    '-video_size', '1600x348', '-framerate', '30', '-i', '-', '-an', '-c:v', 'libx264',
    '-threads', '3', '-pix_fmt', 'yuv420p', '-crf', '20', '-movflags', '+faststart', str(OUT)
], stdin=subprocess.PIPE)
for frame in range(240):
    canvas = Image.new('RGBA', (1600, 348), (240, 232, 214, 255))
    draw = ImageDraw.Draw(canvas)
    for col, (clip, info) in enumerate(meta['clips'].items()):
        index = int(frame / 30 * info['fps']) % info['frames'] if info['loop'] else min(
            int((frame % 60) / 30 * info['fps']), info['frames'] - 1)
        canvas.alpha_composite(frames[clip][index], (col * 320, 28))
        draw.text((col * 320 + 8, 6), clip, fill=(60, 50, 40, 255))
    encoder.stdin.write(canvas.convert('RGB').tobytes())
encoder.stdin.close()
assert encoder.wait() == 0, 'Video encoder failed'
probe = json.loads(subprocess.check_output([
    'ffprobe', '-v', 'error', '-show_streams', '-of', 'json', str(OUT)
]))['streams'][0]
assert (probe['codec_name'], probe['pix_fmt'], probe['width'], probe['height']) == (
    'h264', 'yuv420p', 1600, 348)
assert int(probe['nb_frames']) == 240 and abs(float(probe['duration']) - 8) < .01
OUT.with_suffix('.json').write_text(json.dumps({
    'codec': 'h264', 'pixel_format': 'yuv420p', 'frames': 240, 'seconds': 8,
    'size': [1600, 348], 'source': 'decoded trimmed atlas',
    'atlas_sha256': hashlib.sha256(ATLAS.read_bytes()).hexdigest(),
    'metadata_sha256': hashlib.sha256(ATLAS.with_suffix('.json').read_bytes()).hexdigest(),
}, indent=2))
print(OUT)
