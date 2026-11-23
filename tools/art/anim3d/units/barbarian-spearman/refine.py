"""Fit complete volumes to rest-view landmarks, retaining MPFB skinning and depth."""
import bpy, os, math, json
from pathlib import Path
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view

M=Path(os.environ['ANIM_ROOT'])/'masters/barbarian-spearman'
bpy.ops.wm.open_mainfile(filepath=str(M/'plain.blend'))
s=bpy.context.scene; rig=bpy.data.objects['Barbarian skeleton'];cam=s.camera
body=bpy.data.objects['MPFB barbarian anatomy']
if body.data.shape_keys:
 bpy.context.view_layer.objects.active=body
 bpy.ops.object.shape_key_remove(all=True,apply_mix=True)
assert len(body.data.vertices)==19158
# A continuous thick shoulder pelt fills gaps between the original separate tufts.
verts=[];faces=[];n=64
for j in range(9):
 t=j/8;rx=.105+.24*t;ry=.105+.10*t
 for i in range(n):
  a=2*math.pi*i/n;fold=.008*math.sin(a*17)*(t+.2)
  z=1.69-.16*t-.10*t*max(0,math.cos(a))+.009*math.sin(a*13)*t
  verts.append(((rx+fold)*math.sin(a),-(ry+fold)*math.cos(a),z))
for j in range(8):
 for i in range(n):a=j*n+i;b=j*n+(i+1)%n;faces.append((a,b,b+n,a+n))
me=bpy.data.meshes.new('Continuous pelt mantle');me.from_pydata(verts,[],faces);me.update()
ob=bpy.data.objects.new('Continuous pelt mantle',me);s.collection.objects.link(ob);me.materials.append(bpy.data.materials['Wolf brown fur'])
for poly in me.polygons:poly.use_smooth=True
mod=ob.modifiers.new('Pelt thickness','SOLIDIFY');mod.thickness=.018
mod=ob.modifiers.new('Soft pelt edge','BEVEL');mod.width=.004;mod.segments=3
world=ob.matrix_world.copy();ob.parent=rig;ob.parent_type='BONE';ob.parent_bone='spine_03';bpy.context.view_layer.update();ob.matrix_world=world

# Freeze curves and static finish BEFORE calibrating projected UVs.
for ob in list(s.objects):
 if ob.type=='CURVE':
  bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
  bpy.ops.object.convert(target='MESH')
bpy.context.view_layer.update()
q=cam.matrix_world.to_quaternion();right=q@Vector((1,0,0));up=q@Vector((0,1,0));ray=q@Vector((0,0,1));px=cam.data.ortho_scale/256
bones={b.name:b.matrix@b.bone.matrix_local.inverted() for b in rig.pose.bones}

def fitted(p):
 x,y=p
 shoulder=math.exp(-((x-101)/22)**2-((y-61)/18)**2)
 elbow=math.exp(-((x-80)/10)**2-((y-86)/14)**2)
 torso=math.exp(-((x-124)/28)**2-((y-99)/25)**2)
 skirt=math.exp(-((x-118)/40)**2-((y-139)/13)**2)
 dx=-14*shoulder-3*elbow+(.12*(x-126)-1.5)*torso
 dy=-9*shoulder-2*elbow+5*skirt
 # Broaden bent-knee silhouette and remove the forward-facing tiny shoes.
 leg=max(0,min(1,(y-150)/55))
 if x<128:
  dx+=(-7+.15*(x-88))*leg;dy-=11*leg
 else:
  dx+=(2+.28*(x-157))*leg;dy-=10*leg
 return Vector((x+dx,y+dy))

changed=0
for ob in list(s.objects):
 if ob.type!='MESH' or ob.name=='Stationary cream base':continue
 if any(k in ob.name.lower() for k in ['shield','spear','shaft','socket']):continue
 skinned=any(m.type=='ARMATURE' for m in ob.modifiers)
 inv=ob.matrix_world.inverted()
 for v in ob.data.vertices:
  skin=Matrix.Identity(4)
  if skinned:
   inf=[(bones[ob.vertex_groups[g.group].name],g.weight) for g in v.groups if ob.vertex_groups[g.group].name in bones]
   total=sum(w for _,w in inf)
   if total:skin=sum((a*(w/total) for a,w in inf),Matrix(((0.,)*4,)*4))
  world=ob.matrix_world@(skin@v.co)
  uv=world_to_camera_view(s,cam,world);p=Vector((uv.x*256,(1-uv.y)*256));d=fitted(p)-p
  if ob.name.startswith('Swept shoulder hair'):
   d.x-=12*math.exp(-((p.x-118)/18)**2-((p.y-40)/17)**2)
  moved=world+right*d.x*px-up*d.y*px
  # Feet move along the camera ray back onto the original contact plane.
  foot=max(0,min(1,(p.y-183)/15))
  moved+=ray*((world.z-moved.z)*foot/ray.z)
  v.co=skin.inverted_safe()@(inv@moved)
 ob.data.update();changed+=1
