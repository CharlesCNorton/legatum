"""Fit full-depth geometry before frozen projection; restart from plain build."""
import math
import bpy
from mathutils import Matrix, Vector
from bpy_extras.object_utils import world_to_camera_view


def refine(sc):
    rig = bpy.data.objects['RIG-barbarian-archer']
    from common import pose
    pose(rig)
    from garments import clean_regions
    clean_regions()
    from footwear import close_toes
    close_toes()
    camera = sc.camera
    right = camera.matrix_world.to_quaternion() @ Vector((1, 0, 0))
    up = camera.matrix_world.to_quaternion() @ Vector((0, 1, 0))
    pixel = camera.data.ortho_scale / 256

    def screen(v):
        p = world_to_camera_view(sc, camera, v)
        return Vector((p.x * 256, (1-p.y)*256))

    def fit(v):
        p = screen(v)
        # Smooth displacement of real anatomy and all enclosing kit, retaining depth.
        dx = dy = 0
        for x, y, sx, sy, radius in [(149,175,-8,-7,25), (83,180,0,-7,21),
                                     (173,216,-5,-2,15), (105,77,-5,1,17),
                                     (150,75,0,7,14), (183,62,-1,7,11), (73,221,-5,-8,11)]:
            weight = math.exp(-((p.x-x)**2+(p.y-y)**2)/(radius*radius))
            dx += sx*weight
            dy += sy*weight
        return v + pixel*(right*dx-up*dy)

    # Curved quiver surfaces need the same frozen painting UVs as the clothing.
    for o in list(sc.objects):
        if o.type=='CURVE' and ('quiver' in o.name.lower() or 'Spare arrow' in o.name):
            bpy.ops.object.select_all(action='DESELECT');o.select_set(True)
            bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')

    for o in list(sc.objects):
        if o.type != 'MESH' or 'Stationary' in o.name or 'Arrowhead' in o.name:
            continue
        if o.data.shape_keys:
            mixed = o.shape_key_add(name='Frozen macro mix', from_mix=True)
            coords = [v.co.copy() for v in mixed.data]
            o.shape_key_clear()
            for v, co in zip(o.data.vertices, coords):
                v.co = co
        arm = next((m for m in o.modifiers if m.type == 'ARMATURE'), None)
        matrices = {}
        if arm:
            for group in o.vertex_groups:
                if group.name in rig.pose.bones:
                    pb = rig.pose.bones[group.name]
                    matrices[group.index] = (o.matrix_world.inverted() @ rig.matrix_world @
                        pb.matrix @ pb.bone.matrix_local.inverted() @
                        rig.matrix_world.inverted() @ o.matrix_world)
        for v in o.data.vertices:
            transform = Matrix.Identity(4)
            if arm:
                weights = [(g.weight, matrices[g.group]) for g in v.groups if g.group in matrices]
                total = sum(w for w, _ in weights)
                if total:
                    transform = sum((mat*(w/total) for w, mat in weights), Matrix(((0,)*4,)*4))
            posed = o.matrix_world @ transform @ v.co
            fitted = fit(posed)
            if o.name=='GEO-MPFB-anatomy':
                hand_weight=sum(g.weight for g in v.groups
                    if o.vertex_groups[g.group].name.endswith('_l') and
                    o.vertex_groups[g.group].name.split('_')[0] in
                    ('hand','thumb','index','middle','ring','pinky'))
                if hand_weight:
                    p=screen(fitted)
                    # Register the full-depth native palm/fingers, not a painted
                    # replacement hand. Skin weights and camera depth survive.
                    fitted+=pixel*min(1,hand_weight)*(right*((180-p.x)*.28)-up*((p.y-70)*.18))
            if o.name=='GEO-Boots' or o.name.startswith('GEO-Boot toe cap') or o.name=='GEO-MPFB-anatomy':
                p=screen(fitted)
                for x,y,dx,dy in [(72,217,2,-1.5),(170,218,-1.5,-1)]:
                    w=math.exp(-((p.x-x)**2+(p.y-y)**2)/64)
                    fitted+=pixel*w*(right*dx-up*dy)
            if 'Wolf muzzle' in o.name or 'Wolf nose' in o.name:
                fitted += pixel*(-right*7+up*5)
            elif o.name=='GEO-Wolf pointed ear.001':
                fitted += pixel*(-right*5-up*5)
            v.co = transform.inverted_safe() @ o.matrix_world.inverted() @ fitted
        o.data.update()
    # Keep boot lacing on the same fitted calf surfaces.
    for o in sc.objects:
        if o.type == 'CURVE' and 'Boot wrapped' in o.name:
            inverse = o.matrix_world.inverted()
            for spline in o.data.splines:
                for p in spline.points:
                    p.co = (*(inverse @ fit(o.matrix_world @ Vector(p.co[:3]))), 1)

    # Put the full-depth quiver and separate fletchings at the painted hip.
    for o in sc.objects:
        if 'Spare arrow' not in o.name and 'quiver' not in o.name.lower():
            continue
        inverse=o.matrix_world.inverted()
        for v in o.data.vertices:
            world=o.matrix_world@v.co;p=screen(world)
            dx=(p.y-131)*-.28-10 if 'Spare arrow' in o.name else 0
            v.co=inverse@(world+pixel*(right*dx-up*18))

    bow = bpy.data.objects['GEO-Bow stave']
    points = bow.data.splines[0].points
    grip = bow.matrix_world @ Vector(points[len(points)//2].co[:3])
    grip_screen = screen(grip)
    # Catmull-Rom samples of the actual painted stave, two halves share the grip.
    lower = [(166,140),(165,135),(170,126),(177,116),(183,103),(185,91),(183,79),(182,68)]
    upper = [(182,68),(179,54),(174,40),(164,29),(150,22),(138,15),(136,12)]
    def sample(nodes, t):
        f = min(t*(len(nodes)-1), len(nodes)-1-1e-8)
        k = int(f); u = f-k
        a,b,c,d = [Vector(nodes[max(0,min(len(nodes)-1,i))]) for i in (k-1,k,k+1,k+2)]
        return .5*((2*b)+(-a+c)*u+(2*a-5*b+4*c-d)*u*u+(-a+3*b-3*c+d)*u*u*u)
    inv = bow.matrix_world.inverted()
    for i,p in enumerate(points):
        q = sample(lower,i/32) if i <= 32 else sample(upper,(i-32)/32)
        q += grip_screen-Vector((182,68))
        world = grip+pixel*(right*(q.x-grip_screen.x)-up*(q.y-grip_screen.y))
        p.co = (*(inv @ world),1)
    bow.data.bevel_depth = .008
    bpy.data.objects['GEO-Bowstring'].data.bevel_depth = .0009
    sync_weapon()
    # Standard preserves projected painted illumination. Physical lights are reduced
    # accordingly; this is a painted asset, not a photographic color preset.
    for name,power in [('key',440),('fill',88),('rim',108)]:
        bpy.data.objects['LGT-'+name].data.energy = power
    bpy.data.objects['LGT-key'].data.color = (1,.95,.86)
    base = bpy.data.objects['GEO-Stationary cream base']
    base.modifiers['Rounded edges'].segments = 5
    base.modifiers['Rounded edges'].width = .006
    sc['round2_finished_projection'] = True
    bpy.context.view_layer.update()


def sync_weapon():
    """Use the same endpoints and arrow direction at rest as the keyed clips."""
    rig = bpy.data.objects['RIG-barbarian-archer']
    bow = bpy.data.objects['GEO-Bow stave']
    points = bow.data.splines[0].points
    grip = bow.matrix_world @ Vector(points[len(points)//2].co[:3])
    nock = rig.matrix_world @ rig.pose.bones['hand_r'].tail+Vector((.02,-.015,.012))
    ends = [bow.matrix_world @ Vector(points[i].co[:3]) for i in (0,-1)]
    for p,v in zip(bpy.data.objects['GEO-Bowstring'].data.splines[0].points,[ends[0],nock,ends[1]]):
        p.co = (*v,1)
    direction = (grip-nock).normalized()
    end = grip+direction*.15
    for p,v in zip(bpy.data.objects['GEO-Nocked arrow'].data.splines[0].points,[nock,end]):
        p.co = (*v,1)
    tip = bpy.data.objects['GEO-Arrowhead']
    tip.location = end
    tip.rotation_euler = Vector((1,0,0)).rotation_difference(direction).to_euler()
    bpy.context.view_layer.update()
