"""Bind the fitted costume at its real joints before retargeting open motion.

The earlier screen-only shoe fit moved the mesh far behind the skeletal ankle.
Preserve the painted rest silhouette, connect the stockings in depth, and move
the bind pivots to those joints. This is rest calibration, never motion editing.
"""
import bpy
import math
from mathutils import Vector


def calibrate(rig):
    scene = bpy.context.scene
    # Flush the fitted base location/scale before reading its matrix. Otherwise
    # assigning matrix_world below would silently restore the old disc placement.
    bpy.context.view_layer.update()
    # The orthographic reference does not constrain depth. Move the disc and
    # shoes together along camera rays so the shins have anatomical lengths,
    # with exactly the same screen silhouette and sole-to-stone contact.
    ray = scene.camera.matrix_world.to_quaternion() @ Vector((0, 0, -1))
    depth_shift = ray * (-.24 / ray.y)
    for o in scene.objects:
        if 'shoe' in o.name or o.name == 'GEO-stationary cream base':
            world = o.matrix_world.copy()
            world.translation += depth_shift
            o.matrix_world = world
    bpy.context.view_layer.update()
    attachments = {o: o.matrix_world.copy() for o in scene.objects if o.parent == rig}
    skinned = []
    for o in scene.objects:
        if o.type != 'MESH':
            continue
        arm = next((m for m in o.modifiers if m.type == 'ARMATURE' and m.object == rig), None)
        if not arm:
            continue
        others = [m for m in o.modifiers if m != arm and m.show_viewport]
        for m in others:
            m.show_viewport = False
        bpy.context.view_layer.update()
        ev = o.evaluated_get(bpy.context.evaluated_depsgraph_get())
        me = ev.to_mesh()
        assert len(me.vertices) == len(o.data.vertices), o.name
        fitted = [v.co.copy() for v in me.vertices]
        ev.to_mesh_clear()
        for v, co in zip(o.data.vertices, fitted):
            v.co = co
        for m in others:
            m.show_viewport = True
        arm.show_viewport = False
        skinned.append(arm)
    bpy.ops.object.select_all(action='DESELECT')
    rig.select_set(True)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='POSE')
    bpy.ops.pose.armature_apply(selected=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    for o, world in attachments.items():
        o.matrix_world = world
    bpy.context.view_layer.update()

    joints = {}
    inv = rig.matrix_world.inverted()
    for side in ('l', 'r'):
        shoe = bpy.data.objects['GEO-latchet shoe '+side]
        points = [shoe.matrix_world @ v.co for v in shoe.data.vertices]
        center = sum(points, Vector()) / len(points)
        ankle = center + Vector((-.025 if side == 'l' else 0, .025, .035))
        # Calibrate the actual shoe's heel-to-toe direction, not a guessed yaw.
        # The fitted rest silhouette stays fixed; source motion rotates this bind
        # axis into travel direction without any post-retarget foot correction.
        local_y = [v.co.y for v in shoe.data.vertices]
        low_y, high_y = min(local_y), max(local_y)
        toe_indices = [v.index for v in shoe.data.vertices if v.co.y < low_y+.20*(high_y-low_y)]
        heel_indices = [v.index for v in shoe.data.vertices if v.co.y > high_y-.20*(high_y-low_y)]
        toe_center = sum((points[i] for i in toe_indices), Vector())/len(toe_indices)
        heel_center = sum((points[i] for i in heel_indices), Vector())/len(heel_indices)
        axis = toe_center-heel_center
        axis.z = 0
        axis.normalize()
        toe = ankle+axis*.14+Vector((0,0,-.07))
        shoe['toe_vertices'] = toe_indices
        shoe['heel_vertices'] = heel_indices
        stocking = bpy.data.objects['GEO-ivory stocking '+side]
        vertices = [stocking.matrix_world @ v.co for v in stocking.data.vertices]
        low, high = min(v.z for v in vertices), max(v.z for v in vertices)
        bottom = [v for v in vertices if v.z < low+.025]
        old = sum(bottom, Vector()) / len(bottom)
        displacement = ankle-old
        for v, world in zip(stocking.data.vertices, vertices):
            weight = max(0, min(1, (high-world.z)/(high-low)))
            v.co += stocking.matrix_world.to_3x3().inverted() @ (displacement*weight)
        joints[side] = (inv @ ankle, inv @ toe)

    # Change only the bind joints; rendered attachments retain their rest matrices.
    bpy.ops.object.mode_set(mode='EDIT')
    for side, (ankle, toe) in joints.items():
        calf, foot, ball = [rig.data.edit_bones[n+'_'+side] for n in ('calf', 'foot', 'ball')]
        foot.use_connect = ball.use_connect = False
        calf.tail = ankle
        foot.head, foot.tail = ankle, toe
        ball.head = toe
        ball.tail = toe + (toe-ankle).normalized()*.065
    bpy.ops.object.mode_set(mode='OBJECT')
    for arm in skinned:
        arm.show_viewport = True
    for o, world in attachments.items():
        o.matrix_world = world
    bpy.context.view_layer.update()

    # The closed trousers/stockings/shoes replace covered anatomy in the render;
    # retain native vertices/weights for editing, without exposed duplicate toes.
    body = bpy.data.objects['GEO-MPFB arquebusier anatomy']
    group = body.vertex_groups.new(name='Visible anatomy above closed leg clothing')
    keep = []
    for v in body.data.vertices:
        covered = sum(g.weight for g in v.groups if body.vertex_groups[g.group].name.startswith(('thigh_', 'calf_', 'foot_', 'ball_')))
        if covered < .5:
            keep.append(v.index)
    group.add(keep, 1, 'REPLACE')
    mask = body.modifiers.new('Covered leg anatomy mask', 'MASK')
    mask.vertex_group = group.name
    # Place the mask before subdivision to avoid stray generated toe fragments.
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.modifier_move_up(modifier=mask.name)
    # A continuous gathered knee panel bridges the two rigid garment segments.
    # Blend its weights across the joint so flexion cannot expose a hollow tube.
    for side in ('l', 'r'):
        thigh, calf = [rig.data.bones[n+'_'+side] for n in ('thigh', 'calf')]
        a = thigh.tail_local.lerp(thigh.head_local, .20)
        b = calf.head_local.lerp(calf.tail_local, .20)
        axis = (b-a).normalized()
        u = axis.cross(Vector((0, 1, 0))).normalized()
        v = axis.cross(u).normalized()
        verts, faces = [], []
        for j in range(13):
            t = j/12
            radius = .081-.010*t + .003*math.sin(t*math.pi*5)
            for k in range(48):
                angle = 2*math.pi*k/48
                fold = 1+.035*math.cos(angle*8+t*2)
                verts.append(a.lerp(b, t)+(u*math.cos(angle)+v*math.sin(angle))*radius*fold)
        for j in range(12):
            for k in range(48):
                i = j*48+k
                n = j*48+(k+1)%48
                faces.append((i, n, n+48, i+48))
        mesh = bpy.data.meshes.new('Gathered knee joint '+side)
        mesh.from_pydata(verts, [], faces)
        mesh.update()
        o = bpy.data.objects.new('GEO-gathered knee joint '+side, mesh)
        scene.collection.objects.link(o)
        o.parent = rig
        o.matrix_world = rig.matrix_world.copy()
        material = bpy.data.objects[('GEO-ivory stocking ' if side == 'l' else 'GEO-red knee garter ')+side].data.materials[0]
        o.data.materials.append(material)
        upper = o.vertex_groups.new(name='thigh_'+side)
        lower = o.vertex_groups.new(name='calf_'+side)
        for j in range(13):
            t = j/12
            w = t*t*(3-2*t)
            indices = list(range(j*48, (j+1)*48))
            upper.add(indices, 1-w, 'REPLACE')
            lower.add(indices, w, 'REPLACE')
        arm = o.modifiers.new('Continuous knee tailoring', 'ARMATURE')
        arm.object = rig
        thickness = o.modifiers.new('Woven cloth thickness', 'SOLIDIFY')
        thickness.thickness = .004
        for p in mesh.polygons:
            p.use_smooth = True
    return {side: {'ankle': list(a), 'toe': list(t)} for side, (a, t) in joints.items()}
