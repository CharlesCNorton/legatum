"""Archer-only geometry helpers, adapted from the infantry lead (MIT)."""
import os, json, math
from pathlib import Path
import bpy
from mathutils import Vector, Matrix
ROOT=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')))
MASTER=ROOT/'masters/archer'; ASSETS=ROOT/'assets/archer'; REVIEW=ROOT/'review/3d-v2'
CLIPS={'idle':(8,10,True),'move':(8,12,True),'attack':(10,14,False),'hit':(4,12,False),'death':(10,10,False)}
for p in (MASTER,ASSETS,REVIEW):p.mkdir(parents=True,exist_ok=True)
def log(message):
 with (REVIEW/'archer-log.md').open('a') as f:f.write(message+'\n')
def mat(name,color,metal=0,rough=.65):
 m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*color,1)
 s=m.node_tree.nodes.get('Principled BSDF');s.inputs['Base Color'].default_value=(*color,1);s.inputs['Metallic'].default_value=metal;s.inputs['Roughness'].default_value=rough
 return m
def mesh(name,vs,fs,m):
 d=bpy.data.meshes.new(name);d.from_pydata(vs,[],fs);d.update();o=bpy.data.objects.new('GEO-'+name,d);bpy.context.collection.objects.link(o)
 if m:d.materials.append(m)
 for p in d.polygons:p.use_smooth=True
 return o
def solid(o,t=.006):
 m=o.modifiers.new('Physical thickness','SOLIDIFY');m.thickness=t;return o
def bevel(o,w=.003):
 m=o.modifiers.new('Worn rounded edges','BEVEL');m.width=w;m.segments=3;return o
def curve(name,pts,r,m):
 d=bpy.data.curves.new(name,'CURVE');d.dimensions='3D';s=d.splines.new('POLY');s.points.add(len(pts)-1)
 for p,v in zip(s.points,pts):p.co=(*v,1)
 d.bevel_depth=r;d.bevel_resolution=2;o=bpy.data.objects.new('GEO-'+name,d);bpy.context.collection.objects.link(o);d.materials.append(m);return o
def ball(name,p,scale,m):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,location=p);o=bpy.context.object;o.name='GEO-'+name;o.scale=scale;o.data.materials.append(m)
 for f in o.data.polygons:f.use_smooth=True
 return o
def attach(o,rig,bone):
 bpy.context.view_layer.update();w=o.matrix_world.copy();o.parent=rig;o.parent_type='BONE';o.parent_bone=bone;bpy.context.view_layer.update();o.matrix_world=w;o['attachment']=bone;return o
def aim(rig,name,direction):
 p=rig.pose.bones[name];q=p.bone.matrix_local.to_quaternion();v=q@Vector((0,1,0));rot=(v.rotation_difference(Vector(direction).normalized())@q).to_matrix().to_4x4();rot.translation=p.head.copy();p.matrix=rot;bpy.context.view_layer.update()
def limb(rig,upper,lower,target,pole):
 a=rig.pose.bones[upper].head.copy();t=Vector(target);axis=t-a;l1=rig.data.bones[upper].length;l2=rig.data.bones[lower].length;d=min(axis.length,l1+l2-.0001);axis.normalize();along=(l1*l1-l2*l2+d*d)/(2*d);h=max(0,l1*l1-along*along)**.5;side=Vector(pole)-a;side=(side-axis*side.dot(axis)).normalized();elbow=a+axis*along+side*h;aim(rig,upper,elbow-a);aim(rig,lower,t-elbow)
def pose(rig,draw=1):
 limb(rig,'thigh_r','calf_r',(-.37,-.04,.04),(-.36,-.35,.5));limb(rig,'thigh_l','calf_l',(.37,.015,.04),(.38,-.32,.5))
 limb(rig,'upperarm_l','lowerarm_l',(.72,-.15,1.43),(.48,-.10,1.46));aim(rig,'hand_l',(0,0,.09))
 limb(rig,'upperarm_r','lowerarm_r',(-.005+.38*(1-draw),-.22,1.43),(-.55,-.08,1.52));aim(rig,'hand_r',(.085,0,.015))
 for side in ('r','l'):
  for digit in ['index','middle','ring','pinky']:
   for k in range(1,4):
    p=rig.pose.bones[f'{digit}_{k:02d}_{side}'];p.rotation_mode='XYZ';p.rotation_euler.x=1.1 if side=='l' else .6
 for side,sg in [('l',1),('r',-1)]:
  aim(rig,'foot_'+side,(sg*.075,-.13,-.035));aim(rig,'ball_'+side,(sg*.075,-.13,0))
 p=rig.pose.bones['head'];pivot=p.head.copy();p.matrix=Matrix.Translation(Vector((-.05,0,0)))@Matrix.Translation(pivot)@Matrix.Rotation(.72,4,'Z')@Matrix.Translation(-pivot)@p.matrix
 bpy.context.view_layer.update()
def save(path):
 bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(path))
