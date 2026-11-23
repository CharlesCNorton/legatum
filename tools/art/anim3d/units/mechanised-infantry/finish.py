"""Painted rotating wheel albedo and occlusion-free pigment on the real stone."""
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view


def finish(scene, camera, base, assets):
    wheel_image = bpy.data.images.load(str(assets/'wheel-fill-source.png'))
    stone_image = bpy.data.images.load(str(assets/'stone-projection.png'))
    for im in [wheel_image, stone_image]:
        im.pack()
    for obj in scene.objects:
        wheel = obj.parent if obj.parent and obj.parent.name.startswith('RIG-wheel ') else None
        if obj.type != 'MESH' or not (wheel or obj == base):
            continue
        uv = obj.data.uv_layers.new(name='PaintedSurface')
        for loop in obj.data.loops:
            world = obj.matrix_world @ obj.data.vertices[loop.vertex_index].co
            if wheel:
                p = wheel.matrix_world.inverted() @ world
                radius = wheel['radius']-.008
                coord = (.5+.475*p.x/radius, .5+.475*p.z/radius)
            else:
                p = world_to_camera_view(scene, camera, world)
                coord = (p.x,p.y)
            uv.data[loop.index].uv = coord
        material = bpy.data.materials.new('MAT-painted '+obj.name)
        material.use_nodes = True
        n,l = material.node_tree.nodes,material.node_tree.links
        shader = n.get('Principled BSDF')
        texture=n.new('ShaderNodeTexImage');texture.image=wheel_image if wheel else stone_image
        texture.extension='EXTEND'
        texcoord=n.new('ShaderNodeUVMap');texcoord.uv_map=uv.name
        l.new(texcoord.outputs[0],texture.inputs[0])
        pigment=texture.outputs['Color']
        if wheel:
            dust=n.new('ShaderNodeHueSaturation');dust.inputs['Saturation'].default_value=.72;dust.inputs['Value'].default_value=1.20
            l.new(pigment,dust.inputs['Color']);pigment=dust.outputs[0]
        if obj==base:
            fallback=n.new('ShaderNodeMixRGB');fallback.inputs[1].default_value=(.815,.624,.352,1)
            l.new(texture.outputs['Alpha'],fallback.inputs[0]);l.new(pigment,fallback.inputs[2]);pigment=fallback.outputs[0]
        ao=n.new('ShaderNodeAmbientOcclusion');ao.inputs['Distance'].default_value=.20 if obj==base else .08
        color=n.new('ShaderNodeMixRGB');color.blend_type='MULTIPLY';color.inputs[0].default_value=.60 if obj==base else .38
        l.new(pigment,color.inputs[1]);l.new(ao.outputs['Color'],color.inputs[2])
        l.new(color.outputs[0],shader.inputs['Base Color'])
        shader.inputs['Roughness'].default_value=.83
        # Albedo follows the axle; highlights/shadows come from world lighting.
        # The generated texture has no ellipse or directional painted shadow.
        l.new(color.outputs[0],shader.inputs['Emission Color'])
        shader.inputs['Emission Strength'].default_value=.32 if wheel else .52
        if obj==base:
            painted=n.new('ShaderNodeBsdfPrincipled');painted.inputs['Base Color'].default_value=(0,0,0,1)
            painted.inputs['Specular IOR Level'].default_value=0
            painted.inputs['Emission Strength'].default_value=1;l.new(color.outputs[0],painted.inputs['Emission Color'])
            ray=n.new('ShaderNodeLightPath');weight=n.new('ShaderNodeMath');weight.operation='MULTIPLY';weight.inputs[1].default_value=.90;l.new(ray.outputs['Is Camera Ray'],weight.inputs[0])
            mix=n.new('ShaderNodeMixShader');l.new(weight.outputs[0],mix.inputs[0]);l.new(shader.outputs[0],mix.inputs[1]);l.new(painted.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],n.get('Material Output').inputs['Surface'])
        noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=90
        coords=n.new('ShaderNodeTexCoord');l.new(coords.outputs['Generated'],noise.inputs[0])
        bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.18;bump.inputs['Distance'].default_value=.002
        l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],shader.inputs['Normal'])
        obj.data.materials.clear();obj.data.materials.append(material)
