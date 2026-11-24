"""Render-only foot pigment and soft stone shadow, from evaluated animated feet.

The R14 'sole' flash is mostly the instep (confirmed by an object-ID pass).
Keep its frozen pigment detail; shade it as the whole foot rolls away from its
planted orientation. No pose, mesh, UV, donor rotation or saved scene changes.
"""
import math
import bpy
from mathutils import Vector
from kit.continuity import smooth

ATTRIBUTE = 'Spearman foot pigment regions'


def settings(scene, cfg):
    # Keep the accepted R14 rest/held-clip shadow when the requested smaller
    # pools regress its colour metric. Host A/B exposes that alternative via
    # ground_pools=1. Move always uses compact, evaluated-sole shadows; the
    # legacy toggle permits a same-path R14 replay on the identical master.
    if scene.get('clip') != 'move':
        cfg['foot_roll'] = 0
    if cfg.get('ground_follow', 1) and (scene.get('clip') == 'move' or cfg.get('ground_pools', 0)):
        cfg.update(ground_follow=2, ground_shadow=.4, ground_back=.035,
                   ground_in=.02, ground_depth=.09, ground_width=.07,
                   base_cast=.08, base_contact=.20, contact_reach=.025)


def prepare(scene, classify):
    for ob in scene.objects:
        if ob.type != 'MESH':
            continue
        part = classify(ob)
        if part not in ('skin', 'sandal_l', 'sandal_r'):
            continue
        mesh = ob.data
        attr = mesh.color_attributes.get(ATTRIBUTE) or mesh.color_attributes.new(
            name=ATTRIBUTE, type='FLOAT_COLOR', domain='CORNER')
        for loop in mesh.loops:
            v = mesh.vertices[loop.vertex_index]
            values = [0., 0., 0., 1.]
            for index, side in enumerate('lr'):
                if part == 'sandal_' + side:
                    values[index] = 1.
                elif part == 'skin':
                    weight = sum(g.weight for g in v.groups if ob.vertex_groups[g.group].name
                                 in ('foot_'+side, 'ball_'+side))
                    values[index] = smooth(.3, .8, weight)*(1-smooth(.07, .14, v.co.z))
            attr.data[loop.index].color = values


def pigment(g, colour):
    attr = g.node('ShaderNodeVertexColor', layer_name=ATTRIBUTE)
    split = g.node('ShaderNodeSeparateColor')
    g.l.new(attr.outputs['Color'], split.inputs[0])
    amount = None
    for i, side in enumerate('lr'):
        roll = g.node('ShaderNodeValue')
        roll.name = 'Spearman foot roll ' + side
        roll.outputs[0].default_value = 0
        mask = g.math('MULTIPLY', split.outputs[i], roll.outputs[0])
        amount = mask if amount is None else g.math('ADD', amount, mask)
    # Preserve painted straps/toes and their contrast, while suppressing the
    # light dot as the instep turns upright at toe-off. Linear colour factors.
    return g.mix(amount, colour, (.45, .38, .31, 1), 'MULTIPLY')


def update(scene):
    """Called after frame_set, before BOTH delivery and look-CLI render paths."""
    rig = bpy.data.objects.get('Spearman • MPFB game_engine')
    if rig is None:
        return {}
    dg = bpy.context.evaluated_depsgraph_get()
    evaluated = rig.evaluated_get(dg)
    report = {}
    for side in 'lr':
        foot = evaluated.pose.bones['foot_'+side]
        up = (evaluated.matrix_world.to_3x3() @ foot.matrix.to_3x3()
              @ foot.bone.matrix_local.to_3x3().inverted() @ Vector((0, 0, 1))).normalized()
        roll = smooth(.12, .27, 1-up.z)
        marker = bpy.data.objects.get('LOOK ankle '+side)
        sole = bpy.data.objects.get('Leather sandal sole '+side)
        if marker and marker.get('evaluated_sole') and sole:
            ev = sole.evaluated_get(dg)
            mesh = ev.to_mesh()
            points = [ev.matrix_world @ v.co for v in mesh.vertices]
            ev.to_mesh_clear()
            center = sum(points, Vector())/len(points)
            # Ground beneath the actual articulated sole, not the ankle joint.
            # Mean height fades a rolling foot as well as a fully lifted one.
            anchor = center if marker['evaluated_sole'] == 2 else evaluated.matrix_world @ foot.head
            marker.location = anchor
            report[side] = {'sole_center': list(center), 'anchor': list(anchor), 'roll': roll,
                            'tilt_degrees': math.degrees(math.acos(max(-1, min(1, up.z))))}
        for material in bpy.data.materials:
            if material.name.startswith('LOOK ') and material.use_nodes:
                node = material.node_tree.nodes.get('Spearman foot roll '+side)
                if node:
                    node.outputs[0].default_value = roll
    bpy.context.view_layer.update()
    return report
