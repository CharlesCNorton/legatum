"""Project the original painting onto true skinned meshes; fill unseen surfaces.

The UVs are fixed in the bind pose and move with vertices. Never a billboard.
Projection uses direct rest-camera UVs, with incidence and image-alpha masks.
"""
import bpy,os,ast,math,json
from pathlib import Path
from mathutils import Vector,Matrix
from bpy_extras.object_utils import world_to_camera_view
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/horseman-3d';A=R/'assets/horseman'
bpy.ops.wm.open_mainfile(filepath=str(M/'horseman-unpainted.blend'));sc=bpy.context.scene;hrig=bpy.data.objects['AnimalArmature'];rig=bpy.data.objects['Rider MPFB game_engine']
for node in ast.parse(Path('tools/art/anim3d/scene.py').read_text()).body:
 if isinstance(node,ast.FunctionDef) and node.name in {'curve','mesh','solid','material','aim_bone','limb'}:exec(compile(ast.Module(body=[node],type_ignores=[]),'<shared geometry>','exec'))
# Match the painting's raised near forehoof with a real pose from the source walk.
for a in bpy.data.actions:a.use_fake_user=True
hrig.animation_data.action=bpy.data.actions['AnimalArmature|Walk'];hrig.animation_data.action_slot=hrig.animation_data.action.slots[0];sc.frame_set(19)
raised={p.name:p.matrix_basis.copy() for p in hrig.pose.bones if p.name.endswith('.R') and p.name.split('.')[0] in ['FrontShoulder','FrontUpperLeg','FrontLowerLeg','IKFrontLeg','FF','PoleTarget']}
hrig.animation_data.action=bpy.data.actions['AnimalArmature|Idle'];hrig.animation_data.action_slot=hrig.animation_data.action.slots[0];sc.frame_set(0)
rest={p.name:p.matrix_basis.copy() for p in hrig.pose.bones};rest.update(raised);obmat=hrig.matrix_basis.copy();hrig.animation_data_clear();hrig.animation_data_create();hrig.animation_data.action=bpy.data.actions.new('Horseman painted rest')
hrig.matrix_basis=obmat
for p in hrig.pose.bones:
 p.matrix_basis=rest[p.name];p.rotation_mode='QUATERNION'
 for prop in ['location','rotation_quaternion','scale']:p.keyframe_insert(prop,frame=0)
hrig['raised_idle_foreleg']=json.dumps({n:[list(row) for row in v] for n,v in raised.items()});sc.frame_set(0);bpy.context.view_layer.update()
horse=bpy.data.objects['Horse']
for v in horse.data.vertices:
 neck=sum(g.weight for g in v.groups if horse.vertex_groups[g.group].name.startswith('Neck'))
 v.co.x*=1+.22*neck
 shoulder=math.exp(-((v.co.y+.026)/.006)**2-((v.co.z+.013)/.006)**2)
 if abs(v.co.x)>.001:v.co.x+=math.copysign(.00065*shoulder,v.co.x)
horse.data.update()
# Replace the source's tapered rod tail with authored volumetric locks.
import bmesh
bm=bmesh.new();bm.from_mesh(horse.data);layer=bm.verts.layers.deform.active
tail_groups={g.index for g in horse.vertex_groups if g.name.startswith('Tail')}
if layer:
 doomed=[v for v in bm.verts if sum(w for group,w in v[layer].items() if group in tail_groups)>.55]
 bmesh.ops.delete(bm,geom=doomed,context='VERTS')
bm.to_mesh(horse.data);bm.free()
# Round 2: calibrate view and actual pose before freezing projection UVs.
sc.camera.location=(-8,-6,3.55)
sc.camera.rotation_euler=(Vector((0,0,1.4))-sc.camera.location).to_track_quat('-Z','Y').to_euler()
sc.camera.data.shift_x=-.020
base=bpy.data.objects['Stationary cream stone'];base.scale.x=base.scale.y=.795
# Solve hands/feet in the painting's pixel coordinates at their existing depth.
# The shared limb helper expects armature-local coordinates, not world coordinates.
def pixel_target(bone, xy):
 world=rig.matrix_world@rig.pose.bones[bone].head
 q=world_to_camera_view(sc,sc.camera,world)
 right=sc.camera.matrix_world.to_3x3()@Vector((1,0,0))
 up=sc.camera.matrix_world.to_3x3()@Vector((0,1,0))
 world+=right*((xy[0]/256-q.x)*sc.camera.data.ortho_scale)
 world+=up*((1-xy[1]/256-q.y)*sc.camera.data.ortho_scale)
 return rig.matrix_world.inverted()@world
