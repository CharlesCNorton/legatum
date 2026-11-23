"""Real Cycles AO and Pointiness bakes on the worked kit; separate fixed bake UVs."""
import bpy,json,os
from pathlib import Path
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/barbarian-musketman';OUT=M/'textures/baked';OUT.mkdir(parents=True,exist_ok=True)

def bake():
 sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=8;sc.render.bake.margin=5;sc.render.bake.use_clear=True;records=[]
 for index,name in enumerate(['GEO-weathered buff waistcoat','GEO-broad weathered hat brim','GEO-carved walnut musket stock']):
  obj=bpy.data.objects[name];bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
  shells=[(m,m.show_render,m.show_viewport) for m in obj.modifiers if m.type=='SOLIDIFY']
  for m,_,_ in shells:m.show_render=m.show_viewport=False
  uv=obj.data.uv_layers.new(name='BakeUV');obj.data.uv_layers.active=uv;uv.active_render=True
  bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.15,island_margin=.025);bpy.ops.object.mode_set(mode='OBJECT')
  mat=obj.data.materials[0].copy();obj.data.materials.clear();obj.data.materials.append(mat);n=mat.node_tree.nodes;l=mat.node_tree.links;bs=n.get('Principled BSDF');output=n.get('Material Output');uvnode=n.new('ShaderNodeUVMap');uvnode.uv_map='BakeUV';maps={}
  for mode in ('AO','curvature'):
   im=bpy.data.images.new(name+' '+mode,width=512,height=512,alpha=False);im.colorspace_settings.name='Non-Color';tex=n.new('ShaderNodeTexImage');tex.image=im;n.active=tex;l.new(uvnode.outputs[0],tex.inputs[0]);old=output.inputs['Surface'].links[0].from_socket
   if mode=='curvature':
    geo=n.new('ShaderNodeNewGeometry');em=n.new('ShaderNodeEmission');l.new(geo.outputs['Pointiness'],em.inputs[0]);l.new(em.outputs[0],output.inputs['Surface'])
   bpy.ops.object.bake(type='AO' if mode=='AO' else 'EMIT')
   if mode=='curvature':l.new(old,output.inputs['Surface']);n.remove(geo);n.remove(em)
   im.filepath_raw=str(OUT/f'{index}-{mode}.png');im.file_format='PNG';im.save();maps[mode]=tex
  old=bs.inputs['Base Color'].links[0].from_socket if bs.inputs['Base Color'].is_linked else None
  ao=n.new('ShaderNodeMixRGB');ao.blend_type='MULTIPLY';ao.inputs[0].default_value=.35
  if old:l.new(old,ao.inputs[1])
  else:ao.inputs[1].default_value=bs.inputs['Base Color'].default_value
  l.new(maps['AO'].outputs['Color'],ao.inputs[2]);l.new(ao.outputs[0],bs.inputs['Base Color'])
  rough=n.new('ShaderNodeMapRange');rough.inputs['From Min'].default_value=.45;rough.inputs['From Max'].default_value=.55;rough.inputs['To Min'].default_value=.85;rough.inputs['To Max'].default_value=.5;l.new(maps['curvature'].outputs['Color'],rough.inputs[0]);l.new(rough.outputs[0],bs.inputs['Roughness'])
  for m,r,v in shells:m.show_render=r;m.show_viewport=v
  records.append({'mesh':name,'size':512,'maps':{key:tex.image.filepath_raw for key,tex in maps.items()},'method':'Cycles AO and Pointiness emission; Solidify disabled while baking'})
 (OUT/'manifest.json').write_text(json.dumps(records,indent=2));bpy.ops.file.pack_all()
