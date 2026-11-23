"""Render one frame per Blender process, with verified resumable checkpoints.

The round-one Metal process trapped after 27 renders. Its log did not identify
the cause. Fresh processes avoid carrying render/volume state between frames;
only complete source/settings/hash-matched stages receive render.json.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(os.environ.get('ANIM_ROOT', Path.home()/'LegatumRuns/anim-pilot'))
MASTER = ROOT/'masters/musketman'
HERE = Path(__file__).resolve().parent
STAGES = {'b-plain': [1], 'c-textured-lit': [1], 'd-rig-poses': [1, 3, 5, 7],
          **{'e-'+name: list(range(1, count+1)) for name, count in
             [('idle', 8), ('move', 8), ('attack', 10), ('hit', 4), ('death', 10)]},
          'g-feet-top': list(range(1, 9)), 'g-feet-front': list(range(1, 9))}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def blend_for(stage):
    name = ('plain.blend' if stage == 'b-plain' else 'musketman.blend'
            if stage == 'c-textured-lit' else 'clips/attack.blend'
            if stage == 'd-rig-poses' else 'clips/move.blend'
            if stage.startswith('g-feet-') else f'clips/{stage[2:]}.blend')
    return MASTER/name


def settings(stage):
    return {'stage': stage, 'engine': 'CYCLES',
            'device': os.environ.get('CYCLES_DEVICE', 'CPU'),
            'resolution': int(os.environ.get('RESOLUTION', '256')),
            'samples': int(os.environ.get('SAMPLES', '6')),
            'blend_sha256': sha(blend_for(stage)),
            'renderer_sha256': sha(HERE/'scene.py') + sha(__file__)}


def matches(path, expected):
    try:
        record = json.loads(path.with_suffix('.json').read_text())
        return record == dict(expected, png_sha256=sha(path))
    except (OSError, ValueError):
        return False


def render_one(configure):
    import bpy
    from mathutils import Vector
    stage, index = os.environ['RENDER_STAGE'], int(os.environ['RENDER_INDEX'])
    frame = STAGES[stage][index]
    expected = dict(settings(stage), index=index, frame=frame)
    out = MASTER/'renders'/stage
    out.mkdir(parents=True, exist_ok=True)
    path = out/f'{index:02}.png'
    path.with_suffix('.json').unlink(missing_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(blend_for(stage)))
    scene = configure()
    assert scene.camera is not None
    assert scene.cycles.device == expected['device']
    if stage.startswith('g-feet-'):
        target = Vector((0, .08, .22))
        camera = scene.camera
        camera.location = target + Vector((0, 0, 5) if stage.endswith('top') else (5, 0, .18))
        camera.rotation_euler = (target-camera.location).to_track_quat('-Z', 'Y').to_euler()
        camera.data.ortho_scale = 1.35
        for obj in scene.objects:
            if obj.type == 'MESH':
                obj.hide_render = not any(word in obj.name for word in
                                          ('boot', 'stocking', 'breeches', 'stationary cream base'))
    if stage == 'b-plain':
        material = bpy.data.materials.new('MAT-review clay')
        material.diffuse_color = (.45, .4, .32, 1)
        scene.view_layers[0].material_override = material
    # The final death sample is an exact hold, including sampling noise.
    if stage == 'e-death' and index == 9:
        previous = out/'08.png'
        assert matches(previous, dict(settings(stage), index=8, frame=9))
        path.write_bytes(previous.read_bytes())
    else:
        scene.frame_set(frame)
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
    path.with_suffix('.json').write_text(json.dumps(dict(expected, png_sha256=sha(path))))


def run(stage):
    from PIL import Image
    expected = settings(stage)
    out = MASTER/'renders'/stage
    out.mkdir(parents=True, exist_ok=True)
    manifest = out/'render.json'
    manifest.unlink(missing_ok=True)
    for index, frame in enumerate(STAGES[stage]):
        path = out/f'{index:02}.png'
        record = dict(expected, index=index, frame=frame)
        if not matches(path, record):
            env = dict(os.environ, RENDER_STAGE=stage, RENDER_INDEX=str(index))
            command = ['blender', '-b', '--disable-autoexec', '--factory-startup',
                       '--python-exit-code', '1', '--python', str(HERE/'scene.py'), '--', 'frame']
            # The global gate retries SIGABRT/SEGV, but not the observed SIGTRAP.
            # Retry that signal once in a fresh process, never hide other failures.
            for attempt in range(2):
                result = subprocess.run(command, env=env)
                if result.returncode not in (133, -5) or attempt:
                    result.check_returncode()
                    break
                print(f'Retrying trapped frame {stage}/{index} once', flush=True)
        assert matches(path, record), (stage, index, 'checkpoint mismatch')
        with Image.open(path) as image:
            assert image.size == (expected['resolution'],)*2 and image.mode == 'RGBA'
    # Check again after the sequence in case a source was replaced during it.
    assert settings(stage) == expected, 'Source/settings changed during stage'
    receipt = dict(expected, frames=len(STAGES[stage]),
                   frame_sha256={f'{i:02}.png': sha(out/f'{i:02}.png') for i in range(len(STAGES[stage]))})
    manifest.write_text(json.dumps(receipt))
    subprocess.run([sys.executable, str(HERE/'finish.py'), 'review', stage], check=True)
    with (ROOT/'review/3d-v2/musketman-log.md').open('a') as log:
        log.write(f'- Posted {stage} review ({expected["device"]}, {expected["resolution"]} px); isolated verified frame jobs.\n')


if __name__ == '__main__':
    for stage in sys.argv[1:] or STAGES:
        run(stage)
