"""Frozen rest-camera UV projection onto true meshes, with incidence/alpha blending."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
from bpy_extras.object_utils import world_to_camera_view
bpy.ops.wm.open_mainfile(filepath=str(M/'peltast-unpainted.blend'));sc=bpy.context.scene;rig=bpy.data.objects['RIG-Peltast']
image=bpy.data.images.load(str(A/'painting-aligned.png'));view=(sc.camera.location-TARGET).normalized();records=[]
objects=[o for o in sc.objects if o.type=='MESH' and o.name not in ['GEO-Stationary cream base','GEO-MPFB eyes'] and not 'iron leaf' in o.name and not 'brooch' in o.name and not 'nose' in o.name]
for o in objects:
 states=[(m,m.show_viewport) for m in o.modifiers]
 for m,_ in states:
  if m.type!='ARMATURE':m.show_viewport=False
 bpy.context.view_layer.update();ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();assert len(me.vertices)==len(o.data.vertices)
 coords=[];amount=[]
 for v in me.vertices:
  world=ev.matrix_world@v.co;q=world_to_camera_view(sc,sc.camera,world);normal=(ev.matrix_world.to_3x3().inverted().transposed()@v.normal).normalized()
  coords.append((q.x,q.y));amount.append(max(0,min(1,(normal.dot(view)+.05)/.5)))
 ev.to_mesh_clear()
 for m,s in states:m.show_viewport=s
 uv=o.data.uv_layers.get('Painting rest UV') or o.data.uv_layers.new(name='Painting rest UV');attr=o.data.color_attributes.new(name='Painting facing',type='FLOAT_COLOR',domain='CORNER')
 for i,loop in enumerate(o.data.loops):uv.data[i].uv=coords[loop.vertex_index];attr.data[i].color=(amount[loop.vertex_index],)*3+(1,)
 for i,old in enumerate(list(o.data.materials)):
  mat=old.copy();mat.name=o.name+' projected paint';o.data.materials[i]=mat;n=mat.node_tree.nodes;l=mat.node_tree.links;s=n.get('Principled BSDF')
  uvn=n.new('ShaderNodeUVMap');uvn.uv_map=uv.name;tex=n.new('ShaderNodeTexImage');tex.image=image;tex.extension='CLIP';l.new(uvn.outputs[0],tex.inputs['Vector']);att=n.new('ShaderNodeVertexColor');att.layer_name=attr.name
  mul=n.new('ShaderNodeMath');mul.operation='MULTIPLY';l.new(tex.outputs['Alpha'],mul.inputs[0]);l.new(att.outputs[0],mul.inputs[1]);strength=n.new('ShaderNodeMath');strength.operation='MULTIPLY';strength.inputs[1].default_value=.9;l.new(mul.outputs[0],strength.inputs[0]);mix=n.new('ShaderNodeMixRGB')
  old=s.inputs['Base Color'].links[0].from_socket if s.inputs['Base Color'].is_linked else None
  if old:l.new(old,mix.inputs[1])
  else:mix.inputs[1].default_value=s.inputs['Base Color'].default_value
  l.new(strength.outputs[0],mix.inputs[0]);l.new(tex.outputs['Color'],mix.inputs[2]);l.new(mix.outputs[0],s.inputs['Base Color']);l.new(mix.outputs[0],s.inputs['Emission Color']);s.inputs['Emission Strength'].default_value=.15
 records.append({'mesh':o.name,'vertices':len(o.data.vertices),'method':'Fixed camera UV on deformed rest mesh, alpha and normal incidence blend into generated/procedural unseen material'})
sc['painting_projection']='Frozen rest-pose UV; original project painting, real moving geometry';save('peltast.blend');(M/'projection.json').write_text(json.dumps(records,indent=2));log('- Applied original-painting camera projection to full anatomy and physical clothing/equipment; unseen faces use painted fills and surface shaders. No billboard or relief image plane.')
