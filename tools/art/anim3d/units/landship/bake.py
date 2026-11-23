"""Actual Cycles AO/curvature bakes for hull and sponson physical fallback."""
import bpy,os,json
from pathlib import Path
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/landship';T=M/'textures/baked';T.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(M/'landship.blend'));sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=8
report=[]
for name in ('GEO-near_rhomboid_armour','GEO-central_armoured_hull','GEO-sponson'):
    o=bpy.data.objects[name];bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
    uv=o.data.uv_layers.new(name='WearBake');o.data.uv_layers.active=uv
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(island_margin=.04);bpy.ops.object.mode_set(mode='OBJECT')
    mat=o.data.materials[0].copy();o.data.materials[0]=mat;n=mat.node_tree.nodes;l=mat.node_tree.links;out=n.get('Material Output');surface=out.inputs['Surface'].links[0].from_socket
    maps={}
    for kind in ('AO','curvature'):
        im=bpy.data.images.new(name+'-'+kind,256,256,alpha=False);im.colorspace_settings.name='Non-Color';node=n.new('ShaderNodeTexImage');node.image=im
        for x in n:x.select=False
        node.select=True;n.active=node
        if kind=='curvature':
            geo=n.new('ShaderNodeNewGeometry');e=n.new('ShaderNodeEmission');l.new(geo.outputs['Pointiness'],e.inputs['Color']);l.new(e.outputs[0],out.inputs['Surface'])
        bpy.ops.object.bake(type='AO' if kind=='AO' else 'EMIT',margin=8,use_clear=True)
        path=T/f'{name}-{kind}.png';im.filepath_raw=str(path);im.file_format='PNG';im.save();maps[kind]=node
        l.new(surface,out.inputs['Surface'])
        if kind=='curvature':n.remove(e);n.remove(geo)
    coord=n.new('ShaderNodeUVMap');coord.uv_map='WearBake'
    for node in maps.values():l.new(coord.outputs[0],node.inputs['Vector'])
    s=n.get('Principled BSDF');old=s.inputs['Base Color'].links[0].from_socket if s.inputs['Base Color'].is_linked else None
    mix=n.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=.35
    if old:l.new(old,mix.inputs[1])
    else:mix.inputs[1].default_value=s.inputs['Base Color'].default_value
    l.new(maps['AO'].outputs['Color'],mix.inputs[2]);l.new(mix.outputs[0],s.inputs['Base Color'])
    ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.44;ramp.color_ramp.elements[0].color=(.9,.9,.9,1);ramp.color_ramp.elements[1].position=.57;ramp.color_ramp.elements[1].color=(.43,.43,.43,1);l.new(maps['curvature'].outputs['Color'],ramp.inputs[0]);l.new(ramp.outputs[0],s.inputs['Roughness'])
    report.append({'mesh':name,'maps':['AO','curvature'],'size':256,'engine':'CYCLES','device':'CPU'})
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(M/'landship.blend'));(T/'manifest.json').write_text(json.dumps(report,indent=2));print('SIX ACTUAL BAKES SAVED')
