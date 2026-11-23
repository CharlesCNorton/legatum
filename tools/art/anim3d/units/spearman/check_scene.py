"""Verify the saved round-6 surface pipeline before rebuilding cloth/clips."""
import json
import os
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

root = Path(os.environ['ANIM_ROOT'])
bpy.ops.wm.open_mainfile(filepath=str(root/'masters/spearman-3d-v2/spearman.blend'))
sc = bpy.context.scene
assert sc['infantry_refinement'] == 6
assert len(bpy.data.objects['MPFB anatomical male • original topology'].data.vertices) == 19158
assert bpy.data.objects['MPFB anatomical male • original topology'].data.shape_keys is None
assert len(bpy.data.objects['Spearman • MPFB game_engine'].data.bones) == 53
assert sc.camera is not None and not sc.camera.data.dof.use_dof

painted = 0
for mat in bpy.data.materials:
    if not mat.use_nodes or ' | rest paint | ' not in mat.name:
        continue
    output = next(n for n in mat.node_tree.nodes if n.type == 'OUTPUT_MATERIAL')
    blend = output.inputs['Surface'].links[0].from_node
    assert blend.type == 'MIX_SHADER', mat.name
    factor = blend.inputs[0].links[0].from_node
    assert factor.type == 'MATH' and factor.operation == 'MULTIPLY', mat.name
    camera = factor.inputs[1].links[0].from_socket
    assert camera.node.type == 'LIGHT_PATH' and camera.name == 'Is Camera Ray', mat.name
    painted += 1
assert painted > 300, painted

for ob in sc.objects:
    if ob.type != 'MESH' or ob.hide_render:
        continue
    assert min(abs(s) for s in ob.scale) > .0001, ob.name
    if ob.name != 'Stationary cream stone' and not any(m.type in {'ARMATURE', 'CLOTH', 'MASK'} for m in ob.modifiers):
        assert not any(m.type in {'SOLIDIFY', 'BEVEL', 'SUBSURF'} for m in ob.modifiers), ob.name

base = bpy.data.objects['Stationary cream stone']
assert base.data.uv_layers.get('Painting camera rest') is None
assert abs(max((base.matrix_world @ v.co).z for v in base.data.vertices)-.105) < .0001
for side in ['l', 'r']:
    sole = bpy.data.objects['Leather sandal sole '+side]
    lowest = min((sole.matrix_world @ v.co).z for v in sole.data.vertices)
    assert lowest >= .100, (sole.name, lowest)
for mat in base.data.materials:
    bsdf = mat.node_tree.nodes['Principled BSDF']
    strength = bsdf.inputs['Emission Strength'].links[0].from_node
    camera = strength.inputs[0].links[0].from_socket
    assert strength.operation == 'MULTIPLY'
    assert camera.node.type == 'LIGHT_PATH' and camera.name == 'Is Camera Ray'
# Check face interiors too: endpoint-only seating missed triangles cutting
# through the convex shield. All real side/back faces must clear the shell.
shell = bpy.data.objects['Convex bronze aspis']
tree = BVHTree.FromPolygons([shell.matrix_world @ v.co for v in shell.data.vertices],
                           [list(p.vertices) for p in shell.data.polygons])
view = sc.camera.matrix_world.to_quaternion() @ Vector((0, 0, 1))
clearance = {}
for ob in sc.objects:
    if not ob.name.startswith('Sunburst raised ray'):
        continue
    assert len(ob.data.vertices) > 100, ob.name
    distances = []
    for poly in ob.data.polygons:
        center = ob.matrix_world @ poly.center
        hit = tree.ray_cast(center+view*5, -view, 10)[0]
        assert hit is not None, ob.name
        distances.append((center-hit).dot(view))
    clearance[ob.name] = min(distances)
    assert min(distances) > .001, (ob.name, min(distances))
assert len(clearance) == 12
report = {'refinement': 6, 'painted_materials': painted, 'camera_only_pigment': True,
          'rigid_finish_before_projection': True, 'body_vertices': 19158, 'bones': 53,
          'base_top': .105, 'camera': list(sc.camera.location),
          'shield_ray_min_face_clearance': clearance}
(root/'review/3d-v2/spearman-scene-checks.json').write_text(json.dumps(report, indent=2)+'\n')
print('SCENE_CHECKS', json.dumps(report))
