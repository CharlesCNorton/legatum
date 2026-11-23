"""Registered stone pigment and continuous wheel paint on complete solid meshes."""
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view


def stone_finish(scene, camera, base, assets, bounds):
    image = bpy.data.images.load(str(assets / 'stone-fill-source.png'))
    image.pack()
    material = base.data.materials[0]
    nodes, links = material.node_tree.nodes, material.node_tree.links
    physical = nodes.get('Principled BSDF')
    uv = base.data.uv_layers.new(name='CleanStone')
    points = [world_to_camera_view(scene, camera, base.matrix_world @ v.co)
              for v in base.data.vertices]
    x0, x1 = min(p.x for p in points), max(p.x for p in points)
    y0, y1 = min(p.y for p in points), max(p.y for p in points)
    # The source fill is registered to the actual disc, not to the gun's bounds.
    # A small inset avoids antialias/fringe pixels; source alpha never cuts mesh.
    left, top, right, bottom = bounds
    width, height = image.size
    for loop in base.data.loops:
        p = points[loop.vertex_index]
        u = (left + 3 + (p.x-x0)/(x1-x0)*(right-left-6))/width
        v = 1-(bottom-3-(p.y-y0)/(y1-y0)*(bottom-top-6))/height
        uv.data[loop.index].uv = (u, v)
    tex = nodes.new('ShaderNodeTexImage'); tex.image = image; tex.extension = 'EXTEND'
    coord = nodes.new('ShaderNodeUVMap'); coord.uv_map = uv.name
    links.new(coord.outputs[0], tex.inputs[0])
    pigment = nodes.new('ShaderNodeBsdfPrincipled')
    pigment.name = 'Clean stone pigment with live contact'
    pigment.inputs['Base Color'].default_value = (0, 0, 0, 1)
    pigment.inputs['Specular IOR Level'].default_value = 0
    pigment.inputs['Emission Strength'].default_value = 1
    ao = nodes.new('ShaderNodeAmbientOcclusion'); ao.inputs['Distance'].default_value = .12
    contact = nodes.new('ShaderNodeMixRGB'); contact.blend_type = 'MULTIPLY'
    contact.inputs[0].default_value = .55
    links.new(tex.outputs['Color'], contact.inputs[1]); links.new(ao.outputs['Color'], contact.inputs[2])
    links.new(contact.outputs[0], pigment.inputs['Emission Color'])
    ray = nodes.new('ShaderNodeLightPath')
    strength = nodes.new('ShaderNodeMath'); strength.operation = 'MULTIPLY'; strength.inputs[1].default_value = .96
    links.new(ray.outputs['Is Camera Ray'], strength.inputs[0])
    mix = nodes.new('ShaderNodeMixShader')
    links.new(strength.outputs[0], mix.inputs[0]); links.new(physical.outputs[0], mix.inputs[1])
    links.new(pigment.outputs[0], mix.inputs[2]); links.new(mix.outputs[0], nodes.get('Material Output').inputs['Surface'])


def wheel_finish(scene, camera, wheels, assets):
    """Keep hub paint rotating while its broad illumination stays in world space.

    This approximates lighting separation; it does not recover intrinsic albedo.
    Rubber receives a continuous physical material separately, because hidden
    tire points overlap unrelated gun parts in the source painting.
    """
    camera_right=camera.rotation_euler.to_matrix() @ Vector((1,0,0))
    records=[]
    for wheel in wheels:
        center=wheel.matrix_world.translation.copy()
        parts=[o for o in wheel.children_recursive if o.type=='MESH']
        radius=max((o.matrix_world@v.co-center).length for o in parts for v in o.data.vertices)
        frame=bpy.data.objects.new('RIG-fixed light '+wheel.name,None)
        scene.collection.objects.link(frame);frame.parent=wheel.parent
        frame.matrix_world.translation=center
        follow=frame.constraints.new('COPY_LOCATION');follow.target=wheel
        frame['role']='non-rolling wheel illumination coordinates'
        for o in parts:
            if any(k in o.name for k in ['Pneumatic tire','Chevron tread','Rubber sidewall']):continue
            light=o.data.color_attributes.new(name='RestWheelLight',type='FLOAT_COLOR',domain='CORNER')
            for loop in o.data.loops:
                q=(o.matrix_world@o.data.vertices[loop.vertex_index].co-center)/radius
                f=max(.45,.80+.22*q.z-.10*q.dot(camera_right))
                light.data[loop.index].color=(f,f,f,1)
            for material in o.data.materials:
                nodes,links=material.node_tree.nodes,material.node_tree.links
                pigment=nodes.get('Camera-only painted illumination')
                if pigment is None:continue
                source=pigment.inputs['Emission Color'].links[0].from_socket
                old_light=nodes.new('ShaderNodeVertexColor');old_light.layer_name=light.name
                neutral=nodes.new('ShaderNodeMixRGB');neutral.blend_type='DIVIDE';neutral.inputs[0].default_value=1
                links.new(source,neutral.inputs[1]);links.new(old_light.outputs['Color'],neutral.inputs[2])
                coord=nodes.new('ShaderNodeTexCoord');coord.object=frame
                dot=nodes.new('ShaderNodeVectorMath');dot.operation='DOT_PRODUCT'
                dot.inputs[1].default_value=(-.10*camera_right.x/radius,-.10*camera_right.y/radius,.22/radius)
                links.new(coord.outputs['Object'],dot.inputs[0])
                add=nodes.new('ShaderNodeMath');add.operation='ADD';add.inputs[1].default_value=.80;links.new(dot.outputs['Value'],add.inputs[0])
                lit=nodes.new('ShaderNodeMixRGB');lit.blend_type='MULTIPLY';lit.inputs[0].default_value=1
                links.new(neutral.outputs[0],lit.inputs[1]);links.new(add.outputs[0],lit.inputs[2]);links.new(lit.outputs[0],pigment.inputs['Emission Color'])
            records.append({'mesh':o.name,'lighting':'rest field divided out, fixed non-rolling field reapplied'})
    return records