# Lift the upper torso without changing the saddle attachment.
spine=rig.pose.bones['spine_01'];mat=spine.matrix.copy();mat.translation.z+=.065;spine.matrix=mat
bpy.context.view_layer.update()
limb('upperarm_r','lowerarm_r',pixel_target('hand_r',(96,78)),pixel_target('lowerarm_r',(101,98)))
# Spear's upper end leans a little left; real bone-parented geometry follows the grip.
up=sc.camera.matrix_world.to_3x3()@Vector((-.12,1,0))
aim_bone('hand_r',rig.matrix_world.to_3x3().inverted()@up)
limb('upperarm_l','lowerarm_l',pixel_target('hand_l',(143,105)),pixel_target('lowerarm_l',(146,91)))
limb('thigh_r','calf_r',pixel_target('foot_r',(125,173)),pixel_target('calf_r',(129,139)))
# Shorten only the portion of the spear above the grip, retaining the broad iron blade.
bpy.context.view_layer.update()
hand=rig.matrix_world@rig.pose.bones['hand_r'].head
shaft=bpy.data.objects['Spear ash shaft'];blade=bpy.data.objects['Iron spear blade']
axis=(rig.matrix_world.to_3x3()@rig.pose.bones['hand_r'].vector).normalized()
for ob in (shaft,blade):
 inv=ob.matrix_world.inverted()
 vertices=ob.data.vertices if ob.type=='MESH' else ob.data.splines[0].points
 for v in vertices:
  local=v.co.xyz if ob.type=='CURVE' else v.co
  w=ob.matrix_world@local;distance=(w-hand).dot(axis)
  if distance>0:
   w-=axis*min(.17,distance*.20)
   co=inv@w
   if ob.type=='CURVE':v.co=(*co,1)
   else:v.co=co
from mathutils import Quaternion
head=rig.pose.bones['head'];head.rotation_mode='QUATERNION';head.rotation_quaternion=head.rotation_quaternion@Quaternion((0,1,0),-.12)
bpy.context.view_layer.update()
rig['seated_pose']=json.dumps({p.name:[list(row) for row in p.matrix_basis] for p in rig.pose.bones})
# Sleeveless linen as painted; remove tubular fake folds and sculpt the cloth shell.
import bmesh
for o in list(sc.objects):
 if o.name.startswith('Linen chest fold'):bpy.data.objects.remove(o,do_unlink=True)
shirt=bpy.data.objects['Rider linen shirt and sleeves']
bm=bmesh.new();bm.from_mesh(shirt.data)
bmesh.ops.delete(bm,geom=[v for v in bm.verts if abs(v.co.x)>.205 and v.co.z>1.28],context='VERTS')
bm.to_mesh(shirt.data);bm.free()
for v in shirt.data.vertices:
 if v.co.y<0:
  v.co.y-=.004*math.sin(52*v.co.z+18*v.co.x)*math.sin(math.pi*max(0,min(1,(v.co.z-1.02)/.43)))
shirt.data.update()
# Register the full-depth horse, bridle and mane before projecting colour.
import sys
sys.path.insert(0,str(Path('tools/art/anim3d/mounted').resolve()))
from register import Registration, LANDMARKS
registration=Registration(sc)
for ob in list(sc.objects):
 if ob==horse or (ob.parent==hrig and ob.type in {'MESH','CURVE'}):
  registration.object(ob)
bpy.context.view_layer.update()
# Ground the actual sculpted hooves before storing the rest, preserving depth.
bpy.context.view_layer.update();ev=horse.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
floor=min((ev.matrix_world@v.co).z for v in me.vertices);ev.to_mesh_clear()
ground_lift=max(0,.112-floor)
bpy.data.objects['Horse world control'].location.z+=ground_lift
bpy.context.view_layer.update()
rider_world=rig.matrix_world.copy();rider_world.translation.z-=ground_lift;rig.matrix_world=rider_world
bpy.context.view_layer.update()

