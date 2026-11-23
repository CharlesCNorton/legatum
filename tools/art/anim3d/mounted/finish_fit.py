"""Small full-depth anatomical corrections after resetting sparse source actions."""
import bpy
from mathutils import Matrix, Vector
from bpy_extras.object_utils import world_to_camera_view
from register import Registration


def finish_fit(scene, horse):
    arm = next(m.object for m in horse.modifiers if m.type=='ARMATURE')
    transforms = {g.index:arm.pose.bones[g.name].matrix @ arm.data.bones[g.name].matrix_local.inverted()
                  for g in horse.vertex_groups if g.name in arm.pose.bones}
    right = scene.camera.matrix_world.to_3x3() @ Vector((1,0,0))
    up = scene.camera.matrix_world.to_3x3() @ Vector((0,1,0))
    scale = scene.camera.data.ortho_scale/256
    for v in horse.data.vertices:
        groups = [(g.weight,transforms[g.group]) for g in v.groups if g.group in transforms and g.weight>0]
        if not groups:
            continue
        total = sum(w for w,m in groups)
        deform = Matrix([[sum(w*m[r][c] for w,m in groups)/total for c in range(4)] for r in range(4)])
        transform = arm.matrix_world @ deform @ arm.matrix_world.inverted() @ horse.matrix_world
        world = transform @ v.co
        q = world_to_camera_view(scene,scene.camera,world)
        y = (1-q.y)*256
        blend = max(0.,min(1.,(y-145)/55))
        blend = blend*blend*(3-2*blend)
        dx = dy = strength = 0.
        for g in v.groups:
            name = horse.vertex_groups[g.group].name
            if name.startswith(('Back','FFB.','IKBack')):
                dx += g.weight*(9 if name.endswith('.R') else 16)
                dy += g.weight*(2 if name.endswith('.R') else 3)
                strength += g.weight
            elif name.startswith(('Front','FF.','IKFront')):
                dx += g.weight*(-6 if name.endswith('.R') else -2)
                dy += g.weight*(-5 if name.endswith('.R') else 0)
                strength += g.weight
        # Offsets grow gradually along the limb; no ambiguous nearest-path fold.
        world += (right*dx-up*dy)*scale*blend
        normal = (transform.to_3x3().inverted().transposed()@v.normal).normalized()
        world += normal*.009*strength*blend
        v.co = transform.inverted()@world
    horse.data.update()
    bpy.context.view_layer.update()
    # Restore the higher poll/arched neck after removing inherited Walk channels.
    neck = Registration(scene,[((174,96),(175,88)),((183,111),(185,109)),
                               ((189,122),(189,121)),((154,134),(154,134)),
                               ((130,150),(130,150))],radius=18)
    for ob in list(scene.objects):
        if ob==horse or (ob.parent==arm and ob.type in {'MESH','CURVE'}):
            neck.object(ob)
    bpy.context.view_layer.update()


def fit_bridle(scene, horse):
    """Solid leather curves sit on the actual muzzle, rather than in open air."""
    evaluated = horse.evaluated_get(bpy.context.evaluated_depsgraph_get())
    inverse = evaluated.matrix_world.inverted()
    normal_matrix = evaluated.matrix_world.to_3x3().inverted().transposed()
    for ob in scene.objects:
        if not ob.name.startswith(('Cheek bridle','Nose band')):
            continue
        old = [ob.matrix_world@p.co.xyz for p in ob.data.splines[0].points]
        data = ob.data
        for spline in list(data.splines):
            data.splines.remove(spline)
        spline = data.splines.new('POLY')
        points = []
        for i in range(len(old)-1):
            for step in range(8):
                point = old[i].lerp(old[i+1],step/8)
                hit,local,normal,_ = evaluated.closest_point_on_mesh(inverse@point)
                if hit:
                    point = evaluated.matrix_world@local+(normal_matrix@normal).normalized()*.009
                points.append(point)
        hit,local,normal,_ = evaluated.closest_point_on_mesh(inverse@old[-1])
        points.append(evaluated.matrix_world@local+(normal_matrix@normal).normalized()*.009 if hit else old[-1])
        spline.points.add(len(points)-1)
        inv = ob.matrix_world.inverted()
        for p,world in zip(spline.points,points):
            p.co = (*(inv@world),1)
        data.bevel_depth = .011
        data.bevel_resolution = 3
    bpy.context.view_layer.update()
