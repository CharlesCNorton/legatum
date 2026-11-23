"""Frozen camera UVs on true geometry, masked by pigment and surface incidence."""
import bpy,os,json,math
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
R=Path(os.environ['ANIM_ROOT']);M=Path(os.environ['ANIM_MASTER']);A=R/'assets/spartan-hoplite'
bpy.ops.wm.open_mainfile(filepath=str(M/('unpainted.blend' if (M/'unpainted.blend').exists() else 'spearman.blend')));sc=bpy.context.scene
import runpy
runpy.run_path('tools/art/anim3d/units/spartan-hoplite/shield_normals.py')['repair']()
bpy.ops.wm.save_as_mainfile(filepath=str(M/'unpainted.blend'))
# Correct bake's metal wear treatment on linen, retaining its true AO map.
for obname in ['Forged bronze muscle cuirass','Convex bronze aspis']:
 ob=bpy.data.objects[obname];mat=ob.data.materials[0];n=mat.node_tree.nodes;l=mat.node_tree.links;s=n.get('Principled BSDF')
 for link in list(s.inputs['Roughness'].links):l.remove(link)
 s.inputs['Roughness'].default_value=.82;s.inputs['Metallic'].default_value=0
 if obname=='Convex bronze aspis':
  for link in list(s.inputs['Normal'].links):l.remove(link)
 # AO is preserved via the baked map; linen never inherits golden curvature paint.
 ao=next((x for x in n if x.type=='TEX_IMAGE' and x.image and x.image.name.endswith(' AO')),None)
 tex=n.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(R/'assets/horseman/fill-linen.png'),check_existing=True);tex.projection='BOX';tex.projection_blend=.3
 coord=n.new('ShaderNodeTexCoord');l.new(coord.outputs['Generated'],tex.inputs['Vector'])
 mix=n.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=.6;l.new(tex.outputs[0],mix.inputs[1])
 if ao:l.new(ao.outputs[0],mix.inputs[2])
 else:mix.inputs[2].default_value=(1,1,1,1)
 l.new(mix.outputs[0],s.inputs['Base Color'])
