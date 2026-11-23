"""Finished full-depth surfaces with frozen camera projection and painted unseen fills."""
import bpy,os,sys,json,math
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
sys.path.insert(0,str(Path(__file__).parent))
from surface import finish,pigment
from register import Registration
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/knight';A=R/'assets/knight'
bpy.ops.wm.open_mainfile(filepath=str(M/'knight-plain.blend'));sc=bpy.context.scene
# Finish actual surfaces before camera UV capture. Native anatomy keeps skin weights.
objects=[o for o in sc.objects if o.type=='MESH' and o.name!='Stationary cream stone']
records=finish(objects)
# Bind-space registration keeps all thickness, bone weights and camera depth.
horsefit=Registration(sc,[((91,86),(80,98)),((81,111),(73,130)),((109,126),(105,139)),((143,141),(145,150)),((151,207),(156,217)),((116,208),(101,220)),((170,207),(170,216))],radius=22)
for ob in objects:
 if ob.name=='Horse' or ob.name.startswith(('GEO caparison','GEO chest','Ivory woven')):horsefit.object(ob)
# Match torso and helmet with a small full-depth displacement.
riderfit=Registration(sc,[((130,70),(125,72)),((131,103),(124,104)),((141,160),(135,162)),((146,185),(137,173)),((98,94),(98,94)),((151,114),(151,114))],radius=18)
for ob in objects:
 if ob.name.startswith(('Rider MPFB','GEO chainmail','GEO blue','GEO enclosed','GEO helmet','GEO split','GEO articulated')):riderfit.object(ob)
bpy.context.view_layer.update()
# Microfinish and painted fills on unseen sides; physical materials still cast shadows.
for mat in list(bpy.data.materials):
 if not mat.use_nodes:continue
 n=mat.node_tree.nodes;l=mat.node_tree.links;s=n.get('Principled BSDF')
 if not s:continue
 s.inputs['Metallic'].default_value=1 if any(w in mat.name.lower() for w in ['steel','bronze','iron','gold']) else 0
 noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=170;noise.inputs['Detail'].default_value=3
 bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.16;bump.inputs['Distance'].default_value=.004;l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs['Normal'],s.inputs['Normal'])
 kind='linen' if any(w in mat.name.lower() for w in ['linen','cloth']) else 'bronze' if 'Bronze' in mat.name else 'hair' if 'hair' in mat.name else None
 if kind:
  tex=n.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(A/f'fill-{kind}.png'),check_existing=True);tex.projection='BOX';tex.projection_blend=.3
  coord=n.new('ShaderNodeTexCoord');l.new(coord.outputs['Generated'],tex.inputs[0]);mix=n.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=.40;mix.inputs[1].default_value=s.inputs['Base Color'].default_value;l.new(tex.outputs['Color'],mix.inputs[2]);l.new(mix.outputs[0],s.inputs['Base Color'])
 # AO supplies live cavity roughness; no fresh AO/curvature bake is claimed.
 ao=n.new('ShaderNodeAmbientOcclusion');ao.inputs['Distance'].default_value=.035;ao.samples=8
 rough=n.new('ShaderNodeMapRange');rough.inputs['To Min'].default_value=.22;rough.inputs['To Max'].default_value=.65;l.new(ao.outputs['AO'],rough.inputs['Value']);l.new(rough.outputs['Result'],s.inputs['Roughness'])
