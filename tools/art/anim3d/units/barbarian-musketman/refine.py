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
