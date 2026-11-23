"""Bake real geometry AO and Cycles curvature for metal, skin and cloth wear."""
import bpy,os,json
from pathlib import Path
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/spearman-3d-v2';out=M/'textures/baked';out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(M/'spearman.blend'))
sc=bpy.context.scene;sc.render.threads_mode='FIXED';sc.render.threads=4;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=12
sc.render.bake.margin=8;sc.render.bake.use_clear=True
names=['Forged bronze muscle cuirass','Convex bronze aspis','Corinthian helmet crown','MPFB anatomical male • original topology']
records=[]
for idx,name in enumerate(names):
 obj=bpy.data.objects[name];bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
 # Smart UV unwrap authored code geometry; preserve MPFB's native anatomical UVs.
 if not obj.data.uv_layers:
  bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.15,island_margin=.025);bpy.ops.object.mode_set(mode='OBJECT')
 m=obj.data.materials[0].copy();obj.data.materials.clear();obj.data.materials.append(m)
 n=m.node_tree.nodes;l=m.node_tree.links;s=n.get('Principled BSDF');output=next(x for x in n if x.type=='OUTPUT_MATERIAL')
 maps={}
 for mode in ['AO','curvature']:
  image=bpy.data.images.new(f'{name} {mode}',512,512,alpha=False);image.colorspace_settings.name='Non-Color'
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
 if idx<3:
  ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.48;ramp.color_ramp.elements[0].color=(0,0,0,1)
  ramp.color_ramp.elements[1].position=.55;ramp.color_ramp.elements[1].color=(.25,.25,.25,1);l.new(maps['curvature'].outputs[0],ramp.inputs[0])
  wear=n.new('ShaderNodeMixRGB');wear.blend_type='MIX';wear.inputs[2].default_value=(.70,.42,.12,1)
  l.new(ramp.outputs[0],wear.inputs[0]);l.new(ao.outputs[0],wear.inputs[1]);l.new(wear.outputs[0],s.inputs['Base Color'])
 records.append({'object':name,'AO':maps['AO'].image.filepath_raw,'curvature':maps['curvature'].image.filepath_raw,'size':512})
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(M/'spearman.blend'))
(out/'manifest.json').write_text(json.dumps(records,indent=2));print('BAKED',len(records),'AO and curvature pairs')
