"""Frozen camera projection on real deforming geometry, ray-visible surfaces only."""
import sys,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
from bpy_extras.object_utils import world_to_camera_view
bpy.ops.wm.open_mainfile(filepath=str(M/'surface.blend'));sc=bpy.context.scene;sc.frame_set(1)
bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();evaluated={}
for o in sc.objects:
 if o.type!='MESH' or o.hide_render:continue
 masks=[m for m in o.modifiers if m.type=='MASK' and m.show_viewport]
 for m in masks:m.show_viewport=False
 bpy.context.view_layer.update();ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();points=[o.matrix_world@v.co for v in me.vertices];normals=[(o.matrix_world.to_3x3().inverted().transposed()@v.normal).normalized() for v in me.vertices];ev.to_mesh_clear()
 for m in masks:m.show_viewport=True
 bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();evaluated[o.name]=(points,normals)
view=sc.camera.matrix_world.to_quaternion()@Vector((0,0,1));im=bpy.data.images.load(str(A/'projection.png'));cache={};coverage={}
for o in sc.objects:
 if o.name not in evaluated or o.name=='GEO-cream-stone-base':continue
 points,normals=evaluated[o.name];assert len(points)==len(o.data.vertices),o.name
 camera_inverse=sc.camera.matrix_world.inverted();scale=sc.camera.data.ortho_scale
 projected=[camera_inverse@p for p in points]
 projected=[(p.x/scale+.5,p.y/scale+.5) for p in projected]
 weights=[];loop_weights=[]
 # Polygon-centre visibility retains full paint on a finished front face.
 # Averaged boundary-vertex normals previously erased broad feather faces.
 for face in o.data.polygons:
  center=sum((points[i] for i in face.vertices),Vector())/len(face.vertices)
  va,vb,vc=[points[i] for i in list(face.vertices)[:3]]
  normal=(vb-va).cross(vc-va)
  facing=abs(normal.normalized().dot(view)) if normal.length>1e-10 else 0
  ok,hit,_,index,hit_object,_=sc.ray_cast(dg,center+view*8,-view,distance=8.1)
  distance=(hit-center).length if ok else 99
  same_surface=ok and hit_object.original==o
  # Raised weaving and adjacent vane edges must not cut holes in the pigment
  # on their support; farther occluded sides retain their generated/PBR fill.
  tolerance=.065 if 'feather' in o.name.lower() or 'wicker shield' in o.name else .025
  visible=ok and (distance<tolerance or same_surface and distance<.035)
  weight=max(0,min(1,(facing-.025)/.20)) if visible else 0
  for li in face.loop_indices:loop_weights.append((li,weight))
  weights.append(weight)
 # Commit attributes only after all rays for this object; writing them during
 # sampling repeatedly invalidates Blender's evaluated geometry.
 uv=o.data.uv_layers.new(name='Rest-camera painting');mask=o.data.color_attributes.new(name='Rest visibility',type='FLOAT_COLOR',domain='CORNER')
 for li,weight in loop_weights:
  uv.data[li].uv=projected[o.data.loops[li].vertex_index];mask.data[li].color=(weight,weight,weight,1)
 coverage[o.name]=round(sum(weights)/max(1,len(weights)),3)
 for i,original in enumerate(list(o.data.materials)):
  if not original or not original.use_nodes:continue
  if original.name in cache:o.data.materials[i]=cache[original.name];continue
  mat=original.copy();mat.name=original.name+' | frozen painting';cache[original.name]=mat;o.data.materials[i]=mat;n=mat.node_tree.nodes;l=mat.node_tree.links;out=next(n for n in n if n.type=='OUTPUT_MATERIAL');physical=out.inputs['Surface'].links[0].from_socket
  bs=n.get('Principled BSDF');fill=n.new('ShaderNodeBsdfPrincipled');fill.inputs['Base Color'].default_value=(0,0,0,1);fill.inputs['Specular IOR Level'].default_value=0;fill.inputs['Emission Strength'].default_value=1
  ao=n.new('ShaderNodeAmbientOcclusion');ao.inputs['Distance'].default_value=.10
  tint=n.new('ShaderNodeMixRGB');tint.blend_type='MULTIPLY';tint.inputs[0].default_value=.40;l.new(ao.outputs['Color'],tint.inputs[2])
  if bs.inputs['Base Color'].links:l.new(bs.inputs['Base Color'].links[0].from_socket,tint.inputs[1])
  else:tint.inputs[1].default_value=bs.inputs['Base Color'].default_value
  l.new(tint.outputs[0],fill.inputs['Emission Color']);fill_ray=n.new('ShaderNodeLightPath');fill_amount=n.new('ShaderNodeMath');fill_amount.operation='MULTIPLY';fill_amount.inputs[1].default_value=.65;l.new(fill_ray.outputs['Is Camera Ray'],fill_amount.inputs[0]);fill_mix=n.new('ShaderNodeMixShader');l.new(fill_amount.outputs[0],fill_mix.inputs[0]);l.new(physical,fill_mix.inputs[1]);l.new(fill.outputs[0],fill_mix.inputs[2]);physical=fill_mix.outputs[0]
  coords=n.new('ShaderNodeUVMap');coords.uv_map=uv.name;tex=n.new('ShaderNodeTexImage');tex.image=im;tex.extension='CLIP';l.new(coords.outputs[0],tex.inputs[0]);attr=n.new('ShaderNodeVertexColor');attr.layer_name=mask.name
  mul=n.new('ShaderNodeMath');mul.operation='MULTIPLY';l.new(attr.outputs['Color'],mul.inputs[0]);l.new(tex.outputs['Alpha'],mul.inputs[1]);strength=n.new('ShaderNodeMath');strength.operation='MULTIPLY';strength.inputs[1].default_value=.98;ray=n.new('ShaderNodeLightPath');camera=n.new('ShaderNodeMath');camera.operation='MULTIPLY';l.new(mul.outputs[0],camera.inputs[0]);l.new(ray.outputs['Is Camera Ray'],camera.inputs[1]);l.new(camera.outputs[0],strength.inputs[0])
  pigment=n.new('ShaderNodeBsdfPrincipled');pigment.inputs['Base Color'].default_value=(0,0,0,1);pigment.inputs['Roughness'].default_value=1;pigment.inputs['Specular IOR Level'].default_value=0;pigment.inputs['Emission Strength'].default_value=1;l.new(tex.outputs['Color'],pigment.inputs['Emission Color']);blend=n.new('ShaderNodeMixShader');l.new(strength.outputs[0],blend.inputs[0]);l.new(physical,blend.inputs[1]);l.new(pigment.outputs[0],blend.inputs[2]);l.new(blend.outputs[0],out.inputs['Surface'])
sc['projection']='Frozen rest UV; evaluated scene visibility and facing mask; generated backfill; true geometry only';sc['source_sha256']=hashlib.sha256((A/'painting-source.png').read_bytes()).hexdigest();save('eagle-warrior.blend');(M/'projection.json').write_text(json.dumps(coverage,indent=2));log('- Froze painting camera UVs and ray-tested visibility, with generated feather backfill on unseen surfaces.');print('PAINT_OK',len(coverage),flush=True)
