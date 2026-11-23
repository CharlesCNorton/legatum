"""Actual AO/curvature bakes plus fixed rest-camera projection, not a billboard."""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
from bpy_extras.object_utils import world_to_camera_view
bpy.ops.wm.open_mainfile(filepath=str(M/'medjay-plain.blend'));sc=configure();sc.cycles.samples=6
# Freeze actual finished surfaces before calibrating UVs. The editable original
# MPFB macro body remains in round1-cpu; the plain cage and weights survive.
for obj in list(sc.objects):
 if obj.type not in {'MESH','CURVE'}:continue
 bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
 if obj.type=='CURVE':bpy.ops.object.convert(target='MESH')
 if obj.data.shape_keys:bpy.ops.object.shape_key_remove(all=True,apply_mix=True)
 deform=[(m,m.show_viewport) for m in obj.modifiers if m.type in {'ARMATURE','MASK'}]
 for m,_ in deform:m.show_viewport=False
 for mod in list(obj.modifiers):
  if mod.type in {'ARMATURE','MASK'}:continue
  if mod.type=='SUBSURF' and mod.levels==0:obj.modifiers.remove(mod);continue
  mod.show_viewport=True
  bpy.ops.object.modifier_apply(modifier=mod.name)
 for m,enabled in deform:m.show_viewport=enabled
 bpy.context.view_layer.update()
