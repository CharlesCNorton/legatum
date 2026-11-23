"""Knight armour and horse caparison; all cloth has depth and curved cross-sections."""
import bpy,os,sys,ast,math,json
from pathlib import Path
from mathutils import Vector, Matrix
from math import sin,cos,pi
from bpy_extras.object_utils import world_to_camera_view
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/knight'
bpy.ops.wm.open_mainfile(filepath=str(M/'knight-base.blend'))
for node in ast.parse(Path('tools/art/anim3d/scene.py').read_text()).body:
 if isinstance(node,ast.FunctionDef) and node.name in {'material','mesh','bevel','solid','curve','sphere','attach','aim_bone','limb'}:exec(compile(ast.Module(body=[node],type_ignores=[]),'<shared geometry>','exec'))
sc=bpy.context.scene;rig=bpy.data.objects['Rider MPFB game_engine'];hrig=bpy.data.objects['AnimalArmature'];horse=bpy.data.objects['Horse']
for a in bpy.data.actions:a.use_fake_user=True
sc.camera.location=(6,-8,3.45);sc.camera.rotation_euler=(Vector((0,0,1.4))-sc.camera.location).to_track_quat('-Z','Y').to_euler();sc.camera.data.ortho_scale=3.5;sc.camera.data.shift_y=.025
bpy.context.view_layer.update()
# Match the raised near foreleg using the source action, retaining its foot axis.
hrig.animation_data.action=bpy.data.actions['AnimalArmature|Walk'];hrig.animation_data.action_slot=hrig.animation_data.action.slots[0];sc.frame_set(19)
raised={p.name:p.matrix_basis.copy() for p in hrig.pose.bones if p.name.endswith('.L') and p.name.split('.')[0] in ['FrontShoulder','FrontUpperLeg','FrontLowerLeg','IKFrontLeg','FF','PoleTarget']}
hrig.animation_data.action=bpy.data.actions['AnimalArmature|Idle'];hrig.animation_data.action_slot=hrig.animation_data.action.slots[0];sc.frame_set(0)
rest={p.name:p.matrix_basis.copy() for p in hrig.pose.bones};rest.update(raised);ob=hrig.matrix_basis.copy();hrig.animation_data_clear();hrig.matrix_basis=ob
for p in hrig.pose.bones:p.matrix_basis=rest[p.name]
hrig['raised_idle_foreleg']=json.dumps({n:[list(row) for row in v] for n,v in raised.items()})
bpy.context.view_layer.update()
cream=material('GEO cream linen',(.81,.70,.51),0,.84);blue=bpy.data.materials['Painted indigo cloth'];gold=bpy.data.materials['Bronze • polished edges'];steel=bpy.data.materials['Worn bright steel'];leather=bpy.data.materials['Oxide leather']
right=sc.camera.matrix_world.to_3x3()@Vector((1,0,0));up=sc.camera.matrix_world.to_3x3()@Vector((0,1,0));view=sc.camera.matrix_world.to_3x3()@Vector((0,0,1))
def horse_attach(o,bone):
 bpy.context.view_layer.update();world=o.matrix_world.copy();o.parent=hrig;o.parent_type='BONE';o.parent_bone=bone;bpy.context.view_layer.update();o.matrix_world=world;return o
def pixel_world(x,y,reference):
 q=world_to_camera_view(sc,sc.camera,reference)
 return reference+right*((x/256-q.x)*sc.camera.data.ortho_scale)+up*((1-y/256-q.y)*sc.camera.data.ortho_scale)
# Rest-view helmet/torso scale is set by rider position, not by texture stretching.
w=rig.matrix_world.copy();w.translation.z-=.16;rig.matrix_world=w
bpy.context.view_layer.update()
# Arm IK moves actual joints to the lance grip and shield support.
def target(bone,xy):return rig.matrix_world.inverted()@pixel_world(*xy,rig.matrix_world@rig.pose.bones[bone].head)
limb('upperarm_r','lowerarm_r',target('hand_r',(99,94)),target('lowerarm_r',(105,113)))
limb('upperarm_l','lowerarm_l',target('hand_l',(144,114)),target('lowerarm_l',(143,101)))
aim_bone('hand_r',rig.matrix_world.to_3x3().inverted()@up)
bpy.context.view_layer.update()
# Lance length/angle fits the painted upright, preserving a round tapered shaft.
shaft=bpy.data.objects['Spear ash shaft'];blade=bpy.data.objects['Iron spear blade']
for obj in (shaft,blade):
 inv=obj.matrix_world.inverted()
 if obj==shaft:
  for p,xy in zip(obj.data.splines[0].points,[(100,132),(94,27)]):p.co=(*(inv@pixel_world(*xy,obj.matrix_world@p.co.xyz)),1)
 else:
  ws=[obj.matrix_world@v.co for v in obj.data.vertices];qs=[world_to_camera_view(sc,sc.camera,w) for w in ws];low=min(q.y for q in qs);high=max(q.y for q in qs)
  for v,q,w in zip(obj.data.vertices,qs,ws):
   v.co=inv@pixel_world(94+(q.x-sum(t.x for t in qs)/len(qs))*256,27-(q.y-low)/(high-low)*15,w)
# Gold spiral follows the actual lance and is bone-parented with it.
a=shaft.matrix_world@shaft.data.splines[0].points[0].co.xyz;b=shaft.matrix_world@shaft.data.splines[0].points[-1].co.xyz
pts=[]
for i in range(220):
 t=i/219;pts.append(tuple(a.lerp(b,t)+right*(.014*cos(t*28*pi))+view*(.014*sin(t*28*pi))))
