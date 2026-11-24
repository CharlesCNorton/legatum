"""Round 9a rest-view contour fitting, before the painting UVs are frozen.

Only geometry changes here. Keep the calibrated camera, materials, motion,
anatomical feet and all camera-axis depth. Weighted surfaces are fitted in the
posed guard then returned through their original blended skin transforms.
"""
import math

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Matrix, Vector


def fit_silhouette(scene, screen_sculpt):
    rig = bpy.data.objects['Spearman • MPFB game_engine']
    transforms = {b.name: b.matrix @ b.bone.matrix_local.inverted()
                  for b in rig.pose.bones}
    changed = {}
    for ob in scene.objects:
        if ob.type != 'MESH':
            continue
        shield = ob.parent and ob.parent.name == 'Aspis control'
        cloak = ob.name.startswith('Cloak •')
        arm = ob.name in {'MPFB anatomical male • original topology',
                         'Linen tunic shoulder sleeves'}
        crest = ob.name.startswith(('Horsehair crest tuft', 'Horsehair painted fibre'))
        if not any((shield, cloak, arm, crest)):
            continue
        skinned = any(m.type == 'ARMATURE' for m in ob.modifiers)
        count = 0
        for vertex in ob.data.vertices:
            skin = Matrix.Identity(4)
            if skinned:
                influences = [(transforms[ob.vertex_groups[g.group].name], g.weight)
                              for g in vertex.groups
                              if ob.vertex_groups[g.group].name in transforms]
                total = sum(w for _, w in influences)
                if total < .001:
                    continue
                skin = sum((m * (w / total) for m, w in influences),
                           Matrix(((0,) * 4,) * 4))
            posed = skin @ vertex.co
            camera = world_to_camera_view(scene, scene.camera, ob.matrix_world @ posed)
            p = Vector((camera.x * 256, (1-camera.y) * 256))
            delta = Vector((0, 0))
            if shield:
                # The upper rim was seven pixels above the painted shield.
                # Taper the correction to zero at its registered central boss;
                # apply the same field to shell, rim, back and raised ornament.
                t = max(0, min(1, (139-p.y)/39))
                delta.y = 6.5*t*t*(3-2*t)
            if cloak:
                # Shorter side tails; retain the low central folded hem and
                # shoulder pins. No alpha trimming or new cloth settings.
                t = max(0, min(1, (p.y-145)/48))
                left = max(0, min(1, (125-p.x)/25))
                right = max(0, min(1, (p.x-140)/28))
                delta += Vector((2.5*left-7*right, -2-5*left-7*right))*t
            if arm:
                cap = math.exp(-((p.x-109)/7)**2-((p.y-106)/6)**2)
                bicep = math.exp(-((p.x-107)/6)**2-((p.y-120)/7)**2)
                delta += Vector((2.3, 2.0))*cap + Vector((-1.0, .5))*bicep
            if crest:
                # Lift the forward brush tip while keeping the attached saddle
                # and rear fan unchanged. These remain full-depth tuft meshes.
                tip = max(0, min(1, (p.x-134)/10))*max(0, min(1, (78-p.y)/13))
                delta += Vector((1.2, -.6))*tip
            if delta.length < .00001:
                continue
            vertex.co = skin.inverted_safe() @ screen_sculpt(ob, posed, p+delta)
            count += 1
        if count:
            ob.data.update()
            changed[ob.name] = count
    scene['spearman_silhouette_round'] = '9a'
    bpy.context.view_layer.update()
    print('SILHOUETTE_9A', len(changed), 'meshes', sum(changed.values()), 'vertices')
