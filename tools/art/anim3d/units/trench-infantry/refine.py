"""Full-depth contour fitting and clean stone pigment; no flat relief geometry.

Topology/skin-space conversion adapted from the project's rifleman refinement.
"""
import bpy,bmesh,math,json
from mathutils import Matrix,Vector
from bpy_extras.object_utils import world_to_camera_view


def finish(rig,body):
 sc=bpy.context.scene;cam=sc.camera
 if body.data.shape_keys:
  key=body.shape_key_add(name='Frozen anatomy',from_mix=True);coords=[v.co.copy() for v in key.data];body.shape_key_clear()
  for v,c in zip(body.data.vertices,coords):v.co=c
 # Freeze visible subdivision/thickness before projection. Keep armature editable.
 for o in list(sc.objects):
  if o.type!='MESH':continue
  bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
  for m in list(o.modifiers):
   if m.type=='ARMATURE':continue
   if m.type=='SUBSURF' and m.levels==0:o.modifiers.remove(m);continue
   while list(o.modifiers).index(m)>0:bpy.ops.object.modifier_move_up(modifier=m.name)
   bpy.ops.object.modifier_apply(modifier=m.name)
  bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
 bpy.context.view_layer.update()
 right=cam.matrix_world.to_quaternion() @ Vector((1,0,0));up=cam.matrix_world.to_quaternion() @ Vector((0,1,0));unit=cam.data.ortho_scale/256
 def deform(o,transform,predicate=None):
  ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();assert len(me.vertices)==len(o.data.vertices),o.name
  for v in o.data.vertices:
   groups={o.vertex_groups[g.group].name:g.weight for g in v.groups if o.vertex_groups[g.group].name in rig.pose.bones}
   if predicate and not predicate(groups):continue
   w=ev.matrix_world @ me.vertices[v.index].co;p=world_to_camera_view(sc,cam,w);x,y=p.x*256,(1-p.y)*256
   tx,ty=transform(x,y);delta=(right*(tx-x)-up*(ty-y))*unit
   skin=o.matrix_world.copy()
   if any(m.type=='ARMATURE' for m in o.modifiers) and groups:
    matrix=Matrix(((0.,)*4,)*4);total=sum(groups.values())
    for n,weight in groups.items():matrix+=(rig.pose.bones[n].matrix @ rig.data.bones[n].matrix_local.inverted())*(weight/total)
    skin=rig.matrix_world @ matrix @ rig.matrix_world.inverted() @ o.matrix_world
   v.co+=skin.to_3x3().inverted() @ delta
  ev.to_mesh_clear();o.data.update()
 def affine(src,dst):return lambda x,y:(dst[0]+(x-src[0])*(dst[2]-dst[0])/(src[2]-src[0]),dst[1]+(y-src[1])*(dst[3]-dst[1])/(src[3]-src[1]))
 def sleeve_r(x,y):return (96+(x-96)*.72+3,y+1.0)
 def sleeve_l(x,y):return (143+(x-143)*.88,y)
 for o in list(sc.objects):
  if o.type!='MESH':continue
  name=o.name
  if 'greatcoat folded wool' in name:
   # Hem drapes asymmetrically; shoulder narrows into neck instead of a box.
   def coat(x,y):
    t=max(0,min(1,(y-110)/60));width=.89+.04*t
    shoulder=max(0,min(1,(115-x)/12))*max(0,1-abs(y-55)/25)*5
    return (130+(x-128)*width+shoulder,y+max(0,1-(y-40)/25)*7+t*(2.0+1.1*math.sin((x-100)*.11)))
   deform(o,coat)
  elif 'sleeve' in name or 'cuff' in name:deform(o,sleeve_r if name.endswith('r') else sleeve_l)
  elif 'blanket' in name:deform(o,affine((112.3,21.2,164.8,47.9),(135,41,170,57)))
  elif 'canvas backpack' in name:deform(o,affine((111.1,37.8,158.6,95),(139,53,175,107)))
  elif 'haversack' in name:deform(o,affine((146.8,96.1,167.6,125.4),(150,97,165,132)))
  elif 'helmet' in name:deform(o,lambda x,y:(x-.6,12.5+(y-9.5)*1.08+(128-x)*.32))
  elif any(k in name for k in ('boot','lace')):
   deform(o,lambda x,y:(99+(x-98.7)*20/17,y) if ' r' in name else (140+(x-142.1)*23.5/17.1,y))
 # Anatomical underlayers retain sensible materials if exposed by moving sleeves.
 for material in ['MAT-weathered horizon blue wool','MAT-ochre puttee cloth','MAT-scuffed tan leather']:
  body.data.materials.append(bpy.data.materials[material])
 for face in body.data.polygons:
  counts={}
  for i in face.vertices:
   for g in body.data.vertices[i].groups:
    n=body.vertex_groups[g.group].name
    if n in rig.pose.bones:counts[n]=counts.get(n,0)+g.weight
  if counts:
   n=max(counts,key=counts.get)
   if n.startswith(('spine','pelvis','clavicle','upperarm','lowerarm','thigh')):face.material_index=1
   elif n.startswith('calf'):face.material_index=2
   elif n.startswith(('foot','ball')):face.material_index=3
 # Fit the covered right arm as well; otherwise the old anatomy protrudes.
 deform(body,sleeve_r,lambda groups:sum(w for n,w in groups.items() if n in ('upperarm_r','lowerarm_r'))>.8)
 for side in ('r','l'):
  deform(body,lambda x,y:(99+(x-98.7)*20/17,y) if side=='r' else (140+(x-142.1)*23.5/17.1,y),lambda groups:sum(w for n,w in groups.items() if n in ('foot_'+side,'ball_'+side))>.65)
 bpy.data.objects['LGT-rim'].data.energy=65
 bpy.data.objects['LGT-rim'].data.color=(.88,.93,1)
 bpy.context.view_layer.update()


