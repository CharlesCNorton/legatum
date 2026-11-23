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
 dx=-11*shoulder-3*elbow+(.12*(x-126)-1.5)*torso
 dy=-7*shoulder-2*elbow+5*skirt
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
s['registration']='Round 2: full-depth shoulder/torso/foot fit, shield and boss registration; no alpha cutout'
(M/'registration.json').write_text(json.dumps({'meshes_fitted':changed,'body_vertices':len(body.data.vertices),'bones':len(rig.data.bones),'camera':list(cam.location),'scale':cam.data.ortho_scale,'method':s['registration']},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(M/'registered.blend'))
print('REGISTERED',changed)