# Finish rigid kit and clothing before projection; freeze static MPFB macros.
from surface import finish, pigment
objects=[o for o in sc.objects if o.type=='MESH' and (o.name=='Horse' or o.name.startswith(('Rider MPFB CC0','Rider linen','Split riding tunic','Rider bronze helmet','Bronze cheekguard','Ivory woven saddle','Helmet dark crest fibre','Leather baldric')))]
surface_records=finish(objects)
# Relax the seat and exposed spear-side shoulder, retaining all camera depth.
rider_fit=Registration(sc,[((112,77),(108,71)),((127,105),(126,102)),
 ((129,141),(122,140)),((128,171),(122,172)),((97,78),(97,78)),
 ((129,52),(129,52)),((145,98),(144,99))],radius=19)
for ob in list(sc.objects):
 if ob in objects and ob!=horse and not ob.name.startswith('Ivory woven'):
  rider_fit.object(ob)
 elif ob.parent==rig and ob.type in {'MESH','CURVE'}:
  rider_fit.object(ob)
bpy.context.view_layer.update()

# Fit the real fan fibres to the painting's swept crest, retaining depth.
right=sc.camera.matrix_world.to_3x3()@Vector((1,0,0))
up=sc.camera.matrix_world.to_3x3()@Vector((0,1,0))
crests=sorted((o for o in sc.objects if o.name.startswith('Helmet dark crest fibre')),key=lambda o:o.name)
for j,ob in enumerate(crests):
 t=j/(len(crests)-1);inv=ob.matrix_world.inverted()
 targets=[(114+18*t,49-9*t),(109+27*t,48-17*math.sin(t*math.pi/2))]
 for point,(x,y) in zip(ob.data.splines[0].points,targets):
  w=ob.matrix_world@point.co.xyz;q=world_to_camera_view(sc,sc.camera,w)
  w+=right*((x/256-q.x)*sc.camera.data.ortho_scale)
  w+=up*((1-y/256-q.y)*sc.camera.data.ortho_scale)
  point.co=(*(inv@w),1)
 ob.data.bevel_depth=.007
surface_records.extend(finish(crests))
from strap import fit_baldric
surface_records.extend(finish([fit_baldric(sc,rig)]))

# Freeze UVs in the native 256 px camera coordinates.
# The source file is aligned to the committed token, not independently reframed.
painting=bpy.data.images.load(str(A/'painting-aligned-1024.png'),check_existing=True)
projections={k:bpy.data.images.load(str(A/f'projection-{k}.png'),check_existing=True) for k in ['coat','linen','skin']}
fills={k:bpy.data.images.load(str(A/f'fill-{k}.png'),check_existing=True) for k in ['coat','linen','bronze','hair']}
# Generated fills only supplement areas the original painting cannot describe.
for m in list(bpy.data.materials):
 if not m.use_nodes:continue
 kind='coat' if m.name.startswith('Bay') else 'linen' if m.name.startswith('Warm ivory') else 'bronze' if m.name.startswith('Bronze') else 'hair' if m.name.startswith('Black mane') else None
 if not kind:continue
 n=m.node_tree.nodes;l=m.node_tree.links;s=n.get('Principled BSDF');tex=n.new('ShaderNodeTexImage');tex.image=fills[kind];tex.projection='BOX';tex.projection_blend=.35
 coord=n.new('ShaderNodeTexCoord');l.new(coord.outputs['Generated'],tex.inputs['Vector'])
 old=s.inputs['Base Color'].links[0].from_socket if s.inputs['Base Color'].is_linked else None
 mix=n.new('ShaderNodeMixRGB');mix.blend_type='MIX';mix.inputs[0].default_value=.82
 if old:l.new(old,mix.inputs[1])
 else:mix.inputs[1].default_value=s.inputs['Base Color'].default_value
 l.new(tex.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],s.inputs['Base Color'])
