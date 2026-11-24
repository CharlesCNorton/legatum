"""Fit full-depth bind geometry and skeleton before freezing finished-surface UVs."""
import bpy, bmesh, os, json
import numpy as np
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
M=Path(os.environ['ANIM_ROOT'])/'masters/barbarian-scout'
bpy.ops.wm.open_mainfile(filepath=str(M/'plain.blend'))
s=bpy.context.scene;cam=s.camera;rig=bpy.data.objects['Scout • MPFB rig']
original_lengths={b.name:b.length for b in rig.data.bones}
assert not s.get('round2_registered'), 'Rebuild plain input before re-registering'
# Pixel landmarks are measured in the unlabelled 256 px source/render cells.
# Full 3D surfaces retain camera depth; no cutout or frame-dependent reprojection.
controls=[
 ((142,24),(142,24),19), ((143,48),(143,48),19),
 ((167,37),(183,31),18), ((151,38),(166,29),14),
 ((194,52),(203,52),20), ((162,72),(173,68),20),
 ((98,76),(89,77),22), ((99,115),(85,113),22),
 ((101,155),(100,147),19), ((128,121),(128,115),22),
 ((165,159),(165,138),23), ((175,218),(161,195),26),
 ((179,230),(169,204),20), ((112,189),(99,195),20),
 ((83,202),(76,188),19), ((80,217),(74,198),15),
 ((54,59),(51,76),18), ((68,119),(63,124),22),
 ((128,92),(128,92),22), ((128,154),(126,150),20),
]
centers=np.array([a for a,b,r in controls]); radii=np.array([r for a,b,r in controls]);delta=np.array([np.subtract(b,a) for a,b,r in controls])
K=np.exp(-np.sum((centers[:,None,:]-centers[None,:,:])**2,axis=2)/(2*radii[None,:]**2))
weights=np.linalg.solve(K+np.eye(len(K))*.015,delta)
old_rotation=cam.matrix_world.to_quaternion().copy()
old_camera_inv=cam.matrix_world.inverted().copy()
cam.location=(0,-6,1.95)
cam.rotation_euler=(Vector((0,0,.67))-cam.location).to_track_quat('-Z','Y').to_euler()
bpy.context.view_layer.update()
view_rotation=cam.matrix_world.to_quaternion()@old_rotation.inverted()
right=cam.matrix_world.to_quaternion()@Vector((1,0,0));up=cam.matrix_world.to_quaternion()@Vector((0,1,0));ray=cam.matrix_world.to_quaternion()@Vector((0,0,-1));scale=cam.data.ortho_scale/256
camera_inv=old_camera_inv
def fitted_surface(v):
 q=camera_inv@v; px=np.array([128+q.x/scale,128-q.y/scale])
 d=np.exp(-np.sum((centers-px)**2,axis=1)/(2*radii**2))@weights
 out=Vector((0,0,.67))+view_rotation@(v-Vector((0,0,.67)))+right*(float(d[0])*scale)-up*(float(d[1])*scale)
 return out
# A shared depth translation per side preserves leg and torso proportions.
# Smoothly blend across the centre instead of shearing calves by vertex height.
foot_depth={}
for side in ('l','r'):
 b=rig.pose.bones['foot_'+side]
 v=rig.matrix_world@((b.head+b.tail)*.5)
 foot_depth[side]=(v.z-fitted_surface(v).z)/ray.z

def fitted(v):
 out=fitted_surface(v)
 t=max(0,min(1,(v.x+.12)/.24));t=t*t*(3-2*t)
 correction=foot_depth['r']*(1-t)+foot_depth['l']*t
 return out+ray*correction
wrist=fitted(rig.matrix_world@rig.pose.bones['hand_l'].head)
def is_raised_hand(name):
 return name.endswith('_l') and name.startswith(('hand','index','middle','ring','pinky','thumb'))
def salute(point):return wrist+(point-wrist)*.65
# Convert curves and finish the rendered surface BEFORE deriving projection UVs.
for o in list(s.objects):
 if o.type=='CURVE':
  bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
for o in list(s.objects):
 if o.type!='MESH' or o.name=='GEO-stationary-cream-base':continue
 bpy.context.view_layer.objects.active=o
 for mod in list(o.modifiers):
  if mod.type in ('SOLIDIFY','BEVEL','SUBSURF'):
   if mod.type=='SUBSURF':mod.levels=mod.render_levels=1
   bpy.ops.object.modifier_apply(modifier=mod.name)
