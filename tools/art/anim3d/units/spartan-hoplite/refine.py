"""Repeatable round-two fitting and frozen paint on finished 3D surfaces."""
import bpy, json, os, math, runpy
from pathlib import Path
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view
R=Path(os.environ['ANIM_ROOT']); M=Path(os.environ['ANIM_MASTER'])
bpy.ops.wm.open_mainfile(filepath=str(M/'unpainted.blend'))
sc=bpy.context.scene; rig=bpy.data.objects['Spearman • MPFB game_engine']
sc.frame_set(1)
cloth=bpy.data.objects['Cloak • simulated wool']; cloth.modifiers['Cloth per clip'].show_viewport=False
runpy.run_path('tools/art/anim3d/units/spartan-hoplite/shield_normals.py')['repair']()
body=bpy.data.objects['MPFB anatomical male • original topology']
if body.data.shape_keys:
 bpy.context.view_layer.objects.active=body; bpy.ops.object.shape_key_remove(all=True,apply_mix=True)
assert len(body.data.vertices)==19158
sc.camera.location=(2.5,-7,2.72)
sc.camera.rotation_euler=(Vector((0,0,1.05))-sc.camera.location).to_track_quat('-Z','Y').to_euler()
sc.camera.data.dof.use_dof=False
bpy.context.view_layer.update()
rot=sc.camera.matrix_world.to_quaternion(); right=rot @ Vector((1,0,0)); up=rot @ Vector((0,1,0)); view=rot @ Vector((0,0,1))
def pixel(ob,co):
 p=world_to_camera_view(sc,sc.camera,ob.matrix_world @ co);return Vector((256*p.x,256*(1-p.y)))
def sculpt(ob,co,target):
 p=pixel(ob,co); delta=(right*(target.x-p.x)-up*(target.y-p.y))*sc.camera.data.ortho_scale/256
 return ob.matrix_world.inverted()@(ob.matrix_world @ co+delta)
def aim(name,direction):
 p=rig.pose.bones[name];q=p.bone.matrix_local.to_quaternion();delta=(q @ Vector((0,1,0))).rotation_difference(Vector(direction).normalized())
 mat=(delta @ q).to_matrix().to_4x4();mat.translation=p.head;p.matrix=mat;bpy.context.view_layer.update()
def limb(u,l,target,pole):
 a=rig.pose.bones[u].head.copy();v=Vector(target)-a;l1=rig.data.bones[u].length;l2=rig.data.bones[l].length;d=min(v.length,l1+l2-.0001);v.normalize()
 along=(l1*l1-l2*l2+d*d)/(2*d);side=Vector(pole)-a;side=(side-v*side.dot(v)).normalized();elbow=a+along*v+max(0,l1*l1-along*along)**.5*side
 aim(u,elbow-a);aim(l,Vector(target)-elbow)
weapons=[o for o in sc.objects if o.name.startswith(('Ash dory','Spear bronze','Leaf spearhead','Iron spear butt'))]
weapon_world={o.name:o.matrix_world.copy() for o in weapons}
limb('upperarm_r','lowerarm_r',(-.37,-.31,1.43),(-.55,-.04,.95));aim('hand_r',(0,-.03,.09))
for ob in weapons:ob.matrix_world=weapon_world[ob.name]
bpy.context.view_layer.update()
# Curves become actual beveled solids before camera registration. The shaft stays
# a curve because animation and grip audits use its exact two endpoints.
for ob in list(sc.objects):
 if ob.type=='CURVE' and ob not in weapons:
  bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob;bpy.ops.object.convert(target='MESH')
# Finish static kit before UVs, preserving the weighted anatomy and cloth stack.
for ob in list(sc.objects):
 if ob.type!='MESH' or ob.hide_render:continue
 if any(m.type in {'ARMATURE','CLOTH'} for m in ob.modifiers):continue
 bpy.context.view_layer.objects.active=ob
 for mod in list(ob.modifiers):
  if mod.type in {'BEVEL','SOLIDIFY','SUBSURF'}:
   bpy.ops.object.modifier_apply(modifier=mod.name)
transforms={b.name:b.matrix @ b.bone.matrix_local.inverted() for b in rig.pose.bones}
def skin(ob,v):
 if not any(m.type=='ARMATURE' for m in ob.modifiers):return Matrix.Identity(4)
 entries=[(transforms[ob.vertex_groups[g.group].name],g.weight) for g in v.groups if ob.vertex_groups[g.group].name in transforms];total=sum(w for _,w in entries)
 return sum((m*(w/total) for m,w in entries),Matrix(((0,)*4,)*4)) if total else Matrix.Identity(4)
