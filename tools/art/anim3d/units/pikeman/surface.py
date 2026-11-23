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
        # Applied Bevel/Subsurf interpolation can extrapolate deform weights
        # below zero (observed -0.949 on a trouser vertex). Clamp and normalize
        # after finishing, before the armature sees them; otherwise a tiny seam
        # becomes a metre-long spike when the pose rotates.
        if armatures:
            rig = armatures[0][0].object
            for vertex in obj.data.vertices:
                values = [(g.group, max(0., min(1., g.weight))) for g in vertex.groups
                          if obj.vertex_groups[g.group].name in rig.data.bones]
                total = sum(w for _, w in values)
                if total:
                    for index, weight in values:
                        obj.vertex_groups[index].add([vertex.index], weight/total, 'REPLACE')
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
            p=world_to_camera_view(scene,cam,world);x,y=256*p.x,256*(1-p.y);dx=dy=0
            if obj.name in ['GEO-kettle-helmet-brim','GEO-helmet-rolled-rim']:
                dx=(112+(x-112)*.91-1.4)-x
                dy=88+(y-88)*.60-(x-112)*.32-y
            elif obj.name=='GEO-kettle-helmet-dome' or obj.name.startswith('GEO-helmet-rivet'):
                dx=-.8-(x-111)*.08;dy=1.2
            elif obj.name=='GEO-MPFB-anatomy' and y<84:
                dx=-(x-111)*.16;dy=1.5
            elif obj.name in ['GEO-steel-breastplate','GEO-waist-belt'] and x>115:
                dx=-(x-115)*.57
            elif 92<y<117 and x>114:
                fade=min(1,(117-y)/15);dx=-(x-114)*.27*fade
            if not (dx or dy):continue
            up=cam.matrix_world.to_quaternion()@Vector((0,1,0))
            world_delta=(right*dx-up*dy)*(cam.data.ortho_scale/256)
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


def fit_contours():
    """Fit limited upper-body overhangs; retain camera depth and skin weights.

    This is a bind-mesh edit, never an alpha cutout. Off-camera sides keep their
    original depth. The fixed camera UVs are created only after this operation.
    """
    import json
    import os
    from pathlib import Path
    import numpy as np
    from mathutils import Matrix
    from mathutils.kdtree import KDTree

    scene = bpy.context.scene
    camera = scene.camera
    root = Path(os.environ['ANIM_ROOT'])
    im = bpy.data.images.load(str(root / 'assets/pikeman/body-fit-mask.png'))
    pixels = np.array(im.pixels[:]).reshape(256, 256, 4)[::-1, :, 0]
    points = [(x+.5, y+.5) for y in range(70, 166) for x in range(60, 151)
              if pixels[y, x] > .5]
    tree = KDTree(len(points))
    for i, (x, y) in enumerate(points):
        tree.insert((x, y, 0), i)
    tree.balance()
    right = camera.matrix_world.to_quaternion() @ Vector((1, 0, 0))
    up = camera.matrix_world.to_quaternion() @ Vector((0, 1, 0))
    rig = bpy.data.objects['RIG-pikeman']
    deps = bpy.context.evaluated_depsgraph_get()
    records = []
    for obj in scene.objects:
        if obj.type != 'MESH' or obj.name in ['GEO-cream-stone-base', 'GEO-ash-pike-shaft', 'GEO-iron-pike-point']:
            continue
        if obj.name.startswith(('GEO-wrinkled-trousers', 'GEO-cuisses', 'GEO-greave',
                                'GEO-knee', 'GEO-leather-boots', 'GEO-fluted-tasset',
                                'GEO-tasset-polished')):
            continue
        evaluated = obj.evaluated_get(deps)
        mesh = evaluated.to_mesh()
        worlds = [evaluated.matrix_world @ v.co for v in mesh.vertices]
        evaluated.to_mesh_clear()
        arm = next((m for m in obj.modifiers if m.type == 'ARMATURE'), None)
        count = 0
        for vertex, world in zip(obj.data.vertices, worlds):
            p = world_to_camera_view(scene, camera, world)
            x, y = p.x * 256, (1-p.y) * 256
            if not (60 < x < 151 and 70 < y < 158):
                continue
            # A smooth local field, averaged over a two-pixel neighbourhood,
            # avoids piling every boundary vertex onto the exact same pixel.
            dx = dy = total = 0.
            for sx, sy, weight in [(0,0,4),(-1,0,1),(1,0,1),(0,-1,1),(0,1,1)]:
                xx, yy = x+sx, y+sy
                if pixels[int(yy), int(xx)] < .5:
                    near, _, distance = tree.find((xx, yy, 0))
                    amount = min(1., 8. / max(distance, .001))
                    dx += (near.x-xx) * amount * weight
                    dy += (near.y-yy) * amount * weight
                total += weight
            delta = (right*dx-up*dy) * (camera.data.ortho_scale/256/total)
            if delta.length < .00001:
                continue
            local = obj.matrix_world.inverted().to_3x3() @ delta
            if arm:
                skin = Matrix(((0.,0.,0.,0.),)*4)
                weight = 0
                for group in vertex.groups:
                    name = obj.vertex_groups[group.group].name
                    if name in rig.pose.bones:
                        skin += group.weight*(rig.pose.bones[name].matrix @ rig.data.bones[name].matrix_local.inverted())
                        weight += group.weight
                if weight:
                    skin *= 1/weight
                    transform = obj.matrix_world.inverted() @ rig.matrix_world @ skin @ rig.matrix_world.inverted() @ obj.matrix_world
                    local = transform.to_3x3().inverted_safe() @ local
            # Mixed joint transforms can approach singular at a bent elbow.
            # Reject an unstable inverse instead of growing a sliver/spike.
            if local.length > .16:
                continue
            vertex.co += local
            count += 1
        records.append({'mesh': obj.name, 'fitted_vertices': count})
    bpy.context.view_layer.update()
    (root/'masters/pikeman/contour-fit.json').write_text(json.dumps(records, indent=2))
