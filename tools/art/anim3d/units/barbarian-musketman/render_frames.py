"""Fresh gated Blender process per frame, with content-bound restart checkpoints."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from PIL import Image
from finish import CLIPS, HERE, M, review, sha, stage_blend


def render_stage(stage, frames):
    out = M / 'renders' / stage
    out.mkdir(parents=True, exist_ok=True)
    manifest = out / 'render.json'
    manifest.unlink(missing_ok=True)
    settings = dict(stage=stage, engine='CYCLES', device=os.environ.get('CYCLES_DEVICE', 'CPU'),
                    samples=int(os.environ.get('SAMPLES', '6')),
                    resolution=int(os.environ.get('RESOLUTION', '256')),
                    blend_sha256=sha(stage_blend(stage)), frames=len(frames))
    code = hashlib.sha256(b''.join(p.read_bytes() for p in sorted(HERE.glob('*.py')))).hexdigest()
    signature = dict(settings, code_sha256=code)
    for index, frame in enumerate(frames):
        path = out / f'{index:02}.png'
        checkpoint = path.with_suffix('.checkpoint.json')
        expected = dict(signature, frame=frame, index=index)
        if stage == 'e-death' and index == len(frames)-1:
            expected['held_frame_sha256'] = sha(out / f'{index-1:02}.png')
        if checkpoint.exists() and path.exists():
            if json.loads(checkpoint.read_text()) == dict(expected, png_sha256=sha(path)):
                print(f'CHECKPOINT {stage}/{index:02}', flush=True)
                continue
        checkpoint.unlink(missing_ok=True)
        # The gate already retries abort/bus/segfault. SIGTRAP (133) was not included.
        for attempt in range(2):
            result = subprocess.run([str(HERE / 'render.sh'), 'frame-' + stage],
                                    env=dict(os.environ, FRAME_INDEX=str(index)))
            if result.returncode == 0:
                break
            if result.returncode not in (133, -5) or attempt:
                raise subprocess.CalledProcessError(result.returncode, result.args)
            print(f'SIGTRAP: retrying only {stage}/{index:02} in a fresh gated process', flush=True)
        with Image.open(path) as image:
            image.load()
            assert image.size == (settings['resolution'],) * 2 and image.mode == 'RGBA'
        checkpoint.write_text(json.dumps(dict(expected, png_sha256=sha(path))))
    manifest.write_text(json.dumps(settings))
    review(stage)


def main():
    stages = {'b-plain': [1], 'c-textured-lit': [1], 'd-rig-poses': [1, 3, 5, 7]}
    stages.update({'e-' + c: list(range(1, n + 1)) for c, (n, _, _) in CLIPS.items()})
    stages.update({'g-feet-' + view: list(range(1, 9)) for view in ('top', 'front')})
    selected = sys.argv[1:]
    for stage, frames in stages.items():
        if not selected or stage in selected:
            render_stage(stage, frames)


if __name__ == '__main__':
    main()
