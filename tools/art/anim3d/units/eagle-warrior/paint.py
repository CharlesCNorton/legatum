"""Frozen camera projection on real deforming geometry, ray-visible surfaces only."""
import sys,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
from bpy_extras.object_utils import world_to_camera_view
from mathutils.bvhtree import BVHTree
bpy.ops.wm.open_mainfile(filepath=str(M/'unpainted.blend'));sc=bpy.context.scene;sc.frame_set(1)
# Keep indexing unchanged while evaluating skin weights. Masks stay in visibility BVH.
saved=[]
for o in sc.objects:
 for mod in o.modifiers:
  if mod.type in {'SUBSURF','SOLIDIFY','BEVEL'}:saved.append((mod,mod.show_viewport));mod.show_viewport=False
bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();verts=[];polys=[];evaluated={}
for o in sc.objects:
 if o.type!='MESH' or o.hide_render:continue
 ev=o.evaluated_get(dg);me=ev.to_mesh();points=[o.matrix_world@v.co for v in me.vertices];offset=len(verts);verts.extend(points);polys.extend([tuple(offset+i for i in p.vertices) for p in me.polygons]);ev.to_mesh_clear()
 masks=[m for m in o.modifiers if m.type=='MASK' and m.show_viewport]
 for m in masks:m.show_viewport=False
 bpy.context.view_layer.update();ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();points=[o.matrix_world@v.co for v in me.vertices];normals=[(o.matrix_world.to_3x3().inverted().transposed()@v.normal).normalized() for v in me.vertices];ev.to_mesh_clear()
 for m in masks:m.show_viewport=True
 bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();evaluated[o.name]=(points,normals)
tree=BVHTree.FromPolygons(verts,polys);view=sc.camera.matrix_world.to_quaternion()@Vector((0,0,1));im=bpy.data.images.load(str(A/'projection.png'));cache={};coverage={}
for o in sc.objects:
 if o.name not in evaluated or o.name=='GEO-cream-stone-base':continue
 points,normals=evaluated[o.name];assert len(points)==len(o.data.vertices),o.name
 uv=o.data.uv_layers.new(name='Rest-camera painting');mask=o.data.color_attributes.new(name='Rest visibility',type='FLOAT_COLOR',domain='CORNER');weights=[]
 for p,n in zip(points,normals):
  hit,_,_,_=tree.ray_cast(p+view*8,-view,8.03);visible=hit is not None and (hit-p).length<.022;weights.append(max(0,min(1,(abs(n.dot(view))-.06)/.35)) if visible else 0)
 for loop in o.data.loops:
  v=world_to_camera_view(sc,sc.camera,points[loop.vertex_index]);uv.data[loop.index].uv=(v.x,v.y);w=weights[loop.vertex_index];mask.data[loop.index].color=(w,w,w,1)
 coverage[o.name]=round(sum(weights)/max(1,len(weights)),3)
 for i,original in enumerate(list(o.data.materials)):
  if not original or not original.use_nodes:continue
  if original.name in cache:o.data.materials[i]=cache[original.name];continue
  mat=original.copy();mat.name=original.name+' | frozen painting';cache[original.name]=mat;o.data.materials[i]=mat;n=mat.node_tree.nodes;l=mat.node_tree.links;out=next(n for n in n if n.type=='OUTPUT_MATERIAL');physical=out.inputs['Surface'].links[0].from_socket
  coords=n.new('ShaderNodeUVMap');coords.uv_map=uv.name;tex=n.new('ShaderNodeTexImage');tex.image=im;tex.extension='CLIP';l.new(coords.outputs[0],tex.inputs[0]);attr=n.new('ShaderNodeVertexColor');attr.layer_name=mask.name
  mul=n.new('ShaderNodeMath');mul.operation='MULTIPLY';l.new(attr.outputs['Color'],mul.inputs[0]);l.new(tex.outputs['Alpha'],mul.inputs[1]);strength=n.new('ShaderNodeMath');strength.operation='MULTIPLY';strength.inputs[1].default_value=.92;l.new(mul.outputs[0],strength.inputs[0])
  pigment=n.new('ShaderNodeBsdfPrincipled');pigment.inputs['Base Color'].default_value=(0,0,0,1);pigment.inputs['Roughness'].default_value=1;pigment.inputs['Specular IOR Level'].default_value=0;pigment.inputs['Emission Strength'].default_value=1;l.new(tex.outputs['Color'],pigment.inputs['Emission Color']);blend=n.new('ShaderNodeMixShader');l.new(strength.outputs[0],blend.inputs[0]);l.new(physical,blend.inputs[1]);l.new(pigment.outputs[0],blend.inputs[2]);l.new(blend.outputs[0],out.inputs['Surface'])
for mod,state in saved:mod.show_viewport=state
sc['projection']='Frozen rest UV; BVH visibility and facing mask; generated backfill; true geometry only';sc['source_sha256']=hashlib.sha256((A/'painting-source.png').read_bytes()).hexdigest();save('eagle-warrior.blend');(M/'projection.json').write_text(json.dumps(coverage,indent=2));log('- Froze painting camera UVs and ray-tested visibility, with generated feather backfill on unseen surfaces.');print('PAINT_OK',len(coverage),flush=True)
