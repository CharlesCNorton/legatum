"""Rest-space horse/tack sculpture on the clean fitted checkpoint.

All corrections move real vertices with depth retained and invert the existing
skin transform. The original CC0 skeleton and animation remain editable.
"""
import math
import bpy
from mathutils import Matrix, Vector
from bpy_extras.object_utils import world_to_camera_view


def finish(sc):
    horse = bpy.data.objects['Horse']
    arm = bpy.data.objects['AnimalArmature']
    right = sc.camera.matrix_world.to_quaternion() @ Vector((1, 0, 0))
    up = sc.camera.matrix_world.to_quaternion() @ Vector((0, 1, 0))
    unit = sc.camera.data.ortho_scale / 256

    def project(w):
        p = world_to_camera_view(sc, sc.camera, w)
        return p.x * 256, (1-p.y) * 256

    def move(w, dx, dy):
        return w + (right*dx-up*dy)*unit

    # Remove the source's broad ivory patches; the painting supplies its own
    # narrow blaze and fetlock pigments. Retain the dark horn material.
    for face in horse.data.polygons:
        if face.material_index == 8:
            face.material_index = 0
    to_arm = arm.matrix_world.inverted() @ horse.matrix_world
    transforms = {p.name: to_arm.inverted() @ p.matrix @ p.bone.matrix_local.inverted() @ to_arm
                  for p in arm.pose.bones}
    tail_targets = [(88, 121), (77, 125), (69, 133), (64, 142),
                    (58, 150), (52, 157), (46, 164)]
    tail_delta = {}
    for i, target in enumerate(tail_targets, 1):
        name = f'Tail{i}'
        p = project(arm.matrix_world @ arm.pose.bones[name].head)
        tail_delta[name] = (target[0]-p[0], target[1]-p[1])
    for v in horse.data.vertices:
        weights = {horse.vertex_groups[g.group].name: g.weight for g in v.groups
                   if horse.vertex_groups[g.group].name in transforms}
        total = sum(weights.values())
        skin = sum((transforms[n]*(w/total) for n,w in weights.items()),
                   Matrix(((0,)*4,)*4)) if total else Matrix.Identity(4)
        world = horse.matrix_world @ (skin @ v.co)
        x, y = project(world)
        def gaussian(cx, cy, rx, ry):
            return math.exp(-((x-cx)/rx)**2-((y-cy)/ry)**2)
        # Lower/round the croup and match the muzzle; native legs stay intact.
        rump = gaussian(82, 111, 24, 30)
        head = gaussian(194, 82, 23, 33)
        muzzle = gaussian(204, 102, 15, 18)
        dx, dy = 9*rump-2*head, 17*rump+10*head+10*muzzle
        # Preserve the native articulated leg volumes. Projected rest-view
        # corrections displaced flesh far from its joints and pinched in motion.
        limb_weight=sum(w for n,w in weights.items() if any(k in n for k in ('Leg','Shoulder','FF')))
        dx*=1-min(1,limb_weight);dy*=1-min(1,limb_weight)
        # Tail is fitted by its actual weighted chain, not a nearby leg mask.
        tail_weight = sum(w for n,w in weights.items() if n in tail_delta)
        if tail_weight:
            tx = sum(tail_delta[n][0]*w for n,w in weights.items() if n in tail_delta)/total
            ty = sum(tail_delta[n][1]*w for n,w in weights.items() if n in tail_delta)/total
            dx = dx*(1-tail_weight/total)+tx
            dy = dy*(1-tail_weight/total)+ty
        world = move(world, dx, dy)
        v.co = skin.inverted_safe() @ (horse.matrix_world.inverted() @ world)
    horse.data.update()
    bpy.context.view_layer.update()
    from contacts import fit_rest_contacts
    fit_rest_contacts()

    # Fit the real leather to the muzzle instead of the old oversized snout.
    targets = {
        'Cheek bridle': [(180, 78), (189, 94), (197, 119)],
        'Cheek bridle.001': [(187, 77), (196, 94), (202, 117)],
        'Nose band': [(197, 119), (205, 116)],
        'Nose band.001': [(202, 117), (205, 116)],
        'GEO-steel-stirrup': [(111, 153), (108, 160), (118, 162), (121, 154), (111, 153)],
        'GEO-steel-stirrup.001': [(133, 139), (132, 146), (139, 147), (140, 140), (133, 139)],
        'GEO-stirrup-leather': [(123, 111), (113, 154)],
        'GEO-stirrup-leather.001': [(145, 104), (137, 140)],
    }
    for name, pixels in targets.items():
        ob = bpy.data.objects[name]
        points = ob.data.splines[0].points
        assert len(points) == len(pixels), name
        for p, target in zip(points, pixels):
            w = ob.matrix_world @ p.co.xyz
            x, y = project(w)
            p.co = (*(ob.matrix_world.inverted() @ move(w, target[0]-x, target[1]-y)), 1)
        ob.data.bevel_depth *= .65
    for ob in sc.objects:
        if ob.type == 'CURVE' and ob.name.startswith(('Leather breast strap', 'Saddle girth', 'Slack leather rein')):
            ob.data.bevel_depth *= .65

    for name,target in [('Bronze bridle rosette',(188,94)),('Bronze bridle rosette.001',(195,93))]:
        ob=bpy.data.objects[name];w=ob.matrix_world.translation.copy();x,y=project(w)
        matrix=ob.matrix_world.copy();matrix.translation=move(w,target[0]-x,target[1]-y);ob.matrix_world=matrix

    # Tapered solid hair locks follow the source tail bones. Each tube carries
    # skin weights through its whole length; no rigid billboard or alpha card.
    verts, faces, skin_weights = [], [], []
    for strand in range(13):
        spread = (strand-6)/6
        for j in range(25):
            t = j/24
            index = min(5, int(t*6)); a = t*6-index
            x = tail_targets[index][0]*(1-a)+tail_targets[index+1][0]*a
            y = tail_targets[index][1]*(1-a)+tail_targets[index+1][1]*a
            x += spread*(3+7*math.sin(math.pi*t)) + 1.5*math.sin(t*9+strand)*t
            y += spread*2*t
            bone = arm.pose.bones[f'Tail{index+1}']
            center = arm.matrix_world @ bone.head
            px, py = project(center)
            center = move(center, x-px, y-py)
            # Move toward camera so the fine locks sit on the visible surface.
            center += (sc.camera.location-center).normalized()*(.018+abs(spread)*.006)
            radius = .010*(1-.92*t)
            for k in range(6):
                angle = k*math.tau/6
                world = center + right*(radius*math.cos(angle)) + (right.cross(up))*(radius*math.sin(angle))
                weights = {f'Tail{index+1}': 1-a, f'Tail{index+2}': a}
                blend = sum((transforms[n]*w for n,w in weights.items()), Matrix(((0,)*4,)*4))
                verts.append(blend.inverted_safe() @ (horse.matrix_world.inverted() @ world))
                skin_weights.append(weights)
            if j:
                start = len(verts)-12
                for k in range(6):
                    faces.append((start+k, start+(k+1)%6, start+6+(k+1)%6, start+6+k))
        start = strand*25*6
        faces.extend([tuple(start+k for k in reversed(range(6))), tuple(start+24*6+k for k in range(6))])
    me=bpy.data.meshes.new('Swept weighted tail locks');me.from_pydata(verts,[],faces);me.update()
    ob=bpy.data.objects.new('GEO-swept-tail-locks',me);sc.collection.objects.link(ob)
    ob.parent=horse.parent;ob.parent_type=horse.parent_type
    ob.matrix_parent_inverse=horse.matrix_parent_inverse.copy();ob.matrix_basis=horse.matrix_basis.copy()
    me.materials.append(bpy.data.materials['Black mane and tail'])
    for i,weights in enumerate(skin_weights):
        for name,w in weights.items():
            group=ob.vertex_groups.get(name) or ob.vertex_groups.new(name=name)
            group.add([i],w,'REPLACE')
    mod=ob.modifiers.new('Original CC0 tail motion','ARMATURE');mod.object=arm
    for face in me.polygons:face.use_smooth=True
    bpy.context.view_layer.update()
