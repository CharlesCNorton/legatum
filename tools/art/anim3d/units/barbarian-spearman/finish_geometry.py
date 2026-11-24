"""Continuous fitted leather and articulated cloth, after the rest-pose rebind."""
import bpy
from mathutils import Matrix, Vector
from mathutils.kdtree import KDTree


def apply():
    rig = bpy.data.objects['Barbarian skeleton']
    body = bpy.data.objects['MPFB barbarian anatomy']
    body_group = body.vertex_groups['body'].index
    visible = {v.index for v in body.data.vertices if any(
        g.group == body_group and g.weight > 0 for g in v.groups)}
    tree = KDTree(len(body.data.vertices))
    for v in body.data.vertices:
        if v.index in visible:
            tree.insert(body.matrix_world @ v.co, v.index)
    tree.balance()

    def bind(ob):
        world = ob.matrix_world.copy()
        ob.parent = rig
        ob.parent_type = 'OBJECT'
        ob.matrix_parent_inverse = Matrix.Identity(4)
        ob.matrix_world = world
        for group in list(ob.vertex_groups):
            ob.vertex_groups.remove(group)
        groups = {g.index: ob.vertex_groups.new(name=g.name) for g in body.vertex_groups}
        for v in ob.data.vertices:
            _, index, _ = tree.find(world @ v.co)
            for g in body.data.vertices[index].groups:
                groups[g.group].add([v.index], g.weight, 'REPLACE')
        mod = ob.modifiers.new('Continuous anatomical skinning', 'ARMATURE')
        mod.object = rig

    # The former rigid calf shell included toes, overlapping a second ankle shoe.
    # One continuous anatomical leather shell now follows the native skin weights.
    shoe_bounds = {}
    for side in ['r', 'l']:
        shoe = bpy.data.objects['Lasted leather shoe ' + side]
        coords = [shoe.matrix_world @ v.co for v in shoe.data.vertices]
        shoe_bounds[side] = [(min(p[k] for p in coords), max(p[k] for p in coords)) for k in range(3)]
    for ob in list(bpy.context.scene.objects):
        if ob.name.startswith(('Leather boot ', 'Lasted leather shoe ', 'Shoe wrap')):
            bpy.data.objects.remove(ob, do_unlink=True)
    for side, sign in [('r', -1), ('l', 1)]:
        selected = [p for p in body.data.polygons if all(
            i in visible and (body.matrix_world @ body.data.vertices[i].co).z < .58
            and (body.matrix_world @ body.data.vertices[i].co).x * sign > 0
            for i in p.vertices)]
        ids = sorted({i for p in selected for i in p.vertices})
        remap = {i: j for j, i in enumerate(ids)}
        verts = [body.matrix_world @ (body.data.vertices[i].co +
                 body.data.vertices[i].normal * .015) for i in ids]
        # Fit the continuous toe/sole to the already reviewed lasted volume.
        toes = [p for p in verts if p.z < .25]
        source_bounds = [(min(p[k] for p in toes), max(p[k] for p in toes)) for k in range(3)]
        for p in verts:
            t = max(0, min(1, (.34-p.z)/.09))
            t = t*t*(3-2*t)
            for k, ((lo, hi), (a, b)) in enumerate(zip(source_bounds, shoe_bounds[side])):
                target = a + (p[k]-lo)/(hi-lo)*(b-a)
                p[k] += (target-p[k])*t
        mesh = bpy.data.meshes.new('Continuous leather ankle ' + side)
        mesh.from_pydata(verts, [], [[remap[i] for i in p.vertices] for p in selected])
        mesh.update()
        ob = bpy.data.objects.new('Lasted leather shoe ' + side, mesh)
        bpy.context.collection.objects.link(ob)
        mesh.materials.append(bpy.data.materials['Scuffed hide leather'])
        for p in mesh.polygons:
            p.use_smooth = True
        bind(ob)
        # Preserve source weights through the toe fitting, rather than snapping
        # the reshaped forefoot to a possibly different nearest joint.
        for g in ob.vertex_groups:
            g.remove(list(range(len(verts))))
        for j, index in enumerate(ids):
            for g in body.data.vertices[index].groups:
                ob.vertex_groups[g.group].add([j], g.weight, 'REPLACE')
        mod = ob.modifiers.new('Leather thickness', 'SOLIDIFY')
        mod.thickness = .006
        mod = ob.modifiers.new('Supple leather', 'SUBSURF')
        mod.levels = mod.render_levels = 1
    for ob in list(bpy.context.scene.objects):
        if ob.type == 'MESH' and ob.name.startswith(('Crossed calf bindings', 'Hide breeches')):
            bind(ob)
    # The skirt must follow the hips and legs, rather than remain a rigid bell.
    skirt = bpy.data.objects['Torn folded linen skirt']
    bind(skirt)
    for g in skirt.vertex_groups:
        g.remove(list(range(len(skirt.data.vertices))))
    for v in skirt.data.vertices:
        p = skirt.matrix_world @ v.co
        hem = max(0, min(1, (1.06-p.z)/.32))
        hem = hem*hem*(3-2*hem)*.30
        left = max(0, min(1, .5+p.x/.45))
        left = left*left*(3-2*left)
        for name, weight in [('pelvis', 1-hem), ('thigh_l', hem*left), ('thigh_r', hem*(1-left))]:
            skirt.vertex_groups[name].add([v.index], weight, 'REPLACE')
    bpy.context.view_layer.update()
    bpy.context.scene['footwear'] = 'Continuous MPFB-weighted leather; no calf-attached duplicate toes'
