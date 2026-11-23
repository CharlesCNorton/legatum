"""Actual UV AO/curvature bakes; avoid Solidify's overlapping inner surfaces."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
bpy.ops.wm.open_mainfile(filepath=str(M/'peltast.blend'));sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=8;sc.render.bake.margin=6
out=M/'textures/baked';out.mkdir(exist_ok=True,parents=True);records=[]
for idx,name in enumerate(['GEO-Dished wicker crescent pelta','GEO-Folded red chiton','GEO-MPFB peltast anatomy']):
 o=bpy.data.objects[name];bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
 states=[(m,m.show_render,m.show_viewport) for m in o.modifiers if m.type=='SOLIDIFY']
 for m,_,_ in states:m.show_render=m.show_viewport=False
 uv=o.data.uv_layers.new(name='Baked surface UV');o.data.uv_layers.active=uv;uv.active_render=True
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.15,island_margin=.02);bpy.ops.object.mode_set(mode='OBJECT')
 m=o.data.materials[0];n=m.node_tree.nodes;l=m.node_tree.links;s=n.get('Principled BSDF');output=next(x for x in n if x.type=='OUTPUT_MATERIAL');coord=n.new('ShaderNodeUVMap');coord.uv_map=uv.name;maps={}
 for kind in ['AO','curvature']:
  im=bpy.data.images.new(name+' '+kind,512,512,alpha=False);im.colorspace_settings.name='Non-Color';tex=n.new('ShaderNodeTexImage');tex.image=im;n.active=tex;l.new(coord.outputs[0],tex.inputs['Vector']);old=output.inputs['Surface'].links[0].from_socket
  if kind=='curvature':
   geo=n.new('ShaderNodeNewGeometry');em=n.new('ShaderNodeEmission');l.new(geo.outputs['Pointiness'],em.inputs[0]);l.new(em.outputs[0],output.inputs['Surface'])
  bpy.ops.object.bake(type='AO' if kind=='AO' else 'EMIT')
  if kind=='curvature':l.new(old,output.inputs['Surface']);n.remove(em);n.remove(geo)
  im.filepath_raw=str(out/f'{idx}-{kind}.png');im.file_format='PNG';im.save();maps[kind]=tex
 base=s.inputs['Base Color'].links[0].from_socket;mul=n.new('ShaderNodeMixRGB');mul.blend_type='MULTIPLY';mul.inputs[0].default_value=.32;l.new(base,mul.inputs[1]);l.new(maps['AO'].outputs[0],mul.inputs[2]);l.new(mul.outputs[0],s.inputs['Base Color'])
 rough=n.new('ShaderNodeMapRange');rough.inputs['From Min'].default_value=.42;rough.inputs['From Max'].default_value=.58;rough.inputs['To Min'].default_value=.86;rough.inputs['To Max'].default_value=.62;l.new(maps['curvature'].outputs[0],rough.inputs[0]);l.new(rough.outputs[0],s.inputs['Roughness'])
 for mod,a,b in states:mod.show_render=a;mod.show_viewport=b
 records.append({'object':name,'size':512,'maps':{k:v.image.filepath_raw for k,v in maps.items()},'purpose':'AO cavity shading and curvature roughness variation'})
save('peltast.blend');(out/'manifest.json').write_text(json.dumps(records,indent=2));log('- Baked real 512 px AO and curvature on anatomy, red chiton and pelta; AO drives recesses and curvature drives surface roughness. Solidify disabled only during baking.')
