"""Real AO and Cycles curvature maps for major visible surfaces."""
import bpy,os
from pathlib import Path
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/barbarian-spearman';T=M/'textures';T.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(M/'barbarian-spearman.blend'));sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device=os.environ.get('CYCLES_DEVICE','CPU');sc.cycles.samples=8
if sc.cycles.device=='GPU':
 prefs=bpy.context.preferences.addons['cycles'].preferences;backend=os.environ.get('CYCLES_BACKEND','METAL');prefs.compute_device_type=backend;prefs.get_devices()
 assert any(d.type==backend for d in prefs.devices),f'No {backend} bake device'
 for d in prefs.devices:d.use=d.type==backend
for name in ['MPFB barbarian anatomy','Linen fitted tunic','Convex oval rawhide shield','Domed iron shield boss']:
 ob=bpy.data.objects[name];bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
 mods=[]
 for mod in ob.modifiers:
  if mod.type in ['SOLIDIFY','BEVEL','SUBSURF']:mods.append((mod,mod.show_render));mod.show_render=False
 uv=ob.data.uv_layers.new(name='Baked surface');ob.data.uv_layers.active=uv
 for layer in ob.data.uv_layers:layer.active_render=layer==uv
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(island_margin=.02);bpy.ops.object.mode_set(mode='OBJECT')
 mat=ob.data.materials[0];n=mat.node_tree.nodes;l=mat.node_tree.links;bs=n.get('Principled BSDF')
 coords=n.new('ShaderNodeUVMap');coords.uv_map='Baked surface'
 for kind in ['AO','curvature']:
  im=bpy.data.images.new(name+' '+kind,width=256,height=256,alpha=False);im.colorspace_settings.name='Non-Color'
  tex=n.new('ShaderNodeTexImage');tex.image=im;n.active=tex;l.new(coords.outputs[0],tex.inputs['Vector'])
  if kind=='curvature':
   output=n.get('Material Output');prior=output.inputs['Surface'].links[0].from_socket
   geom=n.new('ShaderNodeNewGeometry');emit=n.new('ShaderNodeEmission');l.new(geom.outputs['Pointiness'],emit.inputs['Color']);l.new(emit.outputs[0],output.inputs['Surface'])
  bpy.ops.object.bake(type='AO' if kind=='AO' else 'EMIT',margin=4,use_clear=True)
  im.filepath_raw=str(T/(name.replace(' ','-')+'-'+kind+'.png'));im.file_format='PNG';im.save();im.pack()
  if kind=='AO':
   for node in n:
    if node.type=='MIX_RGB' and node.blend_type=='MULTIPLY':l.new(tex.outputs['Color'],node.inputs[2]);break
  else:
   l.new(prior,output.inputs['Surface']);n.remove(emit);n.remove(geom)
   if bs.inputs['Metallic'].default_value==1:
    ramp=next(node for node in n if node.type=='VALTORGB');l.new(tex.outputs['Color'],ramp.inputs[0])
 for mod,value in mods:mod.show_render=value
sc['baked_maps']='Actual 256px AO and Cycles pointiness: anatomy, linen, shield, iron boss'
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(M/'barbarian-spearman.blend'))
print('BAKE_READY')
