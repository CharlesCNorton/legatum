"""Rest-pose camera paint on genuine rigged surfaces, with feathered unseen fills.

Run after finish. Repeats start from a preserved pre-projection master, never from
an already modified mesh. UVs and visibility are fixed at rest, not reprojected
per frame, so brushwork follows the mesh through animation.
"""
import bpy
import hashlib
import json
import math
import os
import shutil
import sys
from pathlib import Path
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view

ROOT = Path(os.environ['ANIM_ROOT'])
MASTER = ROOT / 'masters/spearman-3d-v2'
fill_lock = json.loads((Path(__file__).parent/'fills.lock.json').read_text())
for name, expected in fill_lock.items():
    asset = MASTER/'textures/generated'/name
    assert hashlib.sha256(asset.read_bytes()).hexdigest() == expected, f'Generated fill changed: {name}'
path = MASTER / 'spearman.blend'
checkpoint = MASTER / 'projection-input.blend'
bpy.ops.wm.open_mainfile(filepath=str(path))
if bpy.context.scene.get('projection_v3'):
    assert checkpoint.exists(), 'Missing preserved projection input'
    bpy.ops.wm.open_mainfile(filepath=str(checkpoint))
else:
    shutil.copyfile(path, checkpoint)
sc = bpy.context.scene
rig = bpy.data.objects['Spearman • MPFB game_engine']
body = bpy.data.objects['MPFB anatomical male • original topology']
sc.frame_set(1)
cloth_obj = bpy.data.objects['Cloak • simulated wool']
cloth = cloth_obj.modifiers['Cloth per clip']
cloth.show_viewport = False


def aim(name, direction):
    p = rig.pose.bones[name]
    q = p.bone.matrix_local.to_quaternion()
    delta = (q @ Vector((0, 1, 0))).rotation_difference(Vector(direction).normalized())
    mat = (delta @ q).to_matrix().to_4x4()
    mat.translation = p.head
    p.matrix = mat
    bpy.context.view_layer.update()


def limb(u, l, target, pole):
    a = rig.pose.bones[u].head.copy()
    axis = Vector(target) - a
    l1, l2 = rig.data.bones[u].length, rig.data.bones[l].length
    d = min(axis.length, l1 + l2 - .0001)
    axis.normalize()
    along = (l1*l1-l2*l2+d*d)/(2*d)
    side = Vector(pole)-a
    side = (side-axis*side.dot(axis)).normalized()
    elbow = a+axis*along+max(0, l1*l1-along*along)**.5*side
    aim(u, elbow-a)
    aim(l, Vector(target)-elbow)


# Match the painted disc ellipse. Keep this exact camera in
# rest, clips and final renders; render.py must not reset it after UV calibration.
sc.camera.location = (2.5, -7, 3.0)
sc.camera.rotation_euler = (Vector((0, 0, 1.20))-sc.camera.location).to_track_quat('-Z', 'Y').to_euler()
sc.camera.data.ortho_scale = 2.90
sc.camera.data.dof.use_dof = False
rig.location.x = .065
head = rig.pose.bones['head']
pivot = head.head.copy()
head.matrix = Matrix.Translation(pivot) @ Matrix.Rotation(1.5, 4, 'Z') @ Matrix.Diagonal((1.10, 1.10, 1.10, 1)) @ Matrix.Translation(-pivot) @ head.matrix
bpy.context.view_layer.update()
limb('thigh_r', 'calf_r', (-.39, -.075, .082), (-.43, -.40, .48))
limb('thigh_l', 'calf_l', (.21, .15, .082), (.36, -.36, .48))
# Raised fist / bent elbow rather than a straight lowered forearm.
limb('upperarm_r', 'lowerarm_r', (-.37, -.31, 1.34), (-.48, -.12, 1.08))
aim('hand_r', (0, -.03, .09))
# Preserve the spear's tip and ground contact while raising the hand on its shaft.
bpy.context.view_layer.update()
for ob in sc.objects:
    if ob.name.startswith(('Ash dory shaft', 'Spear bronze ferrule', 'Leaf spearhead', 'Iron spear butt')):
        mat = ob.matrix_world.copy()
        mat.translation.z -= .15
        ob.matrix_world = mat
