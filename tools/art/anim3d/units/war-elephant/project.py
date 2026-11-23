"""Fit full-depth surfaces, then freeze camera pigment on the finished mesh.

Repeatable from sculpt-input.blend. Never moves UVs during animation and never
uses source alpha to remove geometry. Original skin weights and rigs survive.
"""
import json
import math
import os
from pathlib import Path

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(os.environ['ANIM_ROOT'])
M = ROOT / 'masters/war-elephant'
bpy.ops.wm.open_mainfile(filepath=str(M / 'sculpt-input.blend'))
sc = bpy.context.scene
cam = sc.camera
base = bpy.data.objects['GEO-Stationary cream stone base']


def pixel(world):
    q = world_to_camera_view(sc, cam, world)
    return Vector((q.x * 256, (1 - q.y) * 256))


def skin_matrices(ob):
    mod = next((m for m in ob.modifiers if m.type == 'ARMATURE'), None)
    if not mod:
        return None
    rig = mod.object
    to_rig = rig.matrix_world.inverted() @ ob.matrix_world
    return {b.name: to_rig.inverted() @ b.matrix @ b.bone.matrix_local.inverted() @ to_rig
            for b in rig.pose.bones}


def skin_for(ob, vertex, transforms):
    if transforms is None:
        return Matrix.Identity(4)
    weights = [(transforms[ob.vertex_groups[g.group].name], g.weight)
               for g in vertex.groups if ob.vertex_groups[g.group].name in transforms]
    total = sum(w for _, w in weights)
    if total < .00001:
        return Matrix.Identity(4)
    return sum((m * (w / total) for m, w in weights), Matrix(((0.,) * 4,) * 4))


# Macro keys must be baked before mesh fitting. Finish geometry without baking
# skeletal deformation; apply skinning to the same finished vertex topology.
for ob in list(sc.objects):
    if ob.type != 'MESH':
        continue
    bpy.context.view_layer.objects.active = ob
    if ob.data.shape_keys:
        bpy.ops.object.shape_key_remove(all=True, apply_mix=True)
    for mod in list(ob.modifiers):
        if mod.type == 'ARMATURE':
            continue
        if mod.type == 'SUBSURF' and mod.levels == 0:
            ob.modifiers.remove(mod)
        else:
            bpy.ops.object.modifier_apply(modifier=mod.name)
    if any(s in ob.name for s in ('Howdah', 'Bronze post')):
        mod = ob.modifiers.new('Interior projection samples', 'SUBSURF')
        mod.subdivision_type = 'SIMPLE'
        mod.levels = mod.render_levels = 2
        bpy.ops.object.modifier_apply(modifier=mod.name)
bpy.context.view_layer.update()

# Keep the initial camera coordinates as a measurable fitting source. Targets
# are landmarks on the unmodified padded 256px token, not texture warps.
records = {}
for ob in sc.objects:
    if ob.type != 'MESH' or ob == base:
        continue
    transforms = skin_matrices(ob)
    records[ob.name] = [(pixel(ob.matrix_world @ (skin_for(ob, v, transforms) @ v.co)),
                         skin_for(ob, v, transforms)) for v in ob.data.vertices]

cam.location = (3, -10, 3.35)
target = Vector((.19, 0, 1.65))
cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
bpy.context.view_layer.update()
right = cam.matrix_world.to_quaternion() @ Vector((1, 0, 0))
shift = right * (-12 * cam.data.ortho_scale / 256)
cam.location += shift
target += shift
bpy.context.view_layer.update()
right = cam.matrix_world.to_quaternion() @ Vector((1, 0, 0))
up = cam.matrix_world.to_quaternion() @ Vector((0, 1, 0))
view = cam.matrix_world.to_quaternion() @ Vector((0, 0, 1))


