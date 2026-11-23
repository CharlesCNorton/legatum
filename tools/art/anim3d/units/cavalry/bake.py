"""Bake real geometry AO and Cycles curvature for metal, skin and cloth wear."""
import bpy,os,json
from pathlib import Path
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/cavalry';out=M/'textures/baked';out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(M/'cavalry.blend'))
sc=bpy.context.scene;sc.render.threads_mode='FIXED';sc.render.threads=3;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=6
sc.render.bake.margin=8;sc.render.bake.use_clear=True
names=['GEO-kepi-crown','Rider MPFB CC0 anatomy']
records=[]
for idx,name in enumerate(names):
 obj=bpy.data.objects[name];bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
 # Smart UV unwrap authored code geometry; preserve MPFB's native anatomical UVs.
 if not obj.data.uv_layers:
  bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.15,island_margin=.025);bpy.ops.object.mode_set(mode='OBJECT')
 disabled=[m for m in obj.modifiers if m.type=='SOLIDIFY' and m.show_render]
 for mod in disabled:mod.show_render=False
 m=obj.data.materials[0].copy();obj.data.materials.clear();obj.data.materials.append(m)
 n=m.node_tree.nodes;l=m.node_tree.links;s=n.get('Principled BSDF');output=next(x for x in n if x.type=='OUTPUT_MATERIAL')
 maps={}
 for mode in ['AO','curvature']:
  image=bpy.data.images.new(f'{name} {mode}',256,256,alpha=False);image.colorspace_settings.name='Non-Color'
  tex=n.new('ShaderNodeTexImage');tex.image=image;n.active=tex
  old=output.inputs['Surface'].links[0].from_socket
  if mode=='curvature':
   geom=n.new('ShaderNodeNewGeometry');em=n.new('ShaderNodeEmission');l.new(geom.outputs['Pointiness'],em.inputs['Color']);l.new(em.outputs[0],output.inputs['Surface'])
  bpy.ops.object.bake(type='AO' if mode=='AO' else 'EMIT')
  if mode=='curvature':l.new(old,output.inputs['Surface']);n.remove(em);n.remove(geom)
  image.filepath_raw=str(out/f'{idx}-{mode}.png');image.file_format='PNG';image.save();maps[mode]=tex
 base=s.inputs['Base Color'].links[0].from_socket if s.inputs['Base Color'].is_linked else None
 if not base:
  rgb=n.new('ShaderNodeRGB');rgb.outputs[0].default_value=s.inputs['Base Color'].default_value;base=rgb.outputs[0]
 ao=n.new('ShaderNodeMixRGB');ao.blend_type='MULTIPLY';ao.inputs[0].default_value=.7;l.new(base,ao.inputs[1]);l.new(maps['AO'].outputs[0],ao.inputs[2]);l.new(ao.outputs[0],s.inputs['Base Color'])
 if False: # Cap is cloth; metal-only edge tint does not apply.
  ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.48;ramp.color_ramp.elements[0].color=(0,0,0,1)
  ramp.color_ramp.elements[1].position=.55;ramp.color_ramp.elements[1].color=(.25,.25,.25,1);l.new(maps['curvature'].outputs[0],ramp.inputs[0])
  wear=n.new('ShaderNodeMixRGB');wear.blend_type='MIX';wear.inputs[2].default_value=(.70,.42,.12,1)
  l.new(ramp.outputs[0],wear.inputs[0]);l.new(ao.outputs[0],wear.inputs[1]);l.new(wear.outputs[0],s.inputs['Base Color'])
 for mod in disabled:mod.show_render=True
 records.append({'object':name,'AO':maps['AO'].image.filepath_raw,'curvature':maps['curvature'].image.filepath_raw,'size':256})
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(M/'cavalry.blend'))
(out/'manifest.json').write_text(json.dumps(records,indent=2));print('BAKED',len(records),'AO and curvature pairs')
# The skinned horse needs one shared UV bake across all its material regions.
obj=bpy.data.objects['Horse'];bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
if not obj.data.uv_layers:
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.15,island_margin=.02);bpy.ops.object.mode_set(mode='OBJECT')
mats=list(dict.fromkeys(obj.data.materials));maps={}
for mode in ['AO','curvature']:
 image=bpy.data.images.new('Horse '+mode,512,512,alpha=False);image.colorspace_settings.name='Non-Color';restore=[]
 for m in mats:
  n=m.node_tree.nodes;l=m.node_tree.links;tex=n.new('ShaderNodeTexImage');tex.image=image;n.active=tex
  output=next(x for x in n if x.type=='OUTPUT_MATERIAL');old=output.inputs['Surface'].links[0].from_socket
  if mode=='curvature':
   geom=n.new('ShaderNodeNewGeometry');em=n.new('ShaderNodeEmission');l.new(geom.outputs['Pointiness'],em.inputs['Color']);l.new(em.outputs[0],output.inputs['Surface']);restore.append((m,old,em,geom))
 bpy.ops.object.bake(type='AO' if mode=='AO' else 'EMIT')
 for m,old,em,geom in restore:
  output=next(x for x in m.node_tree.nodes if x.type=='OUTPUT_MATERIAL');m.node_tree.links.new(old,output.inputs['Surface']);m.node_tree.nodes.remove(em);m.node_tree.nodes.remove(geom)
 image.filepath_raw=str(out/f'horse-{mode}.png');image.file_format='PNG';image.save();maps[mode]=image
for m in mats:
 n=m.node_tree.nodes;l=m.node_tree.links;s=n.get('Principled BSDF');base=s.inputs['Base Color'].links[0].from_socket if s.inputs['Base Color'].is_linked else None
 if not base:
  rgb=n.new('ShaderNodeRGB');rgb.outputs[0].default_value=s.inputs['Base Color'].default_value;base=rgb.outputs[0]
 tex=n.new('ShaderNodeTexImage');tex.image=maps['AO'];mix=n.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=.75;l.new(base,mix.inputs[1]);l.new(tex.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],s.inputs['Base Color'])
 if m.name in ['Bay coat','Bay shaded muscle','Bay warm highlights']:
  tex=n.new('ShaderNodeTexImage');tex.image=maps['curvature'];ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.47;ramp.color_ramp.elements[0].color=(.34,.19,.09,1);ramp.color_ramp.elements[1].position=.56;ramp.color_ramp.elements[1].color=(1,.86,.61,1);l.new(tex.outputs[0],ramp.inputs[0]);paint=n.new('ShaderNodeMixRGB');paint.blend_type='MULTIPLY';paint.inputs[0].default_value=.48;l.new(mix.outputs[0],paint.inputs[1]);l.new(ramp.outputs[0],paint.inputs[2]);l.new(paint.outputs[0],s.inputs['Base Color'])
records.append({'object':'Horse','AO':maps['AO'].filepath_raw,'curvature':maps['curvature'].filepath_raw,'size':512})
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(M/'cavalry.blend'));(out/'manifest.json').write_text(json.dumps(records,indent=2))

import shutil
shutil.copyfile(M/'cavalry.blend',M/'cavalry-unpainted.blend')
