"""Medjay scene helpers. All geometry lives on genuine articulated 3D meshes."""
import os, math, json
from pathlib import Path
import bpy
from mathutils import Vector, Matrix, Quaternion
ROOT=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')))
M=ROOT/'masters/medjay'; A=ROOT/'assets/medjay'; R=ROOT/'review/3d-v2'
for p in (M,A,R): p.mkdir(parents=True,exist_ok=True)
CLIPS={'idle':(8,10,True),'move':(8,12,True),'attack':(10,14,False),'hit':(4,12,False),'death':(10,10,False)}
def log(s):
 with (R/'medjay-log.md').open('a') as f:f.write(s+'\n')
 print(s,flush=True)
def mesh(name,vs,fs,mat):
 d=bpy.data.meshes.new(name);d.from_pydata(vs,[],fs);d.update();o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o)
 if mat:d.materials.append(mat)
 for p in d.polygons:p.use_smooth=True
 return o
def bevel(o,w=.003):
 m=o.modifiers.new('Rounded worked edges','BEVEL');m.width=w;m.segments=3
 return o
def solid(o,t=.006):
 m=o.modifiers.new('Real thickness','SOLIDIFY');m.thickness=t
 return o
def curve(name,pts,r,mat):
 d=bpy.data.curves.new(name,'CURVE');d.dimensions='3D';s=d.splines.new('POLY');s.points.add(len(pts)-1)
 for p,v in zip(s.points,pts):p.co=(*v,1)
 d.bevel_depth=r;d.bevel_resolution=2;o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);d.materials.append(mat)
 return o
def attach(o,rig,bone):
 bpy.context.view_layer.update();world=o.matrix_world.copy();o.parent=rig;o.parent_type='BONE';o.parent_bone=bone;bpy.context.view_layer.update();o.matrix_world=world
 return o
def aim(rig,name,direction):
 p=rig.pose.bones[name];q=p.bone.matrix_local.to_quaternion();delta=(q@Vector((0,1,0))).rotation_difference(Vector(direction).normalized());mat=(delta@q).to_matrix().to_4x4();mat.translation=p.head;p.matrix=mat;bpy.context.view_layer.update()
def limb(rig,upper,lower,target,pole):
 a=rig.pose.bones[upper].head.copy();t=Vector(target);axis=t-a;l1=rig.data.bones[upper].length;l2=rig.data.bones[lower].length;d=min(axis.length,l1+l2-.0001);axis.normalize();along=(l1*l1-l2*l2+d*d)/(2*d);h=max(0,l1*l1-along*along)**.5;side=Vector(pole)-a;side=(side-axis*side.dot(axis)).normalized();elbow=a+axis*along+side*h;aim(rig,upper,elbow-a);aim(rig,lower,t-elbow)
def material(name,col,metal=0,rough=.65,fill=None):
 m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*col,1);n=m.node_tree.nodes;l=m.node_tree.links;s=n.get('Principled BSDF');s.inputs['Base Color'].default_value=(*col,1);s.inputs['Metallic'].default_value=metal;s.inputs['Roughness'].default_value=rough
 noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=90 if fill=='linen' else 115;noise.inputs['Detail'].default_value=3
 bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.15;bump.inputs['Distance'].default_value=.0013;l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],s.inputs['Normal'])
 if fill:
  tex=n.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(A/f'fill-{fill}.png'),check_existing=True);tex.projection='BOX';tex.projection_blend=.3;coord=n.new('ShaderNodeTexCoord');l.new(coord.outputs['Generated'],tex.inputs['Vector']);mix=n.new('ShaderNodeMixRGB');mix.inputs[0].default_value=.45;mix.inputs[1].default_value=(*col,1);l.new(tex.outputs['Color'],mix.inputs[2]);l.new(mix.outputs[0],s.inputs['Base Color'])
 if fill=='linen':s.inputs['Sheen Weight'].default_value=.25
 if fill=='skin':s.inputs['Subsurface Weight'].default_value=.07
 return m
def configure():
 sc=bpy.context.scene;sc.render.engine=os.environ.get('RENDER_ENGINE','CYCLES');sc.render.threads_mode='FIXED';sc.render.threads=3
 if sc.render.engine=='CYCLES':
  device=os.environ.get('CYCLES_DEVICE','CPU');sc.cycles.device=device;sc.cycles.samples=int(os.environ.get('SAMPLES','8'));sc.cycles.use_denoising=True;sc.cycles.max_bounces=4
  if device=='GPU':
   p=bpy.context.preferences.addons['cycles'].preferences;p.compute_device_type='METAL';p.get_devices();devices=[d for d in p.devices if d.type=='METAL'];assert devices,'Metal GPU required; refusing CPU fallback'
   for d in p.devices:d.use=d.type=='METAL'
 sc.render.resolution_x=sc.render.resolution_y=int(os.environ.get('RESOLUTION','256'));sc.render.resolution_percentage=100;sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8';sc.render.use_file_extension=True
 assert sc.camera,'Assigned camera required'
 return sc