def group(name):
    if any(s in name for s in ('Howdah', 'Bronze post')):
        return 'howdah'
    if 'Officer' in name:
        return 'officer'
    if 'Mahout' in name:
        return 'mahout'
    if any(s in name for s in ('saddle cloth', 'cloth hem', 'golden fringe', 'saddle stitching', 'load strap')):
        return 'blanket'
    if any(s in name for s in ('forehead cloth', 'Forehead golden')):
        return 'cap'
    if 'curled trunk' in name:
        return 'trunk'
    if 'ivory tusk' in name:
        return 'tusk-near' if 'near' in name else 'tusk-far'
    if 'Sculpted ear' in name:
        return 'ear-near' if 'near' in name else 'ear-far'
    return 'body'


targets = {
    'howdah': (67, 46, 143, 98),
    'blanket': (49, 87, 132, 168),
    'cap': (145, 79, 199, 114),
    'trunk': (180, 96, 226, 143),
    'tusk-near': (181, 134, 211, 160),
    'tusk-far': (185, 134, 224, 156),
    'ear-near': (121, 95, 164, 145),
    'ear-far': (149, 85, 173, 125),
}
bounds = {}
for name, values in records.items():
    kind = group(name)
    points = [p for p, _ in values]
    box = [min(p.x for p in points), min(p.y for p in points),
           max(p.x for p in points), max(p.y for p in points)]
    old = bounds.get(kind, box)
    bounds[kind] = [min(old[0], box[0]), min(old[1], box[1]),
                    max(old[2], box[2]), max(old[3], box[3])]



for name, values in records.items():
    ob = bpy.data.objects[name]
    kind = group(name)
    for vertex, (p, skin) in zip(ob.data.vertices, values):
        if kind == 'officer':
            shoulder = math.exp(-((p.x-102)/12)**2-((p.y-31)/12)**2)
            dest = Vector((p.x-12*shoulder, p.y+8))
        elif kind == 'mahout':
            hip = math.exp(-((p.x-161)/18)**2-((p.y-78)/18)**2)
            dest = Vector((p.x-14*hip+2, p.y-4))
            if 'guiding staff' in name:
                dest.x = 164+(p.x-166.63)*.54
        elif kind in targets:
            a, b = bounds[kind], targets[kind]
            dest = Vector((b[0] + (p.x-a[0])/(a[2]-a[0])*(b[2]-b[0]),
                           b[1] + (p.y-a[1])/(a[3]-a[1])*(b[3]-b[1])))
        else:
            dest = Vector((.85*p.x+22, p.y-1+12*max(0,min(1,(140-p.y)/65))))
            if 'Elephant tail' in name or 'Tail dark tuft' in name:
                dest += Vector((5,-17))
            leg_adjust = {'front.near':(-20,-8),'front.far':(5,0),
                          'back.near':(-4,-5),'back.far':(8,-7)}
            influences = [(ob.vertex_groups[g.group].name, g.weight) for g in vertex.groups]
            if ob.parent_type == 'BONE':
                influences = [(ob.parent_bone, 1)]
            for bone, weight in influences:
                for leg, delta in leg_adjust.items():
                    if bone.startswith(leg):
                        dest += Vector(delta)*weight*max(0,min(1,(p.y-135)/50))
        world = ob.matrix_world @ (skin @ vertex.co)
        current = pixel(world)
        world += (right * (dest.x-current.x) - up * (dest.y-current.y)) * cam.data.ortho_scale / 256
        if kind == 'ear-near':
            # Separate the dished ear from the shoulder in depth without
            # changing its registered outline or flattening its volume.
            world += view*.24
        if kind == 'trunk':
            influences = {ob.vertex_groups[g.group].name:g.weight for g in vertex.groups}
            dx = 5*influences.get('trunk6',0)+2*influences.get('trunk5',0)
            world += right*dx*cam.data.ortho_scale/256
        if kind == 'body':
            influences = [(ob.vertex_groups[g.group].name,g.weight) for g in vertex.groups]
            if ob.parent_type == 'BONE':influences=[(ob.parent_bone,1)]
            dx = sum(w*(9 if n=='back.far.lower' else 6 if n=='front.far.lower' else 0)
                     for n,w in influences)
            world += right*dx*cam.data.ortho_scale/256
        # Sole fitting can alter vertical contact. Move its underside along the
        # camera ray, preserving the target pixel but keeping real stone contact.
        if 'continuous sculpt' in name and p.y > 190:
            world.z = max(.132, world.z)
        vertex.co = skin.inverted_safe() @ ob.matrix_world.inverted() @ world
    ob.data.update()

