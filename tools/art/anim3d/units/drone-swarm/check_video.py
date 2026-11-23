"""Verify the actual encoded movie, not just FFmpeg's exit status."""
import json
import os
import subprocess
from pathlib import Path

root = Path(os.environ.get('ANIM_ROOT', Path.home() / 'LegatumRuns/anim-pilot'))
path = root / 'review/3d-v2' / f'drone-swarm-round{os.environ.get("ROUND", "2")}.mp4'
result = json.loads(subprocess.check_output([
    'ffprobe', '-v', 'error', '-show_entries',
    'stream=codec_name,pix_fmt,width,height,nb_frames:format=duration',
    '-of', 'json', str(path),
]))
stream = result['streams'][0]
assert (stream['codec_name'], stream['pix_fmt']) == ('h264', 'yuv420p')
assert (stream['width'], stream['height'], int(stream['nb_frames'])) == (1600, 348, 240)
assert abs(float(result['format']['duration']) - 8) < .05
(root / 'masters/drone-swarm/video-validation.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(result))
