"""Full-depth costume fitting before frozen projection; no opacity geometry masks."""
import math
import bpy
from mathutils import Matrix, Vector
from bpy_extras.object_utils import world_to_camera_view


def skin_in_pose(ob, rig, weights):
    """Bind finished geometry without moving its current posed surface."""
    world = [ob.matrix_world @ v.co for v in ob.data.vertices]
    ob.parent = rig
    ob.parent_type = 'OBJECT'
    ob.matrix_parent_inverse = Matrix.Identity(4)
    ob.matrix_basis = Matrix.Identity(4)
    ob.vertex_groups.clear()
    groups = {name: ob.vertex_groups.new(name=name) for name in weights[0]}
    transforms = {name: rig.pose.bones[name].matrix @ rig.data.bones[name].matrix_local.inverted()
                  for name in groups}
    for vertex, point, influence in zip(ob.data.vertices, world, weights):
        blend = Matrix([[sum(influence[name] * transforms[name][r][c] for name in groups)
                         for c in range(4)] for r in range(4)])
        vertex.co = blend.inverted() @ rig.matrix_world.inverted() @ point
        for name, weight in influence.items():
            groups[name].add([vertex.index], weight, 'REPLACE')
    mod = ob.modifiers.new('Continuous costume skin', 'ARMATURE')
    mod.object = rig
    ob['pose_bound_costume'] = True
    bpy.context.view_layer.update()


def finish(sc, rig):
    # Lower the back neck edge into the wrapped shoulder mantle. Displace all
    # shape keys equally so its rest thickness and subsequent folds survive.
    up = sc.camera.matrix_world.to_quaternion() @ Vector((0, 1, 0))
    pixel = sc.camera.data.ortho_scale / 256
    for name, drop in [('Full mantle back', 8), ('Purple shoulder mantle', 3)]:
        ob = bpy.data.objects[name]
        inv = ob.matrix_world.inverted()
        for key in ob.data.shape_keys.key_blocks:
            for vertex in key.data:
                world = ob.matrix_world @ vertex.co
                y = (1 - world_to_camera_view(sc, sc.camera, world).y) * 256
                amount = max(0, min(1, (85 - y) / 30)) ** 2
                vertex.co = inv @ (world - up * drop * pixel * amount)

    # Fit the hair-cap crown to the reference contour in camera space while
    # retaining every vertex's depth. This changes the solid model, never alpha.
    image = next(im for im in bpy.data.images if 'painting-aligned' in im.name)
    width, height = image.size
    pixels = list(image.pixels[:])
    def top_at(x):
        xx = round(x * width / 256)
        if not 101 <= x <= 136:
            return None
        for y in range(round(18 * height / 256), round(43 * height / 256)):
            if pixels[4 * ((height - 1 - y) * width + xx) + 3] > .85:
                return y * 256 / height
        return None
    for ob in sc.objects:
        if not ob.name.startswith(('Sculpted hair cap', 'Sculpted chestnut curl')):
            continue
        inv = ob.matrix_world.inverted()
        for vertex in ob.data.vertices:
            world = ob.matrix_world @ vertex.co
            q = world_to_camera_view(sc, sc.camera, world)
            x, y = q.x * 256, (1 - q.y) * 256
            boundary = top_at(x)
            if boundary is not None and y < boundary + .4:
                world -= up * (boundary + .4 - y) * pixel
            vertex.co = inv @ world

    # Dark woven breeches cover the anatomical thighs revealed by the fall.
    # Keep the same weighted anatomy; assign fabric only to leg-dominant faces.
    body = bpy.data.objects['Heir MPFB anatomy']
    fabric = body.data.materials[0].copy()
    fabric.name = 'Painted dark woven breeches'
    nodes, links = fabric.node_tree.nodes, fabric.node_tree.links
    shader = nodes.get('Principled BSDF')
    shader.inputs['Roughness'].default_value = .92
    shader.inputs['Sheen Weight'].default_value = .18
    pigment = shader.inputs['Base Color'].links[0].from_node
    tex = nodes.new('ShaderNodeTexImage')
    tex.image = next(im for im in bpy.data.images if im.name.startswith('fill-linen'))
    tex.projection = 'BOX'
    tex.projection_blend = .3
    coord = nodes.new('ShaderNodeTexCoord')
    links.new(coord.outputs['Generated'], tex.inputs['Vector'])
    tint = nodes.new('ShaderNodeMixRGB')
    tint.blend_type = 'MULTIPLY'
    tint.inputs[0].default_value = 1
    tint.inputs[2].default_value = (.075, .060, .045, 1)
    links.new(tex.outputs['Color'], tint.inputs[1])
    links.new(tint.outputs[0], pigment.inputs[1])
    body.data.materials.append(fabric)
    leg_groups = {g.index for g in body.vertex_groups
                  if g.name.startswith(('thigh_', 'calf_'))}
    covered = {v.index for v in body.data.vertices
               if sum(g.weight for g in v.groups if g.group in leg_groups) > .55}
    for poly in body.data.polygons:
        if all(i in covered for i in poly.vertices):
            poly.material_index = len(body.data.materials) - 1

    # The shaft used to follow only the calf, opening a gap whenever the foot
    # pitched. Blend a real overlapping leather ankle between calf and foot.
    for side in ['l', 'r']:
        ob = bpy.data.objects['Tall leather boot ' + side]
        weights = []
        for vertex in ob.data.vertices:
            world = ob.matrix_world @ vertex.co
            t = max(0, min(1, (.37 - world.z) / .16))
            t = t * t * (3 - 2 * t)
            weights.append({'calf_' + side: 1 - t, 'foot_' + side: t})
        skin_in_pose(ob, rig, weights)

    # A tunic follows the upper legs instead of remaining a rigid cylinder
    # through a backwards fall. Armour keeps a smaller, stiffer influence.
    for ob in list(sc.objects):
        if ob.name not in {'Lamellar skirt', 'Ivory hem'} and not (
                ob.name.startswith('Rounded lamella relief') and ob.parent_bone == 'pelvis'):
            continue
        worlds = [ob.matrix_world @ v.co for v in ob.data.vertices]
        centre = sum(worlds, Vector()) / len(worlds)
        rigid_plate = ob.name.startswith('Rounded lamella relief')
        weights = []
        for world in worlds:
            point = centre if rigid_plate else world
            t = max(0, min(1, (1.22 - point.z) / .48))
            t *= .65 if ob.name == 'Ivory hem' else .32
            left = max(0, min(1, (point.x + .12) / .24))
            weights.append({'pelvis': 1 - t, 'thigh_l': t * left, 'thigh_r': t * (1 - left)})
        skin_in_pose(ob, rig, weights)

    # Macro-scale limestone mottling under fine grain, with a softly worn rim.
    stone = bpy.data.objects['Stationary cream stone'].data.materials[0]
    nodes, links = stone.node_tree.nodes, stone.node_tree.links
    grain = next(n for n in nodes if n.type == 'TEX_NOISE')
    pores = nodes.new('ShaderNodeTexNoise')
    pores.name = 'Limestone mineral clouds'
    pores.inputs['Scale'].default_value = 11
    pores.inputs['Detail'].default_value = 4
    mix = nodes.new('ShaderNodeMixRGB')
    mix.blend_type = 'MULTIPLY'
    mix.inputs[0].default_value = .35
    links.new(grain.outputs['Fac'], mix.inputs[1])
    links.new(pores.outputs['Fac'], mix.inputs[2])
    return mix.outputs[0]
