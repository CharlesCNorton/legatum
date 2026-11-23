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
    # Register full-volume helmet and near shoulder, preserving depth and skinning.
    # A camera-space fitting field edits bind coordinates, never alpha or per-frame UVs.
    from mathutils import Matrix
    scene=bpy.context.scene;cam=scene.camera;right=cam.matrix_world.to_quaternion()@Vector((1,0,0));rig=bpy.data.objects['RIG-pikeman'];deps=bpy.context.evaluated_depsgraph_get()
    for obj in scene.objects:
        if obj.type!='MESH' or obj.name in ['GEO-cream-stone-base','GEO-ash-pike-shaft','GEO-iron-pike-point']:continue
        evaluated=obj.evaluated_get(deps);mesh=evaluated.to_mesh();worlds=[evaluated.matrix_world@v.co for v in mesh.vertices];evaluated.to_mesh_clear()
        assert len(worlds)==len(obj.data.vertices)
        arm=next((m for m in obj.modifiers if m.type=='ARMATURE'),None)
        for vertex,world in zip(obj.data.vertices,worlds):
            p=world_to_camera_view(scene,cam,world);x,y=256*p.x,256*(1-p.y);dx=0
            if obj.name in ['GEO-kettle-helmet-brim','GEO-helmet-rolled-rim']:
                dx=(112+(x-112)*.76)-x
            elif 92<y<137 and x>114:
                fade=min(1,(137-y)/25);dx=-(x-114)*.34*fade
            if not dx:continue
            world_delta=right*(dx*cam.data.ortho_scale/256)
            local_delta=obj.matrix_world.inverted().to_3x3()@world_delta
            if arm:
                skin=Matrix(((0.,0.,0.,0.),)*4);total=0
                for group in vertex.groups:
                    name=obj.vertex_groups[group.group].name
                    if name in rig.pose.bones:
                        skin+=group.weight*(rig.pose.bones[name].matrix@rig.data.bones[name].matrix_local.inverted());total+=group.weight
                if total:
                    skin*=1/total
                    transform=obj.matrix_world.inverted()@rig.matrix_world@skin@rig.matrix_world.inverted()@obj.matrix_world
                    local_delta=transform.to_3x3().inverted_safe()@local_delta
            vertex.co+=local_delta
    bpy.context.view_layer.update()
