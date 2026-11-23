"""Bake actual AO and curvature on key kit surfaces, independently of camera UVs."""
import bpy,os,json
from pathlib import Path
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/byzantine-heir';out=M/'textures/baked';out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(M/'byzantine-heir.blend'));sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=8;sc.render.bake.margin=4
records=[]
for name in ['Lamellar cuirass','Lamellar skirt','Purple shoulder mantle','Heir MPFB anatomy']:
 ob=bpy.data.objects[name];bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
 states=[(mod,mod.show_viewport,mod.show_render) for mod in ob.modifiers if mod.type=='SOLIDIFY']
 for mod,_,_ in states:mod.show_viewport=False;mod.show_render=False
 uv=ob.data.uv_layers.new(name='Baked surface');ob.data.uv_layers.active=uv;uv.active_render=True;uv_name=uv.name
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.15,island_margin=.025);bpy.ops.object.mode_set(mode='OBJECT')
 mat=ob.data.materials[0];n=mat.node_tree.nodes;l=mat.node_tree.links;s=n.get('Principled BSDF');output=next(x for x in n if x.type=='OUTPUT_MATERIAL');maps={}
 for mode in ['AO','curvature']:
  im=bpy.data.images.new(name+' '+mode,256,256,alpha=False);im.colorspace_settings.name='Non-Color';tex=n.new('ShaderNodeTexImage');tex.image=im;n.active=tex;tc=n.new('ShaderNodeUVMap');tc.uv_map=uv_name;l.new(tc.outputs[0],tex.inputs['Vector']);old=output.inputs['Surface'].links[0].from_socket
  if mode=='curvature':
   geo=n.new('ShaderNodeNewGeometry');em=n.new('ShaderNodeEmission');l.new(geo.outputs['Pointiness'],em.inputs['Color']);l.new(em.outputs[0],output.inputs['Surface'])
  bpy.ops.object.bake(type='AO' if mode=='AO' else 'EMIT')
  if mode=='curvature':l.new(old,output.inputs['Surface']);n.remove(em);n.remove(geo)
  im.filepath_raw=str(out/(name.replace(' ','-')+'-'+mode+'.png'));im.file_format='PNG';im.save();maps[mode]=tex
 old=s.inputs['Base Color'].links[0].from_socket;mix=n.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=.16;l.new(old,mix.inputs[1]);l.new(maps['AO'].outputs[0],mix.inputs[2]);l.new(mix.outputs[0],s.inputs['Base Color'])
 if name.startswith('Lamellar'):
  rough=n.new('ShaderNodeMapRange');rough.inputs['From Min'].default_value=.47;rough.inputs['From Max'].default_value=.54;rough.inputs['To Min'].default_value=.58;rough.inputs['To Max'].default_value=.3;l.new(maps['curvature'].outputs[0],rough.inputs[0]);l.new(rough.outputs[0],s.inputs['Roughness'])
 for mod,v,r in states:mod.show_viewport=v;mod.show_render=r
 records.append({'object':name,'size':256,'maps':{k:v.image.filepath_raw for k,v in maps.items()}})
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(M/'byzantine-heir.blend'));(out/'manifest.json').write_text(json.dumps(records,indent=2));(M/'bake-required').unlink(missing_ok=True);print('BAKES_READY')
