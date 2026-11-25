"""Render-time port of Spearman's frozen per-part pigment and Eevee emission look.

CPU preview substitutes kit.cpu_look's sun cosine and has no cast shadows.
"""
import json,math,sys
from pathlib import Path
import bpy
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from kit.look import Graph
from kit.cpu_look import graph_for_sun


def linear(value):
    value/=255
    return value/12.92 if value<=.04045 else ((value+.055)/1.055)**2.4


def apply(scene, look_dir, gpu=False):
    palettes=json.loads((look_dir/'palettes.json').read_text())
    direction=Vector((-.4,-.6,.7)).normalized()
    graph=Graph if gpu else graph_for_sun(direction)
    for ob in scene.objects:
        if ob.type!='MESH' or ob.hide_render:continue
        part=ob.get('look_part','skin')
        if ob.name.startswith('Stationary'):part='base'
        if ob.name.startswith('GEO-Rigid bronze'):part='shield'
        if ob.name.startswith('GEO-Rigid spear'):part='spear'
        mat=bpy.data.materials.new('Painted '+ob.name)
        g=graph(mat)
        if part=='base':
            normal=g.node('ShaderNodeNewGeometry').outputs['Normal']
            t=g.math('MAXIMUM',g.dot(normal,(0,0,1)),0)
            colour=g.ramp(t,[(0,tuple(linear(v) for v in (182,138,81))+(1,)),(1,tuple(linear(v) for v in (233,207,160))+(1,))])
            position=g.node('ShaderNodeNewGeometry').outputs['Position']
            shadow=g.math('ADD',0,0)
            for side in ('l','r'):
                center=g.node('ShaderNodeCombineXYZ',name='Contact '+side)
                delta=g.node('ShaderNodeVectorMath',operation='SUBTRACT');g.l.new(position,delta.inputs[0]);g.l.new(center.outputs[0],delta.inputs[1])
                scale=g.node('ShaderNodeVectorMath',operation='MULTIPLY');g.l.new(delta.outputs[0],scale.inputs[0]);scale.inputs[1].default_value=(1/.075,1/.13,0)
                radius=g.node('ShaderNodeVectorMath',operation='DOT_PRODUCT');g.l.new(scale.outputs[0],radius.inputs[0]);g.l.new(scale.outputs[0],radius.inputs[1])
                falloff=g.math('EXPONENT',g.math('MULTIPLY',radius.outputs['Value'],-2))
                strength=g.node('ShaderNodeValue',name='Contact strength '+side)
                shadow=g.math('MAXIMUM',shadow,g.math('MULTIPLY',falloff,strength.outputs[0]))
            colour=g.mix(g.math('MULTIPLY',shadow,.35),colour,(.25,.15,.07,1))
        else:
            pal=palettes[part]
            t=g.math('MULTIPLY_ADD',g.lit(),.75,.2,clamp=True)
            colour=g.ramp(t,[(p,tuple(linear(v) for v in c)+(1,)) for p,c in zip(pal['positions'],pal['colours'])])
            if ob.data.uv_layers.get('Painting camera rest'):
                uv=g.node('ShaderNodeUVMap',uv_map='Painting camera rest').outputs[0]
                paint=g.image(look_dir/f'front-{part}.png',uv).outputs['Color']
                visibility=g.node('ShaderNodeVertexColor',layer_name='Painting visibility').outputs['Color']
                colour=g.mix(visibility,colour,paint)
        cast=g.lit(constant_normal=tuple(direction))
        darkness=g.math('MULTIPLY',g.math('SUBTRACT',1,cast),.16 if part=='base' else .22,clamp=True)
        colour=g.mix(darkness,colour,(.50,.36,.34,1),'MULTIPLY')
        g.emit(colour);ob.data.materials.clear();ob.data.materials.append(mat)
    for ob in list(scene.objects):
        if ob.type=='LIGHT':bpy.data.objects.remove(ob,do_unlink=True)
    light=bpy.data.lights.new('Paint key','SUN');light.energy=math.pi;light.angle=math.radians(24)
    ob=bpy.data.objects.new('Paint key',light);scene.collection.objects.link(ob)
    ob.rotation_euler=(-direction).to_track_quat('-Z','Y').to_euler()
    scene.render.engine='BLENDER_EEVEE' if gpu else 'CYCLES'
    scene.view_settings.view_transform='Standard'


def update_contacts(scene):
    body=bpy.data.objects['SuperHero_Male']
    mesh=body.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()
    base=bpy.data.objects['Stationary cream stone'];nodes=base.data.materials[0].node_tree.nodes
    for side in ('l','r'):
        group_ids={g.index for g in body.vertex_groups if g.name in ('foot_'+side,'ball_'+side)}
        ids=[v.index for v in body.data.vertices if any(g.group in group_ids and g.weight>.4 for g in v.groups)]
        points=[body.matrix_world @ mesh.vertices[i].co for i in ids]
        low=min(v.z for v in points);sole=[p for p in points if p.z<low+.025]
        center=sum(sole,Vector())/len(sole)
        for k in range(3):nodes['Contact '+side].inputs[k].default_value=center[k]
        nodes['Contact strength '+side].outputs[0].default_value=max(0,min(1,(.18-low)/.07))
    body.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh_clear()
