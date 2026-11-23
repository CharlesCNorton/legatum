"""Rest-view fitting of full-depth geometry, preserving native MPFB weights."""
import bpy
import math
from mathutils import Matrix, Vector
from bpy_extras.object_utils import world_to_camera_view


def refine(sc):
    rig = bpy.data.objects['Phalangite MPFB game_engine']
    body = bpy.data.objects['MPFB anatomical male • original topology']
    if body.data.shape_keys:
        bpy.context.view_layer.objects.active = body
        bpy.ops.object.shape_key_remove(all=True, apply_mix=True)
    assert len(body.data.vertices) == 19158
    # Convert thick curve straps before fitting their actual surfaces.
    for ob in list(sc.objects):
        if ob.type == 'CURVE':
            bpy.ops.object.select_all(action='DESELECT')
            ob.select_set(True)
            bpy.context.view_layer.objects.active = ob
            bpy.ops.object.convert(target='MESH')
    bpy.context.view_layer.update()
    right = sc.camera.matrix_world.to_quaternion() @ Vector((1, 0, 0))
    up = sc.camera.matrix_world.to_quaternion() @ Vector((0, 1, 0))
    unit = sc.camera.data.ortho_scale / 256
    transforms = {b.name: b.matrix @ b.bone.matrix_local.inverted() for b in rig.pose.bones}

    def fit(p, name):
        x, y = p
        if 'shield' in name:
            # Entire bowl, rim and leather remain convex and retain view depth.
            return Vector((116 + (x-119)*.90 + (123-y)*.19, 122+(y-124)*.96))
        if 'helmet' in name or 'bronze-crest' in name:
            # Low swept crest and broader rear bowl instead of a tall peak.
            return Vector((84+(x-85)*1.05, 80+(y-80)*.84))
        q = p.copy()
        # Smooth fitting includes both real anatomy and its fitted sleeves.
        elbow = math.exp(-((x-68)/10)**2-((y-115)/17)**2)
        q += Vector((-16, 3))*elbow
        fist = math.exp(-((x-71)/8)**2-((y-139)/7)**2)
        q += Vector((-4, -1))*fist
        # Widen the source's foreshortened raised forearm across the shield.
        # Only native left-arm weights select it below, not chest geometry.
        if 'left-arm' in name:
            q = p + Vector((19, 13))*math.exp(-((x-94)/14)**2-((y-111)/13)**2)
        if 'sleeve' in name:
            q.y += max(0, 94-y)*.55
        if y < 89 and 'anatomical' in name:
            q.y += 2.0*max(0, min(1, (89-y)/14))
        if 'linothorax' in name or 'shoulder' in name or 'collar' in name:
            q.y += max(0, 91-y)*.60
        if y > 169:
            # Real greaves, ankles, soles and toe straps fit together.
            if x < 82:
                q.x += -3.4*min(1, (y-169)/38)
            else:
                q.x += (x-108)*.40*min(1, (y-169)/37)
            if y > 211:
                q.y -= 2.0*min(1, (y-211)/10)
        if 171 < y < 211:
            center = (58+(198-y)*.28) if x < 82 else (108+(y-190)*.10)
            q.x = center+(q.x-center)*(1+.16*math.sin(math.pi*(y-171)/40))
        if y > 211 and x > 92:
            q.x = 113+(q.x-113)*1.28
        return q

    for ob in list(sc.objects):
        if ob.type != 'MESH' or any(k in ob.name for k in ['base', 'sarissa', 'iron-butt']):
            continue
        skinned = any(m.type == 'ARMATURE' for m in ob.modifiers)
        world = ob.matrix_world.copy()
        for v in ob.data.vertices:
            skin = Matrix.Identity(4)
            groups = {ob.vertex_groups[g.group].name: g.weight for g in v.groups}
            if skinned:
                inf = [(transforms[n], w) for n, w in groups.items() if n in transforms]
                total = sum(w for _, w in inf)
                if total > .001:
                    skin = sum((m*(w/total) for m, w in inf), Matrix(((0,)*4,)*4))
            posed = skin @ v.co
            w = world @ posed
            screen = world_to_camera_view(sc, sc.camera, w)
            p = Vector((screen.x*256, (1-screen.y)*256))
            name = ob.name
            if sum(weight for n, weight in groups.items() if n in ['upperarm_l', 'lowerarm_l', 'hand_l']) > .5:
                name += ' left-arm'
            target = fit(p, name)
            w += right*((target.x-p.x)*unit) - up*((target.y-p.y)*unit)
            if 'left-arm' in name:
                view = sc.camera.matrix_world.to_quaternion() @ Vector((0,0,1))
                w += view*.14*math.exp(-((p.x-108)/20)**2-((p.y-118)/24)**2)
            v.co = skin.inverted_safe() @ (world.inverted() @ w)
        ob.data.update()
    # Match the painting's shallower stone ellipse with a full-depth solid disc.
    base = bpy.data.objects['GEO-stationary-cream-base']
    for vertex in base.data.vertices:
        vertex.co.x *= 1.02
        vertex.co.y *= .82
        vertex.co.z = .045+(vertex.co.z-.045)*.91
        # Top remains at the same supporting height; deepen only the lower rim
        # to match the painting's base bounds after flattening the top ellipse.
        vertex.co.z -= .04*(.045-vertex.co.z)/.09
    base.location.x -= .018
    # Short nape locks have actual round volume and follow the head bone.
    hair=bpy.data.materials.new('Chestnut nape hair');hair.use_nodes=True
    shader=hair.node_tree.nodes.get('Principled BSDF');shader.inputs['Base Color'].default_value=(.18,.08,.022,1);shader.inputs['Roughness'].default_value=.68
    head_world=rig.matrix_world @ rig.pose.bones['head'].head
    view=sc.camera.matrix_world.to_quaternion() @ Vector((0,0,1))
    for k in range(6):
        data=bpy.data.curves.new('Nape lock','CURVE');data.dimensions='3D';data.bevel_depth=.005;data.bevel_resolution=2
        spline=data.splines.new('POLY');spline.points.add(6)
        for j,point in enumerate(spline.points):
            t=j/6;x=76+(k-2.5)*.5-1.0*math.sin(t*math.pi);y=75+t*9
            q=world_to_camera_view(sc,sc.camera,head_world)
            w=head_world+right*((x-q.x*256)*unit)-up*((y-(1-q.y)*256)*unit)-view*(.075+k*.002)
            point.co=(*w,1)
        ob=bpy.data.objects.new('GEO-nape-hair',data);sc.collection.objects.link(ob);data.materials.append(hair)
        bpy.context.view_layer.update();world=ob.matrix_world.copy();ob.parent=rig;ob.parent_type='BONE';ob.parent_bone='head';bpy.context.view_layer.update();ob.matrix_world=world
    # The finished rigid kit, not its unfinished cage, owns frozen paint UVs.
    for ob in list(sc.objects):
        if ob.type != 'MESH' or any(m.type == 'ARMATURE' for m in ob.modifiers):
            continue
        bpy.context.view_layer.objects.active = ob
        for mod in list(ob.modifiers):
            if mod.type in {'SOLIDIFY', 'BEVEL', 'SUBSURF'}:
                bpy.ops.object.modifier_apply(modifier=mod.name)
    # Standard preserves the already painted illumination; physical fill is subdued.
    sc.view_settings.view_transform = 'Standard'
    sc.view_settings.look = 'None'
    for name, power in [('LGT-warm-key', 330), ('LGT-soft-fill', 66), ('LGT-cool-rim', 100)]:
        bpy.data.objects[name].data.energy = power
    bpy.data.objects['LGT-warm-key'].data.color = (1, .96, .87)
    sc['rest_fit'] = 'Full-depth inverse-skin arm, helmet, shield and footwear fitting; native weights retained'
    bpy.context.view_layer.update()
