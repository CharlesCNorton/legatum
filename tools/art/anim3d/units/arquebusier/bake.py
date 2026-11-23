"""Actual Cycles AO and Pointiness bakes for coat, morion and matchlock stock."""
import bpy,os,json
from pathlib import Path
R=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'));M=R/'masters/arquebusier';T=M/'textures';T.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(M/'arquebusier.blend'));sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=4;sc.render.threads_mode='FIXED';sc.render.threads=3
records=[]
for name in ('GEO-slashed doublet','GEO-morion steel bowl','GEO-walnut matchlock butt and fore-end'):
 o=bpy.data.objects[name];bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
 uv=o.data.uv_layers.get('Surface bakes') or o.data.uv_layers.new(name='Surface bakes');o.data.uv_layers.active=uv;uv.active_render=True
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.15,island_margin=.03);bpy.ops.object.mode_set(mode='OBJECT')
 disabled=[]
 for mod in o.modifiers:
  if mod.type=='SOLIDIFY':disabled.append((mod,mod.show_render));mod.show_render=False
 images={}
 for kind in ('AO','CURVATURE'):
  im=bpy.data.images.new(name+' '+kind,width=256,height=256,alpha=False);im.colorspace_settings.name='Non-Color';images[kind]=im;restores=[]
  for ma in o.data.materials:
   n=ma.node_tree.nodes;l=ma.node_tree.links;tex=n.new('ShaderNodeTexImage');tex.image=im;n.active=tex
   if kind=='CURVATURE':
    out=n.get('Material Output');old=out.inputs['Surface'].links[0].from_socket;geo=n.new('ShaderNodeNewGeometry');em=n.new('ShaderNodeEmission');l.new(geo.outputs['Pointiness'],em.inputs[0]);l.new(em.outputs[0],out.inputs['Surface']);restores.append((ma,out,old,geo,em))
  bpy.ops.object.bake(type='AO' if kind=='AO' else 'EMIT',margin=5)
  im.filepath_raw=str(T/(name.replace('GEO-','').replace(' ','-')+'-'+kind.lower()+'.png'));im.file_format='PNG';im.save();im.pack()
  for ma,out,old,geo,em in restores:ma.node_tree.links.new(old,out.inputs['Surface']);ma.node_tree.nodes.remove(geo);ma.node_tree.nodes.remove(em)
 for mod,value in disabled:mod.show_render=value
 for ma in o.data.materials:
  n=ma.node_tree.nodes;l=ma.node_tree.links;p=n.get('Principled BSDF');old=p.inputs['Base Color'].links[0].from_socket if p.inputs['Base Color'].is_linked else None
  if not old:rgb=n.new('ShaderNodeRGB');rgb.outputs[0].default_value=p.inputs['Base Color'].default_value;old=rgb.outputs[0]
  uvn=n.new('ShaderNodeUVMap');uvn.uv_map='Surface bakes';ao=n.new('ShaderNodeTexImage');ao.image=images['AO'];l.new(uvn.outputs[0],ao.inputs[0]);mix=n.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=.25;l.new(old,mix.inputs[1]);l.new(ao.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],p.inputs['Base Color'])
  cur=n.new('ShaderNodeTexImage');cur.image=images['CURVATURE'];l.new(uvn.outputs[0],cur.inputs[0]);ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.40;ramp.color_ramp.elements[0].color=(.6,.6,.6,1);ramp.color_ramp.elements[1].position=.57;ramp.color_ramp.elements[1].color=(.25,.25,.25,1);l.new(cur.outputs[0],ramp.inputs[0])
  if 'morion' in name:l.new(ramp.outputs[0],p.inputs['Roughness'])
 records.append({'object':name,'maps':[im.filepath_raw for im in images.values()],'size':256})
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(M/'arquebusier.blend'));(M/'bakes.json').write_text(json.dumps(records,indent=2));print('Six real AO/curvature bakes saved')
