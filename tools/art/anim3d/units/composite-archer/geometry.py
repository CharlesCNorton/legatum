"""Geometry and MPFB fitting helpers adapted from the infantry lead scene.py."""
import bpy, math
from mathutils import Vector, Matrix
def material(name, color, metal=0, rough=0.52):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    s = m.node_tree.nodes.get('Principled BSDF')
    s.inputs['Base Color'].default_value = (*color, 1)
    s.inputs['Metallic'].default_value = metal
    s.inputs['Roughness'].default_value = rough
    return m

def mesh(name, verts, faces, mat, smooth=True):
    d = bpy.data.meshes.new(name)
    d.from_pydata(verts, [], faces)
    d.update()
    o = bpy.data.objects.new(name, d)
    bpy.context.collection.objects.link(o)
    if mat:
        d.materials.append(mat)
    for p in d.polygons:
        p.use_smooth = smooth
    return o

def bevel(o, width=0.004, segments=2):
    m = o.modifiers.new('Forged rounded edges', 'BEVEL')
    m.width = width
    m.segments = segments
    return o

def solid(o, t=0.004):
    m = o.modifiers.new('Physical thickness', 'SOLIDIFY')
    m.thickness = t
    return o

def curve(name, pts, radius, mat):
    d = bpy.data.curves.new(name, 'CURVE')
    d.dimensions = '3D'
    d.resolution_u = 2
    s = d.splines.new('POLY')
    s.points.add(len(pts) - 1)
    for p, v in zip(s.points, pts):
        p.co = (*v, 1)
    d.bevel_depth = radius
    d.bevel_resolution = 2
    o = bpy.data.objects.new(name, d)
    bpy.context.collection.objects.link(o)
    d.materials.append(mat)
    return o

def sphere(name, loc, scale, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    o.data.materials.append(mat)
    for p in o.data.polygons:
        p.use_smooth = True
    return o

def attach(o, bone):
    bpy.context.view_layer.update()
    world = o.matrix_world.copy()
    o.parent = rig
    o.parent_type = 'BONE'
    o.parent_bone = bone
    bpy.context.view_layer.update()
    o.matrix_world = world
    o['attachment'] = bone
    return o

def aim_bone(name, direction):
    p = rig.pose.bones[name]
    rest = p.bone.matrix_local
    q = rest.to_quaternion()
    v = q  @  Vector((0, 1, 0))
    delta = v.rotation_difference(Vector(direction).normalized())
    rot = (delta  @  q).to_matrix().to_4x4()
    rot.translation = p.head.copy()
    p.matrix = rot
    bpy.context.view_layer.update()

def limb(upper, lower, target, pole):
    a = rig.pose.bones[upper].head.copy()
    t = Vector(target)
    axis = t - a
    l1 = rig.data.bones[upper].length
    l2 = rig.data.bones[lower].length
    d = min(axis.length, l1 + l2 - 0.0001)
    axis.normalize()
    along = (l1 * l1 - l2 * l2 + d * d) / (2 * d)
    h = max(0, l1 * l1 - along * along) ** 0.5
    side = Vector(pole) - a
    side = (side - axis * side.dot(axis)).normalized()
    elbow = a + axis * along + side * h
    aim_bone(upper, elbow - a)
    aim_bone(lower, t - elbow)

def fitted_shell(name, predicate, mat, inflate=0.009):
    states=[(m,m.show_viewport) for m in body.modifiers if m.type=='SUBSURF']
    for m,_ in states:m.show_viewport=False
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    ev = body.evaluated_get(dg)
    me = ev.to_mesh()
    faces = [p for p in me.polygons if all((predicate(me.vertices[i].co) for i in p.vertices))]
    ids = sorted(set((i for p in faces for i in p.vertices)))
    mapping = {v: i for i, v in enumerate(ids)}
    vs = [tuple(me.vertices[i].co + me.vertices[i].normal * inflate) for i in ids]
    ob = mesh(name, vs, [[mapping[i] for i in p.vertices] for p in faces], mat)
    for g in body.vertex_groups:
        if g.name in rig.data.bones:
            ob.vertex_groups.new(name=g.name)
    for j, i in enumerate(ids):
        k = i  # topology is unchanged: preserve exact MPFB skin weights
        for g in body.data.vertices[k].groups:
            name = body.vertex_groups[g.group].name
            if name in ob.vertex_groups:
                ob.vertex_groups[name].add([j], g.weight, 'REPLACE')
    ev.to_mesh_clear()
    for m,state in states:m.show_viewport=state
    ob.parent = rig
    ar = ob.modifiers.new('MPFB fitted weights', 'ARMATURE')
    ar.object = rig
    solid(ob, 0.008)
    bevel(ob, 0.003)
    return ob
