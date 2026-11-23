"""Finish real topology before freezing camera UVs; retain armature deformation."""
import bpy


def finish_surfaces():
    records = []
    for obj in list(bpy.context.scene.objects):
        if obj.type not in {'MESH', 'CURVE'} or obj.hide_render:
            continue
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        if obj.type == 'CURVE':
            bpy.ops.object.convert(target='MESH')
        armatures = [m for m in obj.modifiers if m.type == 'ARMATURE']
        states = [(m, m.show_viewport, m.show_render) for m in armatures]
        for m, _, _ in states:
            m.show_viewport = m.show_render = False
        if obj.data.shape_keys:
            # Macro targets are static anatomy, not performance shape keys. Freeze
            # their evaluated mix while retaining original skin weights and rig.
            mixed = obj.shape_key_add(name='Frozen anatomical macro mix', from_mix=True)
            coords = [v.co.copy() for v in mixed.data]
            obj.shape_key_clear()
            for vertex, co in zip(obj.data.vertices, coords):
                vertex.co = co
        applied = []
        for mod in list(obj.modifiers):
            if mod.type == 'ARMATURE' or not mod.show_viewport:
                continue
            if mod.type == 'SOLIDIFY':
                obj['finished_thickness'] = mod.thickness
            if mod.type == 'SUBSURF':
                mod.levels = mod.render_levels
                if mod.levels == 0:
                    obj.modifiers.remove(mod)
                    continue
            if mod.type == 'MASK' and not mod.vertex_group:
                obj.modifiers.remove(mod)
                continue
            print('FINISH_SURFACE', obj.name, mod.name, mod.type, flush=True)
            applied.append(mod.type)
            bpy.ops.object.modifier_apply(modifier=mod.name)
        for m, viewport, render in states:
            m.show_viewport, m.show_render = viewport, render
        records.append({'object': obj.name, 'applied': applied, 'vertices': len(obj.data.vertices)})
    bpy.context.view_layer.update()
    return records
