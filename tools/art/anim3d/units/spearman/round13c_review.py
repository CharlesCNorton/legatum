"""Matched R12/R13c CPU proxy evidence. Lane ANIM_ROOT only; no shipped writes.

Blender: -- <label> <blend> [comma-separated delivered sample indices]
Python: --assemble. Final evidence must use baked clips, not diagnostics.
"""
import hashlib
import json
import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
ROOT = Path(os.environ['ANIM_ROOT'])
MASTER = ROOT/'masters/spearman-3d-v2'
OUT = ROOT/'preview'
REVIEW = Path.home()/'LegatumRuns/anim-pilot/review/3d-v2'
COUNTS = {'idle': 8, 'move': 8, 'attack': 10, 'hit': 4, 'death': 10}


def render():
    import bpy
    from bpy_extras.object_utils import world_to_camera_view
    from mathutils import Vector
    from kit.ab import preview_settings, render_still, invariant
    from kit.cpu_look import graph_for_sun
    from kit.contact import sole_points
    from kit.motion_metrics import sample, summarise
    from kit.audit import check_bounds_and_contact
    import look
    args = sys.argv[sys.argv.index('--')+1:]
    label, path = args[0], Path(args[1])
    bpy.ops.wm.open_mainfile(filepath=str(path))
    scene = bpy.context.scene
    if 'diagnostic' in path.name:
        for ob in scene.objects:
            for mod in ob.modifiers:
                if mod.type == 'CLOTH': mod.show_render = mod.show_viewport = False
    look.Graph = graph_for_sun(look.directions(scene)[1])
    look.apply_scene(scene, 'beauty')
    settings = preview_settings(scene, samples=8)
    look.apply_materials(scene, 'beauty', MASTER/'look', dict(look.LOOK, continuity=1, base_contact=.40))
    scene.render.dither_intensity = 0
    frames = json.loads(scene['sample_frames']) if label != 'rest' else [1]
    indices = ([] if args[2]=='metrics' else [int(v) for v in args[2].split(',')]) if len(args)>2 else list(range(len(frames)))
    folder = OUT/label; folder.mkdir(parents=True, exist_ok=True)
    receipt = {'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'settings': settings,
               'actions': invariant(scene)['actions'], 'frames': frames, 'cloth_baked': bool(scene.get('cloth_baked'))}
    rig = bpy.data.objects['Spearman • MPFB game_engine']
    if label != 'rest':
        rows, rotations, cloth = sample(scene, rig, frames,
            equipment={'shield': (bpy.data.objects['Aspis control'], 'lowerarm_l', 'tail')},
            cloth=bpy.data.objects['Cloak • simulated wool'])
        receipt['motion'] = summarise(rows, rotations, cloth)
        receipt['pose'] = []
        receipt['contact_findings'] = []
        base = bpy.data.objects['Stationary cream stone']
        radius = max(Vector((v.co.x, v.co.y)).length for v in base.data.vertices)
        inverse = base.matrix_world.inverted()
        for frame in frames:
            scene.frame_set(frame)
            findings, _ = check_bounds_and_contact(scene, base, f'{label}/{frame}')
            receipt['contact_findings'].extend(findings)
            def point(name): return rig.matrix_world @ rig.pose.bones[name].head
            def screen(name):
                v = world_to_camera_view(scene, scene.camera, point(name))
                return [256*v.x, 256*(1-v.y)]
            joints = ['pelvis','spine_01','spine_02','spine_03','neck_01','head','thigh_l','thigh_r','calf_l','calf_r','foot_l','foot_r']
            joints = [n for n in joints if n in rig.pose.bones]
            body = bpy.data.objects.get('MPFB anatomical body')
            body = body or next(ob for ob in scene.objects if ob.name.startswith('MPFB anatomical'))
            ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); mesh = ev.to_mesh()
            vertices = [inverse @ (body.matrix_world @ v.co) for v in mesh.vertices]
            on_disc = sum(v.x*v.x+v.y*v.y <= radius*radius for v in vertices)/len(vertices)
            ev.to_mesh_clear()
            receipt['pose'].append({'frame':frame, 'body_vertices_over_disc_fraction':on_disc,
                'joints': {n:list(point(n)) for n in joints}, 'head_px':screen('head'),
                'ankle_separation_px':abs(screen('foot_l')[0]-screen('foot_r')[0]),
                'sole_min_z':{s:min(v.z for v in sole_points(s)) for s in ('l','r')}})
    done = {}
    for i in indices:
        target = folder/f'{i:02}.png'; frame=frames[i]
        if frame in done: target.write_bytes(done[frame].read_bytes())
        else: render_still(scene, target, frame); done[frame]=target
    (folder/'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print('R13C_PREVIEW', label, flush=True)


def assemble():
    from PIL import Image, ImageDraw
    from kit.images import resize_rgba
    painting = Image.open('app/src/assets/units/spearman-256.png').convert('RGBA')
    for clip in ('move','death','rest'):
        count = COUNTS.get(clip,1)
        for size in (256,160,64):
            sheet = Image.new('RGB', ((count+1)*(size+8), 24+2*(size+28)), '#f8f3e7')
            draw = ImageDraw.Draw(sheet)
            title = f'CPU 8spp | {size}px' if clip=='rest' else f'Cycles CPU proxy | 8 samples seed 17 | {size}px | same R12 master/look | no live cast shadow'
            draw.text((4,4),title, fill='#30281f')
            for row,version in enumerate(('before','after')):
                y=24+row*(size+28)
                for col in range(count+1):
                    path = OUT/('rest' if clip=='rest' else clip+'-'+version)/f'{col-1:02}.png'
                    im = painting if col==0 else Image.open(path if clip!='rest' else OUT/'rest/00.png').convert('RGBA')
                    if col==0 and size==64: im=Image.open('app/src/assets/units/spearman-64.png').convert('RGBA')
                    im=resize_rgba(im,(size,size),space='display')
                    x=4+col*(size+8); sheet.paste(im,(x,y+24),im)
                    draw.text((x,y+5),'Painting' if col==0 else f'{"R12" if row==0 else "R13c"} {col-1}',fill='#30281f')
            sheet.save(REVIEW/f'spearman-r13c-{clip}-{size}.png')
    for clip in ('move','death'):
        frames=[]
        for i in range(COUNTS[clip]):
            canvas=Image.new('RGB',(480,184),'#f8f3e7'); draw=ImageDraw.Draw(canvas)
            for j,(label,im) in enumerate([('Painting',painting),('R12',Image.open(OUT/f'{clip}-before/{i:02}.png').convert('RGBA')),('R13c',Image.open(OUT/f'{clip}-after/{i:02}.png').convert('RGBA'))]):
                small=resize_rgba(im,(160,160),space='display');canvas.paste(small,(160*j,24),small);draw.text((160*j+4,4),label,fill='#30281f')
            frames.append(canvas)
        frames[0].save(REVIEW/f'spearman-r13c-{clip}.webp',save_all=True,append_images=frames[1:],duration=167 if clip=='move' else 250,loop=0,quality=85)
    ending = Image.new('RGB', (768,580), '#f8f3e7')
    draw = ImageDraw.Draw(ending)
    for col, (label, im) in enumerate([('Painting',painting),
            ('R12 ending',Image.open(OUT/'death-before/09.png').convert('RGBA')),
            ('R13c ending',Image.open(OUT/'death-after/09.png').convert('RGBA'))]):
        draw.text((col*256+8,8), label+(' | CPU proxy' if col else ''), fill='#30281f')
        for size,y in ((256,28),(160,310),(64,498)):
            small = Image.open('app/src/assets/units/spearman-64.png').convert('RGBA') if col==0 and size==64 else resize_rgba(im,(size,size),space='display')
            ending.paste(small,(col*256+(256-size)//2,y),small)
    ending.save(REVIEW/'spearman-r13c-death-ending.png')
    receipts={name:json.loads((OUT/name/'receipt.json').read_text()) for name in ('rest','move-before','move-after','death-before','death-after')}
    (REVIEW/'spearman-r13c-motion-metrics.json').write_text(json.dumps(receipts,indent=2)+'\n')


if __name__=='__main__':
    assemble() if '--assemble' in sys.argv else render()
