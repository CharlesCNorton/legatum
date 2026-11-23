"""Keshig shooting pose, three-dimensional bow, quiver, fur and tack."""
from bpy_extras.object_utils import world_to_camera_view
# Native animated quadruped pose; no foot rotations or procedural gait.
hrig.animation_data.action=bpy.data.actions['AnimalArmature|Gallop']
hrig.animation_data.action_slot=hrig.animation_data.action.slots[0]
sc.frame_set(12);bpy.context.view_layer.update()
right=sc.camera.matrix_world.to_quaternion()@Vector((1,0,0));up=sc.camera.matrix_world.to_quaternion()@Vector((0,1,0))
world=rig.matrix_world.copy();world.translation+=right*.38+up*.33;rig.matrix_world=world
bpy.context.view_layer.update()
# Turn at the waist while the legs continue to straddle the saddle.
p=rig.pose.bones['spine_01'];pivot=p.head.copy()
p.matrix=Matrix.Translation(pivot)@Matrix.Rotation(math.radians(110),4,'Z')@Matrix.Translation(-pivot)@p.matrix
bpy.context.view_layer.update()
# Solve wrists at the painting's landmarks, preserving armature-space depth.
right=sc.camera.matrix_world.to_quaternion()@Vector((1,0,0));up=sc.camera.matrix_world.to_quaternion()@Vector((0,1,0))
def pixel_world(x,y,world):
 q=world_to_camera_view(sc,sc.camera,world)
 return world+right*(x/256-q.x)*sc.camera.data.ortho_scale+up*((1-y/256)-q.y)*sc.camera.data.ortho_scale
def target(x,y,bone):
 w=rig.matrix_world@rig.pose.bones[bone].head
 return rig.matrix_world.inverted()@pixel_world(x,y,w)
limb('upperarm_l','lowerarm_l',target(91,67,'hand_l'),target(121,73,'lowerarm_l'))
limb('upperarm_r','lowerarm_r',target(147,62,'hand_r'),target(174,78,'lowerarm_r'))
aim_bone('hand_l',(0,0,1));aim_bone('hand_r',(0,1,0))
bpy.context.view_layer.update()
# All kit points authored in world coordinates, then parented retaining transforms.
grip=rig.matrix_world@(rig.pose.bones['hand_l'].head+rig.pose.bones['hand_l'].vector*.35)
g=world_to_camera_view(sc,sc.camera,grip);gx,gy=g.x*256,(1-g.y)*256
# Recurve bow with real horn/wood limbs, grip wrap and a drawn string.
pts=[pixel_world(gx+dx,gy+dy,grip) for dx,dy in [(16,-47),(20,-40),(12,-31),(2,-22),(-3,-10),(0,0),(-2,11),(5,23),(14,31),(12,37)]]
attach(curve('GEO-composite recurved bow',pts,.014,wood),'hand_l')
attach(curve('GEO-bow bright horn belly',[p+right*.008 for p in pts],.004,gold),'hand_l')
attach(curve('GEO-bow grip wrap',[grip-up*.055,grip+up*.055],.019,leather),'hand_l')
draw=rig.matrix_world@(rig.pose.bones['hand_r'].head+rig.pose.bones['hand_r'].vector*.4)
attach(curve('GEO-drawn bowstring',[pts[0],draw,pts[-1]],.003,linen),'hand_l')
arrowtip=grip-right*.20
attach(curve('GEO-nocked arrow',[draw,arrowtip],.005,wood),'hand_l')
attach(sphere('GEO-arrow iron point',arrowtip,(.025,.009,.009),iron),'hand_l')
# Saddle-attached leather quiver, tall arrows and small metal mouths.
qpos=rig.matrix_world@Vector((.19,.14,1.13))
attach(curve('GEO-leather quiver',[qpos-up*.24,qpos+up*.16],.065,leather),'pelvis')
for i in range(7):
 p=qpos+right*((i-3)*.016)
 attach(curve('GEO-quiver arrow',[p,p+up*(.28+.015*(i%3))],.004,wood),'pelvis')
 attach(curve('GEO-arrow feather',[p+up*.23,p+up*.29],.011,ivory),'pelvis')
# Stirrups and leather boots; no exposed sandals.
for side in ['l','r']:
 p=rig.matrix_world@rig.pose.bones['foot_'+side].head
 attach(curve('GEO-iron stirrup '+side,[p+right*.06,p+right*.07-up*.10,p-right*.07-up*.10,p-right*.06],.009,iron),'foot_'+side)
# Swept tail geometry follows the actual source tail, rather than a vertical rod.
for o in list(sc.objects):
 if o.name.startswith('Tail flowing fibre'):
  bpy.data.objects.remove(o,do_unlink=True)
# Wider footprint matches the galloping composition. It stays stationary in all clips.
base.scale.x=base.scale.y=1.23
sc['rest_frame']=12
rig['seated_pose']=json.dumps({p.name:[list(r) for r in p.matrix_basis] for p in rig.pose.bones})
print('KESHIG_KIT_READY',gx,gy)

# Product key is upper-left in this camera's coordinates; cool light separates the back.
for name,loc in [('Warm key',(-4,4,6)),('Cool fill',(-4,-4,3)),('Warm rim',(4,0,5))]:
 light=bpy.data.objects[name];light.location=loc;light.rotation_euler=(Vector((0,0,1.2))-light.location).to_track_quat('-Z','Y').to_euler()
