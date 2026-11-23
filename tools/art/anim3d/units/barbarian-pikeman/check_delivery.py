"""Receipt only for actual GPU512 renders, all gallery masters and decoded video."""
import hashlib
import json
import os
import subprocess
from pathlib import Path

from PIL import Image

root = Path(os.environ['ANIM_ROOT'])
master = root / 'masters/barbarian-pikeman'
review = root / 'review/3d-v2'
slug = 'barbarian-pikeman'
round_number = os.environ.get('ROUND', '2')
report = json.loads((review / f'{slug}-pack.json').read_text())
validation = json.loads((review / f'{slug}-validation.json').read_text())
assert report['source_resolution'] == 512 and validation['gpu'] and validation['ok']
expected = {'b-plain': 1, 'c-textured-lit': 1, 'c-details': 1, 'd-rig-poses': 4,
            'e-idle': 8, 'e-move': 8, 'e-attack': 10, 'e-hit': 4, 'e-death': 10, 'g-feet-check': 16}
assert set(report['render_sources']) == set(expected)
for stage, count in expected.items():
    manifest = report['render_sources'][stage]
    assert manifest['device'] == 'GPU' and manifest['engine'] == 'CYCLES'
    assert manifest['resolution'] == 512 and manifest['frames'] == count
    source = (master / 'clips' / (stage[2:] + '.blend') if stage.startswith('e-') else
              master / 'clips/attack.blend' if stage == 'd-rig-poses' else
              master / 'clips/move.blend' if stage == 'g-feet-check' else
              master / ('plain.blend' if stage == 'b-plain' else slug + '.blend'))
    assert hashlib.sha256(source.read_bytes()).hexdigest() == manifest['blend_sha256']
    for size in [512, 256]:
        for i in range(count):
            assert Image.open(master / 'graded' / str(size) / stage / f'{i:02}.png').size == (size, size)
movie = review / f'{slug}-round{round_number}.mp4'
probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0',
    '-show_entries', 'stream=width,height,codec_name,pix_fmt,nb_frames:format=duration', '-of', 'json', str(movie)]))
stream = probe['streams'][0]
assert (stream['codec_name'], stream['pix_fmt'], stream['width'], stream['height'],
        int(stream['nb_frames'])) == ('h264', 'yuv420p', 1600, 348, 240)
assert abs(float(probe['format']['duration']) - 8) < .05
receipt = {'round': round_number, 'master_sha256': report['master_sha256'],
           'atlas_sha256': report['atlas_sha256'], 'bytes': report['bytes'],
           'quality': report['quality'], 'gpu512': True, 'gallery256': True,
           'movie_sha256': hashlib.sha256(movie.read_bytes()).hexdigest(), 'art_approved': False}
(review / f'{slug}-gpu-round{round_number}.json').write_text(json.dumps(receipt, indent=2))
print('GPU_DELIVERY_OK', json.dumps(receipt))
