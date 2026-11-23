"""Frozen camera UV on genuine rigged meshes. Incidence/material masks protect backs."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
from bpy_extras.object_utils import world_to_camera_view
bpy.ops.wm.open_mainfile(filepath=str(MASTER/'archer-unpainted.blend'));sc=bpy.context.scene
painting=bpy.data.images.load(str(ASSETS/'painting-aligned.png'),check_existing=True)
records=[];view=(sc.camera.location-Vector((.12,0,1.06))).normalized()
# Per-part landmark registration is documented, never changes rendered mesh alpha.
landmarks={}
for obj in sc.objects:
 if obj.type!='MESH' or obj.name.startswith(('GEO-Stationary','GEO-MPFB eyes')):continue
 if not any(w in obj.name for w in ['MPFB archer','cuirass','tunic','sleeve','helmet','cheekpiece','crest']):continue
 states=[(m,m.show_viewport) for m in obj.modifiers]
 for m,v in states:
  if m.type!='ARMATURE':m.show_viewport=False
 bpy.context.view_layer.update();ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();assert len(me.vertices)==len(obj.data.vertices)
 uvlist=[];weights=[]
 for v in me.vertices:
  q=world_to_camera_view(sc,sc.camera,ev.matrix_world@v.co);uvlist.append((q.x,q.y));normal=(ev.matrix_world.to_3x3().inverted().transposed()@v.normal).normalized();weights.append(max(0,min(1,(normal.dot(view)-.10)/.5)))
 ev.to_mesh_clear()
 for m,v in states:m.show_viewport=v
 uv=obj.data.uv_layers.get('Painting projection') or obj.data.uv_layers.new(name='Painting projection');att=obj.data.color_attributes.new(name='Painting incidence',type='FLOAT_COLOR',domain='CORNER')
 for i,loop in enumerate(obj.data.loops):uv.data[i].uv=uvlist[loop.vertex_index];att.data[i].color=(weights[loop.vertex_index],)*3+(1,)
 # Native skin and bake UVs remain the default for their unrelated textures.
 if len(obj.data.uv_layers)>1:obj.data.uv_layers[0].active_render=True
 for i,m in enumerate(list(obj.data.materials)):
  mat=m.copy();obj.data.materials[i]=mat;n=mat.node_tree.nodes;l=mat.node_tree.links;s=n.get('Principled BSDF');tc=n.new('ShaderNodeUVMap');tc.uv_map=uv.name;tex=n.new('ShaderNodeTexImage');tex.image=painting;tex.extension='CLIP';l.new(tc.outputs[0],tex.inputs[0]);vc=n.new('ShaderNodeVertexColor');vc.layer_name=att.name;mult=n.new('ShaderNodeMath');mult.operation='MULTIPLY';l.new(vc.outputs[0],mult.inputs[0]);l.new(tex.outputs['Alpha'],mult.inputs[1]);strength=n.new('ShaderNodeMath');strength.operation='MULTIPLY';strength.inputs[1].default_value=.78;l.new(mult.outputs[0],strength.inputs[0]);mix=n.new('ShaderNodeMixRGB')
  if s.inputs['Base Color'].is_linked:l.new(s.inputs['Base Color'].links[0].from_socket,mix.inputs[1])
  else:mix.inputs[1].default_value=s.inputs['Base Color'].default_value
  l.new(strength.outputs[0],mix.inputs[0]);l.new(tex.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],s.inputs['Base Color']);l.new(mix.outputs[0],s.inputs['Emission Color']);s.inputs['Emission Strength'].default_value=.12
 records.append({'object':obj.name,'vertices':len(obj.data.vertices)})
sc['projection']='Frozen painting camera UV, incidence and source-alpha blend on real weighted meshes; generated painted fills on unseen sides.'
(MASTER/'projection.json').write_text(json.dumps({'objects':records,'strength':.78,'limitation':'View-dependent painted light; registration requires visual review.'},indent=2));save(MASTER/'archer.blend');log('- Projected source painting onto true meshes in rest pose, preserving physical back-surface fill and alpha.')
