"""Same-settings CPU fold A/B on preserved round-10 rest and baked clips."""
import hashlib
import json
import os
import shutil
from pathlib import Path
import sys

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fold_paint import apply


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def invariant(scene):
    objects = {}
    for ob in scene.objects:
        data = {'matrix': [list(row) for row in ob.matrix_world], 'parent': ob.parent.name if ob.parent else None,
                'bone': ob.parent_bone, 'hidden': [ob.hide_render, ob.hide_viewport]}
        if ob.type == 'MESH':
            data['geometry'] = digest([[list(v.co), [(g.group, g.weight) for g in v.groups]] for v in ob.data.vertices])
            data['faces'] = digest([list(p.vertices) for p in ob.data.polygons])
            data['uv'] = digest({uv.name: [list(v.uv) for v in uv.data] for uv in ob.data.uv_layers})
        if ob.type == 'ARMATURE':
            data['pose'] = [[p.name, [list(row) for row in p.matrix_basis]] for p in ob.pose.bones]
        if ob.type == 'LIGHT':
            data['light'] = [ob.data.energy, list(ob.data.color), getattr(ob.data, 'size', None)]
        if ob.type == 'CAMERA':
            data['camera'] = [ob.data.type, ob.data.ortho_scale, ob.data.lens]
        objects[ob.name] = data
    actions = {}
    for action in bpy.data.actions:
        channels = []
        for layer in action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for curve in bag.fcurves:
                        channels.append([curve.data_path, curve.array_index,
                                         [[list(k.co), list(k.handle_left), list(k.handle_right), k.interpolation]
                                          for k in curve.keyframe_points]])
        actions[action.name] = channels
    return {'objects': digest(objects), 'actions': digest(actions)}


def main():
    root = Path(os.environ['ANIM_ROOT'])
    baseline = Path.home()/'LegatumRuns/anim-pilot/masters/spearman-3d-v2'
    output = root/'fold-ab'; output.mkdir(exist_ok=True)
    receipt = {'blender': bpy.app.version_string, 'device': 'CPU', 'engine': 'CYCLES', 'samples': 16,
               'resolution': 256, 'denoising': False, 'seed': 17,
               'fold_script_sha256': hashlib.sha256(Path(__file__).with_name('fold_paint.py').read_bytes()).hexdigest(),
               'painting_sha256': hashlib.sha256((baseline/'spearman-source.png').read_bytes()).hexdigest(), 'poses': {}}
    selection = os.environ.get('FOLD_POSES', 'rest,hit-1,death-8').split(',')
    after_only = os.environ.get('FOLD_AFTER_ONLY') == '1'
    if selection == ['all']:
        selection = [f'{clip}-{i}' for clip,count in [('idle',8),('move',8),('attack',10),('hit',4),('death',10)] for i in range(count)]
    if after_only and (output/'receipt.json').exists():
        receipt['poses'] = json.loads((output/'receipt.json').read_text())['poses']
    rendered = {}
    for pose in selection:
        clip, index = (pose.split('-') if '-' in pose else ('rest', None))
        rel = Path('spearman.blend') if clip == 'rest' else Path('clips')/clip/(clip+'.blend')
        path = baseline/rel
        bpy.ops.wm.open_mainfile(filepath=str(path))
        scene = bpy.context.scene
        frame = 1 if clip == 'rest' else json.loads(scene['sample_frames'])[int(index)]
        scene.frame_set(frame)
        scene.render.engine = 'CYCLES'; scene.cycles.device = 'CPU'; scene.cycles.samples = 16
        scene.cycles.use_denoising = False; scene.cycles.use_adaptive_sampling = False; scene.cycles.seed = 17
        scene.render.resolution_x = scene.render.resolution_y = 256; scene.render.resolution_percentage = 100
        scene.render.image_settings.file_format = 'PNG'; scene.render.image_settings.color_mode = 'RGBA'
        scene.render.film_transparent = True
        before = invariant(scene)
        if not after_only:
            scene.render.filepath = str(output/(pose+'-before.png')); bpy.ops.render.render(write_still=True)
        coverage = apply(scene)
        after = invariant(scene)
        assert before == after, 'Coverage changed geometry, UV, skinning, actions, camera or lights'
        target=output/(pose+'-after.png')
        key=(str(path),frame)
        if key in rendered:
            shutil.copyfile(rendered[key],target)
        else:
            scene.render.filepath=str(target);bpy.ops.render.render(write_still=True)
            rendered[key]=target
        receipt['poses'][pose] = {'frame': frame, 'baseline_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                                 'invariants_before': before, 'invariants_after': after, 'coverage': coverage,
                                 'camera_matrix': [list(r) for r in scene.camera.matrix_world], 'ortho_scale': scene.camera.data.ortho_scale,
                                 'view_transform': scene.view_settings.view_transform}
        if pose in {'rest','move-0'}:
            bpy.ops.file.pack_all()
            destination=root/'masters/spearman-3d-v2'/rel
            destination.parent.mkdir(parents=True,exist_ok=True)
            bpy.ops.wm.save_as_mainfile(filepath=str(destination))
        (output/'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
        print('FOLD_PREVIEW', pose, flush=True)


if __name__ == '__main__':
    main()
