"""Finish full-depth surfaces before freezing their rest-camera UV coordinates."""
import bpy
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view


def finish_surfaces():
    scene = bpy.context.scene
    camera = scene.camera
    for obj in list(scene.objects):
        if obj.type != 'MESH' or 'muzzle' in obj.name:
            continue
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        # Freeze MPFB macro morphs on the working copy, retaining the skin weights.
        if obj.data.shape_keys:
            obj.shape_key_add(name='Frozen macro mix', from_mix=True)
            for key in list(obj.data.shape_keys.key_blocks)[:-1]:
                obj.shape_key_remove(key)
            obj.shape_key_remove(obj.data.shape_keys.key_blocks[0])
        for mod in list(obj.modifiers):
            if mod.type == 'ARMATURE':
                continue
            if mod.type == 'SUBSURF' and mod.levels == 0:
                obj.modifiers.remove(mod)
            else:
                bpy.ops.object.modifier_apply(modifier=mod.name)
        obj['finished_surface'] = True
    # Register complete hat meshes in the rest view; retain every vertex's depth.
    # This is a physical-coordinate fit, never texture warping or alpha clipping.
    for names, target, slope in [
        (('broad weathered hat brim', 'hat worn rolled rim'), (28, 38, 103, 66), -.20),
        (('pinched felt hat crown', 'hat leather band'), (46, 27, 81, 52), -.12),
    ]:
        objects = [o for o in scene.objects if any(n in o.name for n in names)]
        entries = []
        for obj in objects:
            for vertex in obj.data.vertices:
                world = obj.matrix_world @ vertex.co
                uv = world_to_camera_view(scene, camera, world)
                x, y = uv.x * 256, (1 - uv.y) * 256
                entries.append((obj, vertex, world, x, y + slope * (x - 65)))
        lo_x, hi_x = min(e[3] for e in entries), max(e[3] for e in entries)
        lo_y, hi_y = min(e[4] for e in entries), max(e[4] for e in entries)
        right = camera.matrix_world.to_quaternion() @ Vector((1, 0, 0))
        up = camera.matrix_world.to_quaternion() @ Vector((0, 1, 0))
        for obj, vertex, world, x, tilted_y in entries:
            original = world_to_camera_view(scene, camera, world)
            tx = target[0] + (x - lo_x) / (hi_x - lo_x) * (target[2] - target[0])
            ty = target[1] + (tilted_y - lo_y) / (hi_y - lo_y) * (target[3] - target[1])
            world += (right * (tx - original.x * 256) - up * (ty - (1-original.y)*256)) * camera.data.ortho_scale / 256
            vertex.co = obj.matrix_world.inverted() @ world
        for obj in objects:
            obj.data.update()
    bpy.context.view_layer.update()


def bind_torso(rig):
    """Inverse-skin finished tailored garments without changing their posed fit."""
    scene = bpy.context.scene
    bones = [('pelvis', 138), ('spine_01', 120), ('spine_02', 103), ('spine_03', 81)]
    skin = {name: rig.pose.bones[name].matrix @ rig.data.bones[name].matrix_local.inverted()
            for name, _ in bones}
    for obj in list(scene.objects):
        if not any(word in obj.name for word in ('ivory shirt', 'weathered buff waistcoat')):
            continue
        world = obj.matrix_world.copy()
        points = [world @ vertex.co for vertex in obj.data.vertices]
        obj.parent = rig
        obj.parent_type = 'OBJECT'
        obj.matrix_parent_inverse = Matrix.Identity(4)
        obj.matrix_basis = Matrix.Identity(4)
        groups = {name: obj.vertex_groups.new(name=name) for name, _ in bones}
        for vertex, point in zip(obj.data.vertices, points):
            y = (1-world_to_camera_view(scene, scene.camera, point).y)*256
            weights = {name: max(0, 1-abs(y-center)/25) for name, center in bones}
            total = sum(weights.values())
            assert total > 0
            transform = Matrix(((0,)*4,)*4)
            for name, weight in weights.items():
                if weight:
                    weight /= total
                    groups[name].add([vertex.index], weight, 'REPLACE')
                    transform += skin[name]*weight
            vertex.co = transform.inverted() @ rig.matrix_world.inverted() @ point
        modifier = obj.modifiers.new('Tailored spine deformation', 'ARMATURE')
        modifier.object = rig
        obj['weighted_tailoring'] = True
        obj.data.update()
    bpy.context.view_layer.update()


