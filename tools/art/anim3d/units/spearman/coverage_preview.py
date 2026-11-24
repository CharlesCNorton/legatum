"""Same-settings CPU coverage A/B on preserved round-9 rest and baked clips."""
import hashlib
import json
import os
from pathlib import Path
import sys

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from coverage import apply


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
    baseline = Path.home()/'LegatumRuns/anim-pilot/lanes/spearman-r9-merge/masters/spearman-3d-v2'
    output = root/'coverage-ab'; output.mkdir(exist_ok=True)
    receipt = {'blender': bpy.app.version_string, 'device': 'CPU', 'engine': 'CYCLES', 'samples': 16,
               'resolution': 256, 'denoising': False, 'seed': 17,
               'coverage_script_sha256': hashlib.sha256(Path(__file__).with_name('coverage.py').read_bytes()).hexdigest(),
               'painting_sha256': hashlib.sha256((baseline/'spearman-source.png').read_bytes()).hexdigest(), 'poses': {}}
    selection = os.environ.get('COVERAGE_POSES', 'rest,hit-1,hit-2,death-2,death-3,death-8').split(',')
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
        scene.render.filepath = str(output/(pose+'-before.png')); bpy.ops.render.render(write_still=True)
        mat = scene.objects['Linen tunic shoulder sleeves'].data.materials[0]
        source = next(n.image for n in mat.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image and n.image.name.startswith('spearman-source'))
        coverage = apply(scene, source)
        after = invariant(scene)
        assert before == after, 'Coverage changed geometry, UV, skinning, actions, camera or lights'
        scene.render.filepath = str(output/(pose+'-after.png')); bpy.ops.render.render(write_still=True)
        receipt['poses'][pose] = {'frame': frame, 'baseline_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                                 'invariants_before': before, 'invariants_after': after, 'coverage': coverage,
                                 'camera_matrix': [list(r) for r in scene.camera.matrix_world], 'ortho_scale': scene.camera.data.ortho_scale,
                                 'view_transform': scene.view_settings.view_transform}
        if pose in {'rest', 'hit-1', 'death-2'}:
            bpy.ops.file.pack_all()
            bpy.ops.wm.save_as_mainfile(filepath=str(root/'masters/spearman-3d-v2'/rel))
        (output/'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
        print('COVERAGE_PREVIEW', pose, flush=True)


if __name__ == '__main__':
    main()
