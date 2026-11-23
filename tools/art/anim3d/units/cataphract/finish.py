"""Register volumetric geometry and bake frozen camera UVs onto the weighted meshes."""
import bpy,os,sys,json,math,ast
from pathlib import Path
from mathutils import Vector,Matrix
from bpy_extras.object_utils import world_to_camera_view
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/cataphract';A=R/'assets/cataphract'
bpy.ops.wm.open_mainfile(filepath=str(M/'unpainted.blend'));sc=bpy.context.scene
rig=bpy.data.objects['Rider MPFB game_engine'];hrig=bpy.data.objects['AnimalArmature'];body=bpy.data.objects['Rider MPFB CC0 anatomy']
for node in ast.parse(Path('tools/art/anim3d/scene.py').read_text()).body:
 if isinstance(node,ast.FunctionDef) and node.name=='aim_bone':exec(compile(ast.Module(body=[node],type_ignores=[]),'<shared joints>','exec'))
# Correct parts authored in rider coordinates after saddle parenting.
for o in sc.objects:
 if o.name.startswith('GEO-rider lamellar row'):o.matrix_world=rig.matrix_world@o.matrix_world
# Long lance angles toward the painting's upper-right tip.
aim_bone('hand_r',(0,-.25,1))
aim_bone('hand_l',(0,-.6,-1))
rig['seated_pose']=json.dumps({p.name:[list(r) for r in p.matrix_basis] for p in rig.pose.bones})
bpy.context.view_layer.update()
# Shift the actual rider and all anatomical skin/kit together, retaining saddle parenting.
right=sc.camera.matrix_world.to_quaternion()@Vector((1,0,0))
up=sc.camera.matrix_world.to_quaternion()@Vector((0,1,0))
world=rig.matrix_world.copy();world.translation+=right*(-.12)+up*.22;rig.matrix_world=world
bpy.context.view_layer.update()
# Fit the long lance within the source painting's twelve-pixel headroom.
shaft=bpy.data.objects['Spear ash shaft']
shaft.data.splines[0].points[0].co.z-=.20
shaft.data.splines[0].points[-1].co.z-=.22
for v in bpy.data.objects['Iron spear blade'].data.vertices:v.co.z-=.22
base=bpy.data.objects['Stationary cream stone'];base.scale.x=base.scale.y=.90;base.location-=right*.12
# Convert real bevelled curves to mesh so their painting UVs stay attached in motion.
for o in list(sc.objects):
 if o.type=='CURVE':
  bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
  bpy.ops.object.convert(target='MESH')
# Shape correction cage in image coordinates. This edits real 3D vertices;
# view depth is unchanged and the backs/undersides retain their full volume.
pairs=[((61,140),(61,136)),((99,139),(97,141)),((144,137),(141,137)),((179,111),(178,82)),((204,130),(194,111)),((174,166),(158,163)),((180,225),(161,223)),((154,221),(145,221)),((64,223),(72,223)),((86,216),(86,216))]
def warp(x,y):
 weights=[1/(18+(x-a[0])**2+(y-a[1])**2)**2.4 for a,b in pairs];total=sum(weights)
 return x+sum(w*(b[0]-a[0]) for w,(a,b) in zip(weights,pairs))/total,y+sum(w*(b[1]-a[1]) for w,(a,b) in zip(weights,pairs))/total
horse_objects=[]
for o in sc.objects:
 if o.type!='MESH' or o.name=='Stationary cream stone':continue
 p=o
 while p is not None and p!=rig:p=p.parent
 if p==rig:continue
 horse_objects.append(o)
for o in horse_objects:
 mods=[(m,m.show_viewport) for m in o.modifiers]
 for m,_ in mods:
  if m.type!='ARMATURE':m.show_viewport=False
 bpy.context.view_layer.update();ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
 assert len(me.vertices)==len(o.data.vertices),o.name
 arm=next((m.object for m in o.modifiers if m.type=='ARMATURE'),None)
 Ato=arm.matrix_world.inverted()@o.matrix_world if arm else None
 for v,pv in zip(o.data.vertices,me.vertices):
  world=o.matrix_world@pv.co;q=world_to_camera_view(sc,sc.camera,world);x,y=q.x*256,(1-q.y)*256;xx,yy=warp(x,y)
  delta=(right*(xx-x)+up*(y-yy))*(sc.camera.data.ortho_scale/256)
  local=o.matrix_world.to_3x3().inverted()@delta
  if arm:
   weighted=Matrix(((0.,0.,0.,0.),)*4);total=0
   for g in v.groups:
    name=o.vertex_groups[g.group].name
    if name not in arm.pose.bones:continue
    bone=arm.pose.bones[name];t=bone.matrix@bone.bone.matrix_local.inverted()
    weighted+=t*g.weight;total+=g.weight
   if total>.001:
    skin=Ato.inverted()@(weighted*(1/total))@Ato
    local=skin.to_3x3().inverted_safe()@local
  v.co+=local
 ev.to_mesh_clear()
 for mod,state in mods:mod.show_viewport=state
 o.data.update()
