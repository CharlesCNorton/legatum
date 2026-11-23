"""Frozen camera colour on full-depth meshes; visibility masks and painted back fills.
Adapted from infantry lead project.py; no billboards, alpha-cut geometry or per-frame reprojection.
"""
import bpy, hashlib, json, os
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view
ROOT=Path(os.environ['ANIM_ROOT']);M=ROOT/'masters/gaesatae';A=ROOT/'assets/gaesatae'
bpy.ops.wm.open_mainfile(filepath=str(M/'plain.blend'));sc=bpy.context.scene
# Curves become full tubular meshes so their UVs also follow motion.
for ob in list(sc.objects):
    if ob.type=='CURVE':
        bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob;bpy.ops.object.convert(target='MESH')
# Surface craft: generated painted fills, fine weave/grain, AO cavities and metal edge wear.
for mat in list(bpy.data.materials):
    if not mat.use_nodes:continue
    n=mat.node_tree.nodes;l=mat.node_tree.links;b=n.get('Principled BSDF')
    if not b:continue
    name=mat.name.lower();coord=n.new('ShaderNodeTexCoord');noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=95;noise.inputs['Detail'].default_value=3;l.new(coord.outputs['Generated'],noise.inputs['Vector'])
    bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.19;bump.inputs['Distance'].default_value=.0015;l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs['Normal'],b.inputs['Normal'])
    if any(w in name for w in ('bronze','iron','gold')):
        b.inputs['Metallic'].default_value=1;b.inputs['Roughness'].default_value=.37
        geo=n.new('ShaderNodeNewGeometry');r=n.new('ShaderNodeValToRGB');r.color_ramp.elements[0].position=.42;r.color_ramp.elements[1].position=.56
        r.color_ramp.elements[0].color=(.08,.08,.08,1);r.color_ramp.elements[1].color=(.75,.75,.75,1);l.new(geo.outputs['Pointiness'],r.inputs[0])
        # High curvature is a smoother polished lip, recesses remain rough.
        rough=n.new('ShaderNodeMapRange');rough.inputs['From Min'].default_value=.1;rough.inputs['From Max'].default_value=.75;rough.inputs['To Min'].default_value=.64;rough.inputs['To Max'].default_value=.26;l.new(r.outputs[0],rough.inputs[0]);l.new(rough.outputs[0],b.inputs['Roughness'])
    kind='skin' if 'skin' in name else 'linen' if 'woven' in name else 'hair' if 'hair' in name else 'wood' if 'shaft' in name else None
    if kind and (A/f'fill-{kind}.png').exists():
        tex=n.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(A/f'fill-{kind}.png'),check_existing=True);tex.projection='BOX';tex.projection_blend=.3;l.new(coord.outputs['Generated'],tex.inputs['Vector'])
        mix=n.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=.65;mix.inputs[1].default_value=b.inputs['Base Color'].default_value;l.new(tex.outputs['Color'],mix.inputs[2]);l.new(mix.outputs[0],b.inputs['Base Color'])
    ao=n.new('ShaderNodeAmbientOcclusion');ao.inputs['Distance'].default_value=.035;ao.samples=8
    mix=n.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=.33
    old=b.inputs['Base Color'].links
    if old:l.new(old[0].from_socket,mix.inputs[1])
    else:mix.inputs[1].default_value=b.inputs['Base Color'].default_value
    l.new(ao.outputs['Color'],mix.inputs[2]);l.new(mix.outputs[0],b.inputs['Base Color'])
    if 'woven' in name:b.inputs['Sheen Weight'].default_value=.22
    if 'skin' in name:b.inputs['Subsurface Weight'].default_value=.02
saved=[]
for ob in sc.objects:
    for mod in ob.modifiers:
        if mod.type in {'SUBSURF','SOLIDIFY','BEVEL'}:saved.append((mod,mod.show_viewport));mod.show_viewport=False
bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();vertices=[];polygons=[];evaluated={}
for ob in sc.objects:
    if ob.type!='MESH' or ob.hide_render:continue
    ev=ob.evaluated_get(deps);me=ev.to_mesh();points=[ob.matrix_world@v.co for v in me.vertices];normals=[(ob.matrix_world.to_3x3().inverted().transposed()@v.normal).normalized() for v in me.vertices]
    off=len(vertices);vertices.extend(points);polygons.extend([tuple(off+i for i in p.vertices) for p in me.polygons]);ev.to_mesh_clear()
    if len(points)!=len(ob.data.vertices):
        masks=[m for m in ob.modifiers if m.type=='MASK' and m.show_viewport]
        for m in masks:m.show_viewport=False
        bpy.context.view_layer.update();ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();points=[ob.matrix_world@v.co for v in me.vertices];normals=[(ob.matrix_world.to_3x3().inverted().transposed()@v.normal).normalized() for v in me.vertices];ev.to_mesh_clear()
        for m in masks:m.show_viewport=True
        bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get()
    evaluated[ob.name]=(points,normals)
tree=BVHTree.FromPolygons(vertices,polygons);view=sc.camera.matrix_world.to_quaternion()@Vector((0,0,1))
im=bpy.data.images.load(str(A/'painting-aligned.png'));coverage={}
for ob in sc.objects:
    if ob.name not in evaluated or 'stationary cream' in ob.name:continue
    points,normals=evaluated[ob.name];assert len(points)==len(ob.data.vertices),ob.name
    uv=ob.data.uv_layers.new(name='Painting rest camera');mask=ob.data.color_attributes.new(name='Rest visibility',type='FLOAT_COLOR',domain='CORNER');weights=[]
    for pos,normal in zip(points,normals):
        hit,_,_,_=tree.ray_cast(pos+view*10,-view,10.03);visible=hit is not None and (hit-pos).length<.018
        weights.append(max(0,min(1,(abs(normal.dot(view))-.025)/.22)) if visible else 0)
    for loop in ob.data.loops:
        p=world_to_camera_view(sc,sc.camera,points[loop.vertex_index]);uv.data[loop.index].uv=(p.x,p.y);w=weights[loop.vertex_index];mask.data[loop.index].color=(w,w,w,1)
    coverage[ob.name]=sum(weights)/max(1,len(weights))
    for i,orig in enumerate(list(ob.data.materials)):
        if not orig or not orig.use_nodes:continue
        mat=orig.copy();mat.name=orig.name+' | painted | '+ob.name;ob.data.materials[i]=mat;n=mat.node_tree.nodes;l=mat.node_tree.links;out=n.get('Material Output');physical=out.inputs['Surface'].links[0].from_socket
        coord=n.new('ShaderNodeUVMap');coord.uv_map=uv.name;tex=n.new('ShaderNodeTexImage');tex.image=im;tex.extension='CLIP';l.new(coord.outputs[0],tex.inputs['Vector'])
        attr=n.new('ShaderNodeVertexColor');attr.layer_name=mask.name;mul=n.new('ShaderNodeMath');mul.operation='MULTIPLY';l.new(attr.outputs['Color'],mul.inputs[0]);l.new(tex.outputs['Alpha'],mul.inputs[1]);strength=n.new('ShaderNodeMath');strength.operation='MULTIPLY';l.new(mul.outputs[0],strength.inputs[0]);strength.inputs[1].default_value=.94
        pigment=n.new('ShaderNodeBsdfPrincipled');pigment.inputs['Base Color'].default_value=(0,0,0,1);pigment.inputs['Roughness'].default_value=1;pigment.inputs['Specular IOR Level'].default_value=0;l.new(tex.outputs['Color'],pigment.inputs['Emission Color']);pigment.inputs['Emission Strength'].default_value=1
        blend=n.new('ShaderNodeMixShader');l.new(strength.outputs[0],blend.inputs[0]);l.new(physical,blend.inputs[1]);l.new(pigment.outputs[0],blend.inputs[2]);l.new(blend.outputs[0],out.inputs['Surface'])
for mod,state in saved:mod.show_viewport=state
sc['projection']='Frozen rest-camera UV; visibility/facing mask; generated hidden fills; genuine 3D anatomy'
sc['projection_source_sha256']=hashlib.sha256((A/'painting-aligned.png').read_bytes()).hexdigest()
(M/'projection.json').write_text(json.dumps(coverage,indent=2))
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(M/'gaesatae.blend'))
print('GAESATAE_TEXTURED_READY')
