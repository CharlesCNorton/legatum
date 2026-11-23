"""Fit full-depth anatomy in the rest view, retaining both rigs and skin weights.

Called on the clean unpainted checkpoint, never on an already fitted master.
The smooth field changes mesh coordinates, not texture coordinates or alpha.
"""
import bpy
import bmesh
import numpy as np
from mathutils import Matrix, Vector
from bpy_extras.object_utils import world_to_camera_view


def refine(sc):
    rider = bpy.data.objects['Rider MPFB game_engine']
    # Height-only garment extraction accidentally included the hands. Use the
    # original MPFB weights to cut the sleeve at the wrist, exposing real fingers.
    jacket=bpy.data.objects['GEO-navy-jacket']
    hand_ids={v.index for v in jacket.data.vertices if sum(g.weight for g in v.groups if jacket.vertex_groups[g.group].name.startswith(('hand_', 'thumb_', 'index_', 'middle_', 'ring_', 'pinky_')))>.65}
    bm=bmesh.new();bm.from_mesh(jacket.data);bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm,geom=[bm.verts[i] for i in hand_ids],context='VERTS')
    bm.to_mesh(jacket.data);bm.free()
    horse = bpy.data.objects['Horse']
    # Fit a smooth bind surface, not long low-poly edges across a nonlinear field.
    bpy.context.view_layer.objects.active = horse
    arms = [m for m in horse.modifiers if m.type == 'ARMATURE']
    for m in arms:m.show_viewport = False
    for m in list(horse.modifiers):
        if m.type == 'SUBSURF':bpy.ops.object.modifier_apply(modifier=m.name)
    for m in arms:m.show_viewport = True
    bpy.context.view_layer.update()
    # Measured token landmarks: source model -> original painting (256px).
    rider_pairs = [((90, 64), (80, 55)), ((106, 69), (100, 66)),
                   ((121, 74), (123, 66)), ((133, 47), (140, 46)),
                   ((140, 90), (138, 89)), ((168, 93), (153, 96)),
                   ((126, 119), (121, 116)), ((132, 137), (120, 133)),
                   ((121, 170), (112, 161)), ((100, 120), (100, 120)),
                   ((140, 10), (131, 14))]
    horse_pairs = [((192, 77), (183, 84)), ((213, 107), (202, 115)),
                   ((187, 63), (182, 73)), ((173, 110), (169, 111)),
                   ((158, 145), (164, 146)), ((126, 141), (126, 145)),
                   ((88, 113), (92, 125)), ((83, 160), (92, 164)),
                   ((71, 201), (103, 211)), ((108, 209), (112, 215)),
                   ((148, 202), (149, 190)), ((174, 215), (195, 216)),
                   ((176, 177), (182, 179)), ((71, 141), (62, 145)),
                   ((70, 159), (51, 164))]
    def field(pairs, radius):
        a = np.array([a for a, b in pairs], dtype=float)
        delta = np.array([b for a, b in pairs], dtype=float)-a
        kernel = np.exp(-np.sum((a[:, None]-a[None, :])**2, axis=2)/radius**2)
        weights = np.linalg.solve(kernel+np.eye(len(a))*.025, delta)
        def fit(p):
            return np.clip(np.exp(-np.sum((a-np.array(p))**2, axis=1)/radius**2) @ weights, -18, 18)
        return fit
    def horse_fit(p):
        x,y=p
        def g(cx,cy,rx,ry):return np.exp(-((x-cx)/rx)**2-((y-cy)/ry)**2)
        # Bounded local shape changes avoid the oscillation of a global fit in
        # the sparse, widely separated hind-leg landmarks.
        head=g(200,85,28,36);rear=g(76,198,19,30);front=g(177,214,15,35)
        return (-8*head+14*rear+17*front, 4*head+5*rear)
    fields = [horse_fit, field(rider_pairs, 22)]
    right = sc.camera.matrix_world.to_quaternion() @ Vector((1, 0, 0))
    up = sc.camera.matrix_world.to_quaternion() @ Vector((0, 1, 0))
    unit = sc.camera.data.ortho_scale/256
    def is_rider(ob):
        while ob:
            if ob == rider:return True
            ob = ob.parent
        return False
    records = []
    for ob in list(sc.objects):
        if ob.type not in {'MESH', 'CURVE'} or ob.name == 'Stationary cream stone':continue
        human = is_rider(ob)
        if ob.type == 'MESH' and ob.data.shape_keys:
            bpy.context.view_layer.objects.active = ob
            bpy.ops.object.shape_key_remove(all=True, apply_mix=True)
        arm = next((m.object for m in ob.modifiers if m.type == 'ARMATURE'), None)
        transforms = {}
        if arm:
            to_arm = arm.matrix_world.inverted() @ ob.matrix_world
            transforms = {b.name: to_arm.inverted() @ b.matrix @ b.bone.matrix_local.inverted() @ to_arm for b in arm.pose.bones}
        def fitted(co, groups=()):
            skin = Matrix.Identity(4)
            influences = [(transforms[ob.vertex_groups[g.group].name], g.weight) for g in groups if ob.vertex_groups[g.group].name in transforms]
            total = sum(w for m, w in influences)
            if total > .001:skin = sum((m*(w/total) for m,w in influences), Matrix(((0,)*4,)*4))
            world = ob.matrix_world @ (skin @ co)
            q = world_to_camera_view(sc, sc.camera, world)
            px, py = q.x*256, (1-q.y)*256
            dx, dy = fields[int(human)]((px, py))
            if ob.name.startswith('GEO-stirrup') or ob.name.startswith('GEO-steel-stirrup'):
                weight=max(0,min(1,(py-130)/25))
                dx,dy=-15*weight,-12*weight
            if ob.name.startswith('GEO-sabre'):
                x, y = px-90, py-64
                dx, dy = 80+.866*x-.095*y-px, 55+.095*x+.866*y-py
            world += (right*float(dx)-up*float(dy))*unit
            return skin.inverted_safe() @ (ob.matrix_world.inverted() @ world)
        if ob.type == 'MESH':
            for v in ob.data.vertices:v.co = fitted(v.co, v.groups)
            ob.data.update()
        else:
            for spline in ob.data.splines:
                for p in spline.points:p.co = (*fitted(p.co.xyz), p.co.w)
                for p in spline.bezier_points:
                    p.co = fitted(p.co);p.handle_left = fitted(p.handle_left);p.handle_right = fitted(p.handle_right)
        records.append(ob.name)
    # Finish rigid surfaces before sampling projection. Deforming anatomy retains
    # native weights and subdivision; paint.py samples its evaluated rest surface.
    bpy.ops.object.select_all(action='DESELECT')
    for ob in list(sc.objects):
        if ob.type != 'MESH' or any(m.type == 'ARMATURE' for m in ob.modifiers):continue
        bpy.context.view_layer.objects.active = ob;ob.select_set(True)
        for mod in list(ob.modifiers):
            if mod.type in {'SOLIDIFY', 'BEVEL', 'SUBSURF'}:bpy.ops.object.modifier_apply(modifier=mod.name)
        ob.select_set(False)
    bpy.context.view_layer.update()
    from tack import reins
    reins()
    return {'method':'smooth rest-view full-depth mesh fitting, inverse linear skin transforms',
            'rider_landmarks':rider_pairs, 'horse_landmarks':horse_pairs, 'objects':records,
            'limitation':'Anatomical and camera fit is approximate; original bone pivots retained.'}
