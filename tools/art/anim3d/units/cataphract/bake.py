"""Actual Cycles AO/Pointiness bakes on the steel helmet, feeding cavity/edge wear."""
import bpy,os,json
from pathlib import Path
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/cataphract';T=M/'textures';T.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(M/'cataphract.blend'));sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=8
ob=bpy.data.objects['Rider bronze helmet bowl'];bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
uv=ob.data.uv_layers.new(name='Baked surface');ob.data.uv_layers.active=uv;uv.active_render=True
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(island_margin=.025);bpy.ops.object.mode_set(mode='OBJECT')
# Inside and outside faces share UVs under Solidify; omit thickness only while baking.
mods=[(m,m.show_render) for m in ob.modifiers]
for m,_ in mods:
 if m.type=='SOLIDIFY':m.show_render=False
mat=ob.data.materials[0];nodes=mat.node_tree.nodes;links=mat.node_tree.links;bsdf=nodes.get('Principled BSDF');output=nodes.get('Material Output');original=output.inputs['Surface'].links[0].from_socket
records={}
for kind in ['ao','curvature']:
 im=bpy.data.images.new('Cataphract baked '+kind,width=256,height=256);im.colorspace_settings.name='Non-Color'
 node=nodes.new('ShaderNodeTexImage');node.image=im;nodes.active=node
 if kind=='curvature':
  geo=nodes.new('ShaderNodeNewGeometry');emit=nodes.new('ShaderNodeEmission');links.new(geo.outputs['Pointiness'],emit.inputs['Color']);links.new(emit.outputs[0],output.inputs['Surface'])
 bpy.ops.object.bake(type='AO' if kind=='ao' else 'EMIT',margin=4,use_clear=True)
 im.filepath_raw=str(T/f'helmet-{kind}.png');im.file_format='PNG';im.save();im.pack();records[kind]=im
 if kind=='curvature':links.new(original,output.inputs['Surface']);nodes.remove(emit)
for mod,state in mods:mod.show_render=state
# Frozen projection remains in its explicit UV channel; these maps use their own atlas.
tc=nodes.new('ShaderNodeUVMap');tc.uv_map=uv.name
for node in nodes:
 if node.type=='TEX_IMAGE' and node.image in records.values():links.new(tc.outputs[0],node.inputs['Vector'])
texao=next(n for n in nodes if n.type=='TEX_IMAGE' and n.image==records['ao'])
texcurve=next(n for n in nodes if n.type=='TEX_IMAGE' and n.image==records['curvature'])
mix=nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=.22;links.new(bsdf.inputs['Base Color'].links[0].from_socket,mix.inputs[1]);links.new(texao.outputs['Color'],mix.inputs[2]);links.new(mix.outputs[0],bsdf.inputs['Base Color'])
ramp=nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.35;ramp.color_ramp.elements[0].color=(.55,.55,.55,1);ramp.color_ramp.elements[1].position=.65;ramp.color_ramp.elements[1].color=(.22,.22,.22,1);links.new(texcurve.outputs['Color'],ramp.inputs[0]);links.new(ramp.outputs['Color'],bsdf.inputs['Roughness'])
bpy.ops.wm.save_as_mainfile(filepath=str(M/'cataphract.blend'))
(M/'bakes.json').write_text(json.dumps({'method':'Cycles AO and emitted Pointiness, 256px, 8 samples','object':ob.name,'files':[str(T/f'helmet-{k}.png') for k in records]},indent=2))
print('CATAPHRACT_BAKES_READY')