painting=bpy.data.images.load(str(A/'painting-aligned.png'),check_existing=True)
# Evaluated coordinates must correspond 1:1 with the finished bind mesh.
view=sc.camera.matrix_world.to_3x3()@Vector((0,0,1));deps=bpy.context.evaluated_depsgraph_get();projected=[]
for obj in objects:
 if obj.name.startswith(('Dark eyes','Tail flowing')):continue
 states=[(m,m.show_viewport) for m in obj.modifiers]
 for m,_ in states:
  if m.type!='ARMATURE':m.show_viewport=False
 bpy.context.view_layer.update();ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
 assert len(me.vertices)==len(obj.data.vertices),obj.name
 coords=[];weights=[]
 for v in me.vertices:
  world=ev.matrix_world@v.co;q=world_to_camera_view(sc,sc.camera,world);coords.append((q.x,q.y))
  normal=(ev.matrix_world.to_3x3().inverted().transposed()@v.normal).normalized();inc=max(0,min(1,(normal.dot(view)+.08)/.25))
  if inc and sc.ray_cast(bpy.context.evaluated_depsgraph_get(),world+view*.009,view,distance=20)[0]:inc=0
  weights.append(inc)
 ev.to_mesh_clear()
 for m,state in states:m.show_viewport=state
 uv=obj.data.uv_layers.new(name='Painting projection');attr=obj.data.color_attributes.new(name='Painting incidence',type='FLOAT_COLOR',domain='CORNER')
 for i,loop in enumerate(obj.data.loops):uv.data[i].uv=coords[loop.vertex_index];attr.data[i].color=(weights[loop.vertex_index],)*3+(1,)
 for idx,old in enumerate(list(obj.data.materials)):
  if not old or not old.use_nodes:continue
  mat=old.copy();mat.name=obj.name+' painted '+old.name;obj.data.materials[idx]=mat;n=mat.node_tree.nodes;l=mat.node_tree.links;s=n.get('Principled BSDF')
  if not s:continue
  tc=n.new('ShaderNodeUVMap');tc.uv_map=uv.name;tex=n.new('ShaderNodeTexImage');tex.image=painting;tex.extension='CLIP';l.new(tc.outputs[0],tex.inputs['Vector'])
  att=n.new('ShaderNodeVertexColor');att.layer_name=attr.name;mult=n.new('ShaderNodeMath');mult.operation='MULTIPLY';l.new(att.outputs[0],mult.inputs[0]);l.new(tex.outputs['Alpha'],mult.inputs[1])
  fac=n.new('ShaderNodeMath');fac.operation='MULTIPLY';fac.inputs[1].default_value=.985;l.new(mult.outputs[0],fac.inputs[0]);l.new(pigment(n,l,s.outputs[0],tex.outputs['Color'],fac.outputs[0]),n.get('Material Output').inputs['Surface'])
 projected.append({'object':obj.name,'vertices':len(obj.data.vertices)})
# Shared cream #E9CFA0 converted to scene-linear. Camera pigment, real AO/contact shade.
stone=bpy.data.materials['Cream limestone'];n=stone.node_tree.nodes;l=stone.node_tree.links;s=n.get('Principled BSDF')
def lin(x):return ((x/255+.055)/1.055)**2.4
cream=tuple(lin(v) for v in (233,207,160))+(1,);s.inputs['Base Color'].default_value=cream
for link in list(s.inputs['Base Color'].links):l.remove(link)
ao=n.new('ShaderNodeAmbientOcclusion');ao.inputs['Distance'].default_value=.08;ao.inputs['Color'].default_value=cream;ao.inputs['Distance'].default_value=.035
value=n.new('ShaderNodeValue');value.outputs[0].default_value=.90;l.new(pigment(n,l,s.outputs[0],ao.outputs['Color'],value.outputs[0]),n.get('Material Output').inputs['Surface'])
sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0
for name,power in [('Warm key',300),('Cool fill',65),('Warm rim',120)]:bpy.data.objects[name].data.energy=power
bpy.data.objects['Warm rim'].data.color=(.78,.86,1)
sc['projection']='Frozen rest-camera UV on full-depth surfaces; visibility, incidence and alpha mask; generated fills on unseen surfaces'
(M/'projection.json').write_text(json.dumps({'surfaces':records,'projected':projected,'cream':'#E9CFA0','bakes':'Live AO and procedural grain only; no fresh AO/curvature maps claimed'},indent=2))
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(M/'knight.blend'));print('KNIGHT_PAINT_READY')
