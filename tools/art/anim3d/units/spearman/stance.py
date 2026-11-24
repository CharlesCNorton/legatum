"""Fable B spear-side cloak fit; lower-body scaling was rejected at merge."""
import bpy
from mathutils import Vector


def flare_cloak(scene, screen_sculpt):
    """Spear-side cloak edge: the painting's wool hangs outside the spear arm
    from the elbow to the knee and lower between the legs. Screen-space fit in
    the guard pose, returned through each vertex's blended skin transform (the
    round-9a method), before the painting UVs are frozen."""
    from bpy_extras.object_utils import world_to_camera_view
    from mathutils import Matrix
    rig = bpy.data.objects['Spearman • MPFB game_engine']
    transforms = {b.name: b.matrix @ b.bone.matrix_local.inverted() for b in rig.pose.bones}
    ob = bpy.data.objects['Cloak • simulated wool']
    count = 0
    for vertex in ob.data.vertices:
        influences = [(transforms[ob.vertex_groups[g.group].name], g.weight) for g in vertex.groups
                      if ob.vertex_groups[g.group].name in transforms]
        total = sum(w for _, w in influences)
        if total < .001:
            continue
        skin = sum((m*(w/total) for m, w in influences), Matrix(((0,)*4,)*4))
        posed = skin @ vertex.co
        camera = world_to_camera_view(scene, scene.camera, ob.matrix_world @ posed)
        p = Vector((camera.x*256, (1-camera.y)*256))
        smooth = lambda a, b, x: (lambda t: t*t*(3-2*t))(max(0., min(1., (x-a)/(b-a))))
        # Left (spear-side) edge: widest at hip height, fading at shoulder and hem.
        edge = smooth(124, 104, p.x)*smooth(108, 140, p.y)*(1-.5*smooth(185, 215, p.y))
        # Centre hem between the legs hangs about four pixels lower.
        hem = smooth(120, 135, p.x)*(1-smooth(150, 166, p.x))*smooth(170, 195, p.y)
        delta = Vector((-6.0*edge, 4.0*hem))
        if delta.length < .01:
            continue
        vertex.co = skin.inverted_safe() @ screen_sculpt(ob, posed, p+delta)
        count += 1
    ob.data.update()
    bpy.context.view_layer.update()
    print('CLOAK_FLARE_FABLE_B', count, 'vertices')
