"""Register physical parts and pose to measured token landmarks before UV projection.
All corrections are 3D transforms/IK; no image warp or depth-flattened geometry.
"""
import bpy,json,os,runpy
from pathlib import Path
from mathutils import Vector,Matrix
from bpy_extras.object_utils import world_to_camera_view
M=Path(os.environ['ANIM_ROOT'])/'masters/field-cannon'
bpy.ops.wm.open_mainfile(filepath=str(M/'field-cannon-plain.blend'))
s=bpy.context.scene;c=s.camera;r=bpy.data.objects['Gunner MPFB game_engine'];g=bpy.data.objects['Gun travel and recoil'];barrel=bpy.data.objects['Barrel elevation']
# Lower the view elevation and bring the wheel track into the source's negative space.
c.location=(3,-7,2.72);c.rotation_euler=(Vector((0,0,1.01))-c.location).to_track_quat('-Z','Y').to_euler()
c.data.ortho_scale=2.70
g.rotation_euler.z=-.62;g.location.x=.215;g.location.y=.14;g['rest_location']=list(g.location);g['rest_yaw']=g.rotation_euler.z
barrel.scale.x=1.65;barrel.rotation_euler.y=-.035
barrel.location.x-=.05;barrel.location.z+=.075;barrel.scale.y=barrel.scale.z=1.07
r.scale.z=1.05
# Narrower axle track with wheels still perpendicular to the barrel.
for side in [-1,1]:
 wheel=bpy.data.objects['Wheel '+str(side)];wheel.location.y=-.52 if side<0 else .49
axle=bpy.data.objects['Iron axle'];axle.scale.z=1.06/1.22
bpy.context.view_layer.update()
def pixel(v):
 q=world_to_camera_view(s,c,v);return Vector((q.x*256,(1-q.y)*256))
def screen_target(v,xy):
 delta=Vector(xy)-pixel(v);rot=c.matrix_world.to_quaternion()
 return v+rot @ Vector((delta.x*c.data.ortho_scale/256,-delta.y*c.data.ortho_scale/256,0))
def aim(name,d):
 p=r.pose.bones[name];q=p.bone.matrix_local.to_quaternion();rot=((q @ Vector((0,1,0))).rotation_difference(Vector(d).normalized()) @ q).to_matrix().to_4x4();rot.translation=p.head.copy()
 if name.startswith(('upperarm_','lowerarm_')):rot=rot @ Matrix.Diagonal((1,r.get('arm_length_factor',1),1,1))
 p.matrix=rot;bpy.context.view_layer.update()
def limb(up,low,t,pole):
 a=r.pose.bones[up].head.copy();delta=Vector(t)-a;factor=r.get('arm_length_factor',1) if up.startswith('upperarm_') else 1;l1=r.data.bones[up].length*factor;l2=r.data.bones[low].length*factor;d=min(delta.length,l1+l2-.0001);delta.normalize();along=(l1*l1-l2*l2+d*d)/(2*d);h=max(0,l1*l1-along*along)**.5
 side=Vector(pole)-a;side=(side-delta*side.dot(delta)).normalized();el=a+delta*along+side*h;aim(up,el-a);aim(low,Vector(t)-el)
# Turn the full anatomical head left, retaining its real depth and attached shako.
p=r.pose.bones['head'];p.matrix_basis=p.matrix_basis @ Matrix.Rotation(-.13,4,'X')
bpy.context.view_layer.update()
pivot=p.head.copy();p.matrix=Matrix.Translation(pivot) @ Matrix.Rotation(-.30,4,'Z') @ Matrix.Translation(-pivot) @ p.matrix
bpy.context.view_layer.update()
# The painted adult's arms are ten percent longer than the default MPFB macro.
# Scale actual bone segments (including weighted anatomy and sleeves), never detached hands.
r['arm_length_factor']=1.10
for side in ['l','r']:
 for segment in ['upperarm_','lowerarm_','hand_']:
  r.data.bones[segment+side].inherit_scale='NONE'
# Fit clavicle endpoints before solving the elbows, rather than pulling sleeve vertices off the rig.
for side,xy in [('r',(68,65)),('l',(105,70))]:
 upper=r.pose.bones['upperarm_'+side];clavicle=upper.parent
 target=r.matrix_world.inverted() @ screen_target(r.matrix_world @ upper.head,xy)
 delta=target-clavicle.head;length=r.data.bones[clavicle.name].length
 aim(clavicle.name,delta)
 clavicle.scale.y=delta.length/length
 bpy.context.view_layer.update()
# Fit the barrel's real elevation/length and position from two painted axis landmarks.
# A physical pitch is essential: changing yaw to fix the slope also destroys wheel perspective.
axis_a=Vector((-.31,0,.02));axis_b=Vector((.76,0,.02))
target_a=Vector((130,130));target_b=Vector((211,141));wanted=target_b-target_a
best=None
for step in range(201):
 angle=-.30+step*.002
 barrel.rotation_euler.y=angle;bpy.context.view_layer.update()
 delta=pixel(barrel.matrix_world @ axis_b)-pixel(barrel.matrix_world @ axis_a)
 error=abs(delta.y/delta.x-wanted.y/wanted.x)
 if best is None or error<best[0]:best=(error,angle,wanted.x/delta.x)