def bind_sleeves(rig):
    """Keep the finished rest fit, sharing shoulder/elbow motion across the cloth."""
    for obj in list(bpy.context.scene.objects):
        if 'billowing ivory sleeve' not in obj.name:
            continue
        side = obj.name[-1]
        upper, lower = 'upperarm_' + side, 'lowerarm_' + side
        names = ['spine_03', upper, lower]
        transforms = {n: rig.pose.bones[n].matrix @ rig.data.bones[n].matrix_local.inverted() for n in names}
        points = [obj.matrix_world @ v.co for v in obj.data.vertices]
        a, b = (rig.matrix_world @ rig.pose.bones[upper].head,
                rig.matrix_world @ rig.pose.bones[upper].tail)
        axis = b-a
        obj.parent = rig; obj.parent_type = 'OBJECT'
        obj.matrix_parent_inverse = Matrix.Identity(4); obj.matrix_basis = Matrix.Identity(4)
        groups = {n: obj.vertex_groups.new(name=n) for n in names}
        for vertex, point in zip(obj.data.vertices, points):
            t = (point-a).dot(axis)/axis.length_squared
            shoulder = .65*max(0, min(1, (.22-t)/.22))
            elbow = .35*max(0, min(1, (t-.75)/.30))
            weights = (shoulder, 1-shoulder-elbow, elbow)
            transform = Matrix(((0,)*4,)*4)
            for name, weight in zip(names, weights):
                if weight:
                    groups[name].add([vertex.index], weight, 'REPLACE')
                    transform += transforms[name]*weight
            vertex.co = transform.inverted() @ rig.matrix_world.inverted() @ point
        mod = obj.modifiers.new('Continuous shoulder and elbow cloth', 'ARMATURE'); mod.object = rig
        obj['weighted_tailoring'] = True; obj.data.update()
    bpy.context.view_layer.update()


def underclothing(body, rig, materials):
    """Clothed anatomical regions retain garment pigment when newly revealed."""
    slots = {}
    body.data.materials.clear()
    for poly in body.data.polygons:
        weights = {}
        for index in poly.vertices:
            for entry in body.data.vertices[index].groups:
                name = body.vertex_groups[entry.group].name
                if name in rig.pose.bones: weights[name] = weights.get(name, 0) + entry.weight
        bone = max(weights, key=weights.get)
        kind = ('buff' if bone.startswith(('spine', 'pelvis', 'thigh')) else
                'pants' if bone.startswith('calf') else
                'leather' if bone.startswith(('foot', 'ball')) else
                'linen' if bone.startswith(('upperarm', 'clavicle')) else 'skin')
        key = kind, bone
        if key not in slots:
            mat = materials[kind].copy(); mat.name = 'MAT-underlayer-' + kind + '-' + bone
            mat['projection_bone'] = bone
            slots[key] = len(body.data.materials); body.data.materials.append(mat)
        poly.material_index = slots[key]


def motion_fidelity(rig, reference, frame):
    """Fade misleading rest-view anatomy as its surface turns far from that view."""
    for obj in bpy.context.scene.objects:
        if obj.type != 'MESH': continue
        for slot in obj.material_slots:
            mat = slot.material
            if not mat: continue
            value = mat.node_tree.nodes.get('Projection motion fidelity')
            if value is None: continue
            bone = mat.get('projection_bone')
            if not bone and any(s in obj.name for s in ('ivory shirt', 'waistcoat', 'billowing ivory sleeve')):
                bone = 'upperarm_' + obj.name[-1] if 'sleeve' in obj.name else 'spine_02'
            if not bone or bone not in rig.pose.bones: continue
            current = (rig.matrix_world @ rig.pose.bones[bone].matrix).to_quaternion()
            angle = reference[bone].rotation_difference(current).angle
            weight = max(0, min(1, (1.25-angle)/.85))
            weight = weight*weight*(3-2*weight)
            value.outputs[0].default_value = weight
            value.outputs[0].keyframe_insert('default_value', frame=frame)