# Give the leaf a real broad blade at the source's scale.
blade = bpy.data.objects['Leaf spearhead with medial ridge']
cx = sum(v.co.x for v in blade.data.vertices)/len(blade.data.vertices)
blade_top = max(v.co.z for v in blade.data.vertices)
for v in blade.data.vertices:
    v.co.x = cx + (v.co.x-cx)*1.45
    v.co.z = blade_top + (v.co.z-blade_top)*1.6
shaft = bpy.data.objects['Ash dory shaft']
shaft.data.splines[0].points[-1].co.z -= .114
for ob in sc.objects:
    if ob.name.startswith('Spear bronze ferrule'):
        for spline in ob.data.splines:
            for point in spline.points: point.co.z -= .114
# The source shield is tall, closer to the chest and a little higher.
shield = bpy.data.objects['Aspis control']
mat = shield.matrix_world.copy()
mat.translation += Vector((.015, -.015, .055))
shield.matrix_world = mat

# Wide wool silhouette with modeled folded troughs; light edge pinning retains
# the flare while the middle remains simulated and follows the character.
for v in cloth_obj.data.vertices:
    t = max(0, min(1, (1.51-v.co.z)/1.16))
    v.co.x = v.co.x*.94 - .07*t
    v.co.y += .025*math.sin(v.co.x*39)*t
pin = cloth_obj.vertex_groups['Shoulder pins']
for v in cloth_obj.data.vertices:
    t = max(0, min(1, (1.51-v.co.z)/1.16))
    if t > .05:
        edge = min(1, abs(v.co.x)/(.23+.36*t))
        pin.add([v.index], .10 + .34*edge**6, 'REPLACE')
cloth.settings.use_dynamic_mesh = True
cloth.settings.bending_stiffness = 1.5
for ob in sc.objects:
    if ob.name.startswith('Linen pteruges'):
        for v in ob.data.vertices:
            t = max(0, min(1, (1.13-v.co.z)/.29))
            v.co.y += .009*math.sin(t*math.pi*3+v.co.x*35)*t
        sub = ob.modifiers.new('Soft woven folds', 'SUBSURF')
        sub.levels = sub.render_levels = 1
# Replace the round rope-like baldric with a broad, thick leather ribbon.
old = bpy.data.objects.get('Leather baldric')
if old:
    old.hide_render = True
    old.hide_viewport = True
    verts, faces = [], []
    for i in range(17):
        t = i/16
        x, y, z = -.16+.31*t, -.18-.025*math.sin(t*math.pi), 1.46-.34*t
        for side in [-1, 1]:
            verts.append((x+side*.018, y, z+side*.017))
        if i: faces.append((2*i-2, 2*i-1, 2*i+1, 2*i))
    mesh = bpy.data.meshes.new('GEO-baldric-thick-ribbon')
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(bpy.data.materials['Oxide leather'])
    ob = bpy.data.objects.new(mesh.name, mesh)
    sc.collection.objects.link(ob)
    ob.parent, ob.parent_type, ob.parent_bone = old.parent, old.parent_type, old.parent_bone
    ob.matrix_parent_inverse, ob.matrix_basis = old.matrix_parent_inverse, old.matrix_basis
    solid = ob.modifiers.new('Leather thickness', 'SOLIDIFY'); solid.thickness = .007
    bevel = ob.modifiers.new('Worn rounded leather edges', 'BEVEL'); bevel.width = .003; bevel.segments = 3
