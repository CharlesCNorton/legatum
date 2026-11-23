"""Real UV projection and Cycles AO/curvature bakes on deforming 3D geometry."""
import bpy,os,json,math,hashlib
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/legionary';A=R/'assets/legionary'
bpy.ops.wm.open_mainfile(filepath=str(M/'legionary-plain.blend'));sc=bpy.context.scene
sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=4;sc.render.bake.margin=6
painting=bpy.data.images.load(str(A/'painting-aligned.png'),check_existing=True)
skinpainting=bpy.data.images.load(str(A/'projection-skin.png'),check_existing=True)
fills={k:bpy.data.images.load(str(A/f'fill-{k}.png'),check_existing=True) for k in ['cloth','leather','iron','bronze']}
# Original painted fills extend around backs and undersides; scans are not mistaken for brushwork.
for mat in list(bpy.data.materials):
    if not mat.use_nodes:continue
    n=mat.node_tree.nodes;l=mat.node_tree.links;s=n.get('Principled BSDF')
    if not s:continue
    kind='cloth' if 'wool' in mat.name else 'leather' if 'leather' in mat.name else 'iron' if 'iron' in mat.name else 'bronze' if 'Bronze' in mat.name else None
    if kind:
        tex=n.new('ShaderNodeTexImage');tex.image=fills[kind];tex.projection='BOX';tex.projection_blend=.3
        coord=n.new('ShaderNodeTexCoord');l.new(coord.outputs['Generated'],tex.inputs['Vector'])
        mix=n.new('ShaderNodeMixRGB');mix.inputs[0].default_value=.65 if kind in ['cloth','leather'] else .35;mix.inputs[1].default_value=s.inputs['Base Color'].default_value;l.new(tex.outputs['Color'],mix.inputs[2]);l.new(mix.outputs[0],s.inputs['Base Color'])
        noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=170 if kind=='cloth' else 85;noise.inputs['Detail'].default_value=3
        l.new(coord.outputs['Generated'],noise.inputs['Vector']);bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.18;bump.inputs['Distance'].default_value=.0015;l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],s.inputs['Normal'])
        if kind=='cloth':s.inputs['Sheen Weight'].default_value=.28
    if mat.name.startswith('Skin'):
        s.inputs['Roughness'].default_value=.66;s.inputs['Subsurface Weight'].default_value=.06;s.inputs['Subsurface Radius'].default_value=(1,.3,.15)
    if mat.name=='Cream limestone':
        s.inputs['Base Color'].default_value=(.89,.65,.27,1);s.inputs['Roughness'].default_value=.85
        noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=170;bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.13;bump.inputs['Distance'].default_value=.001;l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],s.inputs['Normal'])
# The scutum gold motif has shallow actual relief aligned with the source pigment.
from array import array
pixels=array('f',[0])*len(painting.pixels);painting.pixels.foreach_get(pixels);w,h=painting.size
ob=bpy.data.objects['GEO-scutum painted convex wood']
bpy.context.view_layer.update()
for v in ob.data.vertices:
    q=world_to_camera_view(sc,sc.camera,ob.matrix_world@v.co);x=max(0,min(w-1,int(q.x*w)));y=max(0,min(h-1,int(q.y*h)));i=4*(y*w+x);r,g,b,a=pixels[i:i+4]
    if a>.5 and r>.25 and g>.10 and r>g*1.1 and g>b*2:v.co.y-=.0025
ob.data.update()

# Bake before adding fixed camera UVs, and pin the bake nodes to their original UV layer.
names=['GEO-bronze helmet bowl','GEO-scutum painted convex wood','GEO-lorica iron band 06','MPFB anatomical male • original topology']
bake_records=[];out=M/'textures/baked';out.mkdir(parents=True,exist_ok=True)
for idx,name in enumerate(names):
    ob=bpy.data.objects[name];bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
    states=[(m,m.show_render,m.show_viewport) for m in ob.modifiers if m.type=='SOLIDIFY']
    for m,_,_ in states:m.show_render=False;m.show_viewport=False
    if not ob.data.uv_layers:
        bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.15,island_margin=.025);bpy.ops.object.mode_set(mode='OBJECT')
    mat=ob.data.materials[0].copy();ob.data.materials[0]=mat;n=mat.node_tree.nodes;l=mat.node_tree.links;s=n.get('Principled BSDF');output=n.get('Material Output');uv=n.new('ShaderNodeUVMap');uv.uv_map=ob.data.uv_layers.active.name
    maps={}
    for mode in ['AO','curvature']:
        im=bpy.data.images.new(f'Legionary {idx} {mode}',512,512,alpha=False);im.colorspace_settings.name='Non-Color';tex=n.new('ShaderNodeTexImage');tex.image=im;n.active=tex
        old=output.inputs['Surface'].links[0].from_socket
        if mode=='curvature':
            geom=n.new('ShaderNodeNewGeometry');em=n.new('ShaderNodeEmission');l.new(geom.outputs['Pointiness'],em.inputs['Color']);l.new(em.outputs[0],output.inputs['Surface'])
        bpy.ops.object.bake(type='AO' if mode=='AO' else 'EMIT')
        if mode=='curvature':l.new(old,output.inputs['Surface']);n.remove(em);n.remove(geom)
        im.filepath_raw=str(out/f'{idx}-{mode}.png');im.file_format='PNG';im.save();l.new(uv.outputs[0],tex.inputs['Vector']);maps[mode]=tex
    base=s.inputs['Base Color'].links[0].from_socket if s.inputs['Base Color'].is_linked else None
    ao=n.new('ShaderNodeMixRGB');ao.blend_type='MULTIPLY';ao.inputs[0].default_value=.45
    if base:l.new(base,ao.inputs[1])
    else:ao.inputs[1].default_value=s.inputs['Base Color'].default_value
    l.new(maps['AO'].outputs[0],ao.inputs[2]);l.new(ao.outputs[0],s.inputs['Base Color'])
    rough=n.new('ShaderNodeMapRange');rough.inputs['From Min'].default_value=.47;rough.inputs['From Max'].default_value=.53;rough.inputs['To Min'].default_value=.55;rough.inputs['To Max'].default_value=.28 if idx<3 else .6;l.new(maps['curvature'].outputs[0],rough.inputs['Value']);l.new(rough.outputs[0],s.inputs['Roughness'])
    for mod,render,viewport in states:mod.show_render=render;mod.show_viewport=viewport
    bake_records.append({'object':name,'AO':maps['AO'].image.filepath_raw,'curvature':maps['curvature'].image.filepath_raw,'size':512})