# Project only surface meshes; props retain their own physical materials.
objects=[o for o in sc.objects if o.type=='MESH' and (o.name=='Horse' or o.name.startswith(('Rider MPFB CC0','Rider linen','Split riding tunic','Rider bronze helmet','Bronze cheekguard','Ivory woven saddle','Helmet dark crest fibre','Leather baldric')))]
records=[]
for obj in objects:
 states=[(m,m.show_viewport) for m in obj.modifiers]
 for m,state in states:
  if m.type!='ARMATURE':m.show_viewport=False
 bpy.context.view_layer.update();ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
 assert len(me.vertices)==len(obj.data.vertices),(obj.name,len(me.vertices),len(obj.data.vertices))
 coords=[];weights=[];view=sc.camera.matrix_world.to_3x3()@Vector((0,0,1))
 deps=bpy.context.evaluated_depsgraph_get()
 for v in me.vertices:
  world=ev.matrix_world@v.co;q=world_to_camera_view(sc,sc.camera,world);x,y=q.x*256,(1-q.y)*256
  coords.append((x/256,1-y/256))
  normal=(ev.matrix_world.to_3x3().inverted().transposed()@v.normal).normalized();inc=max(0,min(1,(normal.dot(view)-.01)/.30))
  if inc and sc.ray_cast(deps,world+view*.008,view,distance=20)[0]:inc=0.
  weights.append(inc)
 ev.to_mesh_clear()
 for mod,state in states:mod.show_viewport=state
 uv=obj.data.uv_layers.get('Painting projection') or obj.data.uv_layers.new(name='Painting projection')
 attr=obj.data.color_attributes.get('Painting incidence') or obj.data.color_attributes.new(name='Painting incidence',type='FLOAT_COLOR',domain='CORNER')
 for i,loop in enumerate(obj.data.loops):uv.data[i].uv=coords[loop.vertex_index];attr.data[i].color=(weights[loop.vertex_index],)*3+(1,)
 if len(obj.data.uv_layers)>1:obj.data.uv_layers[0].active_render=True
 # Per-object copies keep the projection repeatable and distinguish materials in audit.
 oldmats=list(obj.data.materials)
 for idx,oldmat in enumerate(oldmats):
  # Preserve native dark hair/eye/hoof regions and white markings on the horse.
  if obj.name=='Horse' and oldmat.name in ['Dark eyes','Horn hooves']:continue
  mat=oldmat.copy();mat.name=obj.name+' projected '+oldmat.name;obj.data.materials[idx]=mat
  n=mat.node_tree.nodes;l=mat.node_tree.links;s=n.get('Principled BSDF');tc=n.new('ShaderNodeUVMap');tc.uv_map='Painting projection';tex=n.new('ShaderNodeTexImage');tex.image=projections['coat'] if obj.name=='Horse' else projections['skin'] if obj.name=='Rider MPFB CC0 anatomy' else projections['linen'] if any(w in obj.name for w in ['linen','tunic','blanket']) else painting;tex.extension='CLIP';l.new(tc.outputs[0],tex.inputs['Vector'])
  att=n.new('ShaderNodeVertexColor');att.layer_name='Painting incidence';mult=n.new('ShaderNodeMath');mult.operation='MULTIPLY';l.new(att.outputs[0],mult.inputs[0]);l.new(tex.outputs['Alpha'],mult.inputs[1])
  factor=n.new('ShaderNodeMath');factor.operation='MULTIPLY';factor.inputs[1].default_value=.97;l.new(mult.outputs[0],factor.inputs[0])
  # The source already has illumination: do not shade its paint twice.
  output=n.get('Material Output')
  shaded=pigment(n,l,s.outputs[0],tex.outputs['Color'],factor.outputs[0])
  l.new(shaded,output.inputs['Surface'])
 records.append({'object':obj.name,'vertices':len(obj.data.vertices),'mapping':'frozen rest-camera UV with visibility/incidence/alpha blend; geometry remains approximate'})
# The painting's blue border and Greek-key textile pattern on a real blanket.
blue=material('Saddle cloth indigo paint',(.025,.09,.13),0,.85);linen=bpy.data.materials['Warm ivory linen'];gold=bpy.data.materials['Bronze • polished edges'];hair=bpy.data.materials['Black mane and tail']
def attach_horse(o,bone):
 registration.object(o);bpy.context.view_layer.update();world=o.matrix_world.copy();o.parent=hrig;o.parent_type='BONE';o.parent_bone=bone;bpy.context.view_layer.update();o.matrix_world=world
for sg in [-1,1]:
 x=sg*.372
 for z in [1.24,1.285,1.35]:
  o=curve('Blue blanket border',[(x,-.23,z),(x,.52,z)],.009,blue);attach_horse(o,'Torso')
 for j in range(10):
  y=-.22+j*.073;pts=[(x,y,1.29),(x,y,1.335),(x,y+.055,1.335),(x,y+.055,1.305),(x,y+.025,1.305),(x,y+.025,1.32)]
  attach_horse(curve('Woven Greek key',pts,.005,blue),'Torso')
 for j in range(32):
  y=-.23+j*.024;attach_horse(curve('Blanket fringe',[(x,y,1.24),(x+sg*.006,y,1.19)],.005,linen),'Torso')
