"""Real Cycles AO and pointiness bakes for eagle hood, woven shield and club."""
import bpy,os,json
from pathlib import Path
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/eagle-warrior';bpy.ops.wm.open_mainfile(filepath=str(M/'unpainted.blend'));sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=8;sc.render.bake.margin=3
out=M/'textures/baked';out.mkdir(parents=True,exist_ok=True);records=[]
for name in ['GEO-Convex wicker shield','GEO-Eagle skull dome','GEO-Wooden macuahuitl']:
 o=bpy.data.objects[name];bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
 uv=o.data.uv_layers.new(name='BakeAtlas');o.data.uv_layers.active=uv;uv.active_render=True
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(island_margin=.025);bpy.ops.object.mode_set(mode='OBJECT')
 disabled=[]
 for md in o.modifiers:
  if md.type in ['SOLIDIFY','BEVEL']:disabled.append((md,md.show_render));md.show_render=False
 mat=o.active_material.copy();o.data.materials[0]=mat;n=mat.node_tree.nodes;l=mat.node_tree.links;p=n.get('Principled BSDF');output=n.get('Material Output');original_surface=output.inputs['Surface'].links[0].from_socket
 baked={}
 for kind in ['AO','curvature']:
  im=bpy.data.images.new(name+'-'+kind,256,256,alpha=False);im.colorspace_settings.name='Non-Color';node=n.new('ShaderNodeTexImage');node.image=im;n.active=node
  for no in n:no.select=False
  node.select=True
  if kind=='curvature':
   geometry=n.new('ShaderNodeNewGeometry');em=n.new('ShaderNodeEmission');l.new(geometry.outputs['Pointiness'],em.inputs['Color']);l.new(em.outputs[0],output.inputs['Surface'])
  bpy.ops.object.bake(type='AO' if kind=='AO' else 'EMIT')
  im.filepath_raw=str(out/(name+'-'+kind+'.png'));im.file_format='PNG';im.save();im.pack();baked[kind]=node
  if kind=='curvature':l.new(original_surface,output.inputs['Surface']);n.remove(em);n.remove(geometry)
 tc=n.new('ShaderNodeUVMap');tc.uv_map='BakeAtlas'
 for node in baked.values():l.new(tc.outputs[0],node.inputs['Vector'])
 color=p.inputs['Base Color'].links[0].from_socket if p.inputs['Base Color'].links else None;mix=n.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=.28;
 if color:l.new(color,mix.inputs[1])
 else:mix.inputs[1].default_value=p.inputs['Base Color'].default_value
 l.new(baked['AO'].outputs['Color'],mix.inputs[2]);l.new(mix.outputs[0],p.inputs['Base Color'])
 ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.40;ramp.color_ramp.elements[0].color=(.68,.68,.68,1);ramp.color_ramp.elements[1].position=.56;ramp.color_ramp.elements[1].color=(.37,.37,.37,1);l.new(baked['curvature'].outputs['Color'],ramp.inputs[0]);l.new(ramp.outputs[0],p.inputs['Roughness'])
 for md,value in disabled:md.show_render=value
 records.append({'mesh':name,'maps':['AO','Cycles Pointiness'],'resolution':256})
(M/'bakes.json').write_text(json.dumps(records,indent=2));bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(M/'unpainted.blend'));print('BAKE_OK',len(records)*2)
