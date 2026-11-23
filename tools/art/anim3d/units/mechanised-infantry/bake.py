"""Small genuine AO and Cycles pointiness bakes on the main shield/barrel meshes.
Called within the already gated scene process. Original materials are restored.
"""
import bpy

def bake_finish(folder,objects):
 folder.mkdir(parents=True,exist_ok=True);sc=bpy.context.scene;result=[]
 for o in objects:
  bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
  # Real bevel topology makes Pointiness useful; plain geometry stage already saved.
  for mod in list(o.modifiers):
   if mod.type=='BEVEL':bpy.ops.object.modifier_apply(modifier=mod.name)
  bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(island_margin=.025);bpy.ops.object.mode_set(mode='OBJECT')
  o.data.uv_layers.active.name='SurfaceBake';original=list(o.data.materials)
  temp=bpy.data.materials.new('Temporary bake surface');temp.use_nodes=True;n=temp.node_tree.nodes;l=temp.node_tree.links
  target=n.new('ShaderNodeTexImage');geom=n.new('ShaderNodeNewGeometry');emit=n.new('ShaderNodeEmission');l.new(geom.outputs['Pointiness'],emit.inputs['Color'])
  o.data.materials.clear();o.data.materials.append(temp)
  images={}
  for kind in ['AO','CURVATURE']:
   image=bpy.data.images.new(o.name+' '+kind,width=256,height=256,alpha=False);image.colorspace_settings.name='Non-Color';target.image=image;n.active=target
   if kind=='CURVATURE':l.new(emit.outputs[0],n.get('Material Output').inputs['Surface'])
   bpy.ops.object.bake(type='AO' if kind=='AO' else 'EMIT',margin=4,use_clear=True)
   image.filepath_raw=str(folder/(o.name+'-'+kind+'.png'));image.file_format='PNG';image.save();image.pack();images[kind]=image
  o.data.materials.clear()
  for orig in original:
   m=orig.copy();m.name=o.name+' baked finish';o.data.materials.append(m);n=m.node_tree.nodes;l=m.node_tree.links;s=n.get('Principled BSDF');uv=n.new('ShaderNodeUVMap');uv.uv_map='SurfaceBake'
   ao=n.new('ShaderNodeTexImage');ao.image=images['AO'];l.new(uv.outputs[0],ao.inputs[0]);cur=n.new('ShaderNodeTexImage');cur.image=images['CURVATURE'];l.new(uv.outputs[0],cur.inputs[0])
   originalcolor=s.inputs['Base Color'].links[0].from_socket if s.inputs['Base Color'].is_linked else None
   mix=n.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=.23
   if originalcolor:l.new(originalcolor,mix.inputs[1])
   else:mix.inputs[1].default_value=s.inputs['Base Color'].default_value
   l.new(ao.outputs['Color'],mix.inputs[2]);l.new(mix.outputs[0],s.inputs['Base Color'])
   ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.45;ramp.color_ramp.elements[0].color=(.77,.77,.77,1);ramp.color_ramp.elements[1].position=.55;ramp.color_ramp.elements[1].color=(.43,.43,.43,1);l.new(cur.outputs['Color'],ramp.inputs[0]);l.new(ramp.outputs[0],s.inputs['Roughness'])
  result.append(o.name)
 return result
