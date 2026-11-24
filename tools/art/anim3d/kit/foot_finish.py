"""Render-time foot pigment and evaluated-sole shadow coordinates.

Z-up humanoids; mapping, region names and tint belong to the unit. Changes only
shader attributes/nodes and marker locations, never donor rotations or geometry.
The two-channel pigment mask supports a pair of feet. Motion proxy and final
render must call update after frame_set. Extracted and exercised on Spearman R15.
"""
import math
import bpy
from mathutils import Vector
from kit.continuity import smooth

def prepare(scene, classify, *, attribute, skin_part, sandal_parts, bone_groups, z_range=(.07, .14)):
    for ob in scene.objects:
        if ob.type != 'MESH':
            continue
        part = classify(ob)
        if part not in (skin_part, *sandal_parts.values()):
            continue
        mesh = ob.data
        attr = mesh.color_attributes.get(attribute) or mesh.color_attributes.new(
            name=attribute, type='FLOAT_COLOR', domain='CORNER')
        for loop in mesh.loops:
            v = mesh.vertices[loop.vertex_index]
            values = [0., 0., 0., 1.]
            for index, side in enumerate(sandal_parts):
                if part == sandal_parts[side]:
                    values[index] = 1.
                elif part == skin_part:
                    weight = sum(g.weight for g in v.groups if ob.vertex_groups[g.group].name
                                 in bone_groups[side])
                    values[index] = smooth(.3, .8, weight)*(1-smooth(*z_range, v.co.z))
            attr.data[loop.index].color = values


def pigment(g, colour, *, attribute, sides, node_prefix, tint):
    attr = g.node('ShaderNodeVertexColor', layer_name=attribute)
    split = g.node('ShaderNodeSeparateColor')
    g.l.new(attr.outputs['Color'], split.inputs[0])
    amount = None
    for i, side in enumerate(sides):
        roll = g.node('ShaderNodeValue')
        roll.name = node_prefix + side
        roll.outputs[0].default_value = 0
        mask = g.math('MULTIPLY', split.outputs[i], roll.outputs[0])
        amount = mask if amount is None else g.math('ADD', amount, mask)
    # Preserve painted straps/toes and their contrast, while suppressing the
    # light dot as the instep turns upright at toe-off. Linear colour factors.
    return g.mix(amount, colour, tint, 'MULTIPLY')


def update(scene, *, rig_name, foot_bones, sole_names, marker_names, node_prefix):
    """Called after frame_set, before BOTH delivery and look-CLI render paths."""
    rig = bpy.data.objects.get(rig_name)
    if rig is None:
        return {}
    dg = bpy.context.evaluated_depsgraph_get()
    evaluated = rig.evaluated_get(dg)
    report = {}
    for side in foot_bones:
        foot = evaluated.pose.bones[foot_bones[side]]
        up = (evaluated.matrix_world.to_3x3() @ foot.matrix.to_3x3()
              @ foot.bone.matrix_local.to_3x3().inverted() @ Vector((0, 0, 1))).normalized()
        roll = smooth(.12, .27, 1-up.z)
        marker = bpy.data.objects.get(marker_names[side])
        sole = bpy.data.objects.get(sole_names[side])
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
                node = material.node_tree.nodes.get(node_prefix+side)
                if node:
                    node.outputs[0].default_value = roll
    bpy.context.view_layer.update()
    return report