# Surface-class mapping. Target rectangles are measured on the committed token;
# each mapping uses the frozen camera coordinates, not a changing frame projection.
painting=bpy.data.images.load(str(A/'painting-aligned.png'),check_existing=True)
images={k:bpy.data.images.load(str(A/f'projection-{k}.png'),check_existing=True) for k in ['linen','red','bronze','skin']}
# Draw-bounds registration is deliberately recorded, so later rounds can refine it.
regions=[('Forged bronze muscle cuirass','linen',(104,78,139,119)),('Convex bronze aspis','painting',(139,87,181,163)),('Corinthian','bronze',(111,46,139,90)),('Crimson shoulder','red',(97,68,155,94)),('Cloak •','red',(88,94,170,216)),('Horsehair crest','red',(104,27,140,72))]
images['painting']=painting
records=[]
for ob in list(sc.objects):
 if ob.type!='MESH' or ob.hide_render:continue
 match=next((entry for entry in regions if ob.name.startswith(entry[0])),None)
 if not match:continue
 _,kind,target=match
 states=[(mod,mod.show_viewport) for mod in ob.modifiers]
 for mod,_ in states:
  if mod.type!='ARMATURE':mod.show_viewport=False
 bpy.context.view_layer.update();ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
 assert len(me.vertices)==len(ob.data.vertices),(ob.name,'topology changed')
 camera_pts=[];weights=[];view=(sc.camera.location-Vector((0,0,1.2))).normalized()
 for v in me.vertices:
  q=world_to_camera_view(sc,sc.camera,ev.matrix_world@v.co);camera_pts.append((q.x*256,(1-q.y)*256))
  normal=(ev.matrix_world.to_3x3().inverted().transposed()@v.normal).normalized();weights.append(max(0,min(1,(normal.dot(view)-.03)/.55)))
 ev.to_mesh_clear()
 for mod,state in states:mod.show_viewport=state
 # Per-part alignment only on contiguous large surfaces. Crest tuft/helmet pieces
 # share global registration to avoid repeating a full painting patch per part.
 if ob.name.startswith(('Forged','Convex','Crimson shoulder','Cloak •')):
  xs=[p[0] for p in camera_pts];ys=[p[1] for p in camera_pts];bounds=(min(xs),min(ys),max(xs),max(ys))
  coords=[((target[0]+(x-bounds[0])/max(.01,bounds[2]-bounds[0])*(target[2]-target[0]))/256,1-(target[1]+(y-bounds[1])/max(.01,bounds[3]-bounds[1])*(target[3]-target[1]))/256) for x,y in camera_pts]
 else:bounds=None;coords=[(x/256,1-y/256) for x,y in camera_pts]
 uv=ob.data.uv_layers.new(name='Painting projection');attr=ob.data.color_attributes.new(name='Painting incidence',type='FLOAT_COLOR',domain='CORNER')
 for i,loop in enumerate(ob.data.loops):uv.data[i].uv=coords[loop.vertex_index];attr.data[i].color=(weights[loop.vertex_index],)*3+(1,)
 ob.data.uv_layers[0].active_render=True
 for idx,old in enumerate(list(ob.data.materials)):
  m=old.copy();m.name=ob.name+' painted';ob.data.materials[idx]=m;n=m.node_tree.nodes;l=m.node_tree.links;s=n.get('Principled BSDF')
  if kind=='bronze':s.inputs['Metallic'].default_value=1
  tex=n.new('ShaderNodeTexImage');tex.image=images[kind];tex.extension='CLIP';tc=n.new('ShaderNodeUVMap');tc.uv_map=uv.name;l.new(tc.outputs[0],tex.inputs['Vector'])
  attrnode=n.new('ShaderNodeVertexColor');attrnode.layer_name=attr.name;factor=n.new('ShaderNodeMath');factor.operation='MULTIPLY';l.new(attrnode.outputs[0],factor.inputs[0]);l.new(tex.outputs['Alpha'],factor.inputs[1])
  strength=n.new('ShaderNodeMath');strength.operation='MULTIPLY';strength.inputs[1].default_value=.95 if kind=='painting' else .82;l.new(factor.outputs[0],strength.inputs[0])
  mix=n.new('ShaderNodeMixRGB');mix.blend_type='MIX'
  if s.inputs['Base Color'].is_linked:l.new(s.inputs['Base Color'].links[0].from_socket,mix.inputs[1])
  else:mix.inputs[1].default_value=s.inputs['Base Color'].default_value
  l.new(strength.outputs[0],mix.inputs[0]);l.new(tex.outputs['Color'],mix.inputs[2]);l.new(mix.outputs[0],s.inputs['Base Color'])
  l.new(mix.outputs[0],s.inputs['Emission Color']);s.inputs['Emission Strength'].default_value=.12
 records.append({'object':ob.name,'vertices':len(ob.data.vertices),'kind':kind,'camera_bounds':bounds,'painting_bounds':target})
# All metal is metal, cloth is matte. Add generated bronze fill on unseen helmet.
for m in bpy.data.materials:
 if not m.use_nodes:continue
 s=m.node_tree.nodes.get('Principled BSDF')
 if not s:continue
 if m.name.startswith(('Bronze','Incised','Forged iron')):s.inputs['Metallic'].default_value=1
 if m.name.startswith(('Warm ivory','Cinnabar')):s.inputs['Sheen Weight'].default_value=.22
stone=bpy.data.materials['Cream limestone'];s=stone.node_tree.nodes.get('Principled BSDF')
# Linear-space pigment corresponding to warm cream sRGB E9CFA0 under neutral light.
def linear(v):return ((v/255+.055)/1.055)**2.4
s.inputs['Base Color'].default_value=tuple(linear(v)*.8 for v in (233,207,160))+(1,)
s.inputs['Roughness'].default_value=.86
sc.view_settings.look='AgX - Medium High Contrast';sc.view_settings.exposure=.25
sc['projection_method']='Frozen camera UV on MPFB/closed kit, pigment and incidence masks; CC0 backs and generated linen fill'
(M/'projection.json').write_text(json.dumps({'meshes':records,'cream_target':'#E9CFA0','limitation':'Approximate per-part registration; rest silhouette is not painting parity.'},indent=2))
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(M/'spearman.blend'))
