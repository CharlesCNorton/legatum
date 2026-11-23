#!/usr/bin/env python3
"""Blender 5.3/Eevee living painting. Run with blender -b -P ... -- --masters ... --out ... ."""
import os
for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
    os.environ[key] = '6'
import argparse
import json
import math
from pathlib import Path
import shutil
import sys
import bpy
import numpy as np

FRAMES = 168
SETTLE = 145
CAMERA_Z = 8.0
HEIGHT = 2.0
WIDTH = HEIGHT * 16 / 9
RELIEF = 0.38
DOLLY = 0.09
DRIFT = (0.026, 0.008)


def smoother(t):
    t = max(0.0, min(1.0, t))
    return t * t * t * (t * (t * 6 - 15) + 10)


def timing(frame):
    """Position and motion-clock both have zero first/second derivatives at the hold."""
    t = (frame - 1) / (SETTLE - 1)
    progress = smoother(t)
    seconds = (frame - 1) / 24
    # Integrate velocity 1-smoothstep over the last moving second (5..6s).
    q = max(0.0, min(1.0, seconds - 5))
    clock = min(seconds, 5) + q - (q**6 - 3 * q**5 + 2.5 * q**4)
    return progress, clock


def node(nodes, kind, name):
    n = nodes.new(kind)
    n.label = n.name = name
    return n


