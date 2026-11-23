"""Frozen painting on finished 3D surfaces; painted light is camera-only."""
import json
import os
from pathlib import Path

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def project():
    root = Path(os.environ['ANIM_ROOT'])
    scene = bpy.context.scene
    camera = scene.camera
    painting = bpy.data.images.load(str(root / 'assets/barbarian-pikeman/painting-aligned.png'))
    stone_paint = bpy.data.images.load(str(root / 'assets/barbarian-pikeman/stone-registered.png'))
    pixels = list(painting.pixels); image_w, image_h = painting.size
    view = camera.matrix_world.to_quaternion() @ Vector((0, 0, 1))
    deps = bpy.context.evaluated_depsgraph_get()
    vertices, faces = [], []
    for obj in scene.objects:
        if obj.type != 'MESH' or obj.hide_render:
            continue
        evaluated = obj.evaluated_get(deps)
        mesh = evaluated.to_mesh()
        offset = len(vertices)
        vertices.extend(evaluated.matrix_world @ v.co for v in mesh.vertices)
        faces.extend(tuple(i + offset for i in f.vertices) for f in mesh.polygons)
        evaluated.to_mesh_clear()
    visibility = BVHTree.FromPolygons(vertices, faces)
    records = []
    for obj in scene.objects:
        if obj.type != 'MESH' or obj.hide_render:
            continue
        is_stone = obj.name == 'GEO-cream-stone-base'
        evaluated = obj.evaluated_get(deps)
        mesh = evaluated.to_mesh()
        assert len(mesh.vertices) == len(obj.data.vertices), obj.name
        uv = obj.data.uv_layers.new(name='PaintingCamera')
        mask = obj.data.color_attributes.new(name='PaintingFacing', type='FLOAT_COLOR', domain='CORNER')
        coords, weights = [], []
        for vertex in mesh.vertices:
            world = evaluated.matrix_world @ vertex.co
            c = world_to_camera_view(scene, camera, world)
            normal = (evaluated.matrix_world.to_3x3().inverted().transposed() @ vertex.normal).normalized()
            facing = max(0, min(1, normal.dot(view) / .22))
            hit, _, _, _ = visibility.ray_cast(world + view * 10, -view, 10.02)
            visible = hit is not None and (hit - world).length < .012
            coords.append((c.x, c.y))
            # The generated plate contains no feet or cast shadows. Its pigment
            # colors the entire real disc; live AO supplies moving contact.
            weight = facing if visible else 0
            if obj.name.startswith(('GEO-leather-boots', 'GEO-MPFB-anatomy')) and (1-c.y)*256 > 209:
                x = max(0,min(image_w-1,int(c.x*image_w))); y = max(0,min(image_h-1,int(c.y*image_h)))
                color = pixels[4*(y*image_w+x):4*(y*image_w+x)+3]
                # Source stone must not become a painted white toe when a foot
                # rolls into camera. Retain the full dark leather volume there.
                if color[0] > .76 and color[1] > .62 and color[2] > .40: weight = 0
            weights.append(weight)
        for loop in obj.data.loops:
            uv.data[loop.index].uv = coords[loop.vertex_index]
            weight = weights[loop.vertex_index]
            mask.data[loop.index].color = (weight, weight, weight, 1)
        evaluated.to_mesh_clear()
        for slot in obj.material_slots:
            material = slot.material.copy()
            slot.material = material
            nodes, links = material.node_tree.nodes, material.node_tree.links
            output = nodes.get('Material Output')
            physical = output.inputs['Surface'].links[0].from_socket
            tex = nodes.new('ShaderNodeTexImage')
            tex.image = stone_paint if is_stone else painting
            tex.extension = 'CLIP'
            mapping = nodes.new('ShaderNodeUVMap')
            mapping.uv_map = uv.name
            links.new(mapping.outputs[0], tex.inputs[0])
            attr = nodes.new('ShaderNodeVertexColor')
            attr.layer_name = mask.name
            alpha = nodes.new('ShaderNodeMath')
            alpha.operation = 'MULTIPLY'
            links.new(attr.outputs['Color'], alpha.inputs[0])
            links.new(tex.outputs['Alpha'], alpha.inputs[1])
            path = nodes.new('ShaderNodeLightPath')
            camera_weight = nodes.new('ShaderNodeMath')
            camera_weight.operation = 'MULTIPLY'
            links.new(alpha.outputs[0], camera_weight.inputs[0])
            links.new(path.outputs['Is Camera Ray'], camera_weight.inputs[1])
            strength = nodes.new('ShaderNodeMath')
            strength.operation = 'MULTIPLY'
            strength.inputs[1].default_value = .90 if is_stone else .96
            links.new(camera_weight.outputs[0], strength.inputs[0])
            pigment = nodes.new('ShaderNodeEmission')
            pigment.name = 'Camera-only painted illumination'
            links.new(tex.outputs['Color'], pigment.inputs['Color'])
            if is_stone:
                ao = nodes.new('ShaderNodeAmbientOcclusion')
                ao.inputs['Distance'].default_value = .075
                contact = nodes.new('ShaderNodeMixRGB')
                contact.blend_type = 'MULTIPLY'
                contact.inputs[0].default_value = .65
                links.new(tex.outputs['Color'], contact.inputs[1])
                links.new(ao.outputs['Color'], contact.inputs[2])
                links.new(contact.outputs[0], pigment.inputs['Color'])
            if obj.name == 'GEO-ash-pike-shaft':
                # Subpixel source-axis disagreement made the slender shaft pale
                # and broken. Keep a continuous ash pigment on its real cylinder.
                links.remove(pigment.inputs['Color'].links[0])
                pigment.inputs['Color'].default_value = (.29, .105, .025, 1)
                links.remove(camera_weight.inputs[0].links[0])
                camera_weight.inputs[0].default_value = 1
            mix = nodes.new('ShaderNodeMixShader')
            links.new(strength.outputs[0], mix.inputs[0])
            links.new(physical, mix.inputs[1])
            links.new(pigment.outputs[0], mix.inputs[2])
            links.new(mix.outputs[0], output.inputs['Surface'])
        records.append({'mesh': obj.name, 'vertices': len(obj.data.vertices),
                        'uv': uv.name, 'stone_pigment': 'stone-registered.png' if is_stone else None, 'visible_vertices': sum(w > 0 for w in weights)})
    (root / 'masters/barbarian-pikeman/projection.json').write_text(json.dumps(records, indent=2))
    print('PROJECTION_OK', len(records), flush=True)
