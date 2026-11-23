"""Unit-owned paths and atlas contract; Blender and Pillow entry points share this."""
import os
import math
from pathlib import Path

SLUG = 'autonomous-armour'
# Five shoe pitches = three 12-tooth sprocket periods = five 12-stud
# wheel periods. All gear rolls in the same direction without a loop jump.
TRACK_H = 1.49
TRACK_R = 10 * TRACK_H / (11 * math.pi)
TRACK_Z = .24 + .041 + .025 / 2 + TRACK_R
TRACK_LENGTH = 4 * TRACK_H + 2 * math.pi * TRACK_R
MOVE_TRAVEL = 5 * TRACK_LENGTH / 64
ROAD_RADIUS = MOVE_TRAVEL / (5 * math.pi / 6)
ROOT = Path(os.environ.get('ANIM_ROOT', str(Path.home() / 'LegatumRuns/anim-pilot')))
MASTER = ROOT / 'masters' / SLUG
ASSETS = ROOT / 'assets' / SLUG
REVIEW = ROOT / 'review/3d-v2'
HERE = Path(__file__).resolve().parent
CLIPS = {'idle': (8, 10, True), 'move': (8, 12, True),
         'attack': (10, 14, False), 'hit': (4, 12, False), 'death': (10, 10, False)}
for directory in (MASTER, ASSETS, REVIEW):
    directory.mkdir(parents=True, exist_ok=True)


def log(message):
    with (REVIEW / f'{SLUG}-log.md').open('a') as f:
        f.write(message + '\n')