def stone(sc,image):
 o=bpy.data.objects['GEO-stationary cream base'];cam=sc.camera
 uv=o.data.uv_layers.new(name='Clean stone painting')
 for loop in o.data.loops:
  co=world_to_camera_view(sc,cam,o.matrix_world @ o.data.vertices[loop.vertex_index].co);uv.data[loop.index].uv=(co.x,co.y)
 for slot in o.material_slots:
  n=slot.material.node_tree.nodes;l=slot.material.node_tree.links;p=n.get('Principled BSDF');out=n.get('Material Output')
  tc=n.new('ShaderNodeUVMap');tc.uv_map=uv.name;t=n.new('ShaderNodeTexImage');t.image=image;t.extension='EXTEND';l.new(tc.outputs[0],t.inputs[0])
  ao=n.new('ShaderNodeAmbientOcclusion');ao.inputs['Distance'].default_value=.08
  color=n.new('ShaderNodeMixRGB');l.new(t.outputs['Alpha'],color.inputs[0]);color.inputs[1].default_value=(.815,.624,.352,1);l.new(t.outputs['Color'],color.inputs[2])
  shade=n.new('ShaderNodeMixRGB');shade.blend_type='MULTIPLY';shade.inputs[0].default_value=.45;l.new(color.outputs[0],shade.inputs[1]);l.new(ao.outputs['Color'],shade.inputs[2])
  pigment=n.new('ShaderNodeEmission');l.new(shade.outputs[0],pigment.inputs[0]);l.new(color.outputs[0],p.inputs['Base Color'])
  ray=n.new('ShaderNodeLightPath');mix=n.new('ShaderNodeMixShader');l.new(ray.outputs['Is Camera Ray'],mix.inputs[0]);l.new(p.outputs[0],mix.inputs[1]);l.new(pigment.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],out.inputs['Surface'])