# Correct the officer's seated grip through native skin weights. The original
# fitted pose put both hands on the right; the painting's near hand is at the
# left rail. Fingers inherit their hand correction, without changing topology.
officer = bpy.data.objects['RIG-Officer MPFB']
hand_family = {'hand_r'} | {b.name for b in officer.data.bones['hand_r'].children_recursive}
for ob in sc.objects:
    if ob.type != 'MESH' or 'Officer' not in ob.name or not ob.vertex_groups:
        continue
    transforms = skin_matrices(ob)
    for v in ob.data.vertices:
        delta = Vector((0,0))
        for g in v.groups:
            name = ob.vertex_groups[g.group].name
            offset = (-40,-16) if name in hand_family else (-27,-10) if name=='lowerarm_r' else (-1,-2) if name=='upperarm_r' else (0,0)
            delta += Vector(offset)*g.weight
        skin = skin_for(ob,v,transforms)
        world = ob.matrix_world@(skin@v.co)
        world += (right*delta.x-up*delta.y)*cam.data.ortho_scale/256
        hand_weight = sum(g.weight for g in v.groups if ob.vertex_groups[g.group].name in hand_family)
        if hand_weight:
            p = pixel(world)
            relative = p-Vector((80,37))
            angle = math.radians(70)
            turned = Vector((math.cos(angle)*relative.x-math.sin(angle)*relative.y,
                             math.sin(angle)*relative.x+math.cos(angle)*relative.y))*.70
            d = (turned-relative)*hand_weight
            world += (right*d.x-up*d.y)*cam.data.ortho_scale/256
        v.co = skin.inverted_safe()@ob.matrix_world.inverted()@world
    ob.data.update()

# A closed, bevelled wooden grip beneath that hand, following its actual rig.
hand_world = officer.matrix_world@officer.pose.bones['hand_r'].head
def grip_point(x,y):
    p = pixel(hand_world)
    return hand_world+(right*(x-p.x)-up*(y-p.y))*cam.data.ortho_scale/256
a,b = grip_point(79.6,33),grip_point(81.8,51)
bpy.ops.mesh.primitive_cylinder_add(vertices=16,radius=.010,depth=(b-a).length,location=(a+b)/2)
grip=bpy.context.object;grip.name='GEO-Officer wooden hand grip'
grip.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler()
grip.data.materials.append(bpy.data.materials['Howdah aged honey timber'])
bevel=grip.modifiers.new('Worn grip edges','BEVEL');bevel.width=.003;bevel.segments=2
bpy.ops.object.modifier_apply(modifier=bevel.name)
bpy.context.view_layer.update();world=grip.matrix_world.copy()
grip.parent=officer;grip.parent_type='BONE';grip.parent_bone='hand_r'
bpy.context.view_layer.update();grip.matrix_world=world

# Register soles to the real contact plane. An outline fit alone can leave the
# far foot in midair. Lower-bone weights taper this correction into the knees;
# toenails share the correction, and the complete mesh stays articulated.
body = bpy.data.objects['GEO-Elephant continuous sculpt']
transforms = skin_matrices(body)
foot_low = {}
for v in body.data.vertices:
    world = body.matrix_world @ (skin_for(body, v, transforms) @ v.co)
    for g in v.groups:
        bone = body.vertex_groups[g.group].name
        if bone.endswith('.lower') and g.weight > .95:
            foot_low[bone] = min(foot_low.get(bone, 100), world.z)
for ob in sc.objects:
    if ob != body and not ob.name.startswith('GEO-Toenail'):
        continue
    transforms = skin_matrices(ob)
    for v in ob.data.vertices:
        skin = skin_for(ob, v, transforms)
        influences = [(ob.vertex_groups[g.group].name, g.weight) for g in v.groups]
        if ob.parent_type == 'BONE':influences=[(ob.parent_bone,1)]
        dz = sum((.132-foot_low[bone])*w for bone,w in influences if bone in foot_low)
        world = ob.matrix_world @ (skin @ v.co)
        world.z += dz
        v.co = skin.inverted_safe() @ ob.matrix_world.inverted() @ world
    ob.data.update()
