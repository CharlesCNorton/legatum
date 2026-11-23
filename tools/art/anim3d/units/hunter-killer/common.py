"""Unit-local pipeline paths and delivery contract."""
import os
from pathlib import Path
SLUG = 'hunter-killer'
ROOT = Path(os.environ.get('ANIM_ROOT', str(Path.home() / 'LegatumRuns/anim-pilot')))
MASTER = ROOT / 'masters' / SLUG
ASSETS = ROOT / 'assets' / SLUG
REVIEW = ROOT / 'review/3d-v2'
CLIPS = {'idle': (8,10,True), 'move': (8,12,True), 'attack': (10,14,False),
         'hit': (4,12,False), 'death': (10,10,False)}
for path in (MASTER, ASSETS, REVIEW): path.mkdir(parents=True, exist_ok=True)
def log(message):
    with (REVIEW / f'{SLUG}-log.md').open('a') as f: f.write(message+'\n')