# Fit the entire convex shield, then its actual raised iron boss.
for ob in list(s.objects):
 if ob.type!='MESH' or 'shield' not in ob.name.lower():continue
 inv=ob.matrix_world.inverted()
 for v in ob.data.vertices:
  w=ob.matrix_world@v.co;p=world_to_camera_view(s,cam,w);x,y=p.x*256,(1-p.y)*256
  tx=179+(x-181)*.93;ty=110+(y-115)*.98
  tx+=.12*(ty-109)
  if ob.name=='Domed iron shield boss':
   tx=184+(x-181)*.82;ty=109+(y-115)*.82
  v.co=inv@(w+right*(tx-x)*px-up*(ty-y)*px)
 ob.data.update()
# Shorten only the forward spear reach, retaining the palm and rear shaft.
for ob in list(s.objects):
 if ob.type!='MESH' or not any(k in ob.name.lower() for k in ['spear','shaft','socket']):continue
 inv=ob.matrix_world.inverted()
 for v in ob.data.vertices:
  w=ob.matrix_world@v.co;p=world_to_camera_view(s,cam,w);x,y=p.x*256,(1-p.y)*256
  if x>76:v.co=inv@(w-right*((x-76)*.052)*px+up*((y-109)*.052)*px)
 ob.data.update()
# One real stone disc; preserve top and contact height, shift its ground footprint.
base=bpy.data.objects['Stationary cream base'];base.location.x=-.018;base.location.y=.20
for mod in base.modifiers:
 if mod.type=='BEVEL':mod.width=.012;mod.segments=5
# Apply all static finish on rigid kit. Skinned anatomy retains original topology.
for ob in list(s.objects):
 if ob.type!='MESH' or ob==body:continue
 bpy.context.view_layer.objects.active=ob
 for mod in list(ob.modifiers):
  if mod.type in {'SOLIDIFY','BEVEL','SUBSURF'}:bpy.ops.object.modifier_apply(modifier=mod.name)
# Rebind the fitted surface to fitted joints. Merely moving skin vertices along
# camera rays left ankles in front of their shoes; that offset swung underneath
# the body on death and falsely propped the torso above the stone.
bpy.context.view_layer.update()
attached={ob:ob.matrix_world.copy() for ob in s.objects if ob.parent==rig and ob.parent_type=='BONE'}
saved_mods=[]
for mod in body.modifiers:
 if mod.type!='ARMATURE':saved_mods.append((mod,mod.show_viewport));mod.show_viewport=False
bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());surface=ev.to_mesh()
posed=[v.co.copy() for v in surface.vertices];ev.to_mesh_clear()
assert len(posed)==len(body.data.vertices)
old={bone.name:(bone.head.copy(),bone.tail.copy(),bone.matrix.to_quaternion()@Vector((0,0,1))) for bone in rig.pose.bones}
def fit_joint(point):
 world=rig.matrix_world@point;uv=world_to_camera_view(s,cam,world);p=Vector((uv.x*256,(1-uv.y)*256));d=fitted(p)-p
 moved=world+right*d.x*px-up*d.y*px
 foot=max(0,min(1,(p.y-183)/15));moved+=ray*((world.z-moved.z)*foot/ray.z)
 return rig.matrix_world.inverted()@moved
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.ops.object.mode_set(mode='EDIT')
for bone in rig.data.edit_bones:bone.use_connect=False
for bone in rig.data.edit_bones:
 head,tail,zaxis=old[bone.name];bone.head=fit_joint(head);bone.tail=fit_joint(tail);bone.align_roll(zaxis)
bpy.ops.object.mode_set(mode='OBJECT')
for bone in rig.pose.bones:bone.matrix_basis=Matrix.Identity(4)
for v,co in zip(body.data.vertices,posed):v.co=co
body.data.update();bpy.context.view_layer.update()
for ob,world in attached.items():ob.matrix_world=world
for mod,value in saved_mods:mod.show_viewport=value
bpy.context.view_layer.update()
rig['neutral_pose']=json.dumps({p.name:[list(row) for row in p.matrix_basis] for p in rig.pose.bones})

s['registration']='Driver round 2: full-depth shoulder/torso/foot fit, shield and boss registration; no alpha cutout'
(M/'registration.json').write_text(json.dumps({'meshes_fitted':changed,'body_vertices':len(body.data.vertices),'bones':len(rig.data.bones),'camera':list(cam.location),'scale':cam.data.ortho_scale,'method':s['registration']},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(M/'registered.blend'))
print('REGISTERED',changed)