def material(masters, background=False):
    mat = bpy.data.materials.new('Repaired distant paint' if background else 'Living oil paint')
    mat.use_nodes = True
    mat.surface_render_method = 'DITHERED'
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    nodes.clear()
    def connect(value, socket):
        if isinstance(value, (float, int, tuple)):
            socket.default_value = value
        else:
            links.new(value, socket)
    def math_node(op, a, b=0):
        n = node(nodes, 'ShaderNodeMath', op)
        n.operation = op
        connect(a, n.inputs[0]); connect(b, n.inputs[1])
        return n.outputs[0]
    def texture(filename, uv, data=False):
        n = node(nodes, 'ShaderNodeTexImage', filename)
        n.image = bpy.data.images.load(str(masters / filename), check_existing=True)
        if data:
            n.image.colorspace_settings.name = 'Non-Color'
        n.interpolation = 'Linear'
        n.extension = 'EXTEND'
        links.new(uv, n.inputs['Vector'])
        return n.outputs['Color']
    uv = node(nodes, 'ShaderNodeTexCoord', 'Painting coordinates').outputs['UV']
    clock = node(nodes, 'ShaderNodeValue', 'Motion clock (settles at frame 145)')
    for frame in range(1, FRAMES + 1):
        clock.outputs[0].default_value = timing(frame)[1]
        clock.outputs[0].keyframe_insert('default_value', frame=frame)
    water = texture('mask-water.png', uv, True)
    sky = texture('mask-sky.png', uv, True)
    depth = texture('depth-smooth16.png', uv, True)
    components = node(nodes, 'ShaderNodeSeparateXYZ', 'UV components')
    links.new(uv, components.inputs[0])
    x, y = components.outputs['X'], components.outputs['Y']
    # Subpixel ripple in the original paint, not a synthetic water surface.
    wave = math_node('SINE', math_node('ADD', math_node('MULTIPLY', y, 480),
                                     math_node('MULTIPLY', clock.outputs[0], 0.95)))
    wave2 = math_node('SINE', math_node('ADD', math_node('MULTIPLY', x, 130),
                                      math_node('MULTIPLY', clock.outputs[0], -0.65)))
    offset = node(nodes, 'ShaderNodeCombineXYZ', 'Water UV ripple < 0.6 pixel')
    links.new(math_node('MULTIPLY', math_node('MULTIPLY', wave, water), 0.00027), offset.inputs['X'])
    links.new(math_node('MULTIPLY', math_node('MULTIPLY', wave2, water), 0.00013), offset.inputs['Y'])
    add = node(nodes, 'ShaderNodeVectorMath', 'Ripple coordinates')
    add.operation = 'ADD'
    links.new(uv, add.inputs[0]); links.new(offset.outputs[0], add.inputs[1])
    color = texture('background.png' if background else 'painting.png', add.outputs['Vector'])
    # Atmospheric glaze: broad noise, depth weighted; preserve painted contrast and grain.
    noise = node(nodes, 'ShaderNodeTexNoise', 'Slow atmospheric glaze')
    noise.noise_dimensions = '4D'
    noise.inputs['Scale'].default_value = 4.0
    noise.inputs['Detail'].default_value = 1.0
    links.new(uv, noise.inputs['Vector'])
    links.new(math_node('MULTIPLY', clock.outputs[0], 0.035), noise.inputs['W'])
    far = math_node('SUBTRACT', 1, depth)
    haze = math_node('MULTIPLY', math_node('MULTIPLY', noise.outputs['Fac'], far), 0.018)
    # Soft oblique sunlight bands, very low contrast, strongest in distant air.
    ray_phase = math_node('ADD', math_node('MULTIPLY', x, 32), math_node('MULTIPLY', y, 12))
    ray_phase = math_node('ADD', ray_phase, math_node('MULTIPLY', clock.outputs[0], 0.045))
    ray = math_node('POWER', math_node('MAXIMUM', math_node('SINE', ray_phase), 0), 8)
    ray = math_node('MULTIPLY', math_node('MULTIPLY', ray, far), 0.008)
    glaze = node(nodes, 'ShaderNodeMixRGB', 'Warm ivory atmospheric glaze')
    links.new(math_node('ADD', haze, ray), glaze.inputs[0])
    links.new(color, glaze.inputs[1])
    glaze.inputs[2].default_value = (0.80, 0.72, 0.56, 1)
    sky_glaze = node(nodes, 'ShaderNodeMixRGB', 'Sky drift')
    links.new(math_node('MULTIPLY', math_node('MULTIPLY', sky, noise.outputs['Fac']), 0.008), sky_glaze.inputs[0])
    links.new(glaze.outputs[0], sky_glaze.inputs[1])
    sky_glaze.inputs[2].default_value = (0.63, 0.70, 0.76, 1)
    emission = node(nodes, 'ShaderNodeEmission', 'Unlit painted surface (no CG highlights)')
    links.new(sky_glaze.outputs[0], emission.inputs['Color'])
    emission.inputs['Strength'].default_value = 1
    output = node(nodes, 'ShaderNodeOutputMaterial', 'Surface')
    if background:
        links.new(emission.outputs[0], output.inputs['Surface'])
    else:
        attr = node(nodes, 'ShaderNodeAttribute', 'Stretch opacity')
        attr.attribute_name = 'stretch_opacity'
        transparent = node(nodes, 'ShaderNodeBsdfTransparent', 'Repair reveal')
        mix = node(nodes, 'ShaderNodeMixShader', 'Hide stretched depth triangles')
        reveal = node(nodes, 'ShaderNodeValue', 'Repair reveal weight')
        for frame in range(1, FRAMES + 1):
            reveal.outputs[0].default_value = timing(frame)[0]
            reveal.outputs[0].keyframe_insert('default_value', frame=frame)
        opacity = math_node('SUBTRACT', 1, math_node('MULTIPLY',
                            math_node('SUBTRACT', 1, attr.outputs['Fac']), reveal.outputs[0]))
        links.new(opacity, mix.inputs[0])
        links.new(transparent.outputs[0], mix.inputs[1])
        links.new(emission.outputs[0], mix.inputs[2])
        links.new(mix.outputs[0], output.inputs['Surface'])
    # Arrange the graph so it remains inspectable in the saved .blend.
    for i, n in enumerate(nodes):
        n.location = ((i % 9) * 235, -(i // 9) * 250)
    return mat


def mesh_object(name, vertices, faces, uv, mat):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    mesh.materials.append(mat)
    layer = mesh.uv_layers.new(name='Painting UV')
    indices = np.empty(len(mesh.loops), dtype=np.int32)
    mesh.loops.foreach_get('vertex_index', indices)
    layer.data.foreach_set('uv', np.asarray(uv, np.float32)[indices].ravel())
    return obj


def relief(masters):
    with np.load(masters / 'relief.npz') as data:
        depth, cloth = data['depth'], data['cloth']
    rows, cols = depth.shape
    u, v = np.meshgrid(np.linspace(0, 1, cols), np.linspace(1, 0, rows))
    z = depth * RELIEF
    # Camera-projected geometry: every texel lines up at the initial viewpoint,
    # including the hidden background. Naive planar displacement bulges the image.
    xyz = np.stack(((u - 0.5) * WIDTH * (CAMERA_Z - z) / CAMERA_Z,
                    (v - 0.5) * HEIGHT * (CAMERA_Z - z) / CAMERA_Z, z), axis=-1).reshape(-1, 3)
    uv = np.stack((u, v), axis=-1).reshape(-1, 2)
    a = (np.arange(rows - 1)[:, None] * cols + np.arange(cols - 1)[None, :]).ravel()
    faces = np.concatenate((np.stack((a, a + cols, a + 1), axis=1),
                            np.stack((a + 1, a + cols, a + cols + 1), axis=1)))
    obj = mesh_object('Continuous painted relief', xyz.tolist(), faces.tolist(), uv, material(masters))
    # Measure projected stretching along the actual camera move, after removing
    # ordinary zoom. A steep 3D slope alone is harmless at the starting viewpoint;
    # fading it would erase perfectly good brushwork. Catch folded triangles too.
    start_xy = xyz[:, :2] / (CAMERA_Z - xyz[:, 2, None])
    end_z = CAMERA_Z * (1 - DOLLY)
    end_xy = (xyz[:, :2] - DRIFT) / (end_z - xyz[:, 2, None])
    stretch = np.ones(len(faces), np.float32)
    for left, right in ((0, 1), (1, 2), (2, 0)):
        initial = start_xy[faces[:, left]] - start_xy[faces[:, right]]
        final = end_xy[faces[:, left]] - end_xy[faces[:, right]]
        ratio = np.linalg.norm(final, axis=1) / np.maximum(np.linalg.norm(initial, axis=1), 1e-8)
        ratio *= 1 - DOLLY
        stretch = np.maximum(stretch, ratio)
    t = np.clip((stretch - 1.15) / 0.40, 0, 1)
    face_alpha = 1 - t * t * (3 - 2 * t)
    edge_a = end_xy[faces[:, 1]] - end_xy[faces[:, 0]]
    edge_b = end_xy[faces[:, 2]] - end_xy[faces[:, 0]]
    face_alpha[edge_a[:, 0] * edge_b[:, 1] - edge_a[:, 1] * edge_b[:, 0] <= 0] = 0
    alpha = np.zeros(len(xyz), np.float32)
    count = np.zeros(len(xyz), np.float32)
    for corner in range(3):
        np.add.at(alpha, faces[:, corner], face_alpha)
        np.add.at(count, faces[:, corner], 1)
    alpha /= np.maximum(count, 1)
    attr = obj.data.attributes.new('stretch_opacity', 'FLOAT', 'POINT')
    attr.data.foreach_set('value', alpha)
    obj.shape_key_add(name='Basis')
    # Two local deformation modes, no separate sail objects. Motion stays below 0.8px.
    for index, phase in enumerate((0.0, 1.7)):
        key = obj.shape_key_add(name=f'Painted cloth breath {index + 1}')
        displaced = xyz.copy()
        strength = cloth.ravel() * np.sin(u.ravel() * 110 + v.ravel() * 39 + phase)
        displaced[:, 0] += strength * 0.00065
        displaced[:, 2] += strength * 0.0008
        key.data.foreach_set('co', displaced.astype(np.float32).ravel())
        key.slider_min = -1
        for frame in range(1, FRAMES + 1):
            key.value = math.sin(timing(frame)[1] * 1.1 + phase) * 0.65
            key.keyframe_insert('value', frame=frame)
    # One continuous underpainting, behind every relief vertex, with matching projection.
    back_z = -0.045
    scale = (CAMERA_Z - back_z) / CAMERA_Z
    vertices = [(x * WIDTH * scale, y * HEIGHT * scale, back_z)
                for x, y in [(-0.5, -0.5), (0.5, -0.5), (0.5, 0.5), (-0.5, 0.5)]]
    mesh_object('Hidden inpainted underpainting', vertices, [(0, 1, 2, 3)],
                [(0, 0), (1, 0), (1, 1), (0, 1)], material(masters, True))
    return {'vertices': len(xyz), 'triangles': len(faces),
            'faded_vertices_percent': float(np.mean(alpha < 0.95) * 100),
            'fully_faded_vertices_percent': float(np.mean(alpha < 0.05) * 100)}


def birds():
    # Three tiny tapered, curved umber strokes. No flock particles or hard black silhouettes.
    mat = bpy.data.materials.new('Distant painted umber')
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    out = nodes.new('ShaderNodeOutputMaterial')
    emit = nodes.new('ShaderNodeEmission')
    emit.inputs['Color'].default_value = (0.18, 0.17, 0.15, 1)
    mat.node_tree.links.new(emit.outputs[0], out.inputs[0])
    for index, (u, v) in enumerate(((0.40, 0.89), (0.425, 0.875), (0.446, 0.90))):
        curve = bpy.data.curves.new(f'Bird stroke {index + 1}', 'CURVE')
        curve.dimensions = '3D'
        curve.resolution_u = 8
        curve.bevel_depth = 0.00038
        curve.bevel_resolution = 1
        spline = curve.splines.new('BEZIER')
        spline.bezier_points.add(4)
        for p, co, radius in zip(spline.bezier_points,
                [(-0.004, 0.001, 0), (-0.002, 0.0014, 0), (0, 0, 0), (0.002, 0.0014, 0), (0.004, 0.001, 0)],
                [0.12, 0.65, 0.9, 0.65, 0.12]):
            p.co, p.radius = co, radius
            p.handle_left_type = p.handle_right_type = 'AUTO'
        obj = bpy.data.objects.new(curve.name, curve)
        bpy.context.collection.objects.link(obj)
        curve.materials.append(mat)
        for frame in range(1, FRAMES + 1):
            t = timing(frame)[1]
            obj.location = ((u - 0.5) * WIDTH + t * 0.0045, (v - 0.5) * HEIGHT + t * 0.0008, 0.025)
            obj.rotation_euler[2] = 0.06 * math.sin(t * 0.6 + index)
            obj.keyframe_insert('location', frame=frame)
            obj.keyframe_insert('rotation_euler', frame=frame)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--masters', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--frames', default='1-168', help='Inclusive global frame range, e.g. 1-12 or 145-168')
    parser.add_argument('--preview', action='store_true', help='960x540 / 16 samples (same mesh and timing)')
    parser.add_argument('--dry-run', action='store_true', help='Build, validate and save scene.blend; never render')
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
    try:
        start, end = map(int, args.frames.split('-'))
        if not 1 <= start <= end <= FRAMES:
            raise ValueError
    except ValueError:
        parser.error('--frames must be an inclusive range within 1-168')
    args.start, args.end = start, end
    args.masters = args.masters.resolve()
    args.out = args.out.resolve()
    for name in ('relief.npz', 'painting.png', 'background.png', 'depth-smooth16.png',
                 'mask-water.png', 'mask-sky.png', 'mask-cloth.png'):
        if not (args.masters / name).is_file():
            parser.error(f'Missing {args.masters / name}; run depth.py then plates.py')
    return args


def validate_hold(scene):
    """Read evaluated Blender values, including shaders and shape keys; no rendering."""
    def snapshot(frame):
        scene.frame_set(frame)
        state = []
        for obj in scene.objects:
            state.extend(value for row in obj.matrix_world for value in row)
            if obj.type == 'MESH' and obj.data.shape_keys:
                state.extend(key.value for key in obj.data.shape_keys.key_blocks)
        for mat in bpy.data.materials:
            if mat.use_nodes:
                state.extend(n.outputs[0].default_value for n in mat.node_tree.nodes if n.type == 'VALUE')
        return np.array(state)
    held = snapshot(SETTLE)
    assert np.array_equal(held, snapshot(FRAMES)), 'Animation does not settle completely'
    assert not np.array_equal(snapshot(1), held), 'Animation is unexpectedly static'


def main():
    args = parse_args()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    engines = scene.render.bl_rna.properties['engine'].enum_items.keys()
    scene.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in engines else 'BLENDER_EEVEE'
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = 6
    scene.render.resolution_x = 960 if args.preview else 1920
    scene.render.resolution_y = 540 if args.preview else 1080
    scene.render.resolution_percentage = 100
    scene.render.fps = 24
    scene.render.fps_base = 1
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGB'
    scene.render.image_settings.color_depth = '8'
    scene.render.image_settings.compression = 15
    scene.render.film_transparent = False
    scene.render.use_file_extension = True
    scene.render.use_compositing = False
    scene.render.use_sequencer = False
    if hasattr(scene, 'eevee'):
        scene.eevee.taa_render_samples = 16 if args.preview else 64
        if hasattr(scene.eevee, 'use_raytracing'):
            scene.eevee.use_raytracing = False
    # Standard + unlit emission retains the source's pigments. No AgX contrast/sharpening.
    scene.view_settings.view_transform = 'Standard'
    scene.view_settings.look = 'None'
    scene.view_settings.exposure = 0
    scene.view_settings.gamma = 1
    scene.world = bpy.data.worlds.new('Warm dark surround')
    scene.world.color = (0.05, 0.04, 0.03)
    stats = relief(args.masters)
    birds()
    camera_data = bpy.data.cameras.new('Painting camera')
    camera = bpy.data.objects.new('Painting camera', camera_data)
    bpy.context.collection.objects.link(camera)
    scene.camera = camera
    camera_data.type = 'PERSP'
    camera_data.sensor_fit = 'HORIZONTAL'
    camera_data.sensor_width = 36
    camera_data.lens = 36 * CAMERA_Z / WIDTH * 1.015  # 1.5% crop protects the image boundary.
    camera_data.clip_start, camera_data.clip_end = 0.01, 100
    camera_data.dof.use_dof = False
    for frame in range(1, FRAMES + 1):
        p, _ = timing(frame)
        camera.location = (DRIFT[0] * p, DRIFT[1] * p, CAMERA_Z * (1 - DOLLY * p))
        camera.keyframe_insert('location', frame=frame)
    # All keys sampled per frame; their final values are identical throughout 145..168.
    scene.frame_start, scene.frame_end = args.start, args.end
    args.out.mkdir(parents=True, exist_ok=True)
    scene.render.filepath = str(args.out / 'frame_')
    validate_hold(scene)
    scene.frame_set(args.start)
    scene['era_video'] = 'Classical: 168 frames at 24 fps; hold 145-168; no text'
    stats.update({'frames': [args.start, args.end], 'preview': args.preview,
                  'resolution': [scene.render.resolution_x, scene.render.resolution_y],
                  'engine': scene.render.engine, 'hold_frames': [SETTLE, FRAMES],
                  'relief_depth': RELIEF, 'camera_dolly_fraction': DOLLY, 'threads': 6,
                  'hold_state_verified': True,
                  'samples': scene.eevee.taa_render_samples})
    # Pack textures: scene.blend remains usable if transferred with the frames directory.
    bpy.ops.file.pack_all()
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(args.masters / 'scene.blend'))
    (args.masters / 'scene-report.json').write_text(json.dumps(stats, indent=2) + '\n')
    print(json.dumps(stats, indent=2), flush=True)
    if not args.dry_run:
        # Render the moving span normally; copy the final hold so alpha-dither
        # sampling cannot introduce even tiny temporal changes during the hold.
        moving_end = min(args.end, SETTLE)
        if args.start <= moving_end:
            scene.frame_end = moving_end
            bpy.ops.render.render(animation=True)
        if args.end >= SETTLE:
            hold_source = args.out / f'frame_{max(args.start, SETTLE):04d}.png'
            if args.start > SETTLE:
                scene.frame_set(SETTLE)
                scene.render.filepath = str(hold_source)
                bpy.ops.render.render(write_still=True)
            for frame in range(max(args.start, SETTLE) + 1, args.end + 1):
                shutil.copyfile(hold_source, args.out / f'frame_{frame:04d}.png')
    else:
        print('DRY RUN: scene built and saved; no renderer invoked.', flush=True)


if __name__ == '__main__':
    main()
