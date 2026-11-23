"""Frozen camera UVs on articulated geometry; generated backfill on unseen surfaces."""
import bpy,os,json,math
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/cavalry';A=R/'assets/cavalry'
bpy.ops.wm.open_mainfile(filepath=str(M/'cavalry-unpainted.blend'));sc=bpy.context.scene;sc.frame_set(0);bpy.context.view_layer.update()
image=bpy.data.images.load(str(A/'painting-aligned-1024.png'),check_existing=True)
# No view-facing replacement meshes. Projection weight fades over occluded sides.
records=[]
for ob in list(sc.objects):
 if ob.type!='MESH' or ob.name=='Stationary cream stone' or ob.name.startswith('Rider MPFB eyes'):continue
 # Original generated fills supplement the original surface material on unseen sides.
 states=[(m,m.show_viewport) for m in ob.modifiers]
 for mod,v in states:
  if mod.type!='ARMATURE':mod.show_viewport=False
 bpy.context.view_layer.update();ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
 assert len(me.vertices)==len(ob.data.vertices),ob.name
 coords=[];weights=[]
 for v in me.vertices:
  world=ev.matrix_world@v.co;q=world_to_camera_view(sc,sc.camera,world)
  coords.append((q.x,q.y));normal=(ev.matrix_world.to_3x3().inverted().transposed()@v.normal).normalized();view=(sc.camera.location-world).normalized();weights.append(max(0,min(1,(normal.dot(view)+.05)/.55)))
 ev.to_mesh_clear()
 for mod,v in states:mod.show_viewport=v
 uv=ob.data.uv_layers.new(name='Rest painting UV');attr=ob.data.color_attributes.new(name='Projection incidence',type='FLOAT_COLOR',domain='CORNER')
 for j,loop in enumerate(ob.data.loops):uv.data[j].uv=coords[loop.vertex_index];attr.data[j].color=(weights[loop.vertex_index],)*3+(1,)
 # Bakes retain their original UV layer even after projected UVs are added.
 ob.data.uv_layers[0].active_render=True
 for idx,old in enumerate(list(ob.data.materials)):
  if old is None:continue
  # Native eye/hair/hoof regions must not receive misplaced horse colour.
  if ob.name=='Horse' and not old.name.startswith(('Bay','Ivory')):continue
  mat=old.copy();mat.name=ob.name+' | painted | '+old.name;ob.data.materials[idx]=mat;n=mat.node_tree.nodes;l=mat.node_tree.links;s=n.get('Principled BSDF')
  if s is None:continue
  oldcolor=s.inputs['Base Color'].links[0].from_socket if s.inputs['Base Color'].is_linked else None
  fillkind='coat' if ob.name=='Horse' else 'hair' if 'boot' in ob.name else 'linen'
  fill=n.new('ShaderNodeTexImage');fill.image=bpy.data.images.load(str(A/f'fill-{fillkind}.png'),check_existing=True);fill.projection='BOX';fill.projection_blend=.35
  coord=n.new('ShaderNodeTexCoord');l.new(coord.outputs['Generated'],fill.inputs['Vector'])
  tinted=n.new('ShaderNodeMixRGB');tinted.blend_type='MULTIPLY';tinted.inputs[0].default_value=1;l.new(fill.outputs[0],tinted.inputs[1]);tinted.inputs[2].default_value=(.045,.075,.14,1) if fillkind=='linen' else (1,1,1,1)
  back=n.new('ShaderNodeMixRGB');back.inputs[0].default_value=.25
  if oldcolor:l.new(oldcolor,back.inputs[1])
  else:back.inputs[1].default_value=s.inputs['Base Color'].default_value
  l.new(tinted.outputs[0],back.inputs[2])
  uvnode=n.new('ShaderNodeUVMap');uvnode.uv_map=uv.name;tex=n.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(A/('projection-coat.png' if ob.name=='Horse' else 'projection-cloth.png' if any(w in ob.name for w in ['jacket','trousers','kepi-crown','saddle-blanket']) else 'projection-skin.png' if ob.name=='Rider MPFB CC0 anatomy' else 'painting-aligned-1024.png')),check_existing=True);tex.extension='CLIP';l.new(uvnode.outputs[0],tex.inputs['Vector'])
  att=n.new('ShaderNodeVertexColor');att.layer_name=attr.name;mult=n.new('ShaderNodeMath');mult.operation='MULTIPLY';l.new(att.outputs[0],mult.inputs[0]);l.new(tex.outputs['Alpha'],mult.inputs[1])
  fac=n.new('ShaderNodeMath');fac.operation='MULTIPLY';fac.inputs[1].default_value=.90;l.new(mult.outputs[0],fac.inputs[0])
  mix=n.new('ShaderNodeMixRGB');l.new(fac.outputs[0],mix.inputs[0]);l.new(back.outputs[0],mix.inputs[1]);l.new(tex.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],s.inputs['Base Color'])
  l.new(mix.outputs[0],s.inputs['Emission Color']);s.inputs['Emission Strength'].default_value=.12
 records.append({'name':ob.name,'vertices':len(ob.data.vertices),'fixed_uv':True})
stone=bpy.data.materials['Cream limestone'];s=stone.node_tree.nodes.get('Principled BSDF')
for link in list(s.inputs['Base Color'].links):stone.node_tree.links.remove(link)
s.inputs['Base Color'].default_value=(.815,.624,.352,1)
sc.view_settings.look='AgX - Medium High Contrast';sc.view_settings.exposure=.1
bpy.data.objects['Cool fill'].data.energy=150
(M/'projection.json').write_text(json.dumps({'objects':records,'cream_srgb':'#E9CFA0','method':'rest camera projection on genuine meshes; generated backfill; no alpha cutout geometry','limitation':'Round-one alignment and uncovered seams require visual review.'},indent=2))
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(M/'cavalry.blend'))