bpy.context.view_layer.update()
exec(compile(Path('tools/art/anim3d/units/cataphract/refine.py').read_text(), 'cataphract finished surfaces', 'exec'))
sys.path.insert(0,str(Path(__file__).resolve().parent))
from reins import build_reins
from contacts import fit_rest_contacts
fit_rest_contacts()
build_reins()
# Save true-geometry stage before projection, with neutral clay material override.
bpy.ops.wm.save_as_mainfile(filepath=str(M/'plain.blend'))
painting=bpy.data.images.load(str(A/'projection.png'),check_existing=True)
paint_pixels=list(painting.pixels);paint_width=painting.size[0];paint_height=painting.size[1]
fills={k:bpy.data.images.load(str(A/f'fill-{k}.png'),check_existing=True) for k in ['coat','linen','bronze','hair','skin','steel','cloth','leather']}
cloak=bpy.data.objects['GEO-heavy rust riding cloak']
cloak.data.materials[0]=cloak.data.materials[0].copy();cloak.data.materials[0].name='Cataphract rust wool'
# Add multiscale material finish, cavity AO and geometry-driven polished edges.
for m in list(bpy.data.materials):
 if not m.use_nodes:continue
 n=m.node_tree.nodes;l=m.node_tree.links;s=n.get('Principled BSDF')
 if not s:continue
 metal=s.inputs['Metallic'].default_value>.5
 s.inputs['Metallic'].default_value=1 if metal else 0
 tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=150 if metal else 210;tex.inputs['Detail'].default_value=3
 bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.22;bump.inputs['Distance'].default_value=.006 if metal else .003
 l.new(tex.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs['Normal'],s.inputs['Normal'])
 rough=n.new('ShaderNodeMapRange');rough.inputs['To Min'].default_value=.30 if metal else .64;rough.inputs['To Max'].default_value=.53 if metal else .86
 l.new(tex.outputs['Fac'],rough.inputs['Value']);l.new(rough.outputs[0],s.inputs['Roughness'])
 if 'stone' in m.name.lower():continue
 kind='bronze' if metal else 'hair' if any(k in m.name.lower() for k in ['hair','mane','dark','horn']) else 'linen' if 'linen' in m.name.lower() else 'coat'
 if metal and any(k in m.name.lower() for k in ['hammered','iron']):kind='steel'
 elif 'skin' in m.name.lower():kind='skin'
 elif 'wool' in m.name.lower():kind='cloth';s.inputs['Sheen Weight'].default_value=.22
 elif 'leather' in m.name.lower():kind='leather'
 fill=n.new('ShaderNodeTexImage');fill.image=fills[kind];fill.projection='BOX';fill.projection_blend=.3
 tc=n.new('ShaderNodeTexCoord');l.new(tc.outputs['Generated'],fill.inputs['Vector'])
 mix=n.new('ShaderNodeMixRGB');mix.inputs[0].default_value=.45 if kind in ['skin','steel','cloth','leather'] else .22;mix.inputs[1].default_value=s.inputs['Base Color'].default_value;l.new(fill.outputs['Color'],mix.inputs[2]);l.new(mix.outputs[0],s.inputs['Base Color'])
 ao=n.new('ShaderNodeAmbientOcclusion');ao.inputs['Distance'].default_value=.08;ao.inputs['Color'].default_value=(1,1,1,1)
 cavity=n.new('ShaderNodeMixRGB');cavity.blend_type='MULTIPLY';cavity.inputs[0].default_value=.25;l.new(mix.outputs[0],cavity.inputs[1]);l.new(ao.outputs['Color'],cavity.inputs[2]);l.new(cavity.outputs[0],s.inputs['Base Color'])