# A real buckle frame and tongue remain visible when the shield moves aside.
belt = bpy.data.objects['Wide waist belt']
for name, points, radius in [
    ('GEO-waist-buckle-frame', [(x, -.197, z) for x,z in [(.025,1.075),(.080,1.075),(.087,1.082),(.087,1.120),(.080,1.127),(.025,1.127),(.018,1.120),(.018,1.082),(.025,1.075)]], .004),
    ('GEO-waist-buckle-tongue', [(.052,-.201,1.075),(.052,-.204,1.119)], .0025),
]:
    data = bpy.data.curves.new(name, 'CURVE'); data.dimensions = '3D'
    data.bevel_depth = radius; data.bevel_resolution = 3
    spline = data.splines.new('POLY'); spline.points.add(len(points)-1)
    for point, co in zip(spline.points, points): point.co = (*co, 1)
    data.materials.append(bpy.data.materials['Bronze • polished edges'])
    ob = bpy.data.objects.new(name, data); sc.collection.objects.link(ob)
    ob.parent, ob.parent_type, ob.parent_bone = belt.parent, belt.parent_type, belt.parent_bone
    ob.matrix_parent_inverse, ob.matrix_basis = belt.matrix_parent_inverse, belt.matrix_basis
blade_bevel = blade.modifiers.new('Forged blade edge finish', 'BEVEL')
blade_bevel.width = .001; blade_bevel.segments = 3
# Existing rivets and curved hem borders remain real geometry.
for ob in sc.objects:
    for mod in ob.modifiers:
        if mod.type == 'BEVEL': mod.segments = max(3, mod.segments)


def linear(value):
    return value/12.92 if value <= .04045 else ((value+.055)/1.055)**2.4


def colour(hex_value):
    return (*[linear(int(hex_value[i:i+2], 16)/255) for i in (0, 2, 4)], 1)


# Shared cream is specified in sRGB, then converted to Blender linear inputs.
# The old (.85,.60,.30) linear setting is not the requested #E9CFA0.
for name, hex_value in [('Cream limestone', 'E9CFA0'), ('Cream limestone darker rim', 'B68A51')]:
    mat = bpy.data.materials.get(name)
    if mat:
        bsdf = mat.node_tree.nodes.get('Principled BSDF')
        for link in list(bsdf.inputs['Base Color'].links): mat.node_tree.links.remove(link)
        bsdf.inputs['Base Color'].default_value = colour(hex_value)
        bsdf.inputs['Roughness'].default_value = .86
        bsdf.inputs['Metallic'].default_value = 0
        mat['sRGB_base'] = '#'+hex_value
for name, energy, size, rgb in [
    ('Warm upper-left key', 700, 1.8, (1, .88, .70)),
    ('Soft cool fill', 140, 3.0, (.88, .93, 1)),
    ('Warm back rim', 240, 2.0, (.70, .83, 1)),
]:
    ob = bpy.data.objects[name]
    ob.data.energy, ob.data.size, ob.data.color = energy, size, rgb
sc.view_settings.view_transform = 'AgX'
sc.view_settings.look = 'AgX - Medium High Contrast'
sc.view_settings.exposure = 0
# Sculpt the crest's asymmetric swept profile to source landmarks. Preserve
# each vertex's camera depth and nonzero tuft thickness: it remains a volumetric
# bone-attached fan, not a camera-facing replacement for the character.
bpy.context.view_layer.update()
cam = sc.camera.matrix_world
right = cam.to_quaternion() @ Vector((1, 0, 0))
up = cam.to_quaternion() @ Vector((0, 1, 0))
scale = sc.camera.data.ortho_scale


def bezier(points, t):
    return sum((Vector(p)*weight for p, weight in zip(points, [(1-t)**3, 3*t*(1-t)**2, 3*t*t*(1-t), t**3])), Vector((0, 0)))


def screen_sculpt(ob, local, target):
    world = ob.matrix_world @ local
    projected = world_to_camera_view(sc, sc.camera, world)
    world += right*((target.x/256-projected.x)*scale)
    world += up*((1-target.y/256-projected.y)*scale)
    return ob.matrix_world.inverted() @ world