barrel.rotation_euler.y=best[1];barrel.scale.x*=best[2];barrel.scale.y=barrel.scale.z=.93
bpy.context.view_layer.update()
a=barrel.matrix_world @ axis_a
shift=screen_target(a,target_a)-a
barrel.location+=g.matrix_world.to_3x3().inverted() @ shift
bpy.context.view_layer.update()
# Solve the elbow and wrist on their camera rays, retaining real arm lengths/depth.
# A pole alone cannot match this strongly foreshortened forearm.
def on_sphere(point,center,radius):
 direction=(r.matrix_world.to_3x3().inverted() @ (c.matrix_world.to_quaternion() @ Vector((0,0,1)))).normalized()
 offset=point-center;b=offset.dot(direction)
 discriminant=b*b-offset.length_squared+radius*radius
 assert discriminant>=0,'Projected arm landmarks exceed the anatomical segment length'
 return point+direction*(-b+discriminant**.5)
a=r.pose.bones['upperarm_r'].head.copy()
elbow=r.matrix_world.inverted() @ screen_target(r.matrix_world @ a,(49,85))
elbow=on_sphere(elbow,a,r.data.bones['upperarm_r'].length*r['arm_length_factor'])
wrist=r.matrix_world.inverted() @ screen_target(r.matrix_world @ elbow,(57,87))
wrist=on_sphere(wrist,elbow,r.data.bones['lowerarm_r'].length*r['arm_length_factor'])
aim('upperarm_r',elbow-a);aim('lowerarm_r',wrist-elbow);aim('hand_r',(.09,-.01,.015))
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
 if name=='Rammer sponge':o.scale.x=o.scale.y=1.4
# Match the source's lower boot with a grounded foot solve.
for side,xy in [('r',(46,201)),('l',(99,199))]:
 p=r.pose.bones['foot_'+side];world=screen_target(r.matrix_world @ p.head,xy)
 world.z=(r.matrix_world @ p.head).z
 target=r.matrix_world.inverted() @ world
 pole=(-.23 if side=='r' else .23,-.3,.5)
 limb('thigh_'+side,'calf_'+side,target,pole)
 aim('foot_'+side,r.data.bones['foot_'+side].tail_local-r.data.bones['foot_'+side].head_local)
 bpy.context.view_layer.update()
 sole=bpy.data.objects['Boot sole '+side]
 ground=min((sole.matrix_world @ v.co).z for v in sole.data.vertices)
 world=r.matrix_world @ r.pose.bones['foot_'+side].head
 world.z+=.098-ground
 limb('thigh_'+side,'calf_'+side,r.matrix_world.inverted() @ world,pole)
 aim('foot_'+side,r.data.bones['foot_'+side].tail_local-r.data.bones['foot_'+side].head_local)
# Recompute the wrist from the palm contact using the fitted anatomical segment lengths.
bpy.context.view_layer.update();contact=barrel.matrix_world @ Vector((-.20,-.025,.171))
direction=Vector((.11,-.015,-.03)).normalized();target=r.matrix_world.inverted() @ contact-direction*r.data.bones['hand_l'].length
limb('upperarm_l','lowerarm_l',target,(.56,-.24,1.14));aim('hand_l',direction)
r['barrel_contact_local']=[-.20,-.025,.171]
wheel_fit=runpy.run_path(str(Path(__file__).with_name('wheels.py')))['fit_wheels']()
runpy.run_path(str(Path(__file__).with_name('tailoring.py')))['fit_crossbelts']()
r['neutral_pose']=json.dumps({p.name:[list(row) for row in p.matrix_basis] for p in r.pose.bones})
records={}
for name,xy in [('hand_r',(57,87)),('foot_r',(46,201)),('head',(90,57)),('upperarm_r',(68,65)),('upperarm_l',(105,70)),('lowerarm_r',(49,85))]:
 actual=pixel(r.matrix_world @ r.pose.bones[name].head);records[name]={'target':xy,'actual':list(actual),'error_px':(actual-Vector(xy)).length}
for name,xy in [('Wheel -1',(118,170)),('Wheel 1',(198,162))]:
 actual=pixel(bpy.data.objects[name].matrix_world.translation);records[name]={'target':xy,'actual':list(actual),'error_px':(actual-Vector(xy)).length}
for name,point,xy in [('barrel_breech',axis_a,target_a),('barrel_muzzle',axis_b,target_b)]:
 actual=pixel(barrel.matrix_world @ point);records[name]={'target':list(xy),'actual':list(actual),'error_px':(actual-xy).length}
(M/'registration.json').write_text(json.dumps({'landmarks':records,'wheel_surfaces':wheel_fit,'note':'Measured 3D camera/IK fit; residual errors retained honestly. Not an exact viewpoint claim.'},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(M/'field-cannon-plain.blend'));bpy.ops.wm.save_as_mainfile(filepath=str(M/'field-cannon.blend'))
print('REGISTERED',records)
