"""Real AO and curvature bakes on separate UVs; original painting projection remains fixed."""
import bpy,os
from pathlib import Path
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/crossbowman';dest=M/'textures/baked';dest.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(M/'model.blend'));sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=8;sc.cycles.device=os.environ.get('CYCLES_DEVICE','CPU')
if sc.cycles.device=='GPU':
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices()
    assert any(d.type=='METAL' for d in prefs.devices),'Metal required'
    for d in prefs.devices:d.use=d.type=='METAL'
sc.render.bake.margin=4;sc.render.bake.use_clear=True
for name in ['GEO-MPFB anatomical crossbowman','GEO-quilted gambeson','GEO-kettle helmet bowl','GEO-crossbow walnut tiller']:
    o=bpy.data.objects[name];states=[(m,m.show_render,m.show_viewport) for m in o.modifiers]
    for m,_,_ in states:
        if m.type in ['SOLIDIFY','SUBSURF','BEVEL']:m.show_render=m.show_viewport=False
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
    uv=o.data.uv_layers.new(name='Baked surface UV');o.data.uv_layers.active=uv;uv.active_render=True;uv_name=uv.name
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(island_margin=.025);bpy.ops.object.mode_set(mode='OBJECT')
    mats=list(o.data.materials);images={}
    for mode in ['AO','CURVATURE']:
        im=bpy.data.images.new(name+' '+mode,width=512,height=512);im.colorspace_settings.name='Non-Color';images[mode]=im;targets=[];saved=[]
        for mat in mats:
            n=mat.node_tree.nodes;l=mat.node_tree.links;tex=n.new('ShaderNodeTexImage');tex.image=im;n.active=tex;targets.append((n,tex))
            if mode=='CURVATURE':
                output=n.get('Material Output');old=output.inputs['Surface'].links[0].from_socket;geo=n.new('ShaderNodeNewGeometry');emit=n.new('ShaderNodeEmission');l.new(geo.outputs['Pointiness'],emit.inputs[0]);l.new(emit.outputs[0],output.inputs['Surface']);saved.append((mat,old,geo,emit))
        bpy.ops.object.bake(type='AO' if mode=='AO' else 'EMIT')
        for mat,old,geo,emit in saved:
            mat.node_tree.links.new(old,mat.node_tree.nodes.get('Material Output').inputs['Surface']);mat.node_tree.nodes.remove(geo);mat.node_tree.nodes.remove(emit)
        for n,tex in targets:n.remove(tex)
        im.filepath_raw=str(dest/(name.replace(' ','-')+'-'+mode+'.png'));im.file_format='PNG';im.save();im.pack()
    for mat in mats:
        n=mat.node_tree.nodes;l=mat.node_tree.links;coord=n.new('ShaderNodeUVMap');coord.uv_map=uv_name
        ao=n.new('ShaderNodeTexImage');ao.image=images['AO'];l.new(coord.outputs[0],ao.inputs[0])
        for old in [x for x in n if x.type=='AMBIENT_OCCLUSION']:
            for link in list(old.outputs['Color'].links):l.new(ao.outputs['Color'],link.to_socket)
        cur=n.new('ShaderNodeTexImage');cur.image=images['CURVATURE'];l.new(coord.outputs[0],cur.inputs[0])
        # Worn ridges become smoother than the cloth/leather recesses.
        ran=n.new('ShaderNodeMapRange');ran.inputs['From Min'].default_value=.3;ran.inputs['From Max'].default_value=.65;ran.inputs['To Min'].default_value=.62 if 'helmet' in name else .9;ran.inputs['To Max'].default_value=.25 if 'helmet' in name else .6;l.new(cur.outputs[0],ran.inputs['Value']);l.new(ran.outputs[0],n.get('Principled BSDF').inputs['Roughness'])
    for m,r,v in states:m.show_render=r;m.show_viewport=v
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(M/'model.blend'));print('BAKED AO and curvature on four surfaces')