tufts = sorted([o for o in sc.objects if o.name.startswith('Horsehair crest tuft')], key=lambda o:o.name)
outer = [(118, 90), (117, 64), (132, 49), (148, 63)]
inner = [(122, 91), (122, 80), (128, 71), (138, 71)]
for i, tuft in enumerate(tufts):
    t = 1-i/(len(tufts)-1)
    for indices, contour in [((0, 1), inner), ((2, 3), outer)]:
        projected = [world_to_camera_view(sc, sc.camera, tuft.matrix_world @ tuft.data.vertices[j].co) for j in indices]
        centre = sum((Vector((p.x*256, (1-p.y)*256)) for p in projected), Vector((0, 0)))/2
        for j, p in zip(indices, projected):
            offset = Vector((p.x*256, (1-p.y)*256))-centre
            target = bezier(contour, t)+offset*.45
            tuft.data.vertices[j].co = screen_sculpt(tuft, tuft.data.vertices[j].co, target)
    tuft.data.update()
fibres = sorted([o for o in sc.objects if o.name.startswith('Horsehair painted fibre')], key=lambda o:o.name)
for fibre, tuft in zip(fibres, tufts[::2]):
    for point, index in zip(fibre.data.splines[0].points, [0, 3]):
        point.co = (*(fibre.matrix_world.inverted() @ tuft.matrix_world @ tuft.data.vertices[index].co), 1)
saddle = bpy.data.objects['Crest bronze saddle']
points = saddle.data.splines[0].points
for i, point in enumerate(points):
    point.co = (*screen_sculpt(saddle, Vector(point.co[:3]), bezier(inner, 1-i/(len(points)-1))), 1)
bpy.context.view_layer.update()

# Intersect the orthographic reference ray with the stone top. This keeps the
# spear planted instead of shortening its bottom until it floats above the disc.
cam = sc.camera.matrix_world
right = cam.to_quaternion() @ Vector((1, 0, 0))
up = cam.to_quaternion() @ Vector((0, 1, 0))
forward = cam.to_quaternion() @ Vector((0, 0, -1))
scale = sc.camera.data.ortho_scale
origin = cam.translation + right*((94/256-.5)*scale) + up*((.5-220/256)*scale)
floor = origin + forward*((.105-origin.z)/forward.z)
tip = floor + right*(5/256*scale) + Vector((0, 0, (207/256*scale)/up.z))
grip = floor.lerp(tip, (220-115)/207)
hand = rig.matrix_world.inverted() @ (grip-Vector((0, -.012, .047)))
limb('upperarm_r', 'lowerarm_r', hand, (-.48, -.12, 1.08))
aim('hand_r', (0, -.03, .09))
bpy.context.view_layer.update()
shaft = bpy.data.objects['Ash dory shaft']
start = shaft.matrix_world @ Vector(shaft.data.splines[0].points[0].co[:3])
old_tip = max((blade.matrix_world @ v.co for v in blade.data.vertices), key=lambda p:p.z)
axis, target_axis = old_tip-start, tip-floor
rotation = axis.rotation_difference(target_axis).to_matrix().to_4x4()
q = Vector((0, 0, 1)).rotation_difference(axis)
long_scale = q.to_matrix().to_4x4() @ Matrix.Diagonal((1, 1, target_axis.length/axis.length, 1)) @ q.inverted().to_matrix().to_4x4()
transform = Matrix.Translation(floor) @ rotation @ long_scale @ Matrix.Translation(-start)
weapons = [o for o in sc.objects if o.name.startswith(('Ash dory shaft', 'Spear bronze ferrule', 'Leaf spearhead', 'Iron spear butt'))]
originals = {o.name:o.matrix_world.copy() for o in weapons}
for ob in weapons: ob.matrix_world = transform @ originals[ob.name]
rig['guard_hand_target'] = list(hand)
rig['neutral_pose'] = json.dumps({p.name: [list(row) for row in p.matrix_basis] for p in rig.pose.bones})
bpy.context.view_layer.update()

