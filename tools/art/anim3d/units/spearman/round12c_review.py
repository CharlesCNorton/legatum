"""Matched CPU evidence for motion lane c; never writes the shipped atlas.

Run through Blender to render, then the isolated Python with --assemble.
ANIM_ROOT must contain before/<clip>/<clip>.blend and masters/spearman-3d-v2.
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
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
COUNTS = {'idle':8, 'move':8, 'attack':10, 'hit':4, 'death':10}


def render():
    import bpy
    from bpy_extras.object_utils import world_to_camera_view
    from kit.ab import invariant, preview_settings
    from kit.motion_metrics import sample, summarise
    receipt = {'settings': {}, 'inputs': {}, 'motion': {}, 'frozen': {}}
    for clip in ('idle', 'attack'):
        a, b = ROOT/'before'/clip/(clip+'.blend'), MASTER/'clips'/clip/(clip+'.blend')
        hashes = [hashlib.sha256(p.read_bytes()).hexdigest() for p in (a,b)]
        assert hashes[0] == hashes[1], (clip, 'frozen blend changed')
        receipt['frozen'][clip] = {'blend_sha256': hashes[0], 'identical': True}
    cases = [('rest', MASTER/'spearman.blend')]
    cases += [(clip+'-before', ROOT/'before'/clip/(clip+'.blend')) for clip in ('move','hit','death')]
    cases += [(clip+'-after', MASTER/'clips'/clip/(clip+'.blend')) for clip in COUNTS]
    for label, path in cases:
        bpy.ops.wm.open_mainfile(filepath=str(path))
        scene = bpy.context.scene
        receipt['settings'][label] = preview_settings(scene)
        scene.render.dither_intensity = 0
        scene.camera.data.dof.use_dof = False
        frames = json.loads(scene['sample_frames']) if label != 'rest' else [1]
        receipt['inputs'][label] = {'path':str(path), 'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                                    'frames':frames, 'actions':invariant(scene)['actions']}
        if label != 'rest':
            rig = bpy.data.objects['Spearman • MPFB game_engine']
            rows, rotations, cloth = sample(scene, rig, frames,
                equipment={'shield':(bpy.data.objects['Aspis control'], 'lowerarm_l', 'tail')},
                cloth=bpy.data.objects['Cloak • simulated wool'])
            receipt['motion'][label] = summarise(rows, rotations, cloth)
            projections = []
            for frame in frames:
                scene.frame_set(frame)
                def screen(name):
                    p=world_to_camera_view(scene, scene.camera, rig.matrix_world@rig.pose.bones[name].head)
                    return [p.x*256,(1-p.y)*256]
                l,r=screen('foot_l'),screen('foot_r')
                kl,kr=screen('calf_l'),screen('calf_r')
                projections.append({'frame':frame,'ankle_separation_px':abs(l[0]-r[0]),
                                     'knee_separation_px':abs(kl[0]-kr[0])})
            receipt['motion'][label]['screen'] = projections
        for i, frame in enumerate(frames):
            dest=OUT/f'{label}-{i:02}.png'
            if dest.exists():
                continue
            if i and frame == frames[i-1]:
                import shutil
                shutil.copy2(OUT/f'{label}-{i-1:02}.png',dest)
            else:
                scene.frame_set(frame)
                scene.render.filepath=str(dest)
                bpy.ops.render.render(write_still=True)
        (OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')


def assemble():
    from PIL import Image,ImageDraw
    from grade import apply
    from kit.images import resize_rgba
    review=Path.home()/'LegatumRuns/anim-pilot/review/3d-v2'
    lut=json.loads((MASTER/'painting-grade.json').read_text())['luts']
    painting=Image.open('app/src/assets/units/spearman-256.png').convert('RGBA')
    for p in OUT.glob('*.png'):
        if not p.name.startswith('graded-'):
            apply(Image.open(p).convert('RGBA'),lut).save(OUT/('graded-'+p.name))
    for clip in ('move','hit','death','rest'):
        count=1 if clip=='rest' else COUNTS[clip]
        for size in (256,160,64):
            sheet=Image.new('RGB',((count+1)*(size+8),24+2*(size+30)),'#f8f3e7')
            draw=ImageDraw.Draw(sheet)
            draw.text((4,4),f'Cycles CPU | 16 samples seed 17 | fixed R11 LUT | {size}px | hybrid fallback, not final Eevee look',fill='#30281f')
            for row,version in enumerate(('before','after')):
                y=24+row*(size+30)
                for col in range(count+1):
                    p=OUT/('graded-rest-00.png' if clip=='rest' else f'graded-{clip}-{version}-{col-1:02}.png')
                    im=painting if col==0 else Image.open(p).convert('RGBA')
                    if col==0 and size==64:im=Image.open('app/src/assets/units/spearman-64.png').convert('RGBA')
                    im=resize_rgba(im,(size,size),space='display')
                    x=4+col*(size+8);sheet.paste(im,(x,y+26),im)
                    label='Painting' if col==0 else f'{"R11" if row==0 else "R12c"} {col-1}'
                    draw.text((x,y+6),label,fill='#30281f')
            sheet.save(review/f'spearman-r12c-{clip}-{size}.png')
    for clip,count in COUNTS.items():
        folder=OUT/'frames-160'/clip;folder.mkdir(parents=True,exist_ok=True)
        for i in range(count):
            im=Image.open(OUT/f'graded-{clip}-after-{i:02}.png').convert('RGBA')
            resize_rgba(im,(160,160),space='display').save(folder/f'{i:02}.png')
    (review/'spearman-r12c-motion-metrics.json').write_bytes((OUT/'receipt.json').read_bytes())

if __name__=='__main__':
    assemble() if '--assemble' in sys.argv else render()