def rubber_finish(scene, assets):
    """All-around rubber: generated micro-pigment, real bevels and live lighting.

    Camera projection is unsafe here: rear tire points overlap the gun/axle in
    the painting and later rotate into view. No source-lit rubber patch survives.
    """
    material=bpy.data.materials.new('MAT-continuous dusty rubber')
    material.use_nodes=True
    n,l=material.node_tree.nodes,material.node_tree.links
    bsdf=n.get('Principled BSDF')
    bsdf.inputs['Roughness'].default_value=.78
    bsdf.inputs['Specular IOR Level'].default_value=.28
    tc=n.new('ShaderNodeTexCoord')
    tex=n.new('ShaderNodeTexImage');tex.image=bpy.data.images.get('painted-olive.png')
    tex.projection='BOX';tex.projection_blend=.25;l.new(tc.outputs['Generated'],tex.inputs[0])
    gray=n.new('ShaderNodeRGBToBW');l.new(tex.outputs['Color'],gray.inputs[0])
    ramp=n.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position=.02;ramp.color_ramp.elements[0].color=(.12,.112,.097,1)
    ramp.color_ramp.elements[1].position=.35;ramp.color_ramp.elements[1].color=(.27,.245,.205,1)
    l.new(gray.outputs[0],ramp.inputs[0])
    ao=n.new('ShaderNodeAmbientOcclusion');ao.inputs['Distance'].default_value=.025
    mix=n.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=.55
    l.new(ramp.outputs[0],mix.inputs[1]);l.new(ao.outputs['Color'],mix.inputs[2]);l.new(mix.outputs[0],bsdf.inputs['Base Color'])
    noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=150;noise.inputs['Detail'].default_value=3
    l.new(tc.outputs['Generated'],noise.inputs[0])
    bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.28;bump.inputs['Distance'].default_value=.002
    l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],bsdf.inputs['Normal'])
    tread=material.copy();tread.name='MAT-dusty tread faces'
    tread_ramp=next(node for node in tread.node_tree.nodes if node.type=='VALTORGB')
    tread_ramp.color_ramp.elements[0].color=(.22,.195,.16,1)
    tread_ramp.color_ramp.elements[1].color=(.43,.385,.31,1)
    edge=material.copy();edge.name='MAT-dust on real rubber bevels'
    edge_ramp=next(node for node in edge.node_tree.nodes if node.type=='VALTORGB')
    edge_ramp.color_ramp.elements[0].color=(.36,.30,.23,1)
    edge_ramp.color_ramp.elements[1].color=(.62,.53,.41,1)
    for o in scene.objects:
        if o.type=='MESH' and any(k in o.name for k in ['Pneumatic tire','Chevron tread','Rubber sidewall']):
            # Retain bevel face indices established before topology is applied.
            indices=[p.material_index for p in o.data.polygons]
            o.data.materials.clear();o.data.materials.append(tread if 'Chevron tread' in o.name else material);o.data.materials.append(edge)
            for face,index in zip(o.data.polygons,indices):face.material_index=min(index,1)

