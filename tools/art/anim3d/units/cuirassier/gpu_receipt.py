"""A success receipt requires current GPU512 and matching gallery256 images."""
from pathlib import Path
from PIL import Image
import os
import json
import hashlib

root = Path(os.environ['ANIM_ROOT'])
master = root/'masters/cuirassier'
review = root/'review/3d-v2'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
stages = ['b', 'c', 'c-details', 'd', 'e-idle', 'e-move', 'e-attack', 'e-hit', 'e-death']
for stage in stages:
    folder = master/'renders'/stage
    manifest = json.loads((folder/'render.json').read_text())
    assert manifest['engine'] == 'CYCLES' and manifest['device'] == 'GPU', f'{stage}: GPU required'
    assert manifest['resolution'] == 512 and manifest['samples'] >= 48
    clip = stage[2:] if stage.startswith('e-') else 'attack' if stage=='d' else None
    blend = master/'clips'/f'{clip}.blend' if clip else master/('cuirassier-refined-plain.blend' if stage=='b' else 'cuirassier.blend')
    assert manifest['blend_sha256']==sha(blend),f'Stale {stage} source'
    for index in range(len(manifest['frames'])):
        source = folder/f'{index:02}.png'
        for size in [512, 256]:
            image = master/str(size)/stage/source.name
            assert Image.open(image).size == (size, size)
            expected = Image.open(source).resize((size,size),Image.Resampling.LANCZOS)
            assert Image.open(image).tobytes() == expected.tobytes(), f'Stale {image}'
feet=json.loads((master/'feet/manifest.json').read_text())
assert feet['device']=='GPU' and feet['frames']==8
assert feet['clip_sha256']==sha(master/'clips/move.blend')
assert (review/'cuirassier-g-feet-check.png').is_file()
round_number = os.environ['ROUND']
video = review/f'cuirassier-round{round_number}.mp4'
assert video.is_file()
receipt = {
    'round': round_number, 'master_sha256': sha(master/'cuirassier.blend'),
    'gpu512_gallery256': True, 'feet':feet,
    'atlas': json.loads((review/'cuirassier-validation.json').read_text()),
    'geometry': json.loads((review/'cuirassier-audit.json').read_text()),
    'video': json.loads(video.with_suffix('.json').read_text()),
    'video_sha256': sha(video), 'art_approved': False,
}
assert receipt['atlas']['passed'] and receipt['geometry']['passed']
(review/f'cuirassier-gpu-round{round_number}.json').write_text(json.dumps(receipt,indent=2))
print('GPU delivery complete; visual approval remains pending')
