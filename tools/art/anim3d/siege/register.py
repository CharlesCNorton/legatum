"""Register physical parts and pose to measured token landmarks before UV projection.
All corrections are 3D transforms/IK; no image warp or depth-flattened geometry.
"""
import bpy,json,os
from pathlib import Path
from mathutils import Vector,Matrix
from bpy_extras.object_utils import world_to_camera_view
M=Path(os.environ['ANIM_ROOT'])/'masters/field-cannon'
bpy.ops.wm.open_mainfile(filepath=str(M/'field-cannon-plain.blend'))
s=bpy.context.scene;c=s.camera;r=bpy.data.objects['Gunner MPFB game_engine'];g=bpy.data.objects['Gun travel and recoil'];barrel=bpy.data.objects['Barrel elevation']
# Lower the view elevation and bring the wheel track into the source's negative space.
c.location=(3,-7,2.72);c.rotation_euler=(Vector((0,0,1.01))-c.location).to_track_quat('-Z','Y').to_euler()
c.data.ortho_scale=2.70
g.rotation_euler.z=-.70;g.location.x=.215;g.location.y=.14;g['rest_location']=list(g.location);g['rest_yaw']=g.rotation_euler.z
barrel.scale.x=1.65;barrel.rotation_euler.y=-.035
barrel.location.x-=.05;barrel.location.z+=.075;barrel.scale.y=barrel.scale.z=1.07
r.scale.z=1.05
# Narrower axle track with wheels still perpendicular to the barrel.
for side in [-1,1]:
 wheel=bpy.data.objects['Wheel '+str(side)];wheel.location.y=side*.51
axle=bpy.data.objects['Iron axle'];axle.scale.z=1.02/1.22
bpy.context.view_layer.update()
def pixel(v):
 q=world_to_camera_view(s,c,v);return Vector((q.x*256,(1-q.y)*256))
def screen_target(v,xy):
 delta=Vector(xy)-pixel(v);rot=c.matrix_world.to_quaternion()
 return v+rot @ Vector((delta.x*c.data.ortho_scale/256,-delta.y*c.data.ortho_scale/256,0))
def aim(name,d):
 p=r.pose.bones[name];q=p.bone.matrix_local.to_quaternion();rot=((q @ Vector((0,1,0))).rotation_difference(Vector(d).normalized()) @ q).to_matrix().to_4x4();rot.translation=p.head.copy();p.matrix=rot;bpy.context.view_layer.update()
def limb(up,low,t,pole):
 a=r.pose.bones[up].head.copy();delta=Vector(t)-a;l1=r.data.bones[up].length;l2=r.data.bones[low].length;d=min(delta.length,l1+l2-.0001);delta.normalize();along=(l1*l1-l2*l2+d*d)/(2*d);h=max(0,l1*l1-along*along)**.5
 side=Vector(pole)-a;side=(side-delta*side.dot(delta)).normalized();el=a+delta*along+side*h;aim(up,el-a);aim(low,Vector(t)-el)
# Slightly fuller tailored torso, less corrugated sleeves, more lifted face.
for name in ['Tailored blue coat body']:
 o=bpy.data.objects[name]
 for v in o.data.vertices:v.co.x*=1.06
p=r.pose.bones['head'];p.matrix_basis=p.matrix_basis @ Matrix.Rotation(-.13,4,'X')
# Grip on the chest side of the elbow, as in the painting, instead of the outstretched L arm.
bpy.context.view_layer.update();hand=r.pose.bones['hand_r'];target=r.matrix_world.inverted() @ screen_target(r.matrix_world @ hand.head,(57,87))
pole=r.matrix_world.inverted() @ screen_target(r.matrix_world @ Vector((-.45,-.18,1.12)),(47,91))
limb('upperarm_r','lowerarm_r',target,pole);aim('hand_r',(0,-.08,.015))
# Rotate and reposition the rammer in world space: sponge base (54,58), ground tip (83,201).
ram=bpy.data.objects['Rammer hand control'];bpy.context.view_layer.update()
start=ram.matrix_world.translation.copy();top=screen_target(start,(54,58));bottom=screen_target(start,(83,201))
# Preserve real depth; make the bottom touch the base rather than floating.
toward=c.matrix_world.to_quaternion() @ Vector((0,0,1))
bottom+=toward*((.105-bottom.z)/toward.z)
for name,a,b in [('Wooden rammer',bottom,top),('Rammer sponge',top,top+(top-bottom).normalized()*.16)]:
 o=bpy.data.objects[name];mid=(a+b)*.5;delta=b-a
 o.matrix_world=Matrix.Translation(mid) @ delta.to_track_quat('Z','Y').to_matrix().to_4x4()
 # Cone meshes were authored at their original radius/depth; rescale along local Z.
 z=[v.co.z for v in o.data.vertices];o.scale.z=delta.length/(max(z)-min(z))
# Match the source's lower boot with a grounded foot solve.
for side,xy in [('r',(46,201)),('l',(99,199))]:
 p=r.pose.bones['foot_'+side];world=screen_target(r.matrix_world @ p.head,xy)
 world.z=(r.matrix_world @ p.head).z
 target=r.matrix_world.inverted() @ world
 limb('thigh_'+side,'calf_'+side,target,(-.23 if side=='r' else .23,-.3,.5))
# Recompute reachable contact from palm rather than stretching the arm.
bpy.context.view_layer.update();contact=barrel.matrix_world @ Vector((-.27,-.025,.171))
direction=Vector((.11,-.015,-.03)).normalized();target=r.matrix_world.inverted() @ contact-direction*r.data.bones['hand_l'].length
limb('upperarm_l','lowerarm_l',target,(.56,-.24,1.14));aim('hand_l',direction)
r['barrel_contact_local']=[-.27,-.025,.171]
r['neutral_pose']=json.dumps({p.name:[list(row) for row in p.matrix_basis] for p in r.pose.bones})
records={}
for name,xy in [('hand_r',(57,87)),('foot_r',(46,201)),('head',(90,57))]:
 actual=pixel(r.matrix_world @ r.pose.bones[name].head);records[name]={'target':xy,'actual':list(actual),'error_px':(actual-Vector(xy)).length}
for name,xy in [('Wheel -1',(113,170)),('Wheel 1',(195,163))]:
 actual=pixel(bpy.data.objects[name].matrix_world.translation);records[name]={'target':xy,'actual':list(actual),'error_px':(actual-Vector(xy)).length}
(M/'registration.json').write_text(json.dumps({'landmarks':records,'note':'Measured 3D camera/IK fit; residual errors retained honestly. Not an exact viewpoint claim.'},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(M/'field-cannon-plain.blend'));bpy.ops.wm.save_as_mainfile(filepath=str(M/'field-cannon.blend'))
print('REGISTERED',records)
