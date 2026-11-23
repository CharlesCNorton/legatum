"""Local occlusion fills and shadow-free lower-disc painting on solid geometry."""
import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector


def finish_surfaces(assets):
    sc=bpy.context.scene
    wing=bpy.data.objects['Starboard wing • thick tapered airfoil']
    n=wing.data.materials[0].node_tree.nodes;l=wing.data.materials[0].node_tree.links
    source=n['Frozen source pigment'];original=source.inputs[2].links[0].from_socket
    uv=next(x for x in n if x.type=='UVMAP' and x.uv_map=='Frozen rest-camera')
    fill=n.new('ShaderNodeTexImage');fill.name='Generated wing behind propeller'
    fill.image=bpy.data.images.load(str(assets/'occlusion-fill-source.png'));fill.image.pack()
    mapping=n.new('ShaderNodeMapping');mapping.inputs['Scale'].default_value=(.977,.984,1)
    mapping.inputs['Location'].default_value=(.004,.013,0)
    l.new(uv.outputs[0],mapping.inputs[0]);l.new(mapping.outputs[0],fill.inputs['Vector'])
    # Replace only paint occluded by the two foreground blades. A soft transition
    # preserves source brushwork everywhere else and avoids hard material stripes.
    combined=None
    for p0,p1 in [((210,106),(190,66)),((211,104),(237,56))]:
        a=Vector((p0[0]/256,1-p0[1]/256,0));b=Vector((p1[0]/256,1-p1[1]/256,0));ab=b-a
        delta=n.new('ShaderNodeVectorMath');delta.operation='SUBTRACT';l.new(uv.outputs[0],delta.inputs[0]);delta.inputs[1].default_value=a
        dot=n.new('ShaderNodeVectorMath');dot.operation='DOT_PRODUCT';l.new(delta.outputs[0],dot.inputs[0]);dot.inputs[1].default_value=ab/ab.length_squared
        clamp=n.new('ShaderNodeClamp');l.new(dot.outputs['Value'],clamp.inputs[0])
        scaled=n.new('ShaderNodeVectorMath');scaled.operation='SCALE';scaled.inputs[0].default_value=ab;l.new(clamp.outputs[0],scaled.inputs['Scale'])
        dist=n.new('ShaderNodeVectorMath');dist.operation='DISTANCE';l.new(delta.outputs[0],dist.inputs[0]);l.new(scaled.outputs[0],dist.inputs[1])
        mask=n.new('ShaderNodeMapRange');mask.interpolation_type='SMOOTHERSTEP'
        mask.inputs['From Min'].default_value=.008;mask.inputs['From Max'].default_value=.020
        mask.inputs['To Min'].default_value=1;mask.inputs['To Max'].default_value=0;l.new(dist.outputs['Value'],mask.inputs['Value'])
        if combined is None:combined=mask.outputs[0]
        else:
            maximum=n.new('ShaderNodeMath');maximum.operation='MAXIMUM';l.new(combined,maximum.inputs[0]);l.new(mask.outputs[0],maximum.inputs[1]);combined=maximum.outputs[0]
    mix=n.new('ShaderNodeMixRGB');mix.name='Occlusion-only painted repair'
    l.new(combined,mix.inputs[0]);l.new(original,mix.inputs[1]);l.new(fill.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],source.inputs[2])

    base=bpy.data.objects['BASE • stationary cream stone']
    uv=base.data.uv_layers.new(name='Lower disc only')
    for loop in base.data.loops:
        q=world_to_camera_view(sc,sc.camera,base.matrix_world @ base.data.vertices[loop.vertex_index].co)
        uv.data[loop.index].uv=(q.x,q.y)
    image=bpy.data.images.load(str(assets/'projection.png'),check_existing=True);image.pack()
    for material in base.data.materials:
        n=material.node_tree.nodes;l=material.node_tree.links
        tex=n.new('ShaderNodeTexImage');tex.image=image;tex.extension='CLIP'
        coord=n.new('ShaderNodeUVMap');coord.uv_map=uv.name;l.new(coord.outputs[0],tex.inputs[0])
        sep=n.new('ShaderNodeSeparateXYZ');l.new(coord.outputs[0],sep.inputs[0])
        mask=n.new('ShaderNodeMapRange');mask.name='Exclude pedestal and its painted shadow'
        mask.interpolation_type='SMOOTHERSTEP';mask.inputs['From Min'].default_value=1-204/256;mask.inputs['From Max'].default_value=1-195/256
        mask.inputs['To Min'].default_value=.98;mask.inputs['To Max'].default_value=0;l.new(sep.outputs['Y'],mask.inputs[0])
        ray=n.new('ShaderNodeLightPath');factor=n.new('ShaderNodeMath');factor.operation='MULTIPLY'
        l.new(ray.outputs['Is Camera Ray'],factor.inputs[0]);l.new(mask.outputs[0],factor.inputs[1])
        coverage=n.new('ShaderNodeMath');coverage.operation='MULTIPLY'
        l.new(factor.outputs[0],coverage.inputs[0]);l.new(tex.outputs['Alpha'],coverage.inputs[1])
        emission=n.new('ShaderNodeEmission');l.new(tex.outputs[0],emission.inputs[0])
        output=n.get('Material Output');physical=output.inputs[0].links[0].from_socket
        mix=n.new('ShaderNodeMixShader');l.new(coverage.outputs[0],mix.inputs[0]);l.new(physical,mix.inputs[1]);l.new(emission.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],output.inputs[0])
        # Soft limestone grain remains on the live-lit top near the support.
        old_emission=next(node for node in n if node.type=='EMISSION' and node!=emission)
        pigment=old_emission.inputs[0].default_value[:]
        noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=95;noise.inputs['Detail'].default_value=2
        ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=tuple(v*.93 for v in pigment[:3])+(1,)
        ramp.color_ramp.elements[1].color=tuple(min(1,v*1.04) for v in pigment[:3])+(1,)
        l.new(noise.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs[0],old_emission.inputs[0])
