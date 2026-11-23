"""Reject CPU/stale/upsampled masters before a GPU receipt can be written."""
import hashlib
import json
import os
from pathlib import Path
import sys
from PIL import Image

R = Path(os.environ['ANIM_ROOT'])
M = R / 'masters/scout'
V = R / 'review/3d-v2'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
stages = {'b': 3, 'c': 1, 'c-details': 1, 'd': 4,
          'e-idle': 8, 'e-move': 8, 'e-attack': 10, 'e-hit': 4, 'e-death': 10}
for stage, count in stages.items():
    folder = M / 'renders' / stage
    data = json.loads((folder / 'render.json').read_text())
    assert (data['engine'], data['device'], data['resolution'], data['samples']) == (
        'CYCLES', 'GPU', 512, 64), f'Not GPU64/512: {stage}'
    blend = M / 'clips' / (stage[2:] + '.blend') if stage.startswith('e-') else (
        M / 'clips/attack.blend' if stage == 'd' else M / (
            'scout-unpainted.blend' if stage == 'b' else 'scout.blend'))
    assert data['blend_sha256'] == sha(blend), f'Stale master: {stage}'
    if stage != 'b':
        assert data['grade_sha256'] == sha(M / 'grade.json')
    assert data['frames'] == count
    for i in range(count):
        assert Image.open(folder / f'{i:02}.png').size == (512, 512)
        assert Image.open(M / '256' / stage / f'{i:02}.png').size == (256, 256)
feet=json.loads((M/'feet.json').read_text())
assert feet['source_sha256']==sha(M/'clips/move.blend') and feet['device']=='GPU','Stale/CPU feet diagnostic'
assert len(feet['files'])==16
assert feet['stance_max_residual_m']<.005 and feet['toe_lateral_max_m']<.02
for item in feet['files']:assert sha(M/item['path'])==item['sha256']
assert (V/'scout-g-feet-check.png').is_file()
for clip in ['idle','move','hit','death']:
    motion=json.loads((M/('motion-'+clip+'.json')).read_text())
    assert motion['license']=='CC0-1.0' and motion['provider']=='Quaternius Universal Animation Library Standard'
if '--receipt' in sys.argv:
    validation = json.loads((V / 'scout-validation.json').read_text())
    audit = json.loads((V / 'scout-audit.json').read_text())
    assert validation['status'] == audit['status'] == 'PASS'
    movie = V / f"scout-round{os.environ['ROUND']}.mp4"
    assert movie.stat().st_size > 0 and movie.with_suffix('.json').exists()
    video = json.loads(movie.with_suffix('.json').read_text())
    atlas = Path('app/src/assets/units/anim/scout.webp')
    assert audit['source_sha256']==validation['source_sha256']==sha(M/'scout.blend')
    assert validation['atlas_sha256']==sha(atlas)
    assert video['atlas_sha256'] == sha(atlas)
    assert video['metadata_sha256'] == sha(atlas.with_suffix('.json'))
    (V / f"scout-gpu-round{os.environ['ROUND']}.json").write_text(json.dumps({
        'status': 'complete', 'art_approved': False, 'source_sha256': sha(M / 'scout.blend'),
        'validation': validation, 'movie_sha256': sha(movie),
    }, indent=2))
print('GPU masters verified')
