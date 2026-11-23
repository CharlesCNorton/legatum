"""Actual Cycles AO and Pointiness bakes; never synthetic cavity maps."""
import bpy, os, json
from pathlib import Path
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/tagmatic-soldier';T=M/'textures';T.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(M/'tagmatic-soldier.blend'));sc=bpy.context.scene
sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=8;sc.render.bake.margin=3
records=[]
for name in ['GEO-convex wooden kite shield','GEO-conical spangenhelm steel','GEO-overlapping steel lamellae']:
 ob=bpy.data.objects[name];bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
 states=[(m,m.show_render,m.show_viewport) for m in ob.modifiers]
 for m,_,_ in states:
  if m.type in ['SOLIDIFY','BEVEL']:m.show_render=m.show_viewport=False
 uv=ob.data.uv_layers.new(name='WearBakeUV');ob.data.uv_layers.active=uv;uv.active_render=True
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.15,island_margin=.03);bpy.ops.object.mode_set(mode='OBJECT')
 maps={}
 for kind in ['AO','CURVATURE']:
  im=bpy.data.images.new(name+' '+kind,width=256,height=256,alpha=False);im.colorspace_settings.name='Non-Color';im.generated_color=(1,1,1,1)
  restores=[]
  for ma in ob.data.materials:
   n=ma.node_tree.nodes;l=ma.node_tree.links;tex=n.new('ShaderNodeTexImage');tex.image=im;n.active=tex
   if kind=='CURVATURE':
    output=n.get('Material Output');old=output.inputs['Surface'].links[0].from_socket
    geom=n.new('ShaderNodeNewGeometry');emit=n.new('ShaderNodeEmission');l.new(geom.outputs['Pointiness'],emit.inputs['Color']);l.new(emit.outputs[0],output.inputs['Surface']);restores.append((ma,old,geom,emit))
  bpy.ops.object.bake(type='AO' if kind=='AO' else 'EMIT')
  for ma,old,geom,emit in restores:
   ma.node_tree.links.new(old,ma.node_tree.nodes.get('Material Output').inputs['Surface']);ma.node_tree.nodes.remove(geom);ma.node_tree.nodes.remove(emit)
  im.filepath_raw=str(T/(name.replace('GEO-','').replace(' ','-')+'-'+kind.lower()+'.png'));im.file_format='PNG';im.save();im.pack();maps[kind]=im
 for ma in ob.data.materials:
  n=ma.node_tree.nodes;l=ma.node_tree.links;s=n.get('Principled BSDF');tc=n.new('ShaderNodeUVMap');tc.uv_map='WearBakeUV'
  ao=n.new('ShaderNodeTexImage');ao.image=maps['AO'];l.new(tc.outputs[0],ao.inputs['Vector']);mix=n.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=.15
  l.new(s.inputs['Base Color'].links[0].from_socket,mix.inputs[1]);l.new(ao.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],s.inputs['Base Color'])
  cur=n.new('ShaderNodeTexImage');cur.image=maps['CURVATURE'];l.new(tc.outputs[0],cur.inputs['Vector']);ramp=n.new('ShaderNodeMapRange');ramp.inputs['From Min'].default_value=.42;ramp.inputs['From Max'].default_value=.58;ramp.inputs['To Min'].default_value=.55;ramp.inputs['To Max'].default_value=.26;l.new(cur.outputs[0],ramp.inputs['Value']);l.new(ramp.outputs[0],s.inputs['Roughness'])
 for m,a,b in states:m.show_render=a;m.show_viewport=b
 records.append({'object':name,'ao':maps['AO'].filepath_raw,'pointiness':maps['CURVATURE'].filepath_raw,'size':256})
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(M/'tagmatic-soldier.blend'));(M/'bakes.json').write_text(json.dumps(records,indent=2));print('BAKES_READY',len(records)*2)
