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