# Preserve world matrices of bone-parented kit while refitting the skeleton.
worlds={o.name:o.matrix_world.copy() for o in s.objects if o.type=='MESH'}
for o in list(s.objects):
 if o.type!='MESH' or o.name=='GEO-stationary-cream-base':continue
 matrix=worlds[o.name];inv=matrix.inverted()
 for v in o.data.vertices:
  original=matrix@v.co;point=fitted(original)
  if o.name in ('GEO-folded-pelt-cape','GEO-layered-fur-tufts.001'):
   point.x-=.13*max(0,min(1,(1.1-original.z)/.3))*max(0,min(1,-original.x/.25))
  if o.name=='GEO-forged-axe-head':point.x=-.103+(point.x-.09+.103)*.70
  if o.name=='GEO-axe-haft':point.x-=.09*max(0,min(1,(original.z-.42)/.44))
  if o.name in ('GEO-forged-axe-head','GEO-axe-haft'):point-=ray*.085
  if o.vertex_groups:
   hand_weight=min(1,sum(g.weight for g in v.groups if is_raised_hand(o.vertex_groups[g.group].name)))
   if hand_weight:point=point.lerp(salute(point),hand_weight)
  v.co=inv@point
 o.data.update()
 if o.name=='GEO-forged-axe-head' or o.name.startswith('GEO-closed-boot'):
  bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.ops.object.mode_set(mode='EDIT');inv=rig.matrix_world.inverted()
for b in rig.data.edit_bones:
 h=fitted(rig.matrix_world@b.head);t=fitted(rig.matrix_world@b.tail)
 if is_raised_hand(b.name):h=salute(h);t=salute(t)
 b.head=inv@h;b.tail=inv@t
bpy.ops.object.mode_set(mode='OBJECT');bpy.context.view_layer.update()
for name,matrix in worlds.items():bpy.data.objects[name].matrix_world=matrix
base=bpy.data.objects['GEO-stationary-cream-base'];base.location.x-=.042;base.location.y+=.08;base.scale.x*=.955;base.scale.y*=.955
bpy.context.view_layer.update()  # Capture these transforms before restoring bone-parented kit.
rim=base.data.materials[0].copy();rim.name='MAT-cream-stone-rim';rim.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.47,.25,.085,1);base.data.materials.append(rim)
for polygon in base.data.polygons:
 polygon.material_index=0 if polygon.normal.z>.5 else 1
# Retain the painted palette without orange illumination being applied twice.
for o in s.objects:
 if o.type=='LIGHT':o.data.energy*=.55
ratios={b.name:b.length/original_lengths[b.name] for b in rig.data.bones if b.name.startswith(('thigh_','calf_','upperarm_','lowerarm_'))}
assert all(.5<v<1.75 for v in ratios.values()),('Unnatural limb stretch',ratios)
# The first projection hid a forty-pixel hand in the trousers. Fit actual
# palm/fingers and their bind bones together, with a weighted wrist transition.
hand_origin=rig.matrix_world@rig.data.bones['hand_r'].head_local
view=-ray

def right_hand_fit(point):
 d=point-hand_origin
 return (hand_origin-right*4*scale+up*5*scale+view*.105
         +right*(.88*d.dot(right)-.19*d.dot(up))
         +up*(.48*d.dot(up))+view*(.75*d.dot(view)))

def right_hand_bone(name):
 return name.endswith('_r') and name.startswith(('hand','index','middle','ring','pinky','thumb'))
kit_worlds={o.name:o.matrix_world.copy() for o in s.objects if o.type=='MESH'}
for o in s.objects:
 if o.type!='MESH' or not o.vertex_groups:continue
 inv=o.matrix_world.inverted()
 for v in o.data.vertices:
  weight=min(1,sum(g.weight for g in v.groups if right_hand_bone(o.vertex_groups[g.group].name)))
  if weight:
   point=o.matrix_world@v.co
   v.co=inv@point.lerp(right_hand_fit(point),weight)
 o.data.update()
bpy.context.view_layer.objects.active=rig
bpy.ops.object.mode_set(mode='EDIT')
for b in rig.data.edit_bones:
 if right_hand_bone(b.name):
  b.head=rig.matrix_world.inverted()@right_hand_fit(rig.matrix_world@b.head)
  b.tail=rig.matrix_world.inverted()@right_hand_fit(rig.matrix_world@b.tail)
rig.data.edit_bones['lowerarm_r'].tail=rig.data.edit_bones['hand_r'].head
bpy.ops.object.mode_set(mode='OBJECT');bpy.context.view_layer.update()
for name,matrix in kit_worlds.items():bpy.data.objects[name].matrix_world=matrix
# Round 3: fit both actual hands and their bind bones to the painted palm planes.
# Full depth is retained; the salute is compressed vertically, not pasted over the face.
def hand_fit(point,side):
 anchor=rig.matrix_world@rig.data.bones['hand_'+side].head_local
 d=point-anchor
 x,y,z=d.dot(right),d.dot(up),d.dot(view)
 if side=='l':return anchor+right*(x*.82)+up*(y*.32)+view*z
 return anchor-right*3*scale+up*scale+right*(1.15*x-.75*y)+up*(.8*y)+view*z