stripe=curve('GEO lance gold spiral',pts,.0045,gold);attach(stripe,'hand_r')
shaft.data.materials[0]=blue
# Shield: curved, thick heater outline with rolled edge, attached to left forearm.
outline=[(139,91),(147,89),(157,92),(162,98),(160,122),(154,146),(148,139),(141,119)]
center=rig.matrix_world@rig.pose.bones['lowerarm_l'].head+view*.12
vertices=[tuple(pixel_world(150,112,center)+view*.065)]
vertices += [tuple(pixel_world(x,y,center)) for x,y in outline]
shield=bevel(solid(mesh('GEO convex heater shield',vertices,[(0,i+1,(i+1)%len(outline)+1) for i in range(len(outline))],cream),.018),.004)
attach(shield,'lowerarm_l');attach(curve('GEO shield rolled gilt rim',[Vector(v) for v in vertices[1:]]+[Vector(vertices[1])],.008,gold),'lowerarm_l')
for i in range(len(outline)):
 for t in [.25,.65]:
  p=Vector(vertices[1+i]).lerp(Vector(vertices[1+(i+1)%len(outline)]),t)+view*.01
  attach(sphere('GEO shield brass rivet',tuple(p),(.004,)*3,gold),'lowerarm_l')
# Caparison flanks wrap the barrel and hang under gravity, with a scalloped hem.
for side in [-1,1]:
 for panel,(ya,yb) in enumerate([(-.67,-.19),(-.12,.83)]):
  vs=[];fs=[];nu=24;nv=18
  for j in range(nv+1):
   t=j/nv
   for i in range(nu+1):
    u=i/nu;y=ya+(yb-ya)*u
    x=side*(.26+.14*sin(t*pi/2)+.035*sin(u*6*pi)*t)
    z=1.51-1.10*t+.045*cos(u*6*pi)*t**3
    vs.append((x,y,z))
  for j in range(nv):
   for i in range(nu):
    a=j*(nu+1)+i;fs.append((a,a+1,a+nu+2,a+nu+1))
  ob=solid(mesh('GEO caparison flank',vs,fs,cream),.009);sub=ob.modifiers.new('Fabric softened folds','SUBSURF');sub.levels=sub.render_levels=1;horse_attach(ob,'Torso')
  horse_attach(curve('GEO caparison gold hem',vs[-(nu+1):],.009,gold),'Torso')
# Front chest apron follows neck base and curves round both shoulders.
vs=[];nu=32;nv=22
for j in range(nv+1):
 t=j/nv
 for i in range(nu+1):
  a=-1.5+3*i/nu;r=.35+.10*t+.02*sin(i*.8)*t
  vs.append((r*sin(a),-.48-r*cos(a),1.53-1.12*t+.04*cos(i*.65)*t**3))
fs=[(j*(nu+1)+i,j*(nu+1)+i+1,(j+1)*(nu+1)+i+1,(j+1)*(nu+1)+i) for j in range(nv) for i in range(nu)]
horse_attach(solid(mesh('GEO caparison chest',vs,fs,cream),.01),'Torso3');horse_attach(curve('GEO chest gold hem',vs[-(nu+1):],.008,gold),'Torso3')
# Blue mantle is a full-depth folded drape behind the rider.
vs=[];nu=20;nv=24
for j in range(nv+1):
 t=j/nv
 for i in range(nu+1):
  a=-1.6+i*3.2/nu;r=.20+.16*t
  vs.append((r*sin(a),.13+r*cos(a)+.02*sin(i*1.2)*t,2.14-1.30*t+.025*sin(i)*t))
fs=[(j*(nu+1)+i,j*(nu+1)+i+1,(j+1)*(nu+1)+i+1,(j+1)*(nu+1)+i) for j in range(nv) for i in range(nu)]
attach(solid(mesh('GEO folded blue mantle',vs,fs,blue),.008),'spine_03')
# Remove ancient blanket trim and sandal details; caparison covers saddle blanket.
for ob in list(sc.objects):
 if ob.name.startswith(('Blanket bronze stitch','Sandal straps','Rider sandal','Mane painted fibre')):bpy.data.objects.remove(ob,do_unlink=True)
# Replace the source's rigid dark tail with gravity-shaped pale locks.
import bmesh
bm=bmesh.new();bm.from_mesh(horse.data);layer=bm.verts.layers.deform.active
groups={g.index for g in horse.vertex_groups if g.name.startswith('Tail')}
if layer:bmesh.ops.delete(bm,geom=[v for v in bm.verts if sum(w for g,w in v[layer].items() if g in groups)>.55],context='VERTS')
bm.to_mesh(horse.data);bm.free()
for ob in list(sc.objects):
 if ob.name.startswith('Tail flowing fibre'):bpy.data.objects.remove(ob,do_unlink=True)
pale=material('GEO pale tail fibre',(.65,.59,.47),0,.75)
root=hrig.matrix_world@hrig.pose.bones['Tail1'].head
sc['tail_root_local']=json.dumps(list((hrig.matrix_world@hrig.pose.bones['Tail1'].matrix).inverted()@root))
for j in range(32):curve('Knight flowing tail lock',[(0,0,.5)]*13,.009,pale)
sys.path.insert(0,str(Path(__file__).parent))
from tail import update_tail
update_tail()
# The painting's smaller one-step stone disc.
base=bpy.data.objects['Stationary cream stone'];base.scale.x=base.scale.y=.71
rig['seated_pose']=json.dumps({p.name:[list(row) for row in p.matrix_basis] for p in rig.pose.bones})
sc['sample_frames']='[0]';bpy.ops.wm.save_as_mainfile(filepath=str(M/'knight-plain.blend'))
print('KNIGHT_KIT_READY')
