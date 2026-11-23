"""Frozen camera UVs on articulated geometry; generated backfill on unseen surfaces."""
import bpy,os,json,math,sys
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/cavalry';A=R/'assets/cavalry'
bpy.ops.wm.open_mainfile(filepath=str(M/'cavalry-unpainted.blend'));sc=bpy.context.scene;sc.frame_set(0);bpy.context.view_layer.update()
sys.path.insert(0,str(Path(__file__).parent))
from refine import refine
registration=refine(sc)
(M/'registration.json').write_text(json.dumps(registration,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(M/'cavalry-plain.blend'))
image=bpy.data.images.load(str(A/'painting-aligned-1024.png'),check_existing=True)
pixels=list(image.pixels);width,height=image.size
# No view-facing replacement meshes. Projection fades on back-facing surfaces.
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
  world=ev.matrix_world @ v.co;q=world_to_camera_view(sc,sc.camera,world)
  coords.append((q.x,q.y));normal=(ev.matrix_world.to_3x3().inverted().transposed() @ v.normal).normalized();view=(sc.camera.location-world).normalized();weights.append(max(0,min(1,(normal.dot(view)+.05)/.55)))
  if ob.name=='Horse':
   direction=sc.camera.matrix_world.to_quaternion() @ Vector((0,0,-1))
   hit,point,_,_,hit_ob,_=sc.ray_cast(bpy.context.evaluated_depsgraph_get(),world-direction*8,direction,distance=8.01)
   if hit and (point-world).length>.035:weights[-1]=0
   px=max(0,min(width-1,int(q.x*width)));py=max(0,min(height-1,int(q.y*height)))
   if q.y<.18 and min(pixels[4*(py*width+px):4*(py*width+px)+3])>.3:weights[-1]=0
 ev.to_mesh_clear()
 for mod,v in states:mod.show_viewport=v
 uv=ob.data.uv_layers.new(name='Rest painting UV');attr=ob.data.color_attributes.new(name='Projection incidence',type='FLOAT_COLOR',domain='CORNER')
 for j,loop in enumerate(ob.data.loops):uv.data[j].uv=coords[loop.vertex_index];attr.data[j].color=(weights[loop.vertex_index],)*3+(1,)
 # Bakes retain their original UV layer even after projected UVs are added.
 ob.data.uv_layers[0].active_render=True
 for idx,old in enumerate(list(ob.data.materials)):
  if old is None:continue
  # Native eye/hair/hoof regions must not receive misplaced horse colour.
  if ob.name=='Horse' and old.name == 'Dark eyes':continue
  mat=old.copy();mat.name=ob.name+' | painted | '+old.name;ob.data.materials[idx]=mat;n=mat.node_tree.nodes;l=mat.node_tree.links;s=n.get('Principled BSDF')
  if s is None:continue
  oldcolor=s.inputs['Base Color'].links[0].from_socket if s.inputs['Base Color'].is_linked else None
  fillkind='hair' if ('mane' in old.name or 'tail' in ob.name or 'boot' in ob.name) else 'coat' if ob.name=='Horse' else 'linen'
  fill=n.new('ShaderNodeTexImage');fill.image=bpy.data.images.load(str(A/f'fill-{fillkind}.png'),check_existing=True);fill.projection='BOX';fill.projection_blend=.35
  coord=n.new('ShaderNodeTexCoord');l.new(coord.outputs['Generated'],fill.inputs['Vector'])
  tinted=n.new('ShaderNodeMixRGB');tinted.blend_type='MULTIPLY';tinted.inputs[0].default_value=1;l.new(fill.outputs[0],tinted.inputs[1]);tinted.inputs[2].default_value=(.045,.075,.14,1) if fillkind=='linen' else (1,1,1,1)
  back=n.new('ShaderNodeMixRGB');back.inputs[0].default_value=.25
  if oldcolor:l.new(oldcolor,back.inputs[1])
  else:back.inputs[1].default_value=s.inputs['Base Color'].default_value
  l.new(tinted.outputs[0],back.inputs[2])
  uvnode=n.new('ShaderNodeUVMap');uvnode.uv_map=uv.name;tex=n.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(A/('projection-horse.png' if ob.name=='Horse' or 'tail-locks' in ob.name else 'painting-aligned-1024.png' if any(w in ob.name for w in ['jacket','trousers','kepi-crown','saddle-blanket']) else 'projection-skin.png' if ob.name=='Rider MPFB CC0 anatomy' else 'painting-aligned-1024.png')),check_existing=True);tex.extension='CLIP';l.new(uvnode.outputs[0],tex.inputs['Vector'])
  att=n.new('ShaderNodeVertexColor');att.layer_name=attr.name;mult=n.new('ShaderNodeMath');mult.operation='MULTIPLY';l.new(att.outputs[0],mult.inputs[0]);l.new(tex.outputs['Alpha'],mult.inputs[1])
  fac=n.new('ShaderNodeMath');fac.operation='MULTIPLY';fac.inputs[1].default_value=.96;l.new(mult.outputs[0],fac.inputs[0])
  # Painted light is camera-only; physical rays retain real material/shadows.
  l.new(back.outputs[0],s.inputs['Base Color'])
  pigment=n.new('ShaderNodeEmission');pigment.name='Camera-only painted pigment';l.new(tex.outputs[0],pigment.inputs['Color'])
  ray=n.new('ShaderNodeLightPath');camera_weight=n.new('ShaderNodeMath');camera_weight.operation='MULTIPLY';l.new(ray.outputs['Is Camera Ray'],camera_weight.inputs[0]);l.new(fac.outputs[0],camera_weight.inputs[1])
  blend=n.new('ShaderNodeMixShader');l.new(camera_weight.outputs[0],blend.inputs[0]);l.new(s.outputs[0],blend.inputs[1]);l.new(pigment.outputs[0],blend.inputs[2]);l.new(blend.outputs[0],n.get('Material Output').inputs['Surface'])
 records.append({'name':ob.name,'vertices':len(ob.data.vertices),'fixed_uv':True})