# Small bronze shield slung behind the rider, visible chiefly as a shoulder rim.
verts=[];faces=[];center=Vector((.24,.17,1.22))
for ring in range(9):
 radius=.29*ring/8
 for j in range(64):
  a=j*2*math.pi/64;verts.append(tuple(center+Vector((radius*math.sin(a),.05*(1-(radius/.29)**2),radius*math.cos(a)))))
for ring in range(8):
 for j in range(64):a=ring*64+j;b=ring*64+(j+1)%64;faces.append((a,b,b+64,a+64))
shield=solid(mesh('Slung bronze riding shield',verts,faces,bpy.data.materials['Bronze • hammered']),.007)
# Authored in rider space, then attached to the moving chest without becoming a plane.
shield.matrix_world=rig.matrix_world.copy();bpy.context.view_layer.update();world=shield.matrix_world.copy();shield.parent=rig;shield.parent_type='BONE';shield.parent_bone='spine_03';bpy.context.view_layer.update();shield.matrix_world=world
# Volumetric locks hang under gravity rather than inheriting the source's stiff rod.
for o in list(sc.objects):
 if o.name.startswith(('Tail flowing fibre','Skinned tail hair')):bpy.data.objects.remove(o,do_unlink=True)
bpy.context.view_layer.update()
root_world=registration.world(hrig.matrix_world@hrig.pose.bones['Tail1'].head)
sc['tail_root_local']=json.dumps(list((hrig.matrix_world@hrig.pose.bones['Tail1'].matrix).inverted()@root_world))
for j in range(48):
 ob=curve('Horseman flowing tail lock',[(0,0,.5)]*13,.009,hair)
 ob.data.bevel_resolution=3
from tail import update_tail
update_tail()
from reins import update_reins
update_reins()
# Shared cream target sampled from the painting's stone top: sRGB E9CFA0.
stone=bpy.data.materials['Cream limestone'];n=stone.node_tree.nodes;l=stone.node_tree.links;s=n.get('Principled BSDF')
for link in list(s.inputs['Base Color'].links):l.remove(link)
s.inputs['Base Color'].default_value=(.81,.63,.40,1);s.inputs['Roughness'].default_value=.85
# Camera-only limestone pigment keeps the cream bright without lighting the horse.
geo=n.new('ShaderNodeNewGeometry');xyz=n.new('ShaderNodeSeparateXYZ');l.new(geo.outputs['Normal'],xyz.inputs[0])
colour=n.new('ShaderNodeMixRGB');colour.inputs[1].default_value=(.78,.50,.25,1);colour.inputs[2].default_value=(1,.75,.48,1)
l.new(xyz.outputs['Z'],colour.inputs[0])
ao=n.new('ShaderNodeAmbientOcclusion');ao.inputs['Distance'].default_value=.07;ao.samples=8
shade=n.new('ShaderNodeMixRGB');shade.blend_type='MULTIPLY';shade.inputs[0].default_value=.35
l.new(colour.outputs[0],shade.inputs[1]);l.new(ao.outputs['Color'],shade.inputs[2])
amount=n.new('ShaderNodeValue');amount.outputs[0].default_value=.65
l.new(pigment(n,l,s.outputs[0],shade.outputs[0],amount.outputs[0]),n.get('Material Output').inputs['Surface'])
sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0
# Warmer, less front-lit studio treatment; do not flatten painted cavities.
bpy.data.objects['Cool fill'].data.energy=65;bpy.data.objects['Warm key'].data.energy=300
bpy.data.objects['Warm rim'].data.energy=120;bpy.data.objects['Warm rim'].data.color=(.78,.86,1)
sc['painting_projection']='Original CC BY 4.0 painting, fixed UV on skinned geometry, landmark calibrated; generated unseen-surface fills'
(M/'projection.json').write_text(json.dumps({'meshes':records,'finished_surfaces':surface_records,'horse_geometry_landmarks':LANDMARKS,'cream_target_srgb':'#E9CFA0','limitation':'View-specific painted lighting; 3D bind-space landmark sculpture is approximate, not pixel parity.'},indent=2))
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(M/'horseman.blend'))