kit_worlds={o.name:o.matrix_world.copy() for o in s.objects if o.type=='MESH'}
for o in s.objects:
 if o.type!='MESH':continue
 inv=o.matrix_world.inverted()
 for v in o.data.vertices:
  point=o.matrix_world@v.co
  if o.vertex_groups:
   for side in ('l','r'):
    weight=min(1,sum(g.weight for g in v.groups if o.vertex_groups[g.group].name.endswith('_'+side) and o.vertex_groups[g.group].name.startswith(('hand','index','middle','ring','pinky','thumb'))))
    if weight:point=point.lerp(hand_fit(point,side),weight)
  if o.name.startswith(('GEO-sculpted-scalp','GEO-sculpted-hair')):
   px=world_to_camera_view(s,cam,point).x*256
   point+=right*(-6-.10*(px-142))*scale
  if o.name in ('GEO-wolf-pelt-cowl','GEO-layered-fur-tufts','GEO-folded-pelt-cape','GEO-layered-fur-tufts.001'):
   p=world_to_camera_view(s,cam,point);px=p.x*256;py=(1-p.y)*256
   point-=right*(max(0,px-173)*.70*max(0,min(1,(py-50)/18)))*scale
   # A cowl wraps the shoulders; it cannot fill the opening under the salute.
   shoulder_line=44+.45*(px-158)
   point-=up*(max(0,shoulder_line-py)*max(0,min(1,(px-150)/8)))*scale
  v.co=inv@point
 o.data.update()
bpy.context.view_layer.objects.active=rig
bpy.ops.object.mode_set(mode='EDIT')
# Anchors remain unchanged throughout this pass; changing the wrist first must
# not move the coordinate origin for the subsequent finger transforms.
for b in rig.data.edit_bones:
 for side in ('l','r'):
  if b.name.endswith('_'+side) and b.name.startswith(('hand','index','middle','ring','pinky','thumb')):
   b.head=rig.matrix_world.inverted()@hand_fit(rig.matrix_world@b.head,side)
   b.tail=rig.matrix_world.inverted()@hand_fit(rig.matrix_world@b.tail,side)
for side in ('l','r'):rig.data.edit_bones['lowerarm_'+side].tail=rig.data.edit_bones['hand_'+side].head
bpy.ops.object.mode_set(mode='OBJECT');bpy.context.view_layer.update()
for name,matrix in kit_worlds.items():bpy.data.objects[name].matrix_world=matrix
# The raw MPFB head filled the lookout opening with skin. Narrow the true
# skull/face in camera space while retaining its depth and anatomical topology.
def head_fit(point):
 p=world_to_camera_view(s,cam,point)
 return point-right*((p.x*256-140)*.40)*scale
bpy.context.view_layer.update()
worlds={o.name:o.matrix_world.copy() for o in s.objects if o.type=='MESH'}
for o in s.objects:
 if o.type!='MESH':continue
 inv=o.matrix_world.inverted()
 for v in o.data.vertices:
  weight=1 if o.name.startswith('GEO-beard') or 'system eyes' in o.name else 0
  if o.name=='GEO-anatomy':weight=min(1,sum(g.weight*(1 if o.vertex_groups[g.group].name=='head' else .25) for g in v.groups if o.vertex_groups[g.group].name in ('head','neck_01')))
  if weight:
   point=o.matrix_world@v.co;v.co=inv@point.lerp(head_fit(point),weight)
 o.data.update()
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
head=rig.data.edit_bones['head'];head.head=rig.matrix_world.inverted()@head_fit(rig.matrix_world@head.head);head.tail=rig.matrix_world.inverted()@head_fit(rig.matrix_world@head.tail)
rig.data.edit_bones['neck_01'].tail=head.head
bpy.ops.object.mode_set(mode='OBJECT');bpy.context.view_layer.update()
for name,matrix in worlds.items():bpy.data.objects[name].matrix_world=matrix
s['round3_registered']=True
s['round2_registered']=True
(M/'registration.json').write_text(json.dumps({'method':'full-depth bind mesh and skeleton fit before UV projection','round3':'palm/finger and skull camera-space fits; cowl outline; base transform preserved through dependency update','controls':controls,'depth_offsets':foot_depth,'limb_length_ratios':ratios,'max_landmark_residual_px':float(np.max(np.linalg.norm(K@weights-delta,axis=1)))},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(M/'registered.blend'))
print('SCOUT_REGISTERED')
