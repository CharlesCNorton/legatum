"""Painted Eevee look for the Spearman: render-time materials, lights and view.

Run through the Blender gate with the GPU backend (Shader to RGB is Eevee-only):

  blender-slot --factory-startup --disable-autoexec --python-exit-code 1 \
      --gpu-backend metal --python look.py -- BLEND OUT_DIR [options]

It opens a master or clip .blend read-only (nothing is saved), replaces every
material with one emission-only painted material per kit part, swaps the product
lights for one camera-space upper-left key, and renders at the saved camera.
Geometry, weights, UVs, cloth caches, actions and the camera are not touched.

Options: --mode beauty|id   --res N   --samples N   --frames rest|clip|i,j,k
         --orbit DEG (inspection camera turned about the vertical axis)
         --look DIR (part textures and palettes from look_textures.py)
         --set key=value (float overrides of LOOK defaults, for A/B tests)
"""
import json
import math
import os
import shutil
import sys
from pathlib import Path

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Matrix, Vector

PARTS = ['shield', 'helmet', 'crest', 'cuirass', 'greave_l', 'greave_r', 'cloak', 'tunic', 'skirt',
         'belt', 'sandal_l', 'sandal_r', 'skin', 'spear', 'base']
# Well separated sRGB codes; decoded by nearest colour in look_textures.py.
ID_COLOURS = {p: (40 + 70 * (i % 4), 40 + 70 * ((i // 4) % 4), 250 - 100 * (i % 3)) for i, p in enumerate(PARTS)}
PAINT_UV = 'Painting camera rest'
VISIBILITY = 'Painting visibility'

LOOK = {
    'sun_strength': 1.0,      # white diffuse facing the key renders 1.0
    'sun_angle': 12.0,        # degrees; soft painted shadow edge
    'paint_cast': .22,        # how far a live cast shadow darkens projected paint
    'paint_form': .0,         # live form shading on projected paint (0: painted light only)
    'fill_palette': .55,      # unseen surfaces: palette ramp vs local low-frequency paint
    'fill_cast': .45,         # live cast shadow depth on unseen surfaces
    'fill_light': .30,        # camera-right soft fill share of the ramp input
    'ao': .55,                # cavity share of the ramp input
    'stroke': .10,            # brush-patch offset of the ramp input
    'vis_lo': .25, 'vis_hi': .75,
    'base_cast': .30,         # contact shadow depth on the stone
    'shadow_r': .50, 'shadow_g': .36, 'shadow_b': .34,  # warm-dark shadow multiplier
}


def linear(c):
    return c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4


def lin3(rgb):
    return tuple(linear(v / 255) for v in rgb) + (1,)


def part_of(ob):
    name = ob.name.rstrip('.0123456789').lower()
    materials = ' '.join(m.name for m in ob.data.materials if m).lower()
    side = 'l' if name.endswith(' l') else 'r'
    if name.startswith('stationary cream stone'): return 'base'
    if ob.parent and ob.parent.name == 'Aspis control': return 'shield'
    if 'spear' in name or 'dory' in name: return 'spear'
    if 'horsehair' in name: return 'crest'
    if ob.parent_type == 'BONE' and ob.parent_bone == 'head': return 'helmet'
    if 'greave' in name: return 'greave_' + side
    if 'sandal' in name: return 'sandal_' + side
    if name.startswith(('cloak •', 'crimson collar')): return 'cloak'
    if 'tunic' in name: return 'tunic'
    if 'pteruges' in name: return 'skirt'
    if 'mpfb' in name: return 'skin'
    if 'leather' in materials: return 'belt'
    return 'cuirass'


def uv_of_world(scene, source_size):
    """Affine world -> painting UV, matching project.py's frozen calibration."""
    def uv(p):
        q = world_to_camera_view(scene, scene.camera, Vector(p))
        u = (349 + (q.x * 256 - 75) * 556 / 105) / source_size[0]
        v = 1 - (9 + ((1 - q.y) * 256 - 12) * 1236 / 232) / source_size[1]
        return Vector((u, v))
    o = uv((0, 0, 0))
    cols = [uv(e) - o for e in ((1, 0, 0), (0, 1, 0), (0, 0, 1))]
    return Matrix(((cols[0].x, cols[1].x, cols[2].x, o.x), (cols[0].y, cols[1].y, cols[2].y, o.y),
                   (0, 0, 0, 0), (0, 0, 0, 1)))


class Graph:
    def __init__(self, material):
        material.use_nodes = True
        self.tree = material.node_tree
        self.tree.nodes.clear()
        self.n, self.l = self.tree.nodes, self.tree.links

    def node(self, kind, **props):
        node = self.n.new(kind)
        for key, value in props.items():
            setattr(node, key, value)
        return node

    def math(self, op, a, b=None, c=None, clamp=False):
        node = self.node('ShaderNodeMath', operation=op, use_clamp=clamp)
        for socket, value in zip(node.inputs, (a, b, c)):
            if value is None: continue
            if isinstance(value, (int, float)): socket.default_value = value
            else: self.l.new(value, socket)
        return node.outputs[0]

    def mix(self, factor, a, b, blend='MIX'):
        node = self.node('ShaderNodeMix', data_type='RGBA', blend_type=blend, clamp_factor=True)
        for socket, value in ((node.inputs[0], factor), (node.inputs[6], a), (node.inputs[7], b)):
            if isinstance(value, (int, float)): socket.default_value = value
            elif isinstance(value, tuple): socket.default_value = value
            else: self.l.new(value, socket)
        return node.outputs[2]

    def dot(self, vector, constant):
        node = self.node('ShaderNodeVectorMath', operation='DOT_PRODUCT')
        self.l.new(vector, node.inputs[0])
        node.inputs[1].default_value = constant
        return node.outputs['Value']

    def image(self, path, vector, colourspace='sRGB', extension='EXTEND'):
        node = self.node('ShaderNodeTexImage', extension=extension, interpolation='Cubic')
        node.image = bpy.data.images.load(str(path), check_existing=True)
        node.image.colorspace_settings.name = colourspace
        self.l.new(vector, node.inputs['Vector'])
        return node

    def ramp(self, factor, stops, interpolation='EASE'):
        node = self.node('ShaderNodeValToRGB')
        ramp = node.color_ramp
        ramp.interpolation = interpolation
        while len(ramp.elements) < len(stops): ramp.elements.new(.5)
        for element, (position, colour) in zip(ramp.elements, stops):
            element.position, element.color = position, colour
        self.l.new(factor, node.inputs['Fac'])
        return node.outputs['Color']

    def lit(self, normal=None, constant_normal=None):
        """White diffuse -> Shader to RGB -> value: the key light's response."""
        diffuse = self.node('ShaderNodeBsdfDiffuse')
        diffuse.inputs['Color'].default_value = (1, 1, 1, 1)
        if constant_normal is not None: diffuse.inputs['Normal'].default_value = constant_normal
        elif normal is not None: self.l.new(normal, diffuse.inputs['Normal'])
        to_rgb = self.node('ShaderNodeShaderToRGB')
        self.l.new(diffuse.outputs[0], to_rgb.inputs[0])
        bw = self.node('ShaderNodeRGBToBW')
        self.l.new(to_rgb.outputs['Color'], bw.inputs[0])
        return bw.outputs[0]

    def emit(self, colour):
        emission = self.node('ShaderNodeEmission')
        self.l.new(colour, emission.inputs['Color'])
        output = self.node('ShaderNodeOutputMaterial')
        self.l.new(emission.outputs[0], output.inputs['Surface'])


def paint_uv(g, ob, uv_world, rest_matrices):
    if ob.type == 'MESH' and ob.data.uv_layers.get(PAINT_UV):
        return g.node('ShaderNodeUVMap', uv_map=PAINT_UV).outputs[0]
    # Rigid kit without frozen UVs (curves, the stone): the same rest projection
    # from object coordinates, so the paint still travels with the part.
    rest = Matrix(rest_matrices[ob.name]) if ob.name in rest_matrices else ob.matrix_world
    a = uv_world @ rest
    coords = g.node('ShaderNodeTexCoord').outputs['Object']
    combine = g.node('ShaderNodeCombineXYZ')
    for axis in range(2):
        g.l.new(g.math('ADD', g.dot(coords, tuple(a[axis][:3])), a[axis][3]), combine.inputs[axis])
    return combine.outputs[0]


def build_material(ob, part, look_dir, palettes, key_dir, fill_dir, uv_world, rest_matrices, cfg):
    has_uv = ob.type == 'MESH' and ob.data.uv_layers.get(PAINT_UV) is not None
    name = 'LOOK ' + part + ('' if has_uv else ' @ ' + ob.name)
    existing = bpy.data.materials.get(name)
    if existing: return existing
    material = bpy.data.materials.new(name)
    g = Graph(material)
    uv = paint_uv(g, ob, uv_world, rest_matrices)
    paint = g.image(look_dir / f'front-{part}.png', uv).outputs['Color']
    shadow_tint = (cfg['shadow_r'], cfg['shadow_g'], cfg['shadow_b'], 1)
    # Cast shadow alone: a diffuse whose normal is the key direction ignores form.
    cast = g.math('DIVIDE', g.lit(constant_normal=key_dir), cfg['sun_strength'], clamp=True)
    if part == 'base':
        depth = g.math('MULTIPLY', g.math('SUBTRACT', 1, cast), cfg['base_cast'])
        g.emit(g.mix(depth, paint, shadow_tint, 'MULTIPLY'))
        return material
    low = g.image(look_dir / f'low-{part}.png', uv).outputs['Color']
    # Brush patches in rest (generated) coordinates: they stay on the surface.
    coords = g.node('ShaderNodeTexCoord').outputs['Generated' if ob.type == 'MESH' else 'Object']
    mapping = g.node('ShaderNodeMapping')
    mapping.inputs['Scale'].default_value = (9, 9, 26)
    g.l.new(coords, mapping.inputs['Vector'])
    noise = g.node('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = 3
    noise.inputs['Detail'].default_value = 2
    g.l.new(mapping.outputs[0], noise.inputs['Vector'])
    stroke = g.math('MULTIPLY', g.math('SUBTRACT', noise.outputs['Factor'], .5), cfg['stroke'] * 2)
    geometry = g.node('ShaderNodeNewGeometry')
    key = g.math('DIVIDE', g.lit(), cfg['sun_strength'], clamp=True)
    fill = g.math('MULTIPLY_ADD', g.dot(geometry.outputs['Normal'], fill_dir), .5, .5)
    ao = g.node('ShaderNodeAmbientOcclusion', samples=8)
    ao.inputs['Distance'].default_value = .12
    cavity = g.math('ADD', g.math('MULTIPLY', ao.outputs['AO'], cfg['ao']), 1 - cfg['ao'])
    light = g.math('ADD', g.math('MULTIPLY', key, 1 - cfg['fill_light']), g.math('MULTIPLY', fill, cfg['fill_light']))
    t = g.math('ADD', g.math('MULTIPLY', light, cavity), stroke, clamp=True)
    palette = palettes[part]
    ramp = g.ramp(t, [(p, lin3(c)) for p, c in zip(palette['positions'], palette['colours'])])
    # Local paint keeps its hue; the ramp's value range lights it.
    gain = g.ramp(t, [(.08, (.42, .40, .44, 1)), (.45, (.82, .80, .80, 1)), (.85, (1.12, 1.10, 1.04, 1))])
    local = g.mix(1, low, gain, 'MULTIPLY')
    unseen = g.mix(cfg['fill_palette'], local, ramp)
    unseen = g.mix(g.math('MULTIPLY', g.math('SUBTRACT', 1, cast), cfg['fill_cast']), unseen, shadow_tint, 'MULTIPLY')
    seen = g.mix(g.math('MULTIPLY', g.math('SUBTRACT', 1, cast), cfg['paint_cast']), paint, shadow_tint, 'MULTIPLY')
    if cfg['paint_form'] > 0:
        seen = g.mix(g.math('MULTIPLY', g.math('SUBTRACT', 1, key), cfg['paint_form']), seen, shadow_tint, 'MULTIPLY')
    if ob.type == 'MESH' and ob.data.color_attributes.get(VISIBILITY):
        vis = g.node('ShaderNodeVertexColor', layer_name=VISIBILITY).outputs['Color']
        weight = g.node('ShaderNodeMapRange', interpolation_type='SMOOTHSTEP')
        bw = g.node('ShaderNodeRGBToBW')
        g.l.new(vis, bw.inputs[0])
        g.l.new(bw.outputs[0], weight.inputs['Value'])
        weight.inputs['From Min'].default_value, weight.inputs['From Max'].default_value = cfg['vis_lo'], cfg['vis_hi']
        g.emit(g.mix(weight.outputs[0], unseen, seen))
    else:
        # No stored visibility (curves): the camera-facing half carries the paint.
        facing = g.math('ABSOLUTE', g.dot(geometry.outputs['Normal'], tuple(cfg['_view'])))
        g.emit(g.mix(g.math('MULTIPLY', facing, 2.5, clamp=True), unseen, seen))
    return material


def id_material(part):
    material = bpy.data.materials.new('ID ' + part)
    g = Graph(material)
    rgb = g.node('ShaderNodeRGB')
    rgb.outputs[0].default_value = lin3(ID_COLOURS[part])
    g.emit(rgb.outputs[0])
    return material


def apply(scene, mode, look_dir, cfg):
    camera = scene.camera
    view = (camera.matrix_world.to_quaternion() @ Vector((0, 0, 1))).normalized()
    cfg['_view'] = view
    right = camera.matrix_world.to_quaternion() @ Vector((1, 0, 0))
    up = camera.matrix_world.to_quaternion() @ Vector((0, 1, 0))
    # Upper-left key in camera space (the painting's light), soft fill from the right.
    to_key = (-1.5 * right + 2.0 * up + 2.0 * view).normalized()
    fill_dir = (1.2 * right + .2 * up + 1.0 * view).normalized()
    rest_file = look_dir / 'rest-matrices.json'
    is_master = 'clips' not in Path(bpy.data.filepath).parts
    renderable = [o for o in scene.objects if o.type in ('MESH', 'CURVE') and o.data.materials]
    if is_master:
        look_dir.mkdir(parents=True, exist_ok=True)
        rest_file.write_text(json.dumps({o.name: [list(r) for r in o.matrix_world] for o in renderable
                                         if not (o.type == 'MESH' and o.data.uv_layers.get(PAINT_UV))}, indent=1))
    rest_matrices = json.loads(rest_file.read_text()) if rest_file.exists() else {}
    palettes = json.loads((look_dir / 'palettes.json').read_text()) if mode == 'beauty' else {}
    source_size = (1254, 1254)
    uv_world = uv_of_world(scene, source_size)
    ids = {}
    for ob in renderable:
        part = part_of(ob)
        if mode == 'id':
            material = ids.get(part) or ids.setdefault(part, id_material(part))
        else:
            material = build_material(ob, part, look_dir, palettes, tuple(to_key), tuple(fill_dir), uv_world, rest_matrices, cfg)
        for i in range(len(ob.data.materials)):
            ob.data.materials[i] = material
    for ob in scene.objects:
        if ob.type == 'LIGHT': ob.hide_render = True
    sun = bpy.data.lights.new('LOOK upper-left key', 'SUN')
    sun.energy, sun.angle = cfg['sun_strength'], math.radians(cfg['sun_angle'])
    sun_ob = bpy.data.objects.new(sun.name, sun)
    scene.collection.objects.link(sun_ob)
    sun_ob.rotation_euler = to_key.to_track_quat('Z', 'Y').to_euler()
    world = bpy.data.worlds.new('LOOK black world')
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0
    scene.world = world
    # The flat ID pass needs no lighting, so it can use a CPU slot; beauty is Eevee-only.
    scene.render.engine = 'CYCLES' if mode == 'id' else 'BLENDER_EEVEE'
    if mode == 'id':
        scene.cycles.device, scene.cycles.samples = 'CPU', 1
        scene.cycles.use_denoising = False
        scene.cycles.filter_width = .01
        scene.cycles.use_adaptive_sampling = False
    scene.render.film_transparent = True
    scene.view_settings.view_transform = 'Standard'
    scene.view_settings.look = 'None'
    scene.view_settings.exposure, scene.view_settings.gamma = 0, 1
    scene.display_settings.display_device = 'sRGB'
    scene.render.dither_intensity = 0
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.render.use_motion_blur = False


def main():
    args = sys.argv[sys.argv.index('--') + 1:]
    blend, out = Path(args[0]), Path(args[1])
    opts = {'mode': 'beauty', 'res': '512', 'samples': '64', 'frames': 'rest', 'orbit': '0', 'look': None, 'name': None}
    cfg = dict(LOOK)
    i = 2
    while i < len(args):
        key = args[i].lstrip('-')
        if key == 'set':
            k, v = args[i + 1].split('=')
            assert k in cfg, k
            cfg[k] = float(v)
        else:
            opts[key] = args[i + 1]
        i += 2
    bpy.ops.wm.open_mainfile(filepath=str(blend))
    scene = bpy.context.scene
    look_dir = Path(opts['look']) if opts['look'] else Path(os.environ['ANIM_ROOT']) / 'masters/spearman-3d-v2/look'
    apply(scene, opts['mode'], look_dir, cfg)
    scene.render.resolution_x = scene.render.resolution_y = int(opts['res'])
    scene.render.resolution_percentage = 100
    if opts['mode'] == 'id':
        scene.render.filter_size = .01
    else:
        scene.eevee.taa_render_samples = int(opts['samples'])
    orbit = float(opts['orbit'])
    if orbit:
        pivot = Matrix.Translation((0, 0, 0))
        scene.camera.matrix_world = pivot @ Matrix.Rotation(math.radians(orbit), 4, 'Z') @ pivot.inverted() @ scene.camera.matrix_world
    out.mkdir(parents=True, exist_ok=True)

    def render(path):
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)

    if opts['frames'] == 'rest':
        render(out / ((opts['name'] or ('id' if opts['mode'] == 'id' else 'rest')) + '.png'))
    else:
        samples = json.loads(scene['sample_frames'])
        wanted = range(len(samples)) if opts['frames'] == 'clip' else [int(v) for v in opts['frames'].split(',')]
        done = {}
        for index in wanted:
            frame, path = samples[index], out / f'{index:02}.png'
            if frame in done:
                shutil.copyfile(done[frame], path)  # held sample: identical bytes
                continue
            scene.frame_set(frame)
            render(path)
            done[frame] = path
    print('LOOK_READY', out)


if __name__ == '__main__':
    main()
