"""Matched CPU motion A/B. Run through Blender, then --assemble in lane venv.

ANIM_ROOT is an isolated lane containing immutable before/<clip>/<clip>.blend.
Does not write shared masters or the game atlas. Uses one unchanged R10 grade.
"""
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(os.environ['ANIM_ROOT'])
MASTER = ROOT/'masters/spearman-3d-v2'
OUT = ROOT/'preview'
OUT.mkdir(exist_ok=True)
KIT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(KIT))


def render():
    import bpy
    receipt = {'settings': {'engine': 'CYCLES', 'device': 'CPU', 'resolution': 256,
                           'samples': 16, 'seed': 17, 'denoise': False, 'adaptive': False},
               'inputs': {}}
    cases = [('rest', MASTER/'spearman.blend')]
    for clip in ['move', 'death']:
        for version, folder in [('before', ROOT/'before'), ('after', MASTER/'clips')]:
            cases.append((f'{clip}-{version}', folder/clip/(clip+'.blend')))
    for clip in ['idle', 'attack', 'hit']:
        cases.append((f'{clip}-after', MASTER/'clips'/clip/(clip+'.blend')))
    for label, path in cases:
        bpy.ops.wm.open_mainfile(filepath=str(path))
        scene = bpy.context.scene
        scene.render.engine = 'CYCLES'
        scene.cycles.device = 'CPU'
        scene.cycles.samples = 16
        scene.cycles.seed = 17
        scene.cycles.use_denoising = scene.cycles.use_adaptive_sampling = False
        scene.render.resolution_x = scene.render.resolution_y = 256
        scene.render.resolution_percentage = 100
        scene.render.film_transparent = True
        scene.render.image_settings.file_format = 'PNG'
        scene.render.image_settings.color_mode = 'RGBA'
        scene.render.dither_intensity = 0
        scene.camera.data.dof.use_dof = False
        frames = json.loads(scene['sample_frames']) if label != 'rest' else [1]
        receipt['inputs'][label] = {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                                  'frames': frames, 'camera': [list(row) for row in scene.camera.matrix_world],
                                  'ortho': scene.camera.data.ortho_scale}
        for i, frame in enumerate(frames):
            dest = OUT/f'{label}-{i:02}.png'
            if dest.exists():
                continue  # Explicit resumable lane evidence; clear it after edits.
            if i and frame == frames[i-1]:
                import shutil
                shutil.copy2(OUT/f'{label}-{i-1:02}.png', dest)
            else:
                scene.frame_set(frame)
                scene.render.filepath = str(dest)
                bpy.ops.render.render(write_still=True)
        (OUT/'receipt.json').write_text(json.dumps(receipt, indent=2))


def assemble():
    from PIL import Image, ImageDraw
    from grade import apply
    from kit.images import resize_rgba
    review = Path.home()/'LegatumRuns/anim-pilot/review/3d-v2'
    lut = json.loads((MASTER/'painting-grade.json').read_text())['luts']
    painting = Image.open('app/src/assets/units/spearman-256.png').convert('RGBA')
    for p in OUT.glob('*.png'):
        apply(Image.open(p).convert('RGBA'), lut).save(OUT/('graded-'+p.name)) if not p.name.startswith('graded-') else None
    for clip, count in [('move', 8), ('death', 10), ('rest', 1)]:
        expected = [OUT/'graded-rest-00.png'] if clip == 'rest' else [OUT/f'graded-{clip}-{version}-{i:02}.png' for version in ['before', 'after'] for i in range(count)]
        if not all(p.exists() for p in expected):
            continue
        for size in [256, 160, 64]:
            # Two rows, painting in first column; no resized UI screenshots.
            sheet = Image.new('RGB', ((count+1)*(size+8), 24+2*(size+32)), '#e0d7bf')
            draw = ImageDraw.Draw(sheet)
            draw.text((4, 4), f'Cycles CPU | 16 samples | R10 fixed grade | {size}px', fill='#28221b')
            for row, version in enumerate(['before', 'after']):
                y = 24+row*(size+32)
                for col in range(count+1):
                    path = OUT/(f'graded-rest-00.png' if clip == 'rest' else f'graded-{clip}-{version}-{col-1:02}.png')
                    im = painting if col == 0 else Image.open(path).convert('RGBA')
                    x = col*(size+8)+4
                    im = resize_rgba(im, (size, size))
                    sheet.paste(im, (x, y+28), im)
                    label = 'Painting' if col == 0 else (f'R10 {col-1}' if row == 0 else f'R11c {col-1}')
                    draw.text((x, y+6), label, fill='#28221b')
            sheet.save(review/f'spearman-r11c-{clip}-{size}.png')
    for clip, count in [('idle', 8), ('move', 8), ('attack', 10), ('hit', 4), ('death', 10)]:
        folder = OUT/'frames-160'/clip
        folder.mkdir(parents=True, exist_ok=True)
        for i in range(count):
            path = OUT/f'graded-{clip}-after-{i:02}.png'
            if path.exists():
                resize_rgba(Image.open(path).convert('RGBA'), (160, 160)).save(folder/f'{i:02}.png')
    (OUT/'grade-receipt.json').write_text(json.dumps({'grade_sha256': hashlib.sha256((MASTER/'painting-grade.json').read_bytes()).hexdigest(),
                                                   'label': 'Cycles CPU 256px 16 samples seed17 no denoising; R10 fixed LUT'}, indent=2))


if __name__ == '__main__':
    assemble() if '--assemble' in sys.argv else render()
