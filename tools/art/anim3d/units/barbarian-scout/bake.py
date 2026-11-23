"""Real Cycles AO and Pointiness bakes on the scout's principal surfaces."""
import bpy,os,json
from pathlib import Path
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/barbarian-scout';out=M/'textures/baked';out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(M/'barbarian-scout.blend'));sc=bpy.context.scene
sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=8
sc.render.bake.use_clear=True;sc.render.bake.margin=4;sc.render.bake.use_selected_to_active=False
report={}
for name in ['GEO-anatomy','GEO-wolf-pelt-cowl','GEO-forged-axe-head']:
    o=bpy.data.objects[name];bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
    uv=o.data.uv_layers.new(name='SurfaceBake');o.data.uv_layers.active=uv;uv.active_render=True
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(island_margin=.03);bpy.ops.object.mode_set(mode='OBJECT')
    disabled=[]
    for mod in o.modifiers:
        if mod.type=='SOLIDIFY':disabled.append(mod);mod.show_render=False;mod.show_viewport=False
    maps={}
    for mode in ('AO','CURVATURE'):
        img=bpy.data.images.new(name+'-'+mode,256,256,alpha=False);img.colorspace_settings.name='Non-Color'
        saved=[];nodes=[]
        for mat in o.data.materials:
            ns=mat.node_tree.nodes;ls=mat.node_tree.links
            tex=ns.new('ShaderNodeTexImage');tex.image=img;ns.active=tex;tex.select=True;nodes.append((mat,tex))
            if mode=='CURVATURE':
                output=ns.get('Material Output');previous=output.inputs['Surface'].links[0].from_socket
                geom=ns.new('ShaderNodeNewGeometry');em=ns.new('ShaderNodeEmission');ls.new(geom.outputs['Pointiness'],em.inputs[0]);ls.new(em.outputs[0],output.inputs['Surface']);saved.append((mat,output,previous,geom,em))
        bpy.ops.object.bake(type='AO' if mode=='AO' else 'EMIT')
        for mat,output,previous,geom,em in saved:
            mat.node_tree.links.new(previous,output.inputs['Surface']);mat.node_tree.nodes.remove(geom);mat.node_tree.nodes.remove(em)
        img.filepath_raw=str(out/(name+'-'+mode+'.png'));img.file_format='PNG';img.save();img.pack();maps[mode]=img
        for mat,tex in nodes:mat.node_tree.nodes.remove(tex)
    for mod in disabled:mod.show_render=True;mod.show_viewport=True
    o.data.uv_layers['PaintingRest'].active_render=True
    for mat in o.data.materials:
        ns=mat.node_tree.nodes;ls=mat.node_tree.links;bs=ns.get('Principled BSDF')
        u=ns.new('ShaderNodeUVMap');u.uv_map='SurfaceBake'
        ao=ns.new('ShaderNodeTexImage');ao.image=maps['AO'];ls.new(u.outputs[0],ao.inputs[0])
        ramp=ns.new('ShaderNodeMapRange');ramp.inputs['To Min'].default_value=.78;ramp.inputs['To Max'].default_value=1.;ls.new(ao.outputs['Color'],ramp.inputs[0])
        mul=ns.new('ShaderNodeMixRGB');mul.blend_type='MULTIPLY';mul.inputs[0].default_value=1
        prior=bs.inputs['Base Color'].links[0].from_socket;ls.new(prior,mul.inputs[1]);ls.new(ramp.outputs[0],mul.inputs[2]);ls.new(mul.outputs[0],bs.inputs['Base Color'])
        if name=='GEO-forged-axe-head':
            cur=ns.new('ShaderNodeTexImage');cur.image=maps['CURVATURE'];ls.new(u.outputs[0],cur.inputs[0])
            rough=ns.new('ShaderNodeMapRange');rough.inputs['From Min'].default_value=.3;rough.inputs['From Max'].default_value=.7;rough.inputs['To Min'].default_value=.58;rough.inputs['To Max'].default_value=.22;ls.new(cur.outputs['Color'],rough.inputs[0]);ls.new(rough.outputs[0],bs.inputs['Roughness'])
    report[name]={k:v.filepath_raw for k,v in maps.items()}
(M/'bakes.json').write_text(json.dumps(report,indent=2));sc['actual_bakes']='Cycles AO and Pointiness, 256 px, anatomy/cowl/axe'
bpy.ops.wm.save_as_mainfile(filepath=str(M/'barbarian-scout.blend'))
print('AO_CURVATURE_BAKES_READY')
