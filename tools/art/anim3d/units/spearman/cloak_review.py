"""R14b isolated cloth A/B. Blender: --bake or --render; Python: --assemble.

Copy the round-13 master/look and clips to ANIM_ROOT first; before/{move,attack}
contains preserved clips. Never touches shared masters or the shipped atlas.
"""
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
ROOT = Path(os.environ['ANIM_ROOT'])
MASTER = ROOT/'masters/spearman-3d-v2'
OUT = ROOT/'preview'
NAME = 'Cloak • simulated wool'


def bake():
    import bpy
    from cloak import configure
    from kit.ab import invariant
    bpy.ops.wm.open_mainfile(filepath=str(MASTER/'spearman.blend'))
    cloak = bpy.data.objects[NAME]
    group = cloak.vertex_groups['Shoulder pins']
    pins = {v.index: g.weight for v in cloak.data.vertices
            for g in v.groups if g.group == group.index}
    report = {}
    for clip in ('move', 'attack'):
        bpy.ops.wm.open_mainfile(filepath=str(ROOT/'before'/clip/(clip+'.blend')))
        scene = bpy.context.scene
        before = invariant(scene)['actions']
        cloak = bpy.data.objects[NAME]
        cloth = cloak.modifiers['Cloth per clip']
        pc = cloth.point_cache
        with bpy.context.temp_override(point_cache=pc):
            bpy.ops.ptcache.free_bake()
        group = cloak.vertex_groups['Shoulder pins']
        for index, weight in pins.items():
            group.add([index], weight, 'REPLACE')
        settings = configure(cloak, clip)
        scene.frame_set(1)
        destination = MASTER/'clips'/clip/(clip+'.blend')
        bpy.ops.wm.save_as_mainfile(filepath=str(destination))
        with bpy.context.temp_override(point_cache=pc):
            bpy.ops.ptcache.bake(bake=True)
        assert pc.is_baked
        after = invariant(scene)['actions']
        assert before == after, (clip, 'cloth pass changed actions')
        source = json.loads(scene['motion_source'])
        source['cloth_response'] = settings
        scene['motion_source'] = json.dumps(source)
        bpy.ops.wm.save_as_mainfile(filepath=str(destination))
        report[clip] = {'actions_before': before, 'actions_after': after,
                        'actions_identical': True, 'cloth_baked': pc.is_baked,
                        'settings': settings}
        (ROOT/'cloth-bake.json').write_text(json.dumps(report, indent=2)+'\n')
    print('CLOTH_BAKE_OK', json.dumps(report), flush=True)