records=[]
for ob in list(sc.objects):
 if ob.type!='MESH' or ob.hide_render:continue
 name=ob.name
 kind=None
 if name.startswith(('Horsehair crest','Crest bronze')):kind='crest'
 elif ob.parent and ob.parent.name=='Aspis control':kind='shield'
 elif name.startswith(('Corinthian','Raised brow','Helmet')):kind='helmet'
 elif name=='MPFB anatomical male • original topology':kind='body'
 elif name.startswith('Crimson shoulder'):kind='mantle'
 elif name.startswith('Cloak •'):kind='cloak'
 if not kind:continue
 pts=[]
 for v in ob.data.vertices:
  s=skin(ob,v);co=s @ v.co;p=pixel(ob,co);target=p.copy()
  if kind=='crest':target=Vector((122+(p.x-126)*.66, p.y-1))
  elif kind=='helmet':target.y-=6
  elif kind=='body':
   w=max(0,min(1,(87-p.y)/15));target.y-=6*w
  elif kind=='shield':target=Vector((160+(p.x-153)*.83,127+(p.y-129)*.93))
  elif kind=='mantle':
   # Lower raised angular corners and follow the shoulder-to-shield drape.
   target.y+=max(0,77-p.y)*.75
   target.x=124+(p.x-124)*.93
  elif kind=='cloak':
   target.x=126+(p.x-126)*.82
   target.y+=max(0,79-p.y)*.85
  v.co=s.inverted_safe()@sculpt(ob,co,target);pts.append(target)
 ob.data.update()
 records.append({'object':name,'kind':kind,'bounds':[min(p.x for p in pts),min(p.y for p in pts),max(p.x for p in pts),max(p.y for p in pts)]})
# Softer substantial limestone edge, preserving the stationary contact plane.
base=bpy.data.objects['Stationary cream stone'];base.scale.x*=.97;base.scale.y*=.97
# Stored source has a real beveled base. Finished mesh is retained, not a plane.
rig['neutral_pose']=json.dumps({p.name:[list(row) for row in p.matrix_basis] for p in rig.pose.bones})
sc['round']=2;sc['unit']='spartan-hoplite'
bpy.ops.wm.save_as_mainfile(filepath=str(M/'plain.blend'))
# A single rest camera for all parts. No per-part painting rectangle stretches.
painting=bpy.data.images.load(str(R/'assets/spartan-hoplite/painting-aligned.png'),check_existing=True)
images={k:bpy.data.images.load(str(R/f'assets/spartan-hoplite/projection-{k}.png'),check_existing=True) for k in ['linen','red','bronze','skin']}
images['all']=painting
for ob in list(sc.objects):
 if ob.type!='MESH' or ob.hide_render or ob==base:continue
 name=ob.name; kind=None
 if name.startswith(('Horsehair','Crimson','Cloak •')):kind='red'
 elif name.startswith(('Forged bronze muscle','Linen pteruges','Pteruges','Linen armour','Narrow linen','Leather baldric','Baldric')):kind='all'
 elif name.startswith(('Convex bronze','Aspis turned','Aspis oak')):kind='all'
 elif name.startswith(('Corinthian','Raised brow','Helmet','Crest bronze')):kind='all'
 elif name.startswith(('Contoured greave','Greave chased')):kind='bronze'
 elif ob==body:kind='skin'
 elif name.startswith(('Leather sandal','Sandal')):kind='all'
 if not kind:continue
 states=[(m,m.show_viewport) for m in ob.modifiers]
 for m,_ in states:
  if m.type!='ARMATURE':m.show_viewport=False
 bpy.context.view_layer.update();ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
 assert len(me.vertices)==len(ob.data.vertices),(name,'projection topology')
 coords=[];weights=[]
 for v in me.vertices:
  world=ev.matrix_world @ v.co;p=world_to_camera_view(sc,sc.camera,world);coords.append((p.x,p.y))
  normal=(ev.matrix_world.to_3x3().inverted().transposed()@v.normal).normalized()
  weight=max(0,min(1,(normal.dot(view)-.02)/.35))
  # The hidden reverse receives its physical/generated fill, not ghosted paint.
  if weight>0:
   hit,loc,_,_,hitob,_=sc.ray_cast(bpy.context.evaluated_depsgraph_get(),world+view*.002,view,distance=8)
   if hit and (loc-world).length>.006:weight=0
  coords[-1]=(p.x,p.y);weights.append(weight)
 ev.to_mesh_clear()
 for m,state in states:m.show_viewport=state
 uv=ob.data.uv_layers.new(name='Rest painting round2');attr=ob.data.color_attributes.new(name='Rest paint visibility',type='FLOAT_COLOR',domain='CORNER')
 for i,loop in enumerate(ob.data.loops):uv.data[i].uv=coords[loop.vertex_index];attr.data[i].color=(weights[loop.vertex_index],)*3+(1,)
 for idx,old in enumerate(list(ob.data.materials)):
  if not old or not old.use_nodes:continue
  mat=old.copy();mat.name=name+' rest pigment';ob.data.materials[idx]=mat;n=mat.node_tree.nodes;l=mat.node_tree.links;s=n.get('Principled BSDF')
  if not s:continue
  # Keep true PBR, AO/curvature and generated fills on noncamera rays.
  if name.startswith(('Forged bronze muscle','Convex bronze')):
   s.inputs['Metallic'].default_value=0
   for link in list(s.inputs['Roughness'].links):l.remove(link)
   s.inputs['Roughness'].default_value=.8
   fill=n.new('ShaderNodeTexImage');fill.image=bpy.data.images.load(str(R/'assets/horseman/fill-linen.png'),check_existing=True);fill.projection='BOX';fill.projection_blend=.3
   tc=n.new('ShaderNodeTexCoord');l.new(tc.outputs['Generated'],fill.inputs['Vector']);l.new(fill.outputs['Color'],s.inputs['Base Color'])
  tex=n.new('ShaderNodeTexImage');tex.image=images[kind];tex.extension='CLIP';tc=n.new('ShaderNodeUVMap');tc.uv_map=uv.name;l.new(tc.outputs[0],tex.inputs['Vector'])
  at=n.new('ShaderNodeVertexColor');at.layer_name=attr.name;factor=n.new('ShaderNodeMath');factor.operation='MULTIPLY';l.new(at.outputs[0],factor.inputs[0]);l.new(tex.outputs['Alpha'],factor.inputs[1])
  strength=n.new('ShaderNodeMath');strength.operation='MULTIPLY';strength.inputs[1].default_value=.96;l.new(factor.outputs[0],strength.inputs[0])
  pigment=n.new('ShaderNodeBsdfPrincipled');pigment.name='Camera painted pigment';pigment.inputs['Base Color'].default_value=(0,0,0,1);pigment.inputs['Specular IOR Level'].default_value=0; pigment.inputs['Emission Strength'].default_value=1;l.new(tex.outputs['Color'],pigment.inputs['Emission Color'])
  light=n.new('ShaderNodeLightPath');mask=n.new('ShaderNodeMath');mask.operation='MULTIPLY';l.new(light.outputs['Is Camera Ray'],mask.inputs[0]);l.new(strength.outputs[0],mask.inputs[1])
  mix=n.new('ShaderNodeMixShader');l.new(mask.outputs[0],mix.inputs[0]);l.new(s.outputs[0],mix.inputs[1]);l.new(pigment.outputs[0],mix.inputs[2]);out=n.get('Material Output');l.new(mix.outputs[0],out.inputs['Surface'])
sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0
for name,energy in [('Warm upper-left key',400),('Soft cool fill',90),('Warm back rim',160)]:bpy.data.objects[name].data.energy=energy
key=bpy.data.objects['Warm upper-left key'];key.data.size=4;key.data.color=(1,.95,.87)
stone=bpy.data.materials['Cream limestone'];s=stone.node_tree.nodes.get('Principled BSDF')
def linear(v):return ((v/255+.055)/1.055)**2.4
s.inputs['Base Color'].default_value=tuple(linear(v)*.85 for v in (233,207,160))+(1,);s.inputs['Roughness'].default_value=.86
n=stone.node_tree.nodes;l=stone.node_tree.links
pig=n.new('ShaderNodeBsdfPrincipled');pig.inputs['Base Color'].default_value=(0,0,0,1);pig.inputs['Specular IOR Level'].default_value=0;
pig.inputs['Emission Color'].default_value=tuple(linear(v) for v in (233,207,160))+(1,);pig.inputs['Emission Strength'].default_value=1
light=n.new('ShaderNodeLightPath');weight=n.new('ShaderNodeMath');weight.operation='MULTIPLY';weight.inputs[1].default_value=.48;l.new(light.outputs['Is Camera Ray'],weight.inputs[0])
mix=n.new('ShaderNodeMixShader');l.new(weight.outputs[0],mix.inputs[0]);l.new(s.outputs[0],mix.inputs[1]);l.new(pig.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],n.get('Material Output').inputs['Surface'])
sc['projection_method']='Single frozen camera; finished solid kit; camera-only source pigment; original physical backs, AO and generated linen'
(M/'registration.json').write_text(json.dumps({'camera':list(sc.camera.location),'target':[0,0,1.05],'objects':records,'limitations':'Measured contour fit; not an exact camera/pose match'},indent=2))
cloth.modifiers['Cloth per clip'].show_viewport=True
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(M/'spearman.blend'))
print('REFINED',len(records),'fitted objects')
