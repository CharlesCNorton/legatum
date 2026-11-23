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
    bpy.context.view_layer.update()

    # Register complete solid hat/feather assemblies, preserving depth.
    for names,box in [
        (('red beret brim','beret rolled rim','soft beret crown'),(109,42,157,61)),
        (('feather quill','feather vane','feather barb'),(120,31,159,66)),
    ]:
        objects=[o for o in scene.objects if any(name in o.name for name in names)];entries=[]
        for obj in objects:
            for vertex in obj.data.vertices:
                world=obj.matrix_world @ vertex.co;uv=world_to_camera_view(scene,camera,world);entries.append((obj,vertex,world,uv.x*256,(1-uv.y)*256))
        x0,x1=min(e[3] for e in entries),max(e[3] for e in entries);y0,y1=min(e[4] for e in entries),max(e[4] for e in entries)
        right=camera.matrix_world.to_quaternion() @ Vector((1,0,0));up=camera.matrix_world.to_quaternion() @ Vector((0,1,0))
        for obj,vertex,world,x,y in entries:
            tx=box[0]+(x-x0)/(x1-x0)*(box[2]-box[0]);ty=box[1]+(y-y0)/(y1-y0)*(box[3]-box[1]);world+=(right*(tx-x)-up*(ty-y))*camera.data.ortho_scale/256;vertex.co=obj.matrix_world.inverted() @ world
        for obj in objects:obj.data.update()
    bpy.context.view_layer.update()
    # Fit the full-depth anatomical head to its painted extent. Invert each
    # vertex's skin matrix; preserve the mesh, skin weights and depth.
    rig=bpy.data.objects['RIG-Reislaufer MPFB'];body=bpy.data.objects['GEO-MPFB anatomical reislaufer']
    dg=bpy.context.evaluated_depsgraph_get();ev=body.evaluated_get(dg);me=ev.to_mesh();selected=[]
    for vertex in body.data.vertices:
        weight=sum(g.weight for g in vertex.groups if body.vertex_groups[g.group].name=='head')
        if weight>.65:
            co=world_to_camera_view(scene,camera,ev.matrix_world @ me.vertices[vertex.index].co)
            selected.append((co.x*256,(1-co.y)*256))
    ev.to_mesh_clear()
    x0,x1=min(v[0] for v in selected),max(v[0] for v in selected)
    y0,y1=min(v[1] for v in selected),max(v[1] for v in selected)
    print('HEAD_FIT',x0,y0,x1,y1,flush=True)
    right=camera.matrix_world.to_quaternion() @ Vector((1,0,0));up=camera.matrix_world.to_quaternion() @ Vector((0,1,0))
    for obj in [body,bpy.data.objects['GEO-MPFB eyes']]:
        ev=obj.evaluated_get(dg);me=ev.to_mesh();coordinates=[v.co.copy() for v in me.vertices];ev.to_mesh_clear()
        for vertex in obj.data.vertices:
            weights={obj.vertex_groups[g.group].name:g.weight for g in vertex.groups if obj.vertex_groups[g.group].name in rig.data.bones}
            amount=min(1,weights.get('head',0)/.65)
            if amount<.05:continue
            world=obj.matrix_world @ coordinates[vertex.index];co=world_to_camera_view(scene,camera,world);x,y=co.x*256,(1-co.y)*256
            tx=118+(x-x0)/(x1-x0)*25;ty=48+(y-y0)/(y1-y0)*27
            delta=(right*(tx-x)-up*(ty-y))*(camera.data.ortho_scale/256)*amount
            skin=Matrix(((0,0,0,0),)*4);total=sum(weights.values())
            for name,w in weights.items():
                transform=rig.pose.bones[name].matrix @ rig.data.bones[name].matrix_local.inverted()
                for r in range(4):
                    for c in range(4):skin[r][c]+=transform[r][c]*w/total
            vertex.co+=skin.to_3x3().inverted_safe() @ obj.matrix_world.to_3x3().inverted() @ delta
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
