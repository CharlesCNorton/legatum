"""Fit full-depth rest geometry, preserving camera depth and native skin weights."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import *
from bpy_extras.object_utils import world_to_camera_view


def refine():
    sc = bpy.context.scene
    rig = bpy.data.objects['Archer MPFB rig']
    cam = sc.camera
    right = cam.matrix_world.to_quaternion() @ Vector((1, 0, 0))
    up = cam.matrix_world.to_quaternion() @ Vector((0, 1, 0))
    unit = cam.data.ortho_scale / 256
    def screen(v):
        q = world_to_camera_view(sc, cam, v)
        return Vector((q.x * 256, (1-q.y) * 256))
    def move(v, delta):
        return v + right * delta.x * unit - up * delta.y * unit
    records = []
    dynamic = ('GEO-Yew bow', 'GEO-Bow belly highlight', 'GEO-Bowstring', 'GEO-Nocked arrow')
    for obj in list(sc.objects):
        if obj.type not in {'MESH', 'CURVE'} or obj.name in dynamic:
            continue
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        if obj.type == 'CURVE':
            bpy.ops.object.convert(target='MESH')
        arms = [m for m in obj.modifiers if m.type == 'ARMATURE']
        for m in arms:
            m.show_viewport = m.show_render = False
        if obj.data.shape_keys:
            mixed = obj.shape_key_add(name='Frozen macro anatomy', from_mix=True)
            coords = [v.co.copy() for v in mixed.data]
            obj.shape_key_clear()
            for v, co in zip(obj.data.vertices, coords):
                v.co = co
        # Fit the whole bent drawing arm, not only the sleeve cap. Inverse skinning
        # keeps the original MPFB weights and live armature on the modified body.
        if obj.name == 'GEO-MPFB archer anatomy':
            transforms = {g.index: rig.pose.bones[g.name].matrix @ rig.data.bones[g.name].matrix_local.inverted()
                          for g in obj.vertex_groups if g.name in rig.pose.bones}
            groups = {g.index: g.name for g in obj.vertex_groups}
            for v in obj.data.vertices:
                weight = sum(g.weight for g in v.groups if groups[g.group] in {'upperarm_r','lowerarm_r','hand_r'})
                if weight < .01:
                    continue
                skin = Matrix(((0,0,0,0),)*4)
                total = 0
                for g in v.groups:
                    if g.group in transforms:
                        skin += transforms[g.group] * g.weight
                        total += g.weight
                if total < .01:
                    continue
                skin *= 1/total
                world = rig.matrix_world @ skin @ v.co
                p = screen(world)
                elbow = math.exp(-((p.x-84)/19)**2)
                delta = Vector((-22*elbow, -2*elbow)) * min(1,weight)
                v.co = skin.inverted() @ rig.matrix_world.inverted() @ move(world, delta)
        # The crest is an actual thick fan. Fit both roots and tips of its tufts,
        # retaining their camera depth and bone parenting, before solidification.
        if obj.name.startswith('GEO-Pale horsehair crest'):
            index = int(obj.name.rsplit('.',1)[1]) if '.' in obj.name else 0
            t = index/50
            outer = [(114,33),(105,32),(96,35),(88,43),(84,55),(84,66)]
            inner = [(109,45),(105,44),(100,46),(95,50),(92,57),(91,64)]
            def point(path):
                u=t*(len(path)-1);j=min(int(u),len(path)-2)
                return Vector(path[j]).lerp(Vector(path[j+1]),u-j)
            inv = obj.matrix_world.inverted()
            for v in obj.data.vertices:
                target = point(inner if v.index<2 else outer)
                world = obj.matrix_world@v.co
                # Original front/back width is retained around the registered fan.
                target.x += .8 if v.index in (1,2) else -.8
                v.co = inv@move(world,target-screen(world))
        # Apply the real solid/beveled surface before camera UVs are sampled.
        for mod in list(obj.modifiers):
            if mod.type == 'ARMATURE':
                continue
            if mod.type == 'SUBSURF':
                mod.levels = mod.render_levels = 1
            if mod.type == 'MASK' and not mod.vertex_group:
                obj.modifiers.remove(mod)
                continue
            if mod.show_viewport:
                bpy.ops.object.modifier_apply(modifier=mod.name)
        for m in arms:
            m.show_viewport = m.show_render = True
        records.append({'object': obj.name, 'vertices': len(obj.data.vertices)})
    bpy.context.view_layer.update()
    # Recurve the two real bow limbs using measured token centerline landmarks.
    # All original camera depths remain; flex and string endpoints are keyed later.
    landmarks = [(149,140),(148,136),(151,129),(157,123),(168,116),(176,106),
                 (180,95),(181,82),(180,69),(175,52),(166,37),(154,27),(145,20),(144,16),(145,12)]
    for name in dynamic[:2]:
        obj = bpy.data.objects[name]
        obj.data.bevel_depth = .007 if name=='GEO-Yew bow' else .0015
        points = obj.data.splines[0].points
        inv = obj.matrix_world.inverted()
        for i, p in enumerate(points):
            t = i/(len(points)-1)*(len(landmarks)-1)
            j = min(int(t),len(landmarks)-2)
            u=t-j
            p0=Vector(landmarks[max(0,j-1)]);p1=Vector(landmarks[j])
            p2=Vector(landmarks[j+1]);p3=Vector(landmarks[min(len(landmarks)-1,j+2)])
            target=.5*((2*p1)+(-p0+p2)*u+(2*p0-5*p1+4*p2-p3)*u*u+(-p0+3*p1-3*p2+p3)*u*u*u)
            if name.endswith('highlight'):
                target.x -= .45
            world = obj.matrix_world @ Vector(p.co[:3])
            p.co = (*(inv @ move(world,target-screen(world))),1)
    # Refit string ends immediately; animation recomputes them on every sample.
    bow = bpy.data.objects[dynamic[0]]
    string = bpy.data.objects['GEO-Bowstring']
    for j,k in [(0,0),(2,-1)]:
        v = bow.matrix_world @ Vector(bow.data.splines[0].points[k].co[:3])
        string.data.splines[0].points[j].co = (*v,1)
    # Strong painted pigment needs a display transform that does not compress it twice.
    sc.view_settings.view_transform = 'Standard'
    sc.view_settings.look = 'None'
    sc.view_settings.exposure = 0
    for o in sc.objects:
        if o.type == 'LIGHT':
            o.data.energy *= .55
    key = bpy.data.objects['LGT-warm key']
    key.data.size = 4
    key.data.color = (1,.96,.88)
    rim = bpy.data.objects['LGT-cool rim']
    rim.data.energy *= .6
    # Physical stone only: no stationary painted feet/shadows.
    for name, rgb in [('MAT-cream-E9CFA0',(.72,.55,.36)),('MAT-cream-rim',(.63,.43,.25))]:
        m = bpy.data.materials[name]
        s = m.node_tree.nodes.get('Principled BSDF')
        rgb = (.80,.65,.47) if name=='MAT-cream-E9CFA0' else (.70,.49,.30)
        s.inputs['Base Color'].default_value = (*rgb,1)
        n=m.node_tree.nodes;l=m.node_tree.links;output=n.get('Material Output')
        physical=output.inputs['Surface'].links[0].from_socket
        pigment=n.new('ShaderNodeBsdfPrincipled');pigment.inputs['Base Color'].default_value=(0,0,0,1)
        pigment.inputs['Specular IOR Level'].default_value=0
        pigment.inputs['Emission Color'].default_value=(*rgb,1);pigment.inputs['Emission Strength'].default_value=1
        ray=n.new('ShaderNodeLightPath');weight=n.new('ShaderNodeMath');weight.operation='MULTIPLY'
        weight.inputs[1].default_value=.62;l.new(ray.outputs['Is Camera Ray'],weight.inputs[0])
        mix=n.new('ShaderNodeMixShader');l.new(weight.outputs[0],mix.inputs[0]);l.new(physical,mix.inputs[1]);l.new(pigment.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],output.inputs['Surface'])
    (MASTER/'surface.json').write_text(json.dumps(records,indent=2))
    log('- Finished static solid/bevel/subdivision geometry before projection; froze MPFB macro mix with native skin weights; fitted drawing-arm contour and complete recurved bow in the fixed rest camera.')
