"""Actual AO / Pointiness UV bakes; gentle pigment wear on real airframe meshes."""
import bpy,os,json
from pathlib import Path
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/stealth-bomber';out=M/'textures/baked';out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(M/'stealth-bomber.blend'));sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=4;sc.render.bake.margin=4
records=[]
for index,name in enumerate(('GEO-fuselage','GEO-centre crown','GEO-cockpit')):
    o=bpy.data.objects[name];assert 'BakedWear' not in o.data.uv_layers,'Rebuild before rebaking'
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
    uv=o.data.uv_layers.new(name='BakedWear');o.data.uv_layers.active=uv;uv.active_render=True
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.1,island_margin=.025);bpy.ops.object.mode_set(mode='OBJECT')
    mat=o.data.materials[0];n=mat.node_tree.nodes;l=mat.node_tree.links;bs=n.get('Principled BSDF');output=n.get('Material Output');original=output.inputs['Surface'].links[0].from_socket;maps={}
    coord=n.new('ShaderNodeUVMap');coord.uv_map='BakedWear'
    for mode in ('AO','curvature'):
        im=bpy.data.images.new(f'stealth-bomber-{index}-{mode}',512,512,alpha=False);im.colorspace_settings.name='Non-Color';tex=n.new('ShaderNodeTexImage');tex.image=im;l.new(coord.outputs[0],tex.inputs[0]);n.active=tex
        if mode=='curvature':
            geo=n.new('ShaderNodeNewGeometry');em=n.new('ShaderNodeEmission');l.new(geo.outputs['Pointiness'],em.inputs['Color']);l.new(em.outputs[0],output.inputs['Surface'])
        bpy.ops.object.bake(type='AO' if mode=='AO' else 'EMIT')
        if mode=='curvature':l.new(original,output.inputs['Surface']);n.remove(geo);n.remove(em)
        im.filepath_raw=str(out/f'{index}-{mode}.png');im.file_format='PNG';im.save();maps[mode]=tex
    color=bs.inputs['Base Color'].links[0].from_socket
    grime=n.new('ShaderNodeMixRGB');grime.blend_type='MULTIPLY';grime.inputs[0].default_value=.10;l.new(color,grime.inputs[1]);l.new(maps['AO'].outputs['Color'],grime.inputs[2])
    ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.50;ramp.color_ramp.elements[0].color=(0,0,0,1);ramp.color_ramp.elements[1].position=.62;ramp.color_ramp.elements[1].color=(.09,.09,.09,1);l.new(maps['curvature'].outputs[0],ramp.inputs[0])
    wear=n.new('ShaderNodeMixRGB');wear.inputs[2].default_value=(.60,.61,.57,1);l.new(ramp.outputs[0],wear.inputs[0]);l.new(grime.outputs[0],wear.inputs[1]);l.new(wear.outputs[0],bs.inputs['Base Color']);l.new(wear.outputs[0],n['Camera pigment'].inputs['Color'])
    records.append({'object':name,'resolution':512,'AO':maps['AO'].image.filepath_raw,'curvature':maps['curvature'].image.filepath_raw,'method':'Cycles AO / Pointiness EMIT; 10% grime, bounded edge wear'})
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(M/'stealth-bomber.blend'));(out/'manifest.json').write_text(json.dumps(records,indent=2));print('BAKE COMPLETE',len(records))