# Turn only decorative curves into mesh for frozen UVs. The shaft remains a
# curve because the grip/intersection audit reads its explicit centerline.
for ob in list(sc.objects):
    if ob.type == 'CURVE' and not ob.hide_render and not ob.name.startswith(('Ash dory shaft', 'Iron spear butt', 'Spear bronze ferrule')):
        bpy.ops.object.select_all(action='DESELECT')
        ob.select_set(True); bpy.context.view_layer.objects.active = ob
        bpy.ops.object.convert(target='MESH')

# Family-local finishing runs before visibility and UV calibration.
sys.path.insert(0, str(Path(__file__).parent/'infantry'))
from refine import refine
from paint_finish import painted_fill
refine(sc, aim, screen_sculpt)
sys.path.insert(0, str(Path(__file__).parent/'units/spearman'))
from silhouette import fit_silhouette
fit_silhouette(sc, screen_sculpt)
from stance import bulk_legs, flare_cloak
bulk_legs(sc)
flare_cloak(sc, screen_sculpt)
rig['neutral_pose'] = json.dumps({p.name: [list(row) for row in p.matrix_basis] for p in rig.pose.bones})

# Evaluate deformation with original vertex indexing. UVs are written to the
# original mesh before subdivision; armature weights and topology stay intact.
saved_modifiers = []
for ob in sc.objects:
    for mod in ob.modifiers:
        if mod.type in {'SUBSURF', 'SOLIDIFY', 'BEVEL', 'CLOTH'}:
            saved_modifiers.append((mod, mod.show_viewport))
            mod.show_viewport = False
bpy.context.view_layer.update()
deps = bpy.context.evaluated_depsgraph_get()
vertices, polygons, evaluated = [], [], {}
for ob in sc.objects:
    if ob.type != 'MESH' or ob.hide_render: continue
    ev = ob.evaluated_get(deps)
    me = ev.to_mesh()
    points = [ob.matrix_world @ v.co for v in me.vertices]
    normals = [(ob.matrix_world.to_3x3().inverted().transposed() @ v.normal).normalized() for v in me.vertices]
    offset = len(vertices)
    vertices.extend(points)
    polygons.extend([tuple(offset+i for i in p.vertices) for p in me.polygons])
    ev.to_mesh_clear()
    if len(points) != len(ob.data.vertices):
        # MPFB masks hide helper geometry. Keep it out of the visibility BVH,
        # but temporarily disable masks to recover original skin vertex indices.
        masks = [m for m in ob.modifiers if m.type == 'MASK' and m.show_viewport]
        for m in masks: m.show_viewport = False
        bpy.context.view_layer.update()
        ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
        me = ev.to_mesh()
        points = [ob.matrix_world @ v.co for v in me.vertices]
        normals = [(ob.matrix_world.to_3x3().inverted().transposed() @ v.normal).normalized() for v in me.vertices]
        ev.to_mesh_clear()
        for m in masks: m.show_viewport = True
        bpy.context.view_layer.update()
        deps = bpy.context.evaluated_depsgraph_get()
    evaluated[ob.name] = (points, normals)
tree = BVHTree.FromPolygons(vertices, polygons)
view = sc.camera.matrix_world.to_quaternion() @ Vector((0, 0, 1))
image = bpy.data.images.load(str(MASTER/'spearman-source.png'), check_existing=True)
fills = {name: bpy.data.images.load(str(MASTER/'textures/generated'/f'{name}.png'), check_existing=True)
         for name in ['bronze', 'wool', 'linen', 'leather']}
