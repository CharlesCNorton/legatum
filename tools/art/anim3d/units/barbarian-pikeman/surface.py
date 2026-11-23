"""Finish the full-depth geometry before projection, preserving skin weights."""
import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector


def finish_surfaces():
    for obj in list(bpy.context.scene.objects):
        if obj.type != 'MESH' or obj.hide_render:
            continue
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        armatures = [(m, m.show_viewport) for m in obj.modifiers if m.type == 'ARMATURE']
        for mod, _ in armatures:
            mod.show_viewport = False
        if obj.data.shape_keys:
            mixed = obj.shape_key_add(name='Frozen anatomical macro mix', from_mix=True)
            coords = [v.co.copy() for v in mixed.data]
            obj.shape_key_clear()
            for vertex, co in zip(obj.data.vertices, coords):
                vertex.co = co
        for mod in list(obj.modifiers):
            if mod.type == 'ARMATURE' or not mod.show_viewport:
                continue
            if mod.type == 'SUBSURF':
                mod.levels = mod.render_levels
            bpy.ops.object.modifier_apply(modifier=mod.name)
        for mod, visible in armatures:
            mod.show_viewport = visible
        obj['finished_surface'] = True
    bpy.context.view_layer.update()
    # The original bowl sat behind/left of the actual MPFB crown, exposing
    # scalp through the metal. Center the full bowl over the measured skull;
    # blend the inner brim to that center while retaining its outer silhouette.
    for name in ['GEO-kettle-helmet-dome', 'GEO-kettle-helmet-brim']:
        obj = bpy.data.objects[name]
        local_delta = obj.matrix_world.inverted().to_3x3() @ Vector((.025, -.035, .004))
        for vertex in obj.data.vertices:
            radius = ((vertex.co.x / .125) ** 2 + ((vertex.co.y + .015) / .12) ** 2) ** .5
            weight = 1 if name.endswith('dome') else max(0, min(1, (1.4 - radius) / .4))
            vertex.co += local_delta * weight
    # Fit the solid brim's overwide side while preserving its camera depth and
    # complete volume. UVs are frozen only after this physical contour change.
    scene = bpy.context.scene
    right = scene.camera.matrix_world.to_quaternion() @ Vector((1, 0, 0))
    for name in ['GEO-kettle-helmet-brim', 'GEO-helmet-rolled-rim']:
        obj = bpy.data.objects[name]
        inverse = obj.matrix_world.inverted()
        for vertex in obj.data.vertices:
            world = obj.matrix_world @ vertex.co
            x = 256 * world_to_camera_view(scene, scene.camera, world).x
            target = 117 + (x - 117) * .45 if x > 117 else 96 + (x - 96) * .8 if x < 96 else x
            vertex.co = inverse @ (world + right * ((target - x) * scene.camera.data.ortho_scale / 256))
    # The coat's upper side extended beyond the painted shoulder as a bare
    # triangular flap. Fit the volume in the actual guard pose, then inverse-skin
    # that small camera-plane adjustment into the editable weighted mesh.
    rig = bpy.data.objects['RIG-pikeman']
    obj = bpy.data.objects['GEO-quilted-gambeson']
    deps = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(deps); mesh = evaluated.to_mesh()
    from mathutils import Matrix
    for vertex, posed in zip(obj.data.vertices, mesh.vertices):
        world = evaluated.matrix_world @ posed.co
        screen = world_to_camera_view(scene,scene.camera,world)
        x,y = screen.x*256,(1-screen.y)*256
        if 90 < y < 145:
            limit = 124+max(0,y-108)*.12
            excess = max(0,x-limit)
            fade = min(1,(y-90)/8,(145-y)/8)
            if excess > 0:
                transform = Matrix(((0,0,0,0),)*4); total = 0
                for group in vertex.groups:
                    name = obj.vertex_groups[group.group].name
                    if name in rig.pose.bones:
                        transform += (rig.pose.bones[name].matrix @ rig.data.bones[name].matrix_local.inverted())*group.weight
                        total += group.weight
                if total:
                    transform *= 1/total
                    delta = rig.matrix_world.inverted().to_3x3() @ (-right*excess*.85*fade*scene.camera.data.ortho_scale/256)
                    vertex.co += transform.to_3x3().inverted() @ delta
    evaluated.to_mesh_clear()
    bpy.context.view_layer.update()
    # Full-depth sleeve contour fit in the calibrated guard. Only the
    # camera-horizontal component changes; no image silhouettes/alpha geometry.
    for name in ['GEO-padded-sleeves']:
        obj = bpy.data.objects[name]
        evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh = evaluated.to_mesh()
        for vertex, posed in zip(obj.data.vertices, mesh.vertices):
            world = evaluated.matrix_world @ posed.co
            screen = world_to_camera_view(scene, scene.camera, world)
            x, y = screen.x * 256, (1 - screen.y) * 256
            target = x
            if name == 'GEO-padded-sleeves' and 96 < y < 117:
                limit = 123 + (y - 101) * .55
                target -= max(0, x - limit) * min(1, (y - 96) / 5, (117 - y) / 4)
            if target == x:
                continue
            transform = Matrix(((0, 0, 0, 0),) * 4)
            total = 0
            for group in vertex.groups:
                bone = obj.vertex_groups[group.group].name
                if bone in rig.pose.bones:
                    transform += (rig.pose.bones[bone].matrix @ rig.data.bones[bone].matrix_local.inverted()) * group.weight
                    total += group.weight
            if total:
                transform *= 1 / total
                delta = rig.matrix_world.inverted().to_3x3() @ (right * (target - x) * scene.camera.data.ortho_scale / 256)
                vertex.co += transform.to_3x3().inverted() @ delta
        evaluated.to_mesh_clear()
        bpy.context.view_layer.update()
