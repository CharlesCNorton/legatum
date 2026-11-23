"""Finish rigid surfaces before freezing camera UVs; preserve live skin/cloth."""
import bpy


def finish():
    counts = {}
    for obj in list(bpy.context.scene.objects):
        if obj.type not in {'MESH', 'CURVE'} or not obj.name.startswith('GEO-'):
            continue
        if obj.name == 'GEO-Stationary cream base':
            continue
        if obj.type == 'MESH' and (obj.data.shape_keys or any(
                mod.type == 'ARMATURE' for mod in obj.modifiers)):
            continue
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        if obj.type == 'CURVE':
            bpy.ops.object.convert(target='MESH')
        for mod in list(obj.modifiers):
            bpy.ops.object.modifier_apply(modifier=mod.name)
        obj['finished_projection_surface'] = True
        counts[obj.name] = len(obj.data.vertices)
    return counts
