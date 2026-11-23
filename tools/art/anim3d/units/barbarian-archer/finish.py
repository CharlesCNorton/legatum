"""Frozen rest-camera projection, generated hidden-surface fills, AO/curvature bakes."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
from bpy_extras.object_utils import world_to_camera_view
bpy.ops.wm.open_mainfile(filepath=str(MASTER/'plain.blend'))
sc=settings(256,8);painting=bpy.data.images.load(str(ASSET/'painting-registered.png'));painting.pack()
# Painted hidden-side fills use object-space triplanar sampling, never camera planes.
for m in list(bpy.data.materials):
    if not m.use_nodes:continue
    n=m.node_tree.nodes;l=m.node_tree.links;b=n.get('Principled BSDF')
    if not b:continue
    name=m.name.lower();fill=None
    if 'pelt' in name:fill='fur'
    elif 'flax' in name:fill='linen';b.inputs['Sheen Weight'].default_value=.2
    elif 'leather' in name:fill='leather'
    if fill:
        tex=n.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(ASSET/f'fill-{fill}.png'),check_existing=True);tex.image.pack();tex.projection='BOX';tex.projection_blend=.25
        co=n.new('ShaderNodeTexCoord');l.new(co.outputs['Generated'],tex.inputs['Vector'])
        mix=n.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=.35;mix.inputs[2].default_value=b.inputs['Base Color'].default_value
        l.new(tex.outputs['Color'],mix.inputs[1]);l.new(mix.outputs[0],b.inputs['Base Color'])
    noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=190 if 'linen' in name else 95;noise.inputs['Detail'].default_value=3
    bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.20;bump.inputs['Distance'].default_value=.002
    l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs['Normal'],b.inputs['Normal'])
    if 'stone' in name:
        ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(.70,.49,.24,1);ramp.color_ramp.elements[1].color=(.92,.74,.47,1)
        l.new(noise.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs[0],b.inputs['Base Color'])
# Bake AO/curvature on principal meshes with separate UV from projected brushwork.
baked=[]
for name in ['GEO-Tunic chest','GEO-Ragged pleated skirt','GEO-Wolf hood','GEO-MPFB-anatomy']:
    o=bpy.data.objects[name]
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
    original_mods=[(m,m.show_render,m.show_viewport) for m in o.modifiers if m.type in ('SOLIDIFY','SUBSURF')]
    for m,_,_ in original_mods:m.show_render=False;m.show_viewport=False
    uv=o.data.uv_layers.new(name='BakeUV');o.data.uv_layers.active=uv
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(island_margin=.015);bpy.ops.object.mode_set(mode='OBJECT')
    # Each object gets its own painted material and bake targets.
    for slot in o.material_slots:slot.material=slot.material.copy()
    maps={}
    for kind in ('AO','CURVATURE'):
        im=bpy.data.images.new(name+'-'+kind,width=256,height=256,alpha=False);im.colorspace_settings.name='Non-Color'
        restore=[]
        for slot in o.material_slots:
            m=slot.material;n=m.node_tree.nodes;l=m.node_tree.links
            tex=n.new('ShaderNodeTexImage');tex.image=im;tex.label='Actual '+kind+' bake';n.active=tex
            if kind=='CURVATURE':
                out=n.get('Material Output');link=out.inputs['Surface'].links[0];restore.append((m,link.from_socket));l.remove(link)
                geo=n.new('ShaderNodeNewGeometry');emit=n.new('ShaderNodeEmission');l.new(geo.outputs['Pointiness'],emit.inputs['Color']);l.new(emit.outputs[0],out.inputs['Surface'])
        sc.cycles.samples=4;sc.render.bake.margin=4;sc.render.bake.use_clear=True
        bpy.ops.object.bake(type='AO' if kind=='AO' else 'EMIT')
        for m,socket in restore:m.node_tree.links.new(socket,m.node_tree.nodes['Material Output'].inputs['Surface'])
        out=MASTER/'textures'/f'{name}-{kind}.png';out.parent.mkdir(parents=True,exist_ok=True);im.filepath_raw=str(out);im.file_format='PNG';im.save();im.pack();maps[kind]=im
    for slot in o.material_slots:
        m=slot.material;n=m.node_tree.nodes;l=m.node_tree.links;b=n.get('Principled BSDF');uvn=n.new('ShaderNodeUVMap');uvn.uv_map='BakeUV'
        ao=n.new('ShaderNodeTexImage');ao.image=maps['AO'];l.new(uvn.outputs[0],ao.inputs[0])
        mix=n.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=.28
        if b.inputs['Base Color'].is_linked:l.new(b.inputs['Base Color'].links[0].from_socket,mix.inputs[1])
        else:mix.inputs[1].default_value=b.inputs['Base Color'].default_value
        l.new(ao.outputs['Color'],mix.inputs[2]);l.new(mix.outputs[0],b.inputs['Base Color'])
        cv=n.new('ShaderNodeTexImage');cv.image=maps['CURVATURE'];l.new(uvn.outputs[0],cv.inputs[0])
        ramp=n.new('ShaderNodeMapRange');ramp.inputs['From Min'].default_value=.3;ramp.inputs['From Max'].default_value=.7;ramp.inputs['To Min'].default_value=.95;ramp.inputs['To Max'].default_value=.52
        l.new(cv.outputs['Color'],ramp.inputs['Value']);l.new(ramp.outputs[0],b.inputs['Roughness'])
    for m,r,v in original_mods:m.show_render=r;m.show_viewport=v
    baked.append(name)
# Frozen UVs are calculated from the posed evaluated surface before subdivision.
# Incidence and source alpha fade into fills; geometry stays fully opaque.
projected=[]
projected_materials={}
for o in list(sc.objects):
    if o.type!='MESH' or 'Stationary' in o.name or 'eyes' in o.name or 'Arrow' in o.name:continue
    if not o.data.materials:continue
    mods=[(m,m.show_viewport) for m in o.modifiers if m.type != 'ARMATURE']
    for m,_ in mods:m.show_viewport=False
    bpy.context.view_layer.update();ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
    if len(me.vertices)!=len(o.data.vertices):
        ev.to_mesh_clear()
        for m,v in mods:m.show_viewport=v
        continue
    uv=o.data.uv_layers.new(name='PaintingUV');attr=o.data.attributes.new('PaintConfidence','FLOAT','POINT')
    coords=[]
    for v in me.vertices:
        world=o.matrix_world@v.co;p=world_to_camera_view(sc,sc.camera,world);coords.append((p.x,p.y))
        normal=(o.matrix_world.to_3x3()@v.normal).normalized();view=(sc.camera.location-world).normalized()
        attr.data[v.index].value=max(0,min(1,(normal.dot(view)-.06)*2))*.82
    for lp in o.data.loops:uv.data[lp.index].uv=coords[lp.vertex_index]
    ev.to_mesh_clear()
    for m,v in mods:m.show_viewport=v
    for slot in o.material_slots:
        original=slot.material.name
        if original in projected_materials:
            slot.material=projected_materials[original]
            continue
        m=slot.material.copy();projected_materials[original]=m;slot.material=m;n=m.node_tree.nodes;l=m.node_tree.links;b=n.get('Principled BSDF')
        if not b:continue
        uvn=n.new('ShaderNodeUVMap');uvn.uv_map='PaintingUV';tex=n.new('ShaderNodeTexImage');tex.image=painting;tex.extension='CLIP';l.new(uvn.outputs[0],tex.inputs[0])
        at=n.new('ShaderNodeAttribute');at.attribute_name='PaintConfidence';fac=n.new('ShaderNodeMath');fac.operation='MULTIPLY';l.new(at.outputs['Fac'],fac.inputs[0]);l.new(tex.outputs['Alpha'],fac.inputs[1])
        mix=n.new('ShaderNodeMixRGB');l.new(fac.outputs[0],mix.inputs[0])
        if b.inputs['Base Color'].is_linked:l.new(b.inputs['Base Color'].links[0].from_socket,mix.inputs[1])
        else:mix.inputs[1].default_value=b.inputs['Base Color'].default_value
        l.new(tex.outputs['Color'],mix.inputs[2]);l.new(mix.outputs[0],b.inputs['Base Color'])
        # Partially self-lit brushwork avoids lighting the painted highlights twice.
        l.new(mix.outputs[0],b.inputs['Emission Color']);b.inputs['Emission Strength'].default_value=.18
    projected.append(o.name)
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(MASTER/'master.blend'))
(MASTER/'finish-info.json').write_text(json.dumps({'baked':baked,'projected_meshes':projected,'source':'painting-registered.png','fills':'painted-fills.png'},indent=2))
log(f'Finished {len(projected)} solid projected meshes; actual AO/curvature bakes on {len(baked)} principal surfaces; generated hidden-side fills packed.')