# Project reference only where actual visible geometry faces this rest camera.
records=[]
for o in list(sc.objects):
 if o.type!='MESH' or o.name=='Stationary cream stone':continue
 mods=[(m,m.show_viewport) for m in o.modifiers]
 for m,_ in mods:
  if m.type!='ARMATURE':m.show_viewport=False
 bpy.context.view_layer.update();ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
 if len(me.vertices)!=len(o.data.vertices):raise RuntimeError(o.name)
 coords=[];weights=[];deps=bpy.context.evaluated_depsgraph_get();view=sc.camera.matrix_world.to_quaternion()@Vector((0,0,1))
 for v in me.vertices:
  w=ev.matrix_world@v.co;q=world_to_camera_view(sc,sc.camera,w);coords.append((q.x,q.y))
  normal=(ev.matrix_world.to_3x3().inverted().transposed()@v.normal).normalized()
  facing=max(0,min(1,(normal.dot(view)+.02)/.22))
  hit,location,_,_,hit_object,_=sc.ray_cast(deps,w+view*20,-view,distance=20.04)
  visible=hit and (location-w).length<.025
  # Source-object exclusion: cream base must never become painted white socks.
  px=max(0,min(paint_width-1,int(q.x*paint_width)));py=max(0,min(paint_height-1,int(q.y*paint_height)))
  color=paint_pixels[4*(py*paint_width+px):4*(py*paint_width+px)+3]
  if o.name=='Horse' and q.y<.19 and min(color)>.35:visible=False
  weights.append(facing if visible and 'rein_anchors' not in o else 0.)
 ev.to_mesh_clear()
 for mod,state in mods:mod.show_viewport=state
 uv=o.data.uv_layers.new(name='Painting projection');att=o.data.color_attributes.new(name='Projection incidence',type='FLOAT_COLOR',domain='CORNER')
 for i,loop in enumerate(o.data.loops):uv.data[i].uv=coords[loop.vertex_index];att.data[i].color=(weights[loop.vertex_index],)*3+(1,)
 for j,old in enumerate(list(o.data.materials)):
  if old is None or not old.use_nodes:continue
  mat=old.copy();mat.name=o.name+' painted '+old.name;o.data.materials[j]=mat;n=mat.node_tree.nodes;l=mat.node_tree.links;s=n.get('Principled BSDF')
  if s is None:continue
  tc=n.new('ShaderNodeUVMap');tc.uv_map=uv.name;tex=n.new('ShaderNodeTexImage');tex.image=painting;tex.extension='CLIP';l.new(tc.outputs[0],tex.inputs['Vector'])
  incidence=n.new('ShaderNodeVertexColor');incidence.layer_name=att.name
  factor=n.new('ShaderNodeMath');factor.operation='MULTIPLY';l.new(incidence.outputs[0],factor.inputs[0]);l.new(tex.outputs['Alpha'],factor.inputs[1])
  # Keep physical shading for shadow/bounce rays; camera rays see the source's
  # painted illumination, with 4% live response. Backfills retain physical AO.
  emission=n.new('ShaderNodeEmission');emission.name='Painted illumination';l.new(tex.outputs['Color'],emission.inputs['Color'])
  ray=n.new('ShaderNodeLightPath');cam=n.new('ShaderNodeMath');cam.operation='MULTIPLY';l.new(ray.outputs['Is Camera Ray'],cam.inputs[0]);l.new(factor.outputs[0],cam.inputs[1])
  strength=n.new('ShaderNodeMath');strength.operation='MULTIPLY';strength.inputs[1].default_value=.96;l.new(cam.outputs[0],strength.inputs[0])
  shade=n.new('ShaderNodeMixShader');l.new(strength.outputs[0],shade.inputs[0]);l.new(s.outputs[0],shade.inputs[1]);l.new(emission.outputs[0],shade.inputs[2]);l.new(shade.outputs[0],n.get('Material Output').inputs['Surface'])
 records.append({'object':o.name,'vertices':len(o.data.vertices)})
for im in bpy.data.images:
 if im.source=='FILE':im.pack()
sc['painting_projection']='Frozen rest-camera UV on true geometry, finished-surface visibility, normal incidence and source alpha blend; no alpha masking of mesh.'
(M/'projection.json').write_text(json.dumps(records,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(M/'cataphract.blend'))
print('CATAPHRACT_PROJECTION_READY',len(records))