print('FOOT CONTACT CORRECTIONS', foot_low)

# Round-three registration is on finished, skinned volumes. Translate soles
# along the ground plane, not vertically: a camera-space fit followed by a
# vertical contact correction otherwise undoes the painting's foot placement.
sole_fit = {'front.near.lower': (2, -8), 'back.near.lower': (0, -7),
            'front.far.lower': (-2, -2), 'back.far.lower': (0, -6)}
for ob in sc.objects:
    if ob.type != 'MESH' or ob == base:
        continue
    transforms = skin_matrices(ob)
    for v in ob.data.vertices:
        skin = skin_for(ob, v, transforms)
        world = ob.matrix_world @ (skin @ v.co)
        p = pixel(world)
        weights = {ob.vertex_groups[g.group].name: g.weight for g in v.groups}
        if ob.parent_type == 'BONE':
            weights = {ob.parent_bone: 1.0}
        if ob == body or ob.name.startswith('GEO-Toenail'):
            delta = sum((Vector(offset) * weights.get(bone, 0)
                         for bone, offset in sole_fit.items()), Vector((0, 0)))
            shift = (right * delta.x - up * delta.y) * cam.data.ortho_scale / 256
            shift -= view * (shift.z / view.z)
            world += shift
            p = pixel(world)
            knee = max(0, min(1, (210-p.y)/36))
            dx = knee*(8*weights.get('front.near.lower', 0)
                       +7*weights.get('front.far.lower', 0))
            dx += (94-p.x)*.30*weights.get('back.far.lower', 0)
            dx += (53-p.x)*.16*weights.get('back.near.lower', 0)
            world += right*dx*cam.data.ortho_scale/256
        if 'Officer' in ob.name and ob.vertex_groups:
            fore = weights.get('lowerarm_r', 0)
            hand = sum(weights.get(n, 0) for n in hand_family)
            delta = Vector(((82 + (p.x-82)*.55-p.x)*fore + .8*hand,
                            (42 + (p.y-37)*.9-p.y)*fore + 5*hand))
            world += (right*delta.x-up*delta.y)*cam.data.ortho_scale/256
        if ob == grip:
            world -= up*5*cam.data.ortho_scale/256
        if 'curled trunk' in ob.name:
            # Open the hook into the painting's asymmetric S curve. Ring
            # cross-sections retain camera-depth thickness and rig weights.
            dx = -5*weights.get('trunk5', 0)-2*weights.get('trunk4', 0)
            world += right*dx*cam.data.ortho_scale/256
        v.co = skin.inverted_safe() @ ob.matrix_world.inverted() @ world
    ob.data.update()

# Keep the circular stone, with the painting's shallower ellipse and fine grain.
def linear(c):
    c /= 255
    return c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4


stone = base.data.materials[0]
for v in base.data.vertices:
    v.co.z = .065-(.065-v.co.z)*1.35
bpy.context.view_layer.update()
base_pixels = [pixel(base.matrix_world@v.co) for v in base.data.vertices]
base_center = Vector(((min(p.x for p in base_pixels)+max(p.x for p in base_pixels))/2,
                      (min(p.y for p in base_pixels)+max(p.y for p in base_pixels))/2))
delta = Vector((121.5,223.5))-base_center
shift = (right*delta.x-up*delta.y)*cam.data.ortho_scale/256
shift -= view*(shift.z/view.z)
base.location += shift
bpy.context.view_layer.update()
s = stone.node_tree.nodes.get('Principled BSDF')
s.inputs['Base Color'].default_value = tuple(linear(c) for c in (233,207,160)) + (1,)
for node in stone.node_tree.nodes:
    if node.type == 'BUMP':
        node.inputs['Distance'].default_value = .001
        node.inputs['Strength'].default_value = .12
