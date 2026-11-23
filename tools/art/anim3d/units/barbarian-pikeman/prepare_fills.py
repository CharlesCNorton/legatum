"""Register generated pigment to the painting; alpha never changes geometry."""
import hashlib
import json
import os
from pathlib import Path

from PIL import Image

root = Path(os.environ['ANIM_ROOT'])
assets = root / 'assets/barbarian-pikeman'
lock_path = Path(__file__).with_name('assets.lock.json')
lock = json.loads(lock_path.read_text())
for name in ['stone-fill-source.png', 'painted-fills-source.png']:
    path = assets / name
    expected = lock[str(path.relative_to(root))]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, name

source = Image.open(assets / 'stone-fill-source.png').convert('RGBA')
# Ignore isolated alpha specks when measuring the generated plate.
mask = source.getchannel('A').point(lambda a: 255 if a > 220 else 0)
bounds = mask.getbbox()
reference = Image.open(assets / 'painting-aligned.png').convert('RGBA')
target = reference.crop((200, 856, 720, 1024)).getbbox()
target = (target[0] + 200, target[1] + 856, target[2] + 200, target[3] + 856)
plate = Image.new('RGBA', reference.size)
plate.alpha_composite(source.crop(bounds).resize(
    (target[2] - target[0], target[3] - target[1]), Image.Resampling.LANCZOS), target[:2])
# The original lower rim has no occluding boots. Keep its exact painted pigment.
blend = Image.new('L', reference.size)
blend.putdata([max(0, min(255, round((y - 912) / 8 * 255)))
               for y in range(1024) for x in range(1024)])
plate = Image.composite(reference, plate, blend)
plate.save(assets / 'stone-registered.png')

atlas = Image.open(assets / 'painted-fills-source.png').convert('RGB')
w, h = atlas.size
for name, box in {
    'quilt': (0, 0, w // 2, h // 2),
    'trousers': (w // 2, 0, w, h // 2),
    'leather': (0, h // 2, w // 2, h),
    'skin': (w // 2, h // 2, w, h),
}.items():
    atlas.crop(box).save(assets / f'fill-{name}.png')
print('FILLS_OK', target)