def render():
    import bpy
    import hashlib
    import numpy as np
    from bpy_extras.object_utils import world_to_camera_view
    from kit.ab import invariant, preview_settings, render_still
    from kit.cpu_look import graph_for_sun
    import look
    OUT.mkdir(exist_ok=True)
    report = json.loads((OUT/'receipt.json').read_text()) if (OUT/'receipt.json').exists() else {}
    cases = [('rest', MASTER/'spearman.blend')]
    cases += [(f'{clip}-{version}',
               (ROOT/'before'/clip if version == 'before' else MASTER/'clips'/clip)/(clip+'.blend'))
              for clip in ('move','attack') for version in ('before','after')]
    if '--context-only' in sys.argv:
        cases = [(clip, MASTER/'clips'/clip/(clip+'.blend')) for clip in ('idle','hit','death')]
    for label, path in cases:
        if '--after-only' in sys.argv and not label.endswith('-after'):
            continue
        bpy.ops.wm.open_mainfile(filepath=str(path))
        scene = bpy.context.scene
        frames = [1] if label == 'rest' else json.loads(scene['sample_frames'])
        receipt = {'source_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                   'actions': invariant(scene)['actions'], 'frames': frames}
        if label.endswith(('-before', '-after')):
            cloak = bpy.data.objects[NAME]
            rig = bpy.data.objects['Spearman • MPFB game_engine']
            positions, relative, outline = [], [], []
            # Include the duplicate loop endpoint to expose cloth-only seams.
            dense = list(range(25, scene.frame_end+1))
            for frame in dense:
                scene.frame_set(frame)
                evaluated = cloak.evaluated_get(bpy.context.evaluated_depsgraph_get())
                mesh = evaluated.to_mesh()
                world = [cloak.matrix_world @ v.co for v in mesh.vertices]
                carrier_inverse = (rig.matrix_world @ rig.pose.bones['spine_03'].matrix).inverted()
                positions.append(np.array([list(p) for p in world]))
                relative.append(np.array([list(carrier_inverse @ p) for p in world]))
                points = [world_to_camera_view(scene, scene.camera, p) for p in world]
                band = [p.x*256 for p in points if 125 < (1-p.y)*256 < 180]
                shoulder = world_to_camera_view(scene, scene.camera,
                    rig.matrix_world @ rig.pose.bones['spine_03'].head).x*256
                outline.append({'frame': frame, 'left_edge_px': min(band),
                                'left_relative_to_chest_px': min(band)-shoulder})
                evaluated.to_mesh_clear()
            delta = np.linalg.norm(positions[-1]-positions[0], axis=1)
            relative_delta = np.linalg.norm(relative[-1]-relative[0], axis=1)
            edges = [row['left_relative_to_chest_px'] for row in outline]
            receipt['cloth'] = {'dense_frames': len(dense), 'outline': outline,
                'chest_relative_left_edge_range_px': max(edges)-min(edges),
                'endpoint_max_m': float(delta.max()), 'endpoint_p95_m': float(np.percentile(delta,95)),
                'endpoint_chest_relative_p95_m': float(np.percentile(relative_delta,95))}
        look.Graph = graph_for_sun(look.directions(scene)[1])
        look.apply_scene(scene, 'beauty')
        receipt['settings'] = preview_settings(scene, samples=16)
        look.apply_materials(scene, 'beauty', MASTER/'look', dict(look.LOOK))
        scene.render.dither_intensity = 0
        done = {}
        for i, frame in enumerate(frames):
            target = OUT/f'{label}-{i:02}.png'
            if frame in done:
                target.write_bytes(done[frame].read_bytes())
            else:
                render_still(scene, target, frame)
                done[frame] = target
        report[label] = receipt
        (OUT/'receipt.json').write_text(json.dumps(report, indent=2)+'\n')
    for clip in ('move','attack'):
        assert report[clip+'-before']['actions'] == report[clip+'-after']['actions']
    print('CLOAK_REVIEW_OK', flush=True)


def assemble():
    from PIL import Image, ImageDraw
    from kit.images import resize_rgba
    review = Path.home()/'LegatumRuns/anim-pilot/review/3d-v2'
    painting = Image.open('app/src/assets/units/spearman-256.png').convert('RGBA')
    for clip, count in [('move',8),('attack',10),('rest',1)]:
        if clip != 'rest' and not (OUT/f'{clip}-after-{count-1:02}.png').exists():
            continue
        for size in (256,160,64):
            sheet = Image.new('RGB', ((count+1)*(size+8), 30+2*(size+26)), '#f8f3e7')
            draw = ImageDraw.Draw(sheet)
            draw.text((5,5), f'R14b cloak only | Cycles CPU proxy, 16 samples, seed 17 | {size}px',fill='#30281f')
            for row, version in enumerate(('before','after')):
                y = 30+row*(size+26)
                for col in range(count+1):
                    if col == 0:
                        im = painting if size != 64 else Image.open('app/src/assets/units/spearman-64.png').convert('RGBA')
                    else:
                        p = OUT/(f'{clip}-{version}-{col-1:02}.png' if clip != 'rest' else 'rest-00.png')
                        im = Image.open(p).convert('RGBA')
                    im = resize_rgba(im, (size,size), space='display')
                    x = 4+col*(size+8)
                    sheet.paste(im,(x,y+22),im)
                    draw.text((x,y+3), 'Painting' if col == 0 else f'{"R13" if row == 0 else "R14b"} {col-1}',fill='#30281f')
            sheet.save(review/f'spearman-r14b-{clip}-{size}.png')
    # Animated A/B exposes loop and return timing without requiring GPU delivery.
    for clip,count,fps in [('move',8,6),('attack',10,14)]:
        if not (OUT/f'{clip}-after-{count-1:02}.png').exists():
            continue
        frames=[]
        for i in range(count):
            canvas=Image.new('RGB',(3*256,282),'#f8f3e7');draw=ImageDraw.Draw(canvas)
            for col,version in enumerate(('painting','before','after')):
                im=painting if col==0 else Image.open(OUT/f'{clip}-{version}-{i:02}.png').convert('RGBA')
                canvas.paste(im,(col*256,26),im)
                draw.text((col*256+6,6),['Painting','Round 13 CPU','R14b CPU'][col],fill='#30281f')
            frames.append(canvas)
        frames[0].save(review/f'spearman-r14b-{clip}.webp',save_all=True,append_images=frames[1:],duration=round(1000/fps),loop=0,lossless=True)
    (review/'spearman-r14b-cloth-metrics.json').write_bytes((OUT/'receipt.json').read_bytes())


if __name__ == '__main__':
    if '--bake' in sys.argv: bake()
    elif '--assemble' in sys.argv: assemble()
    else: render()
