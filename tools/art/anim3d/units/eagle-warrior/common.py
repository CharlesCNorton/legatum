"""Eagle warrior-owned geometry and skeleton helpers. Units in metres."""
import bpy, math, os, json
from pathlib import Path
from mathutils import Vector, Matrix
from math import sin,cos,pi
ROOT=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'));M=ROOT/'masters/eagle-warrior';A=ROOT/'assets/eagle-warrior';R=ROOT/'review/3d-v2'
CLIPS={'idle':(8,10,True),'move':(8,12,True),'attack':(10,14,False),'hit':(4,12,False),'death':(10,10,False)}
def log(s):
 with (R/'eagle-warrior-log.md').open('a') as f:f.write(s+'\n')
def linear(v):return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
def material(name,color,metal=0,rough=.65,fill=None):
 m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*color,1);n=m.node_tree.nodes;l=m.node_tree.links;s=n.get('Principled BSDF');s.inputs['Base Color'].default_value=(*color,1);s.inputs['Metallic'].default_value=metal;s.inputs['Roughness'].default_value=rough
 noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=150;noise.inputs['Detail'].default_value=3
 bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.20;bump.inputs['Distance'].default_value=.0018;l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs['Normal'],s.inputs['Normal'])
 if fill:
  tex=n.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(A/'painted-feathers.png'),check_existing=True);tex.projection='BOX';tex.projection_blend=.2
  coord=n.new('ShaderNodeTexCoord');l.new(coord.outputs['Generated'],tex.inputs['Vector']);l.new(tex.outputs['Color'],s.inputs['Base Color'])
  if fill in ('red','blue'):s.inputs['Sheen Weight'].default_value=.18
 if metal:
  g=n.new('ShaderNodeNewGeometry');r=n.new('ShaderNodeValToRGB');r.color_ramp.elements[0].position=.45;r.color_ramp.elements[0].color=(.045,.024,.009,1);r.color_ramp.elements[1].position=.54;r.color_ramp.elements[1].color=(*color,1);l.new(g.outputs['Pointiness'],r.inputs[0]);l.new(r.outputs[0],s.inputs['Base Color'])
 return m
def mesh(name,verts,faces,mat,smooth=True):
 d=bpy.data.meshes.new(name);d.from_pydata(verts,[],faces);d.update();o=bpy.data.objects.new('GEO-'+name,d);bpy.context.collection.objects.link(o)
 if mat:d.materials.append(mat)
 for p in d.polygons:p.use_smooth=smooth
 return o
def bevel(o,w=.003):
 m=o.modifiers.new('Soft worn edges','BEVEL');m.width=w;m.segments=3;return o
def solid(o,t=.006):
 m=o.modifiers.new('Real thickness','SOLIDIFY');m.thickness=t;return o
def curve(name,pts,radius,mat):
 d=bpy.data.curves.new(name,'CURVE');d.dimensions='3D';d.resolution_u=2;s=d.splines.new('POLY');s.points.add(len(pts)-1)
 for p,v in zip(s.points,pts):p.co=(*v,1)
 d.bevel_depth=radius;d.bevel_resolution=2;o=bpy.data.objects.new('GEO-'+name,d);bpy.context.collection.objects.link(o);d.materials.append(mat);return o
def sphere(name,loc,scale,mat):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=16,location=loc);o=bpy.context.object;o.name='GEO-'+name;o.scale=scale;o.data.materials.append(mat)
 for p in o.data.polygons:p.use_smooth=True
 return o
def attach(o,rig,bone):
 bpy.context.view_layer.update();world=o.matrix_world.copy();o.parent=rig;o.parent_type='BONE';o.parent_bone=bone
 # Preserve parent shear in the inverse matrix, never decompose it into child TRS.
 o.matrix_parent_inverse=Matrix.Identity(4);o.matrix_basis=Matrix.Identity(4);bpy.context.view_layer.update();parent_world=o.matrix_world.copy();o.matrix_parent_inverse=parent_world.inverted();o.matrix_basis=world;bpy.context.view_layer.update();o['attachment']=bone;return o
def bone_line(rig,name,a,b):
 p=rig.pose.bones[name];a,b=Vector(a),Vector(b);q=p.bone.matrix_local.to_quaternion();direction=q@Vector((0,1,0));rot=direction.rotation_difference((b-a).normalized())@q
 p.matrix=Matrix.Translation(a)@rot.to_matrix().to_4x4()@Matrix.Diagonal((1,(b-a).length/p.bone.length,1,1));bpy.context.view_layer.update()
def bind_posed(o,rig,weights):
 """Bind a newly authored volumetric mesh in the painting pose to the existing rig."""
 for name in {n for ww in weights for n in ww}:o.vertex_groups.new(name=name)
 for v,ww in zip(o.data.vertices,weights):
  mats=[(w,rig.pose.bones[n].matrix@rig.data.bones[n].matrix_local.inverted()) for n,w in ww.items()]
  deform=Matrix([[sum(w*m[r][c] for w,m in mats) for c in range(4)] for r in range(4)])
  v.co=deform.inverted()@v.co
  for name,w in ww.items():o.vertex_groups[name].add([v.index],w,'REPLACE')
 mod=o.modifiers.new('Eagle warrior skinning','ARMATURE');mod.object=rig
 o.parent=rig;o.matrix_parent_inverse=rig.matrix_world.inverted();return o
# Orthographic source calibration: 2.35 m square, 10-degree down view.
ELEV=math.radians(12);SCALE=2.50;TARGET=Vector((0,0,1.13))
def P(x,y,depth=0):return Vector(((x-128)*SCALE/256,depth,1.13+((128-y)*SCALE/256-depth*sin(ELEV))/cos(ELEV)))
def aim(o,target):o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
def save(name):
 bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(M/name))