nodes, links = stone.node_tree.nodes, stone.node_tree.links
ao = nodes.new('ShaderNodeAmbientOcclusion')
ao.inputs['Color'].default_value = tuple(linear(c) for c in (246,224,188))+(1,)
ao.inputs['Distance'].default_value = .16
geometry = nodes.new('ShaderNodeNewGeometry')
separate = nodes.new('ShaderNodeSeparateXYZ')
links.new(geometry.outputs['Normal'], separate.inputs[0])
palette = nodes.new('ShaderNodeMixRGB')
links.new(separate.outputs['Z'], palette.inputs[0])
palette.inputs[1].default_value = tuple(linear(c) for c in (213,176,125))+(1,)
palette.inputs[2].default_value = tuple(linear(c) for c in (246,224,188))+(1,)
grain = nodes.new('ShaderNodeTexNoise')
grain.inputs['Scale'].default_value = 145
grain.inputs['Detail'].default_value = 2
variation = nodes.new('ShaderNodeMixRGB')
variation.blend_type = 'MULTIPLY'
variation.inputs[0].default_value = .055
links.new(palette.outputs[0], variation.inputs[1])
links.new(grain.outputs['Fac'], variation.inputs[2])
links.new(variation.outputs[0], ao.inputs['Color'])
# Registered clean plate supplies the stone's painted grain, never old feet or
# shadows. UVs map to the real beveled disc; live AO supplies current contact.
stone_image = bpy.data.images.load(str(ROOT/'assets/war-elephant/stone-fill-source.png'))
stone_image.pack()
uv = base.data.uv_layers.new(name='Stone clean plate')
points = [pixel(base.matrix_world@v.co) for v in base.data.vertices]
box = (min(p.x for p in points), min(p.y for p in points),
       max(p.x for p in points), max(p.y for p in points))
# Generated plate has retained canvas framing. Use the measured opaque disc
# extent, inset slightly to avoid the antialiased transparent outer boundary.
for i, loop in enumerate(base.data.loops):
    p = points[loop.vertex_index]
    x = .100 + .725*(p.x-box[0])/(box[2]-box[0])
    y = .785 + .155*(p.y-box[1])/(box[3]-box[1])
    uv.data[i].uv = (x, 1-y)
texture = nodes.new('ShaderNodeTexImage'); texture.image = stone_image
uvnode = nodes.new('ShaderNodeUVMap'); uvnode.uv_map = uv.name
links.new(uvnode.outputs[0], texture.inputs['Vector'])
clean_color = nodes.new('ShaderNodeMixRGB')
links.new(texture.outputs['Alpha'], clean_color.inputs[0])
links.new(variation.outputs[0], clean_color.inputs[1])
links.new(texture.outputs['Color'], clean_color.inputs[2])
links.new(clean_color.outputs[0], ao.inputs['Color'])
pigment = nodes.new('ShaderNodeEmission')
links.new(ao.outputs['Color'], pigment.inputs['Color'])
camera = nodes.new('ShaderNodeLightPath')
weight = nodes.new('ShaderNodeMath')
weight.operation = 'MULTIPLY'
weight.inputs[1].default_value = .90
links.new(camera.outputs['Is Camera Ray'], weight.inputs[0])
mix = nodes.new('ShaderNodeMixShader')
links.new(weight.outputs[0], mix.inputs[0])
links.new(s.outputs[0], mix.inputs[1])
links.new(pigment.outputs[0], mix.inputs[2])
links.new(mix.outputs[0], nodes.get('Material Output').inputs['Surface'])
sc.view_settings.view_transform = 'Standard'
sc.view_settings.look = 'None'
for light in [o for o in sc.objects if o.type == 'LIGHT']:
    light.data.energy *= .65
