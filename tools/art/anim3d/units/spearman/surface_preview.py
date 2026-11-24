"""Material-only CPU A/B; refuses any geometry, rig, camera or lighting change.

blender -b --disable-autoexec --python surface_preview.py -- BEFORE.blend OUT_DIR
Outputs raw images and an editable finished master; use surface_review.py for
one frozen histogram grade and native 256/64 px comparisons with the painting.
"""
import hashlib
import json
import os
from pathlib import Path
import sys

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'infantry'))
from surface_finish import apply


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def invariant(scene):
    """Track data owned by the other lanes, including all original UVs/weights."""
    objects = {}
    for ob in scene.objects:
        data = {'matrix': [list(row) for row in ob.matrix_world],
                'parent': ob.parent.name if ob.parent else None,
                'parent_bone': ob.parent_bone,
                'hidden': [ob.hide_render, ob.hide_viewport]}
        if ob.type == 'MESH':
            data['geometry'] = digest([[tuple(v.co), [(g.group, g.weight) for g in v.groups]] for v in ob.data.vertices])
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


before, output = [Path(p).resolve() for p in sys.argv[sys.argv.index('--')+1:]]
output.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(before))
scene = bpy.context.scene
assert scene.camera is not None
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = int(os.environ.get('SAMPLES', '24'))
scene.cycles.use_denoising = True
scene.cycles.use_adaptive_sampling = True
scene.cycles.adaptive_threshold = .025
scene.cycles.seed = 17
scene.render.resolution_x = scene.render.resolution_y = int(os.environ.get('RESOLUTION', '256'))
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'
scene.render.film_transparent = True
baseline = invariant(scene)
if os.environ.get('SKIP_BEFORE') != '1':
    scene.render.filepath = str(output/'before-raw.png')
    bpy.ops.render.render(write_still=True)
source = bpy.data.images.get('spearman-source.png')
assert source is not None
result = apply(scene, source)
assert invariant(scene) == baseline, 'Material pass modified another lane data'
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(output/'spearman-r9b.blend'))
scene.render.filepath = str(output/'after-raw.png')
bpy.ops.render.render(write_still=True)
report = {'baseline_sha256': hashlib.sha256(before.read_bytes()).hexdigest(),
          'candidate_sha256': hashlib.sha256((output/'spearman-r9b.blend').read_bytes()).hexdigest(),
          'engine': 'CYCLES', 'device': 'CPU', 'samples': scene.cycles.samples,
          'resolution': scene.render.resolution_x, 'invariants_before': baseline,
          'invariants_after': invariant(scene), 'finish': result}
(output/'surface-checks.json').write_text(json.dumps(report, indent=2)+'\n')
print('MATERIAL_PREVIEW', json.dumps(report))
