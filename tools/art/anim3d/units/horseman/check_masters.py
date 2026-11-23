"""Reject stale/CPU masters before publishing a GPU completion receipt."""
import hashlib
import json
import os
from pathlib import Path
from PIL import Image

STAGES = {'b': 1, 'c': 1, 'c-details': 1, 'd': 4,
          'e-idle': 8, 'e-move': 8, 'e-attack': 10, 'e-hit': 4, 'e-death': 10}


def check(root):
    master = root / 'masters/horseman-3d'
    grade = hashlib.sha256((master / 'grade.json').read_bytes()).hexdigest()
    results = {}
    for stage, count in STAGES.items():
        folder = master / 'renders' / stage
        meta = json.loads((folder / 'render.json').read_text())
        assert (meta['engine'], meta['device'], meta['resolution']) == ('CYCLES', 'GPU', 512), stage + ': GPU512 required'
        assert meta['samples'] >= 64, stage + ': at least 64 samples required'
        clip = stage[2:] if stage.startswith('e-') else 'attack' if stage == 'd' else None
        blend = master / 'clips' / (clip + '.blend') if clip else master / 'horseman.blend'
        assert meta['blend_sha256'] == hashlib.sha256(blend.read_bytes()).hexdigest(), stage + ': stale blend'
        if stage != 'b':
            assert meta['grade_sha256'] == grade, stage + ': stale grade'
        assert len(list(folder.glob('*.png'))) == count, stage + ': frame count'
        for i in range(count):
            with Image.open(folder / f'{i:02}.png') as source:
                source = source.convert('RGBA')
            for size in (512, 256):
                path = root / 'masters/horseman' / str(size) / stage / f'{i:02}.png'
                with Image.open(path) as image:
                    assert image.size == (size, size) and image.mode == 'RGBA', str(path)
                    expected = source.resize((size, size), Image.Resampling.LANCZOS)
                    assert image.tobytes() == expected.tobytes(), str(path) + ': stale archived pixels'
        results[stage] = meta
    return results


if __name__ == '__main__':
    root = Path(os.environ['ANIM_ROOT'])
    result = check(root)
    (root / 'review/3d-v2/horseman-gpu-masters.json').write_text(json.dumps(result, indent=2))
    print('GPU_MASTERS_OK: nine stages, 512 masters and 256 gallery, current blend/grade hashes')