def hidden_pigment(material):
    """Generated pigment keeps its brushwork with broad live light and contact AO."""
    n, l = material.node_tree.nodes, material.node_tree.links
    bs = n.get('Principled BSDF')
    color = bs.inputs['Base Color']
    geo = n.new('ShaderNodeNewGeometry')
    light = n.new('ShaderNodeVectorMath'); light.operation = 'DOT_PRODUCT'
    light.inputs[1].default_value = Vector((-.4,-.6,.7)).normalized()
    l.new(geo.outputs['Normal'], light.inputs[0])
    shade = n.new('ShaderNodeMapRange'); shade.clamp = True
    shade.inputs['From Min'].default_value = -1; shade.inputs['From Max'].default_value = 1
    shade.inputs['To Min'].default_value = .42; shade.inputs['To Max'].default_value = 1.05
    l.new(light.outputs['Value'], shade.inputs['Value'])
    multiply = n.new('ShaderNodeMixRGB'); multiply.blend_type = 'MULTIPLY'; multiply.inputs[0].default_value = 1
    if color.is_linked: l.new(color.links[0].from_socket, multiply.inputs[1])
    else: multiply.inputs[1].default_value = color.default_value
    l.new(shade.outputs[0], multiply.inputs[2])
    ao = n.new('ShaderNodeAmbientOcclusion'); ao.inputs['Distance'].default_value = .055
    l.new(multiply.outputs[0], ao.inputs['Color'])
    pigment = n.new('ShaderNodeEmission'); pigment.name = 'Hidden painted fill'
    l.new(ao.outputs['Color'], pigment.inputs['Color'])
    cam = n.new('ShaderNodeLightPath')
    weight = n.new('ShaderNodeMath'); weight.operation = 'MULTIPLY'; weight.inputs[1].default_value = .78
    l.new(cam.outputs['Is Camera Ray'], weight.inputs[0])
    mix = n.new('ShaderNodeMixShader'); l.new(weight.outputs[0], mix.inputs[0])
    l.new(bs.outputs[0], mix.inputs[1]); l.new(pigment.outputs[0], mix.inputs[2])
    return mix.outputs[0]


def stone_projection(assets):
    """Clean generated top on the real beveled disc; alpha never clips geometry."""
    scene = bpy.context.scene; obj = bpy.data.objects['GEO-stationary cream base']
    uv = obj.data.uv_layers.new(name='Clean stone')
    for loop in obj.data.loops:
        point = obj.matrix_world @ obj.data.vertices[loop.vertex_index].co
        co = world_to_camera_view(scene, scene.camera, point)
        uv.data[loop.index].uv = co.x, co.y
    material = obj.active_material; n, l = material.node_tree.nodes, material.node_tree.links
    tex = n.new('ShaderNodeTexImage'); tex.image = bpy.data.images.load(str(assets/'stone-projection.png')); tex.extension = 'EXTEND'
    coords = n.new('ShaderNodeUVMap'); coords.uv_map = uv.name; l.new(coords.outputs[0], tex.inputs[0])
    ao = n.new('ShaderNodeAmbientOcclusion'); ao.inputs['Distance'].default_value = .045
    l.new(tex.outputs['Color'], ao.inputs['Color'])
    emit = n.new('ShaderNodeEmission'); l.new(ao.outputs['Color'], emit.inputs['Color'])
    camera = n.new('ShaderNodeLightPath'); mix = n.new('ShaderNodeMixShader')
    l.new(camera.outputs['Is Camera Ray'], mix.inputs[0]); l.new(n.get('Principled BSDF').outputs[0], mix.inputs[1])
    l.new(emit.outputs[0], mix.inputs[2]); l.new(mix.outputs[0], n.get('Material Output').inputs['Surface'])
    obj['clean_generated_stone'] = True


def audit_surface():
    """Check saved calibration on actual evaluated surfaces, not raw cages."""
    scene = bpy.context.scene
    deps = bpy.context.evaluated_depsgraph_get()
    maximum = 0.0
    checked = 0
    for obj in scene.objects:
        if obj.type != 'MESH' or 'muzzle' in obj.name:
            continue
        assert obj.get('finished_surface'), obj.name
        assert not obj.data.shape_keys, (obj.name, 'unfrozen macro morph')
        assert all(m.type == 'ARMATURE' for m in obj.modifiers), obj.name
        uv = obj.data.uv_layers.get('Painting')
        if obj.name == 'GEO-stationary cream base':
            assert uv is None, 'Static base must not retain painted feet'
            assert obj.get('clean_generated_stone') and obj.data.uv_layers.get('Clean stone')
            continue
        if 'eyes' in obj.name:
            continue
        assert uv is not None, obj.name
        evaluated = obj.evaluated_get(deps)
        data = evaluated.to_mesh()
        assert len(data.vertices) == len(obj.data.vertices), obj.name
        for loop in list(obj.data.loops)[::max(1, len(obj.data.loops)//64)]:
            co = world_to_camera_view(scene, scene.camera, evaluated.matrix_world @ data.vertices[loop.vertex_index].co)
            error = (uv.data[loop.index].uv - Vector((co.x, co.y))).length * 256
            maximum = max(maximum, error)
            assert error < .01, (obj.name, 'finished surface UV mismatch', error)
        evaluated.to_mesh_clear()
        for slot in obj.material_slots:
            if slot.material:
                assert slot.material.node_tree.nodes.get('Camera-only pigment'), obj.name
        checked += 1
    return {'finished_meshes': checked, 'maximum_projection_error_px': maximum, 'base_has_no_projected_feet': True}