stone=bpy.data.materials['Cream limestone'];s=stone.node_tree.nodes.get('Principled BSDF')
for link in list(s.inputs['Base Color'].links):stone.node_tree.links.remove(link)
s.inputs['Base Color'].default_value=(.815,.624,.352,1)
sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0
for name,energy in [('Warm key',340),('Cool fill',68),('Cool rim',110)]:bpy.data.objects[name].data.energy=energy
bpy.data.objects['Warm key'].data.color=(1,.95,.86)
s.inputs['Roughness'].default_value=.86
# Warm stone pigment stays independent of the figure painting. Non-camera rays
# and 40% of visible shading retain the physical material and contact shadows.
n=stone.node_tree.nodes;l=stone.node_tree.links
geo=n.new('ShaderNodeNewGeometry');xyz=n.new('ShaderNodeSeparateXYZ');l.new(geo.outputs['Normal'],xyz.inputs[0])
ramp=n.new('ShaderNodeValToRGB')
def linear(v):
 v=v/255;return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
ramp.color_ramp.elements[0].position=.15;ramp.color_ramp.elements[0].color=tuple(linear(v) for v in (209,172,113))+(1,)
ramp.color_ramp.elements[1].position=.8;ramp.color_ramp.elements[1].color=tuple(linear(v) for v in (245,225,186))+(1,)
l.new(xyz.outputs['Z'],ramp.inputs[0]);pig=n.new('ShaderNodeEmission')
noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=95;noise.inputs['Detail'].default_value=3
grain=n.new('ShaderNodeValToRGB');grain.color_ramp.elements[0].color=(.73,.69,.61,1);grain.color_ramp.elements[1].color=(1,1,1,1);l.new(noise.outputs['Fac'],grain.inputs[0])
stonepaint=n.new('ShaderNodeMixRGB');stonepaint.blend_type='MULTIPLY';stonepaint.inputs[0].default_value=.38;l.new(ramp.outputs[0],stonepaint.inputs[1]);l.new(grain.outputs[0],stonepaint.inputs[2]);l.new(stonepaint.outputs[0],pig.inputs['Color'])
ray=n.new('ShaderNodeLightPath');weight=n.new('ShaderNodeMath');weight.operation='MULTIPLY';weight.inputs[1].default_value=.6;l.new(ray.outputs['Is Camera Ray'],weight.inputs[0])
blend=n.new('ShaderNodeMixShader');l.new(weight.outputs[0],blend.inputs[0]);l.new(s.outputs[0],blend.inputs[1]);l.new(pig.outputs[0],blend.inputs[2]);l.new(blend.outputs[0],n.get('Material Output').inputs['Surface'])
(M/'projection.json').write_text(json.dumps({'objects':records,'cream_srgb':'#E9CFA0','method':'rest camera projection on genuine meshes; generated backfill; no alpha cutout geometry','limitation':'Round-one alignment and uncovered seams require visual review.'},indent=2))
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(M/'cavalry.blend'))