bpy.data.objects['LGT-key'].data.color = (1, .95, .86)
bpy.data.objects['LGT-rim'].data.energy *= .5
bpy.context.view_layer.update()
(M/'registration.json').write_text(json.dumps({'old_bounds':bounds,'target_bounds':targets,'foot_original_min_z':foot_low,
    'camera':list(cam.location),'method':'full-depth inverse-skinned geometry fit; fixed camera UVs'},indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(M/'plain.blend'))

# Scene BVH rejects source paint on surfaces occluded by riders/cloth/equipment.
vertices, faces = [], []
for ob in sc.objects:
    if ob.type != 'MESH':
        continue
    ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
    me = ev.to_mesh()
    offset = len(vertices)
    vertices.extend(ev.matrix_world @ v.co for v in me.vertices)
    faces.extend(tuple(offset+i for i in p.vertices) for p in me.polygons)
    ev.to_mesh_clear()
tree = BVHTree.FromPolygons(vertices, faces)
painting = bpy.data.images.load(str(ROOT/'assets/war-elephant/painting-aligned.png'))
projected = []
for ob in list(sc.objects):
    if ob.type != 'MESH' or ob == base:
        continue
    ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
    me = ev.to_mesh()
    assert len(me.vertices) == len(ob.data.vertices), ob.name
    coords, weights = [], []
    for v in me.vertices:
        world = ev.matrix_world @ v.co
        q = world_to_camera_view(sc, cam, world)
        coords.append((q.x, q.y))
        normal = (ev.matrix_world.to_3x3().inverted().transposed() @ v.normal).normalized()
        hit = tree.ray_cast(world + view * .007, view, 10)[0]
        weights.append(max(0, min(1, normal.dot(view)/.18)) if hit is None else 0)
    ev.to_mesh_clear()
    uv = ob.data.uv_layers.new(name='Painting projection')
    attr = ob.data.color_attributes.new(name='Painting incidence', type='FLOAT_COLOR', domain='CORNER')
    for i, loop in enumerate(ob.data.loops):
        uv.data[i].uv = coords[loop.vertex_index]
        attr.data[i].color = (weights[loop.vertex_index],)*3 + (1,)
    for index, old in enumerate(list(ob.data.materials)):
        mat = old.copy()
        mat.name = ob.name + ' painted'
        ob.data.materials[index] = mat
        nodes, links = mat.node_tree.nodes, mat.node_tree.links
        physical = nodes.get('Principled BSDF')
        tex = nodes.new('ShaderNodeTexImage')
        tex.image, tex.extension = painting, 'CLIP'
        uvnode = nodes.new('ShaderNodeUVMap')
        uvnode.uv_map = uv.name
        links.new(uvnode.outputs[0], tex.inputs['Vector'])
        incidence = nodes.new('ShaderNodeVertexColor')
        incidence.layer_name = attr.name
        weight = nodes.new('ShaderNodeMath')
        weight.operation = 'MULTIPLY'
        links.new(incidence.outputs[0], weight.inputs[0])
        links.new(tex.outputs['Alpha'], weight.inputs[1])
        pigment = nodes.new('ShaderNodeEmission')
        pigment.name = 'Preserved painted illumination'
        links.new(tex.outputs['Color'], pigment.inputs['Color'])
        response = nodes.new('ShaderNodeMixShader')
        response.inputs[0].default_value = .96
        links.new(physical.outputs[0], response.inputs[1])
        links.new(pigment.outputs[0], response.inputs[2])
        camera = nodes.new('ShaderNodeLightPath')
        only_camera = nodes.new('ShaderNodeMath')
        only_camera.operation = 'MULTIPLY'
        links.new(weight.outputs[0], only_camera.inputs[0])
        links.new(camera.outputs['Is Camera Ray'], only_camera.inputs[1])
        final = nodes.new('ShaderNodeMixShader')
        links.new(only_camera.outputs[0], final.inputs[0])
        links.new(physical.outputs[0], final.inputs[1])
        links.new(response.outputs[0], final.inputs[2])
        links.new(final.outputs[0], nodes.get('Material Output').inputs['Surface'])
    projected.append(ob.name)
painting.pack()
sc['projected_meshes'] = json.dumps(projected)
sc['projection_method'] = 'finished surfaces; visibility and facing; camera-only pigment'
bpy.ops.wm.save_as_mainfile(filepath=str(M/'war-elephant.blend'))
print('PROJECTED', len(projected), 'finished articulated surfaces')
