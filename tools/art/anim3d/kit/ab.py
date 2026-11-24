"""Same-settings A/B rendering inside Blender: fixed preview settings, scene
invariants, clay override and material-ID render.

Extracted from the Spearman round-10 lane scripts (coverage_preview.py,
identify.py, render.py). Run through the `blender` gate. Nothing here saves
the .blend; callers decide what to keep.

Why each piece exists:
- `preview_settings`: every A/B pair must share engine, size, samples and seed.
- `invariant`: prove a material-only or motion-only change left everything
  else byte-identical (round 10 lanes a and b reported exactly this).
- `material_id_render`: find WHICH surface a pale patch belongs to before
  repainting (round 10b: it was the sleeve, not the cape).
"""
import hashlib
import json

import bpy


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def preview_settings(scene, resolution=256, samples=16, seed=17, denoise=False):
    """Cycles CPU preview for A/B pairs. Returns the receipt to store with them.

    Round-10 A/Bs used 256 px, 16 samples, seed 17, no denoising or adaptive
    sampling, so pixel differences come from the change under test. Production
    stage renders (render.py) keep denoising and adaptive sampling on; do not
    compare a preview against one of those.
    """
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = samples
    scene.cycles.use_denoising = denoise
    scene.cycles.use_adaptive_sampling = False
    scene.cycles.seed = seed
    scene.render.resolution_x = scene.render.resolution_y = resolution
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.render.film_transparent = True
    return {'blender': bpy.app.version_string, 'engine': 'CYCLES', 'device': 'CPU',
            'resolution': resolution, 'samples': samples, 'seed': seed, 'denoising': denoise,
            'camera_matrix': [list(r) for r in scene.camera.matrix_world],
            'ortho_scale': scene.camera.data.ortho_scale,
            'view_transform': scene.view_settings.view_transform}


def render_still(scene, path, frame=None):
    if frame is not None:
        scene.frame_set(frame)
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def invariant(scene, materials=False):
    """Hashes of everything an isolated change must not touch.

    Objects: world matrix, parent, visibility, mesh vertices with weights,
    faces, all UV layers, armature pose, light and camera settings. Actions:
    every keyframe. Compare before and after; assert equality for whichever
    parts the change claims to preserve. Set `materials=True` to also hash
    material slot names (leave False for a material-only change).
    """
    objects = {}
    for ob in scene.objects:
        data = {'matrix': [list(row) for row in ob.matrix_world],
                'parent': ob.parent.name if ob.parent else None,
                'bone': ob.parent_bone, 'hidden': [ob.hide_render, ob.hide_viewport]}
        if ob.type == 'MESH':
            data['geometry'] = digest([[list(v.co), [(g.group, g.weight) for g in v.groups]]
                                       for v in ob.data.vertices])
            data['faces'] = digest([list(p.vertices) for p in ob.data.polygons])
            data['uv'] = digest({uv.name: [list(v.uv) for v in uv.data] for uv in ob.data.uv_layers})
            if materials:
                data['materials'] = [m.name if m else None for m in ob.data.materials]
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


def clay_override(scene, colour=(.42, .36, .26, 1), roughness=.8):
    """Plain clay on every surface, for silhouette and relief review."""
    clay = bpy.data.materials.new('Geometry review clay')
    clay.use_nodes = True
    bsdf = clay.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Base Color'].default_value = colour
    bsdf.inputs['Roughness'].default_value = roughness
    scene.view_layers[0].material_override = clay
    return clay


def material_id_render(scene, colours, path, frame=None, other=(.1, .1, .1, 1), resolution=256):
    """Render flat emission colours per object to identify a surface.

    `colours` maps object names to RGBA, e.g. {'Cloak': (1,0,0,1), 'Body':
    (0,1,0,1), 'Sleeves': (0,0,1,1)}; every other mesh gets `other`.
    DESTRUCTIVE to materials in the open scene: run on a scratch session and do
    not save the file afterwards.
    """
    missing = [name for name in colours if name not in scene.objects]
    assert not missing, f'Unknown objects: {missing}'
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 1
    scene.cycles.use_denoising = False
    scene.render.resolution_x = scene.render.resolution_y = resolution
    scene.render.resolution_percentage = 100
    for ob in scene.objects:
        if ob.type != 'MESH':
            continue
        flat = bpy.data.materials.new('ID '+ob.name)
        flat.use_nodes = True
        nodes = flat.node_tree.nodes
        nodes.clear()
        emission = nodes.new('ShaderNodeEmission')
        emission.inputs[0].default_value = colours.get(ob.name, other)
        output = nodes.new('ShaderNodeOutputMaterial')
        flat.node_tree.links.new(emission.outputs[0], output.inputs[0])
        ob.data.materials.clear()
        ob.data.materials.append(flat)
    render_still(scene, path, frame)