coverage = {}
for ob in list(sc.objects):
    # A coarse static base must not inherit the painting's feet or cast shadows.
    # Keep its shared cream PBR material; moving feet cast real contact shadows.
    if ob.name not in evaluated or ob.name == 'Stationary cream stone': continue
    points, normals = evaluated[ob.name]
    assert len(points) == len(ob.data.vertices), ob.name
    uv = ob.data.uv_layers.get('Painting camera rest') or ob.data.uv_layers.new(name='Painting camera rest')
    mask = ob.data.color_attributes.get('Painting visibility') or ob.data.color_attributes.new(name='Painting visibility', type='FLOAT_COLOR', domain='CORNER')
    weights = []
    for p, normal in zip(points, normals):
        hit, _, _, distance = tree.ray_cast(p+view*10, -view, 10.02)
        visible = hit is not None and (hit-p).length < .018
        # Relief can occlude adjacent shield vertices. The whole front shell
        # carries the same paint beneath it; do not punch PBR wedges into it.
        if ob.name.startswith(('Convex bronze aspis', 'Sunburst raised ray', 'Aspis central omphalos')):
            visible = hit is not None and (hit-p).length < .14
        # Ray visibility rejects hidden backs. Absolute facing also supports
        # double-sided cloth and open armour shells without painting through them.
        facing = abs(normal.dot(view))
        weight = max(0, min(1, (facing-.02)/.18)) if visible else 0
        weights.append(weight)
    for loop in ob.data.loops:
        p = world_to_camera_view(sc, sc.camera, points[loop.vertex_index])
        # Full-resolution painting -> the game's padded 256px reference canvas.
        u = (349+(p.x*256-75)*556/105)/image.size[0]
        v = 1-(9+((1-p.y)*256-12)*1236/232)/image.size[1]
        uv.data[loop.index].uv = (u, v)
        w = weights[loop.vertex_index]
        mask.data[loop.index].color = (w, w, w, 1)
    coverage[ob.name] = round(sum(weights)/max(1, len(weights)), 3)
    # Preserve AO/curvature UV as the active render UV. Painting uses its named UV.
    for layer in ob.data.uv_layers: layer.active_render = layer.name != uv.name
    ob.data.uv_layers.active_index = 0
    for i, original in enumerate(list(ob.data.materials)):
        if original is None or not original.use_nodes: continue
        mat = original.copy(); mat.name = original.name+' | rest paint | '+ob.name
        ob.data.materials[i] = mat
        nodes, links = mat.node_tree.nodes, mat.node_tree.links
        bsdf = nodes.get('Principled BSDF')
        output = next(n for n in nodes if n.type == 'OUTPUT_MATERIAL')
        physical = output.inputs['Surface'].links[0].from_socket
        material_name = original.name.lower()
        if bsdf and 'forged iron' in material_name: bsdf.inputs['Metallic'].default_value = 1
        if bsdf and 'incised bronze patina' in material_name: bsdf.inputs['Metallic'].default_value = 0
        fill_kind = next((kind for key, kind in [('bronze', 'bronze'), ('wool', 'wool'), ('linen', 'linen'), ('leather', 'leather')] if key in material_name), None)
        if fill_kind and bsdf:
            coords = nodes.new('ShaderNodeTexCoord')
            fill = nodes.new('ShaderNodeTexImage'); fill.image = fills[fill_kind]
            fill.projection = 'BOX'; fill.projection_blend = .3
            links.new(coords.outputs['Generated'], fill.inputs['Vector'])
            mix = nodes.new('ShaderNodeMixRGB'); mix.inputs[0].default_value = .65
            old = bsdf.inputs['Base Color'].links
            if old: links.new(old[0].from_socket, mix.inputs[1])
            else: mix.inputs[1].default_value = bsdf.inputs['Base Color'].default_value
            links.new(fill.outputs['Color'], mix.inputs[2]); links.new(mix.outputs[0], bsdf.inputs['Base Color'])
            if 'bronze' in material_name: bsdf.inputs['Metallic'].default_value = 1
        if bsdf and 'skin' in material_name:
            bsdf.inputs['Subsurface Weight'].default_value = .015
            bsdf.inputs['Roughness'].default_value = .7
            tint = nodes.new('ShaderNodeMixRGB'); tint.blend_type = 'MULTIPLY'
            tint.inputs[0].default_value = .55; tint.inputs[2].default_value = (.65, .36, .16, 1)
            old = bsdf.inputs['Base Color'].links
            if old: links.new(old[0].from_socket, tint.inputs[1])
            else: tint.inputs[1].default_value = bsdf.inputs['Base Color'].default_value
            links.new(tint.outputs[0], bsdf.inputs['Base Color'])
        if bsdf and (fill_kind or 'skin' in material_name):
            physical = painted_fill(nodes, links, physical,
                                    bsdf.inputs['Base Color'].links[0].from_socket)
        coord = nodes.new('ShaderNodeUVMap'); coord.uv_map = uv.name
        tex = nodes.new('ShaderNodeTexImage'); tex.image = image; tex.extension = 'CLIP'
        links.new(coord.outputs[0], tex.inputs['Vector'])
        attr = nodes.new('ShaderNodeVertexColor'); attr.layer_name = mask.name
        mul = nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
        links.new(attr.outputs['Color'], mul.inputs[0]); links.new(tex.outputs['Alpha'], mul.inputs[1])
        strength = nodes.new('ShaderNodeMath'); strength.operation = 'MULTIPLY'
        links.new(mul.outputs[0], strength.inputs[0]); strength.inputs[1].default_value = .96
        # Painted illumination is visible pigment, not a lamp. Sending this
        # emission into diffuse bounces made the feet and base glow orange.
        # Non-camera rays retain the actual physical material and live shadows.
        ray = nodes.new('ShaderNodeLightPath')
        camera_paint = nodes.new('ShaderNodeMath'); camera_paint.operation = 'MULTIPLY'
        links.new(strength.outputs[0], camera_paint.inputs[0])
        links.new(ray.outputs['Is Camera Ray'], camera_paint.inputs[1])
        # Brushwork contains painted illumination: preserve it with an emissive
        # pigment layer, leaving 4% actual PBR to reveal moving surface relief.
        pigment = nodes.new('ShaderNodeBsdfPrincipled'); pigment.label = 'Painted illumination, fixed rest UV'
        pigment.inputs['Base Color'].default_value = (0, 0, 0, 1)
        pigment.inputs['Roughness'].default_value = 1
        pigment.inputs['Specular IOR Level'].default_value = 0
        links.new(tex.outputs['Color'], pigment.inputs['Emission Color'])
        pigment.inputs['Emission Strength'].default_value = 1
        blend = nodes.new('ShaderNodeMixShader')
        links.new(camera_paint.outputs[0], blend.inputs[0]); links.new(physical, blend.inputs[1]); links.new(pigment.outputs[0], blend.inputs[2]); links.new(blend.outputs[0], output.inputs['Surface'])
# Material-only lane hook: frozen underpainting after projection, before save.
from surface_finish import apply as finish_surfaces
finish_surfaces(sc, image)
for mod, enabled in saved_modifiers: mod.show_viewport = enabled
cloth.show_viewport = True
sc['projection_v3'] = True
sc['projection_source_sha256'] = hashlib.sha256((MASTER/'spearman-source.png').read_bytes()).hexdigest()
sc['projection_method'] = 'Frozen rest-camera UVs, ray visibility and facing feather; generated fills on unseen geometry; no billboard'
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(path))
(ROOT/'review/3d-v2/spearman-projection.json').write_text(json.dumps({'coverage': coverage, 'source_sha256': sc['projection_source_sha256'], 'camera': list(sc.camera.location), 'ortho_scale': sc.camera.data.ortho_scale}, indent=2))
print('PROJECT_READY', len(coverage), 'meshes')
