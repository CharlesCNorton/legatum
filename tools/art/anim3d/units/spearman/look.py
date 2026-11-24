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

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))  # unit-local modules (continuity.py) under blender --python
import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Matrix, Vector

PARTS = ['shield', 'helmet', 'crest', 'cuirass', 'greave_l', 'greave_r', 'cloak', 'tunic', 'skirt',
         'belt', 'sandal_l', 'sandal_r', 'skin', 'spear', 'base', 'rim']
# Well separated sRGB codes; decoded by nearest colour in look_textures.py.
ID_COLOURS = {p: (40 + 70 * (i % 4), 40 + 70 * ((i // 4) % 4), 250 - 100 * (i % 3)) for i, p in enumerate(PARTS)}
# Thin or fibrous parts whose stored visibility is mostly grazing: always painted.
ALWAYS_PAINT = ('crest', 'spear')
LOCAL_FIRST = ('tunic', 'skirt', 'belt')
PAINT_UV = 'Painting camera rest'
VISIBILITY = 'Painting visibility'

LOOK = {
    'sun_strength': 3.14159,  # Eevee: white diffuse facing a sun of strength pi returns 1.0
    'sun_angle': 24.0,        # degrees; soft painted shadow edge
    'paint_cast': .22,        # how far a live cast shadow darkens projected paint
    'paint_form': .0,         # live form shading on projected paint (0: painted light only)
    'fill_palette': .75,      # unseen surfaces: palette ramp vs local low-frequency paint
    'fill_cast': .30,         # live cast shadow depth on unseen surfaces
    'fill_light': .30,        # camera-right soft fill share of the ramp input
    'ao': .55,                # cavity share of the ramp input
    'stroke': .10,            # brush-patch offset of the ramp input
    'vis_lo': .08, 'vis_hi': .45,
    'base_cast': .16,         # cast shadow depth on the stone
    'base_contact': .40,     # soft contact (AO) shadow depth under the feet
    'contact_reach': .07,     # metres; move profile overrides this to 25 mm
    'ground_shadow': 1.0,     # painted warm shadow on the stone top behind and between the feet
    'ground_back': .24,       # metres behind each evaluated sole (away from camera) ...
    'ground_in': .10,         # ... and toward the other foot
    'ground_depth': .18,      # falloff away from the camera, metres
    'ground_width': .26,      # falloff across the view, metres
    'ground_r': .53, 'ground_g': .38, 'ground_b': .24,  # linear multiplier at full depth (painting, x 114-144 / y 212-214)
    'sandal_r': .90, 'sandal_g': .84, 'sandal_b': .76,  # leather tone multiplier (linear) on sandals and the strapped foot
    'side_drop': .06,         # side band: value lost from the lip down to the foot of the disc
    'side_foot': .18,         # extra darkening of the lowest tenth of the side band (the painted ground line)
    'stone_grain': .08,
    'stone_radius': .594,     # metres, for the near-to-far tone of the top
    'shadow_r': .50, 'shadow_g': .36, 'shadow_b': .34,  # warm-dark shadow multiplier
    'debug': 0,               # 1 paint weight, 2 unseen layer only, 3 projected paint only
    'ground_pools': 0,      # opt-in rest pools: reviewer request, metric regression
    'foot_roll': 1,          # shade registered foot pigment at toe-off; 0 for R14 A/B
    'ground_follow': 1,      # evaluated sole centers, refreshed at every render
    'continuity': 1,          # frozen sole/lining/rear-shoulder pigment; 0 for A/B
}


def linear(c):
    return c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4


def lin3(rgb):
    return tuple(linear(v / 255) for v in rgb) + (1,)


def parts_of(ob):
    """One kit part per material slot (cached before the materials are replaced)."""
    if 'look_parts' not in ob:
        part = classify(ob)
        ob['look_parts'] = ','.join('rim' if part == 'base' and m and 'rim' in m.name.lower() else part
                                    for m in ob.data.materials)
    return ob['look_parts'].split(',')


def classify(ob):
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


from kit.look import Graph


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


def stone(g, colours, cast, shadow_tint, key_dir, cfg):
    """Cream disc shaded from the painting's own stone colours.

    The disc is not projected: the 3D stone is larger than the painted one, and
    painted feet and shadows must not stay behind when the real feet move. Top,
    beveled edge and side are told apart by the object-space normal.
    """
    coords = g.node('ShaderNodeTexCoord')
    up = g.node('ShaderNodeSeparateXYZ')
    g.l.new(coords.outputs['Normal'], up.inputs[0])
    height = g.node('ShaderNodeSeparateXYZ')
    g.l.new(coords.outputs['Generated'], height.inputs[0])

    def step(value, lo, hi):
        node = g.node('ShaderNodeMapRange', interpolation_type='SMOOTHSTEP')
        g.l.new(value, node.inputs['Value'])
        node.inputs['From Min'].default_value, node.inputs['From Max'].default_value = lo, hi
        return node.outputs[0]

    geometry = g.node('ShaderNodeNewGeometry')
    view, left = Vector(cfg['_view']), Vector(cfg['_left'])
    # Painted side: full value facing the viewer, darker round the flanks and
    # darker still on the flank away from the upper-left key.
    facing = g.math('ADD', g.math('MULTIPLY_ADD', g.dot(geometry.outputs['Normal'], tuple(view)), .20, .80),
                    g.math('MULTIPLY', g.dot(geometry.outputs['Normal'], tuple(left)), .07))
    side = g.mix(step(height.outputs['Z'], .15, .85), lin3(colours['lower']), lin3(colours['upper']))
    side = g.mix(1, side, facing, 'MULTIPLY')
    # Painted side band: a little darker toward the table and a dark line where it meets it.
    down = g.math('SUBTRACT', 1, g.math('MULTIPLY', g.math('SUBTRACT', 1, step(height.outputs['Z'], .0, .80)), cfg['side_drop']))
    foot = g.math('SUBTRACT', 1, g.math('MULTIPLY', g.math('SUBTRACT', 1, step(height.outputs['Z'], .02, .14)), cfg['side_foot']))
    side = g.mix(1, side, g.math('MULTIPLY', down, foot), 'MULTIPLY')
    # Painted top: palest at the near edge, deeper cream toward the back.
    toward = Vector((view.x, view.y, 0)).normalized()
    near = g.math('MULTIPLY_ADD', g.dot(coords.outputs['Object'], tuple(toward)), .5 / cfg['stone_radius'], .5, clamp=True)
    top = g.mix(g.math('POWER', near, 2.0), lin3(colours['top']), lin3(colours['top_light']))
    colour = g.mix(step(up.outputs['Z'], .12, .55), side, lin3(colours['edge']))
    colour = g.mix(step(up.outputs['Z'], .80, .97), colour, top)
    # Limestone mottle: fine grain over broader, fainter blotches.
    grain = None
    for scale, amount in ((240, cfg['stone_grain']), (38, cfg['stone_grain'] * .8)):
        noise = g.node('ShaderNodeTexNoise')
        noise.inputs['Scale'].default_value = scale
        noise.inputs['Detail'].default_value = 3
        g.l.new(coords.outputs['Object'], noise.inputs['Vector'])
        layer = g.math('MULTIPLY_ADD', noise.outputs['Factor'], amount, 1 - amount / 2)
        grain = layer if grain is None else g.math('MULTIPLY', grain, layer)
    colour = g.mix(1, colour, grain, 'MULTIPLY')
    # The painting grounds the figure with one soft warm shadow on the top,
    # behind the heels and across the gap between the feet. It is no light's
    # cast shadow (the key throws those elsewhere), so it is drawn from the
    # ankles: one blob per foot, offset back and inward, fading as a foot lifts.
    if cfg['ground_shadow'] > 0 and cfg.get('_ankles'):
        back = Vector((-view.x, -view.y, 0)).normalized()
        across = -Vector((left.x, left.y, 0)).normalized()
        ground = None
        for side, marker in cfg['_ankles'].items():
            at = g.node('ShaderNodeTexCoord')
            at.object = marker
            rel = at.outputs['Object']
            inward = 1 if side == 'r' else -1
            d = g.math('MULTIPLY_ADD', g.dot(rel, tuple(back)), 1 / cfg['ground_depth'], -cfg['ground_back'] / cfg['ground_depth'])
            w = g.math('MULTIPLY_ADD', g.dot(rel, tuple(across)), 1 / cfg['ground_width'], -inward * cfg['ground_in'] / cfg['ground_width'])
            blob = g.math('EXPONENT', g.math('MULTIPLY', g.math('ADD', g.math('MULTIPLY', d, d), g.math('MULTIPLY', w, w)), -1))
            drop = g.node('ShaderNodeSeparateXYZ')
            g.l.new(rel, drop.inputs[0])
            blob = g.math('MULTIPLY', blob, step(drop.outputs['Z'], -.10, -.025) if cfg['ground_follow'] == 2 else step(drop.outputs['Z'], -.30, -.12))
            ground = blob if ground is None else g.math('ADD', ground, blob)
        shade = g.math('MULTIPLY', g.math('MULTIPLY', ground, cfg['ground_shadow'], clamp=True), step(up.outputs['Z'], .80, .97))
        colour = g.mix(shade, colour, (cfg['ground_r'], cfg['ground_g'], cfg['ground_b'], 1), 'MULTIPLY')
    ao = g.node('ShaderNodeAmbientOcclusion', samples=16)
    ao.inputs['Distance'].default_value = cfg['contact_reach']
    contact = g.math('MULTIPLY', g.math('SUBTRACT', 1, ao.outputs['AO']), cfg['base_contact'])
    depth = g.math('ADD', contact, g.math('MULTIPLY', g.math('SUBTRACT', 1, cast), cfg['base_cast']), clamp=True)
    # The painted stone's own shadow colour, as a linear multiplier of its lit top.
    tint = tuple(max(linear(s / 255) / linear(t / 255), .05) for s, t in zip(colours['shadow'], colours['top'])) + (1,)
    g.emit(g.mix(depth, colour, tint, 'MULTIPLY'))


def build_material(ob, part, look_dir, palettes, key_dir, fill_dir, uv_world, rest_matrices, cfg):
    has_uv = ob.type == 'MESH' and ob.data.uv_layers.get(PAINT_UV) is not None
    name = 'LOOK ' + part + ('' if has_uv else ' @ ' + ob.name)
    existing = bpy.data.materials.get(name)
    if existing: return existing
    material = bpy.data.materials.new(name)
    g = Graph(material)
    shadow_tint = (cfg['shadow_r'], cfg['shadow_g'], cfg['shadow_b'], 1)
    # Cast shadow alone: a diffuse whose normal is the key direction ignores form.
    cast = g.math('DIVIDE', g.lit(constant_normal=key_dir), cfg['sun_strength'] / math.pi, clamp=True)
    if part in ('base', 'rim'):
        stone(g, palettes['stone'], cast, shadow_tint, key_dir, cfg)
        return material
    uv = paint_uv(g, ob, uv_world, rest_matrices)
    paint = g.image(look_dir / f'front-{part}.png', uv).outputs['Color']
    low = g.image(look_dir / f'low-{part}.png', uv).outputs['Color']
    # Brush patches in rest (generated) coordinates: they stay on the surface.
    coords = g.node('ShaderNodeTexCoord').outputs['Generated' if ob.type == 'MESH' else 'Object']
    mapping = g.node('ShaderNodeMapping')
    mapping.inputs['Scale'].default_value = (22, 22, 5)  # strokes run along the part's length
    g.l.new(coords, mapping.inputs['Vector'])
    noise = g.node('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = 3
    noise.inputs['Detail'].default_value = 2
    g.l.new(mapping.outputs[0], noise.inputs['Vector'])
    stroke = g.math('MULTIPLY', g.math('SUBTRACT', noise.outputs['Factor'], .5), cfg['stroke'] * 2)
    geometry = g.node('ShaderNodeNewGeometry')
    key = g.math('DIVIDE', g.lit(), cfg['sun_strength'] / math.pi, clamp=True)
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
    # Layers under other painted layers continue their own inpainted paint (the
    # tunic turns cloak-red toward the collar); the rest use the smooth local colour.
    local = g.mix(1, paint if part in LOCAL_FIRST else low, gain, 'MULTIPLY')
    # Torso layers sit under other painted layers (the tunic under the cloak
    # collar): their unseen surface follows local paint more than their own ramp.
    unseen = g.mix(cfg['fill_palette'] * (.3 if part in LOCAL_FIRST else 1), local, ramp)
    if part == 'tunic':
        # The painted cloak lies over both shoulders of the tunic mesh. Where the
        # tunic's own continued paint is red, its unseen surface is cloak, lit
        # with the cloak's ramp; where it is pale it stays linen.
        rgb = g.node('ShaderNodeSeparateColor')
        g.l.new(paint, rgb.inputs[0])
        redness = g.math('DIVIDE', g.math('SUBTRACT', rgb.outputs[0], rgb.outputs[1]), g.math('MAXIMUM', rgb.outputs[0], .02))
        is_cloak = g.node('ShaderNodeMapRange', interpolation_type='SMOOTHSTEP')
        g.l.new(redness, is_cloak.inputs['Value'])
        is_cloak.inputs['From Min'].default_value, is_cloak.inputs['From Max'].default_value = .30, .55
        cloak = palettes['cloak']
        unseen = g.mix(is_cloak.outputs[0], unseen, g.ramp(t, [(p, lin3(c)) for p, c in zip(cloak['positions'], cloak['colours'])]))
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
        lo, hi = (-1, -.5) if part in ALWAYS_PAINT else (cfg['vis_lo'], cfg['vis_hi'])
        weight.inputs['From Min'].default_value, weight.inputs['From Max'].default_value = lo, hi
        final = g.mix(weight.outputs[0], unseen, seen)
        if cfg.get('continuity', 1):
            from continuity import pigment
            final = pigment(g, part, final, g.math('SUBTRACT', 1, weight.outputs[0]), t, lin3, palettes)
        tone = (cfg['sandal_r'], cfg['sandal_g'], cfg['sandal_b'], 1)
        if part.startswith('sandal'):
            final = g.mix(1, final, tone, 'MULTIPLY')
        elif part == 'skin' and cfg.get('continuity', 1) and tone != (1, 1, 1, 1):
            # The strapped foot reads as part of the sandal: same tone, by the frozen foot mask.
            from continuity import ATTRIBUTE
            final = g.mix(g.node('ShaderNodeVertexColor', layer_name=ATTRIBUTE).outputs['Alpha'], final, tone, 'MULTIPLY')
        if cfg.get('foot_roll', 1) and (part.startswith('sandal') or part == 'skin'):
            from foot_finish import pigment as foot_pigment
            final = foot_pigment(g, final)
        if cfg['debug'] == 1: final = g.mix(weight.outputs[0], (0, 0, 0, 1), (1, 1, 1, 1))
        if cfg['debug'] == 2: final = unseen
        if cfg['debug'] == 3: final = seen
        if cfg['debug'] in (4, 5, 6, 7):
            value = {4: key, 5: cast, 6: t, 7: cavity}[int(cfg['debug'])]
            final = g.mix(value, (0, 0, 0, 1), (1, 1, 1, 1))
        g.emit(final)
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


def directions(scene):
    camera = scene.camera
    q = camera.matrix_world.to_quaternion()
    view, right, up = q @ Vector((0, 0, 1)), q @ Vector((1, 0, 0)), q @ Vector((0, 1, 0))
    # Upper-left key in camera space (the painting's light), soft fill from the right.
    return view.normalized(), (-1.5 * right + 2.0 * up + 2.0 * view).normalized(), (1.2 * right + .2 * up + 1.0 * view).normalized()


def ankle_markers(scene, follow_sole=True):
    """World-aligned shader coordinates refreshed from evaluated soles before rendering.

    Render-time only, like the materials: nothing is saved."""
    rig = bpy.data.objects.get('Spearman • MPFB game_engine')
    markers = {}
    for side in 'lr':
        name = 'LOOK ankle ' + side
        marker = bpy.data.objects.get(name)
        if marker is None:
            marker = bpy.data.objects.new(name, None)
            scene.collection.objects.link(marker)
        marker.constraints.clear()
        marker['evaluated_sole'] = int(follow_sole)
        if not follow_sole:
            follow = marker.constraints.new('COPY_LOCATION')
            follow.target, follow.subtarget = rig, 'foot_' + side
        markers[side] = marker
    return markers


def apply_materials(scene, mode, look_dir, cfg):
    """(Re)build the look materials; safe to call again with other settings."""
    from foot_finish import settings
    settings(scene, cfg)
    for material in [m for m in bpy.data.materials if m.name.startswith(('LOOK ', 'ID '))]:
        bpy.data.materials.remove(material)
    view, to_key, fill_dir = directions(scene)
    cfg['_view'] = view
    cfg['_left'] = -(scene.camera.matrix_world.to_quaternion() @ Vector((1, 0, 0)))
    cfg['_ankles'] = ankle_markers(scene, cfg.get('ground_follow', 1)) if mode == 'beauty' else None
    rest_file = look_dir / 'rest-matrices.json'
    is_master = 'clips' not in Path(bpy.data.filepath).parts
    renderable = [o for o in scene.objects if o.type in ('MESH', 'CURVE') and len(o.data.materials)]
    if mode == 'beauty' and cfg.get('continuity', 1):
        from continuity import prepare
        prepare(scene, classify)
    if mode == 'beauty' and cfg.get('foot_roll', 1):
        from foot_finish import prepare as prepare_feet
        prepare_feet(scene, classify)
    if is_master and mode == 'id':
        look_dir.mkdir(parents=True, exist_ok=True)
        rest_file.write_text(json.dumps({o.name: [list(r) for r in o.matrix_world] for o in renderable
                                         if not (o.type == 'MESH' and o.data.uv_layers.get(PAINT_UV))}, indent=1))
    rest_matrices = json.loads(rest_file.read_text()) if rest_file.exists() else {}
    palettes = json.loads((look_dir / 'palettes.json').read_text()) if mode == 'beauty' else {}
    uv_world = uv_of_world(scene, (1254, 1254))
    ids = {}
    for ob in renderable:
        for i, part in enumerate(parts_of(ob)):
            if mode == 'id':
                material = ids.get(part) or ids.setdefault(part, id_material(part))
            else:
                material = build_material(ob, part, look_dir, palettes, tuple(to_key), tuple(fill_dir), uv_world, rest_matrices, cfg)
            ob.data.materials[i] = material
    sun = bpy.data.objects['LOOK upper-left key']
    sun.data.energy, sun.data.angle = cfg['sun_strength'], math.radians(cfg['sun_angle'])


def apply_scene(scene, mode):
    view, to_key, fill_dir = directions(scene)
    for ob in scene.objects:
        if ob.type == 'LIGHT': ob.hide_render = True
    sun = bpy.data.lights.new('LOOK upper-left key', 'SUN')
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


def configure_render(scene, mode='beauty', resolution=512, samples=64):
    """Single render setup used by the look CLI and the delivery renderer."""
    apply_scene(scene, 'id' if mode == 'id' else 'beauty')
    scene.render.resolution_x = scene.render.resolution_y = int(resolution)
    scene.render.resolution_percentage = 100
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = 3
    if mode == 'id':
        scene.render.filter_size = .01
    elif mode == 'proxy':
        from kit.cpu_look import graph_for_sun
        from kit.ab import preview_settings
        global Graph
        Graph = graph_for_sun(directions(scene)[1])
        preview_settings(scene, resolution=int(resolution), samples=int(samples))
    else:
        scene.eevee.taa_render_samples = int(samples)


def render_frame(scene, path, frame=None):
    """Both entry points render through this function; no second light/grade path."""
    if frame is not None:
        scene.frame_set(frame)
    from foot_finish import update
    update(scene)
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def main():
    args = sys.argv[sys.argv.index('--') + 1:]
    blend, out = Path(args[0]), Path(args[1])
    opts = {'mode': 'beauty', 'res': '1280', 'samples': '64', 'frames': 'rest', 'orbit': '0', 'look': None,
            'name': None, 'variants': None}
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
    orbit = float(opts['orbit'])
    configure_render(scene, opts['mode'], int(opts['res']), int(opts['samples']))
    out.mkdir(parents=True, exist_ok=True)

    def render(path):
        render_frame(scene, path)

    # "a:key=v,key=v;b:key=v" renders several settings in one Blender session
    # (one wait for the GPU lock). Without it, one variant named by --name.
    variants = [(opts['name'] or ('id' if opts['mode'] == 'id' else 'rest'), {})]
    if opts['variants']:
        variants = [(v.split(':')[0], dict(kv.split('=') for kv in v.split(':')[1].split(',') if kv)) for v in opts['variants'].split(';')]
    rest_camera = scene.camera.matrix_world.copy()
    for name, overrides in variants:
        settings = dict(cfg)
        turn = orbit
        for key, value in overrides.items():
            if key == 'orbit': turn = float(value); continue
            assert key in settings, key
            settings[key] = float(value)
        # Materials are built at the rest camera (the paint projection's frame).
        scene.camera.matrix_world = rest_camera
        bpy.context.view_layer.update()
        apply_materials(scene, 'id' if opts['mode'] == 'id' else 'beauty', look_dir, settings)
        if turn:
            scene.camera.matrix_world = Matrix.Rotation(math.radians(turn), 4, 'Z') @ rest_camera
        if opts['frames'] == 'rest':
            render(out / (name + '.png'))
            continue
        target = out / name if opts['variants'] else out
        target.mkdir(parents=True, exist_ok=True)
        samples = json.loads(scene['sample_frames'])
        wanted = range(len(samples)) if opts['frames'] == 'clip' else [int(v) for v in opts['frames'].split(',')]
        done = {}
        for index in wanted:
            frame, path = samples[index], target / f'{index:02}.png'
            if frame in done:
                shutil.copyfile(done[frame], path)  # held sample: identical bytes
                continue
            scene.frame_set(frame)
            render(path)
            done[frame] = path
    print('LOOK_READY', out)


if __name__ == '__main__':
    main()