(out/'manifest.json').write_text(json.dumps(bake_records,indent=2))
# Fixed projected UVs follow bones: no camera modifier, no alpha card, no frame warping.
records=[]
objects=[o for o in sc.objects if o.type=='MESH' and o.name!='Stationary cream stone' and not o.name.startswith(('MPFB system eyes','GEO-pilum'))]
view=(sc.camera.location-Vector((0,0,1))).normalized()
for ob in objects:
    states=[(m,m.show_viewport) for m in ob.modifiers]
    for mod,state in states:
        if mod.type!='ARMATURE':mod.show_viewport=False
    bpy.context.view_layer.update();ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
    assert len(me.vertices)==len(ob.data.vertices),ob.name
    coords=[];weights=[]
    for v in me.vertices:
        world=ev.matrix_world@v.co;q=world_to_camera_view(sc,sc.camera,world)
        normal=(ev.matrix_world.to_3x3().inverted().transposed()@v.normal).normalized()
        coords.append((q.x,q.y));weights.append(max(0,min(1,(normal.dot(view)-.05)/.55)))
    ev.to_mesh_clear()
    for mod,state in states:mod.show_viewport=state
    uv=ob.data.uv_layers.new(name='Painting rest projection');att=ob.data.color_attributes.new(name='Painting facing',type='FLOAT_COLOR',domain='CORNER')
    for i,loop in enumerate(ob.data.loops):uv.data[i].uv=coords[loop.vertex_index];att.data[i].color=(weights[loop.vertex_index],)*3+(1,)
    for idx,old in enumerate(list(ob.data.materials)):
        mat=old.copy();mat.name='Projected '+ob.name;ob.data.materials[idx]=mat;n=mat.node_tree.nodes;l=mat.node_tree.links;s=n.get('Principled BSDF')
        if not s:continue
        tc=n.new('ShaderNodeUVMap');tc.uv_map=uv.name;tex=n.new('ShaderNodeTexImage');tex.image=skinpainting if ob.name.startswith('MPFB anatomical') else painting;tex.extension='CLIP';l.new(tc.outputs[0],tex.inputs[0]);col=n.new('ShaderNodeVertexColor');col.layer_name=att.name
        factor=n.new('ShaderNodeMath');factor.operation='MULTIPLY';l.new(col.outputs[0],factor.inputs[0]);l.new(tex.outputs['Alpha'],factor.inputs[1])
        amount=n.new('ShaderNodeMath');amount.operation='MULTIPLY';amount.inputs[1].default_value=.55 if ob.name.startswith('MPFB anatomical') else .80;l.new(factor.outputs[0],amount.inputs[0])
        mix=n.new('ShaderNodeMixRGB');old=s.inputs['Base Color'].links[0].from_socket if s.inputs['Base Color'].is_linked else None
        if old:l.new(old,mix.inputs[1])
        else:mix.inputs[1].default_value=s.inputs['Base Color'].default_value
        l.new(amount.outputs[0],mix.inputs[0]);l.new(tex.outputs['Color'],mix.inputs[2]);l.new(mix.outputs[0],s.inputs['Base Color'])
        l.new(mix.outputs[0],s.inputs['Emission Color']);s.inputs['Emission Strength'].default_value=.16
    records.append({'object':ob.name,'vertices':len(ob.data.vertices),'mapping':'frozen rest camera UV; facing and painting alpha blend'})
sc['painting_projection']='CC BY 4.0 painting onto real weighted meshes; generated fills on unseen surfaces'
sc['cream_target_srgb']='#E9CFA0'
(M/'projection.json').write_text(json.dumps({'meshes':records,'limitation':'Approximate rest registration; view-dependent painted lighting remains.'},indent=2))
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(M/'legionary.blend'))
print('PAINT_READY',len(records),'meshes; 8 actual bakes')
