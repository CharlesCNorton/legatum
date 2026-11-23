"""Freeze one rest-camera projection on visible 3D surfaces; keep filled hidden faces.
No independently stretched regions, billboards or live screen-space shaders.
"""
import bpy,os,json,hashlib
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/field-cannon'
bpy.ops.wm.open_mainfile(filepath=str(M/'field-cannon.blend'))
sc=bpy.context.scene;cam=sc.camera;source=R/'assets/field-cannon/painting-source.png'
image=bpy.data.images.load(str(source),check_existing=True)
navy=bpy.data.images.load(str(R/'assets/field-cannon/projection-navy.png'),check_existing=True)
ivory=bpy.data.images.load(str(R/'assets/field-cannon/projection-ivory.png'),check_existing=True)
machine=bpy.data.images.load(str(R/'assets/field-cannon/projection-machine.png'),check_existing=True)
base=bpy.data.images.load(str(R/'assets/field-cannon/projection-base.png'),check_existing=True)
gun_meshes=set(bpy.data.objects['Gun travel and recoil'].children_recursive)
# Alpha-bounds registration of the original 1254px master to the 256px token.
registration={'source_bbox':[81,7,1172,1247],'reference_bbox':[26,12,230,244]}
toward=cam.matrix_world.to_quaternion() @ Vector((0,0,1));records=[]
for obj in list(sc.objects):
 if obj.type!='MESH' or obj.hide_render:continue
 # Evaluate native pose without topology-changing modifiers for stable frozen UV loops.
 disabled=[]
 for mod in obj.modifiers:
  if mod.type!='ARMATURE' and mod.show_viewport:disabled.append(mod);mod.show_viewport=False
 bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();ev=obj.evaluated_get(dg);me=ev.to_mesh()
 assert len(me.vertices)==len(obj.data.vertices),obj.name
 coords=[world_to_camera_view(sc,cam,ev.matrix_world @ v.co) for v in me.vertices]
 weights=[]
 for v in me.vertices:
  normal=(ev.matrix_world.to_3x3().inverted().transposed() @ v.normal).normalized()
  facing=max(0,min(1,(normal.dot(toward)-.05)/.40))
  world=ev.matrix_world @ v.co
  if facing>0:
   hit,loc,n,index,hit_obj,matrix=sc.ray_cast(dg,world+toward*8,-toward,distance=8.001)
   # Reject painting from occluding geometry; shallow tolerance includes bevels.
   if hit and (loc-world).length>.025:facing=0
  weights.append(facing)
 ev.to_mesh_clear()
 for mod in disabled:mod.show_viewport=True
 uv=obj.data.uv_layers.get('Painting projection') or obj.data.uv_layers.new(name='Painting projection')
 mask=obj.data.color_attributes.get('Painting visibility') or obj.data.color_attributes.new(name='Painting visibility',type='FLOAT_COLOR',domain='CORNER')
 for loop in obj.data.loops:
  i=loop.vertex_index;c=coords[i]
  sx=81+(c.x*256-26)*(1172-81)/(230-26);sy=7+((1-c.y)*256-12)*(1247-7)/(244-12)
  uv.data[loop.index].uv=(sx/image.size[0],1-sy/image.size[1]);f=weights[i];mask.data[loop.index].color=(f,f,f,1)
 obj.data.uv_layers.active_index=0;obj.data.uv_layers[0].active_render=True
 for slot in obj.material_slots:
  if not slot.material or 'bore soot' in slot.material.name:continue
  mat=slot.material.copy();slot.material=mat;n=mat.node_tree.nodes;links=mat.node_tree.links;p=n.get('Principled BSDF')
  if not p:continue
  old=p.inputs['Base Color'].links[0].from_socket if p.inputs['Base Color'].is_linked else None
  if not old:
   rgb=n.new('ShaderNodeRGB');rgb.outputs[0].default_value=p.inputs['Base Color'].default_value;old=rgb.outputs[0]
  tc=n.new('ShaderNodeUVMap');tc.uv_map=uv.name
  tex=n.new('ShaderNodeTexImage');tex.image=navy if mat.name.startswith('Siege indigo wool') else ivory if mat.name.startswith('Siege ivory linen') else machine if obj in gun_meshes else base if obj.name=='Stationary cream base' else image;tex.extension='CLIP';links.new(tc.outputs[0],tex.inputs[0])
  attr=n.new('ShaderNodeVertexColor');attr.layer_name=mask.name
  mult=n.new('ShaderNodeMath');mult.operation='MULTIPLY';links.new(attr.outputs['Color'],mult.inputs[0]);links.new(tex.outputs['Alpha'],mult.inputs[1])
  weight=n.new('ShaderNodeMath');weight.operation='MULTIPLY';weight.inputs[1].default_value=.92;links.new(mult.outputs[0],weight.inputs[0])
  mix=n.new('ShaderNodeMixRGB');links.new(weight.outputs[0],mix.inputs[0]);links.new(old,mix.inputs[1]);links.new(tex.outputs[0],mix.inputs[2]);links.new(mix.outputs[0],p.inputs['Base Color'])
  # A restrained painted-light contribution avoids multiplying all source shadows twice.
  strength=n.new('ShaderNodeMath');strength.operation='MULTIPLY';strength.inputs[1].default_value=.22;links.new(mult.outputs[0],strength.inputs[0]);links.new(strength.outputs[0],p.inputs['Emission Strength']);links.new(tex.outputs[0],p.inputs['Emission Color'])
 records.append({'object':obj.name,'visible_vertices':sum(w>0 for w in weights),'vertices':len(weights)})
sc['painted_projection']='One frozen camera UV projection; native geometry and filled occluded/back surfaces. Registration residuals are in registration.json.'
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(M/'field-cannon.blend'))
(M/'projection.json').write_text(json.dumps({'registration':registration,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'objects':records,'mapping':'shared frozen camera, no local texture warps','note':'Camera/geometry residuals remain; visual comparison determines acceptance.'},indent=2))
print('PAINTED',len(records),'meshes with fixed camera UVs')