painting=bpy.data.images.load(str(A/'painting-aligned.png'),check_existing=True)
# Work in stable rest camera coordinates. UVs are fixed to vertices before animation.
objects=[o for o in sc.objects if o.type=='MESH' and o.name in ['Medjay MPFB anatomical body','Pleated linen kilt','Overlapping pleated apron','Convex painted oxhide shield','Faceted bronze spearhead','Ostrich feather vane','Woven headband','Medjay anatomical eyes']]
records=[];baked=M/'textures/baked';baked.mkdir(parents=True,exist_ok=True)
for obj in objects:
 bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
 if not obj.data.uv_layers:
  bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.15,island_margin=.025);bpy.ops.object.mode_set(mode='OBJECT')
 original_uv=obj.data.uv_layers.active.name

 if obj.name=='Medjay anatomical eyes':obj.data.materials.clear();obj.data.materials.append(material('Brown eye fill',(.045,.018,.008),rough=.45))
 mat=obj.data.materials[0].copy();mat.name=obj.name+' painted material';obj.data.materials.clear();obj.data.materials.append(mat);n=mat.node_tree.nodes;l=mat.node_tree.links;s=n.get('Principled BSDF');out=n.get('Material Output')
 states=[(m,m.show_render,m.show_viewport) for m in obj.modifiers]
 for m,_,_ in states:
  if m.type not in ['ARMATURE']:m.show_render=False;m.show_viewport=False
 bpy.context.view_layer.update()
 maps={}
 for mode in ['AO','curvature']:
  im=bpy.data.images.new(obj.name+' '+mode,256,256,alpha=False);im.colorspace_settings.name='Non-Color';tex=n.new('ShaderNodeTexImage');tex.image=im;n.active=tex;uv=n.new('ShaderNodeUVMap');uv.uv_map=original_uv;l.new(uv.outputs[0],tex.inputs['Vector']);old=out.inputs['Surface'].links[0].from_socket
  if mode=='curvature':
   geom=n.new('ShaderNodeNewGeometry');em=n.new('ShaderNodeEmission');l.new(geom.outputs['Pointiness'],em.inputs['Color']);l.new(em.outputs[0],out.inputs['Surface'])
  sc.render.bake.margin=5;bpy.ops.object.bake(type='AO' if mode=='AO' else 'EMIT')
  if mode=='curvature':l.new(old,out.inputs['Surface']);n.remove(em);n.remove(geom)
  im.filepath_raw=str(baked/f'{obj.name}-{mode}.png');im.file_format='PNG';im.save();maps[mode]=tex
 # Keep broad painted shading; scene AO contributes gentle real cavity depth.
 old=s.inputs['Base Color'].links[0].from_socket if s.inputs['Base Color'].is_linked else None
 ao=n.new('ShaderNodeMixRGB');ao.blend_type='MULTIPLY';ao.inputs[0].default_value=.30
 if old:l.new(old,ao.inputs[1])
 else:ao.inputs[1].default_value=s.inputs['Base Color'].default_value
 l.new(maps['AO'].outputs['Color'],ao.inputs[2]);l.new(ao.outputs[0],s.inputs['Base Color'])
 # Curvature-driven polish on metal, fine roughness variation on organics.
 rough=n.new('ShaderNodeMapRange');rough.inputs['From Min'].default_value=.45;rough.inputs['From Max'].default_value=.55;rough.inputs['To Min'].default_value=.40 if 'spearhead' in obj.name else .88;rough.inputs['To Max'].default_value=.22 if 'spearhead' in obj.name else .62;l.new(maps['curvature'].outputs['Color'],rough.inputs['Value']);l.new(rough.outputs[0],s.inputs['Roughness'])
 ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();assert len(me.vertices)==len(obj.data.vertices),(obj.name,'topology changed')
 view=(sc.camera.location-Vector((0,0,1))).normalized();coords=[];weights=[]
 for v in me.vertices:
  world=ev.matrix_world@v.co;q=world_to_camera_view(sc,sc.camera,world);coords.append((q.x,q.y));normal=(ev.matrix_world.to_3x3().inverted().transposed()@v.normal).normalized();weights.append(max(0,min(1,(normal.dot(view)-.01)/.40)))
 ev.to_mesh_clear();uv=obj.data.uv_layers.new(name='Rest painting projection');attr=obj.data.color_attributes.new(name='Paint confidence',type='FLOAT_COLOR',domain='CORNER')
 for i,loop in enumerate(obj.data.loops):uv.data[i].uv=coords[loop.vertex_index];attr.data[i].color=(weights[loop.vertex_index],)*3+(1,)
 obj.data.uv_layers[original_uv].active_render=True
 for mod,render,viewport in states:mod.show_render=render;mod.show_viewport=viewport
 tex=n.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(A/'projection-skin.png'),check_existing=True) if obj.name=='Medjay MPFB anatomical body' else painting;tex.extension='CLIP';tc=n.new('ShaderNodeUVMap');tc.uv_map=uv.name;l.new(tc.outputs[0],tex.inputs['Vector']);att=n.new('ShaderNodeVertexColor');att.layer_name=attr.name;factor=n.new('ShaderNodeMath');factor.operation='MULTIPLY';l.new(att.outputs[0],factor.inputs[0]);l.new(tex.outputs['Alpha'],factor.inputs[1])
 mix=n.new('ShaderNodeMixRGB');l.new(factor.outputs[0],mix.inputs[0]);l.new(ao.outputs[0],mix.inputs[1]);l.new(tex.outputs['Color'],mix.inputs[2]);l.new(mix.outputs[0],s.inputs['Base Color'])
 # The source includes painted illumination. Camera rays see that pigment;
 # shadow/bounce rays and revealed surfaces retain the generated-fill BSDF.
 # This avoids both double lighting and using the painted skin as a lamp.
 pigment=n.new('ShaderNodeBsdfPrincipled');pigment.name='Camera painted pigment'
 pigment.inputs['Base Color'].default_value=(0,0,0,1)
 pigment.inputs['Specular IOR Level'].default_value=0
 pigment.inputs['Emission Strength'].default_value=1
 l.new(tex.outputs['Color'],pigment.inputs['Emission Color'])
 physical=mix.inputs[1].links[0].from_socket
 l.new(physical,s.inputs['Base Color'])
 path=n.new('ShaderNodeLightPath');camera=n.new('ShaderNodeMath');camera.operation='MULTIPLY'
 l.new(path.outputs['Is Camera Ray'],camera.inputs[0]);l.new(factor.outputs[0],camera.inputs[1])
 strength=n.new('ShaderNodeMath');strength.operation='MULTIPLY';strength.inputs[1].default_value=.96;l.new(camera.outputs[0],strength.inputs[0])
 fill_pigment=n.new('ShaderNodeBsdfPrincipled');fill_pigment.name='Camera unseen painted fill';fill_pigment.inputs['Base Color'].default_value=(0,0,0,1);fill_pigment.inputs['Specular IOR Level'].default_value=0;fill_pigment.inputs['Emission Strength'].default_value=1;l.new(ao.outputs[0],fill_pigment.inputs['Emission Color'])
 fill_weight=n.new('ShaderNodeMath');fill_weight.operation='MULTIPLY';fill_weight.inputs[1].default_value=.55;l.new(path.outputs['Is Camera Ray'],fill_weight.inputs[0])
 fill_shaders=n.new('ShaderNodeMixShader');l.new(fill_weight.outputs[0],fill_shaders.inputs[0]);l.new(s.outputs[0],fill_shaders.inputs[1]);l.new(fill_pigment.outputs[0],fill_shaders.inputs[2])
 shaders=n.new('ShaderNodeMixShader');l.new(strength.outputs[0],shaders.inputs[0]);l.new(fill_shaders.outputs[0],shaders.inputs[1]);l.new(pigment.outputs[0],shaders.inputs[2]);l.new(shaders.outputs[0],out.inputs['Surface'])
 records.append({'object':obj.name,'vertices':len(obj.data.vertices),'AO':maps['AO'].image.filepath_raw,'curvature':maps['curvature'].image.filepath_raw,'projection':'rest-camera UV, normal incidence and source alpha, generated hidden-side fill'})
sc['finished_surface_projection']=True
sc['projection']='CC BY original painting on genuine meshes; fixed UV moves with rig; approximate camera registration'
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(M/'medjay.blend'));(M/'surface-manifest.json').write_text(json.dumps(records,indent=2));log('Finished eight actual AO/curvature bake pairs and frozen-camera painting UVs with incidence blending into generated back-surface fills.')
