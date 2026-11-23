"""Actual Cycles AO/Pointiness maps for helmet and cuirass, packed in master."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
bpy.ops.wm.open_mainfile(filepath=str(MASTER/'archer.blend'));sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=8;sc.render.threads_mode='FIXED';sc.render.threads=3;sc.render.bake.margin=4
out=MASTER/'textures/baked';out.mkdir(parents=True,exist_ok=True);records=[]
for index,name in enumerate(['GEO-Bronze helmet','GEO-Laced leather cuirass']):
 obj=bpy.data.objects[name];bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
 states=[(m,m.show_render,m.show_viewport) for m in obj.modifiers if m.type=='SOLIDIFY']
 for m,r,v in states:m.show_render=False;m.show_viewport=False
 if not obj.data.uv_layers:
  bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(island_margin=.025);bpy.ops.object.mode_set(mode='OBJECT')
 obj.data.uv_layers.active.name='Bake UV';mat=obj.data.materials[0].copy();obj.data.materials[0]=mat;n=mat.node_tree.nodes;l=mat.node_tree.links;s=n.get('Principled BSDF');output=n.get('Material Output');maps={}
 for mode in ['AO','curvature']:
  im=bpy.data.images.new(name+' '+mode,256,256,alpha=False);im.colorspace_settings.name='Non-Color';tex=n.new('ShaderNodeTexImage');tex.image=im;n.active=tex;uv=n.new('ShaderNodeUVMap');uv.uv_map='Bake UV';l.new(uv.outputs[0],tex.inputs['Vector']);old=output.inputs['Surface'].links[0].from_socket
  if mode=='curvature':
   geo=n.new('ShaderNodeNewGeometry');em=n.new('ShaderNodeEmission');l.new(geo.outputs['Pointiness'],em.inputs['Color']);l.new(em.outputs[0],output.inputs['Surface'])
  bpy.ops.object.bake(type='AO' if mode=='AO' else 'EMIT')
  if mode=='curvature':l.new(old,output.inputs['Surface']);n.remove(em);n.remove(geo)
  im.filepath_raw=str(out/f'{index}-{mode}.png');im.file_format='PNG';im.save();maps[mode]=tex
 base=s.inputs['Base Color'].links[0].from_socket;mix=n.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=.6;l.new(base,mix.inputs[1]);l.new(maps['AO'].outputs[0],mix.inputs[2]);l.new(mix.outputs[0],s.inputs['Base Color'])
 if index==0:
  ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.50;ramp.color_ramp.elements[0].color=(0,0,0,1);ramp.color_ramp.elements[1].position=.54;ramp.color_ramp.elements[1].color=(.6,.6,.6,1);l.new(maps['curvature'].outputs[0],ramp.inputs[0]);wear=n.new('ShaderNodeMixRGB');wear.inputs[2].default_value=(.85,.59,.25,1);l.new(ramp.outputs[0],wear.inputs[0]);l.new(mix.outputs[0],wear.inputs[1]);l.new(wear.outputs[0],s.inputs['Base Color'])
 for m,r,v in states:m.show_render=r;m.show_viewport=v
 records.append({'mesh':name,'maps':{k:v.image.filepath_raw for k,v in maps.items()},'size':256})
(out/'manifest.json').write_text(json.dumps(records,indent=2));save(MASTER/'archer-unpainted.blend');save(MASTER/'archer.blend');log('- Baked actual AO and curvature maps for helmet and laced cuirass; no shared-UV Solidify contamination.')
