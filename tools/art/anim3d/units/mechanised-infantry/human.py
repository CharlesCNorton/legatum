import bpy, bmesh, math, os, json
from pathlib import Path
from mathutils import Vector, Matrix
from math import sin, cos, pi
R=Path(os.environ["ANIM_ROOT"]); A=R/"assets/mechanised-infantry"
def mat(name,color,metal=0,rough=.65,fill=None):
 m=bpy.data.materials.new('MAT-'+name);m.use_nodes=True;m.diffuse_color=(*color,1)
 n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF')
 p.inputs['Base Color'].default_value=(*color,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
 tc=n.new('ShaderNodeTexCoord');noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=150;noise.inputs['Detail'].default_value=3
 l.new(tc.outputs['Generated'],noise.inputs['Vector']);b=n.new('ShaderNodeBump');b.inputs['Strength'].default_value=.13;b.inputs['Distance'].default_value=.0014;l.new(noise.outputs['Fac'],b.inputs['Height']);l.new(b.outputs[0],p.inputs['Normal'])
 ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(rough*.7,)*3+(1,);ramp.color_ramp.elements[1].color=(min(1,rough*1.2),)*3+(1,);l.new(noise.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs[0],p.inputs['Roughness'])
 if fill and (A/(fill+'-fill.png')).exists():
  t=n.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(A/(fill+'-fill.png')),check_existing=True);t.projection='BOX';t.projection_blend=.3;l.new(tc.outputs['Generated'],t.inputs[0]);l.new(t.outputs['Color'],p.inputs['Base Color'])
 if fill in ('red','linen'):p.inputs['Sheen Weight'].default_value=.25
 return m

def mesh(name,vs,fs,ma):
 d=bpy.data.meshes.new(name);d.from_pydata(vs,[],fs);d.update();o=bpy.data.objects.new('GEO-'+name,d);bpy.context.collection.objects.link(o)
 if ma:d.materials.append(ma)
 for p in d.polygons:p.use_smooth=True
 return o

def bevel(o,w=.004):
 m=o.modifiers.new('Rounded worked edges','BEVEL');m.width=w;m.segments=3;return o

def solid(o,t=.005):
 m=o.modifiers.new('Real thickness','SOLIDIFY');m.thickness=t;return o

def curve(name,pts,r,ma):
 d=bpy.data.curves.new(name,'CURVE');d.dimensions='3D';s=d.splines.new('POLY');s.points.add(len(pts)-1)
 for p,v in zip(s.points,pts):p.co=(*v,1)
 d.bevel_depth=r;d.bevel_resolution=2;o=bpy.data.objects.new('GEO-'+name,d);bpy.context.collection.objects.link(o);d.materials.append(ma);return o

def sphere(name,loc,scale,ma):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=12,location=loc);o=bpy.context.object;o.name='GEO-'+name;o.scale=scale;o.data.materials.append(ma)
 for p in o.data.polygons:p.use_smooth=True
 return o

def parent(o,pa):
 bpy.context.view_layer.update();w=o.matrix_world.copy();o.parent=pa;o.matrix_world=w;return o

def attach(o,bone):
 bpy.context.view_layer.update();w=o.matrix_world.copy();o.parent=rig;o.parent_type='BONE';o.parent_bone=bone;bpy.context.view_layer.update();o.matrix_world=w;return o

def aim(name,direction):
 p=rig.pose.bones[name];q=p.bone.matrix_local.to_quaternion();v=q @ Vector((0,1,0));rot=(v.rotation_difference(Vector(direction).normalized()) @ q).to_matrix().to_4x4();rot.translation=p.head;p.matrix=rot;bpy.context.view_layer.update()

def limb(upper,lower,target,pole):
 a=rig.pose.bones[upper].head.copy();t=Vector(target);axis=t-a;l1=rig.data.bones[upper].length;l2=rig.data.bones[lower].length;d=min(axis.length,l1+l2-.0001);axis.normalize();along=(l1*l1-l2*l2+d*d)/(2*d);h=max(0,l1*l1-along*along)**.5;side=Vector(pole)-a;side=(side-axis*side.dot(axis)).normalized();elbow=a+axis*along+side*h;aim(upper,elbow-a);aim(lower,t-elbow)

def tube(name,a,b,radii,ma,bone=None,striped=False):
 a=Vector(a);b=Vector(b);axis=(b-a).normalized();u=axis.cross(Vector((0,1,0))).normalized();v=axis.cross(u).normalized();vs=[];fs=[];nr=16;ns=48
 for j in range(nr+1):
  t=j/nr;rad=radii[0]*(1-t)+radii[1]*t+radii[2]*sin(pi*t)**.8
  for k in range(ns):
   ang=2*pi*k/ns;fold=1+.08*cos(ang*8+sin(t*pi)*.25)*sin(t*pi)
   vs.append(tuple(a+(b-a)*t+(u*cos(ang)+v*sin(ang))*rad*fold))
 for j in range(nr):
  for k in range(ns):i=j*ns+k;z=j*ns+(k+1)%ns;fs.append((i,z,z+ns,i+ns))
 o=solid(mesh(name,vs,fs,ma),.005)
 if striped:
  o.data.materials.append(linen)
  for p in o.data.polygons:p.material_index=1 if (p.index%ns)//3%2==1 else 0
 if bone:attach(o,bone)
 return o

def empty(name,loc):
 o=bpy.data.objects.new(name,None);bpy.context.collection.objects.link(o);o.location=loc;return o

def box(name,loc,dimensions,ma,width):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name='GEO-'+name;o.scale=dimensions;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(ma);bevel(o,width);return o

def bind_weights(o,weights):
 # Inverse posed skin transform retains the tailored surface at bind time.
 bpy.context.view_layer.update();o.parent=rig;o.matrix_parent_inverse=rig.matrix_world.inverted()
 for v in o.data.vertices:
  ww={n:w for n,w in weights(v.co).items() if w>0};total=sum(ww.values())
  if not total:ww={'pelvis':1};total=1
  deform=Matrix(((0,0,0,0),)*4)
  for n,w in ww.items():
   w/=total;g=o.vertex_groups.get(n) or o.vertex_groups.new(name=n);g.add([v.index],w,'REPLACE')
   dm=rig.matrix_world @ rig.pose.bones[n].matrix @ rig.data.bones[n].matrix_local.inverted() @ rig.matrix_world.inverted()
   deform+=dm*w
  v.co=deform.inverted() @ v.co
 mod=o.modifiers.new('Weighted articulated wool','ARMATURE');mod.object=rig
 bpy.context.view_layer.objects.active=o
 bpy.ops.object.modifier_move_up(modifier=mod.name)

def sleeve(side,cloth):
 a=rig.pose.bones['upperarm_'+side].head.copy();b=rig.pose.bones['lowerarm_'+side].head.copy();c=rig.pose.bones['hand_'+side].head.copy()
 vs=[];fs=[];weights={};count=32;around=32
 for j in range(count+1):
  t=j/count;center=a.lerp(b,t*2) if t<.5 else b.lerp(c,(t-.5)*2)
  axis=(b-a).normalized().lerp((c-b).normalized(),max(0,min(1,(t-.35)/.3))).normalized()
  u=axis.cross(Vector((0,1,0))).normalized();v=axis.cross(u).normalized()
  radius=.077*(1-t)+.052*t+.014*sin(pi*t)
  lower=max(0,min(1,(t-.37)/.26));lower=lower*lower*(3-2*lower)
  for k in range(around):
   angle=k*2*pi/around;fold=1+.075*sin(t*10*pi+2*cos(angle))*sin(pi*t)
   vs.append(center+(u*cos(angle)+v*sin(angle))*radius*fold);weights[len(vs)-1]=lower
 for j in range(count):
  for k in range(around):i=j*around+k;z=j*around+(k+1)%around;fs.append((i,z,z+around,i+around))
 o=solid(mesh('continuous folded sleeve '+side,vs,fs,cloth),.005)
 # bind_weights receives coordinates, so use the closest sampled ring weight.
 def ww(p):
  i=min(range(len(vs)),key=lambda i:(Vector(vs[i])-p).length_squared);w=weights[i]
  return {'upperarm_'+side:1-w,'lowerarm_'+side:w}
 bind_weights(o,ww)

def build(point,view):
 global rig,linen
 before=set(bpy.data.objects)
 bpy.ops.preferences.addon_enable(module='bl_ext.user_default.mpfb')
 from bl_ext.user_default.mpfb.services.humanservice import HumanService
 from bl_ext.user_default.mpfb.services.targetservice import TargetService
 macro=TargetService.get_default_macro_info_dict();macro.update(gender=1.,age=.4,muscle=.6,weight=.5,height=.5,proportions=.6);macro['race']={'caucasian':1.,'african':0.,'asian':0.}
 body=HumanService.create_human(macro_detail_dict=macro);body.name='GEO-MPFB soldier anatomy'
 bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();height=max(v.co.z for v in me.vertices)-min(v.co.z for v in me.vertices);ev.to_mesh_clear();body.scale=(1.72/height,)*3
 bpy.context.view_layer.objects.active=body;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 rig=HumanService.add_builtin_rig(body,'game_engine');rig.name='RIG-Soldier MPFB'
 skin=mat('Painted warm skin',(.48,.29,.15));cloth=mat('Olive folded combat cloth',(.21,.23,.12),fill='wool');linen=mat('Tan combat webbing',(.37,.30,.17),fill='linen');rubber=mat('Black leather boots',(.06,.052,.035),fill='leather');metal=mat('Rifle gunmetal',(.12,.13,.11),1,.53)
 body.data.materials.clear();body.data.materials.append(skin)
 body.data.materials.append(cloth)
 exposed={g.index for g in body.vertex_groups if g.name.startswith(('head','neck','hand','thumb','index','middle','ring','pinky'))}
 for face in body.data.polygons:
  amount=sum(sum(g.weight for g in body.data.vertices[i].groups if g.group in exposed) for i in face.vertices)/len(face.vertices)
  face.material_index=0 if amount>.55 else 1
 for face in body.data.polygons:face.use_smooth=True
 # Uniform surfaces have actual volume and sleeve/trouser folds.
 limb('thigh_r','calf_r',(-.36,.22,.23),(-.2,-.4,.6));limb('thigh_l','calf_l',(.14,-.12,.085),(.22,-.4,.5))
 limb('upperarm_r','lowerarm_r',(.10,-.30,1.18),(-.37,-.20,1.30));limb('upperarm_l','lowerarm_l',(.40,-.34,1.06),(.36,-.19,1.2))
 # Calibrate the guard's ankle orientation before creating footwear or sampling
 # any donor action. Bent knees must not carry calf pitch into planted soles.
 for side in ['l','r']:
  foot=rig.pose.bones['foot_'+side];reference=foot.bone.matrix_local.copy();reference.translation=foot.head.copy();foot.matrix=reference
  bpy.context.view_layer.update()
 for side in ['l','r']:
  for digit in ['index','middle','ring','pinky']:
   for j in range(1,4):p=rig.pose.bones[f'{digit}_{j:02d}_{side}'];p.rotation_mode='XYZ';p.rotation_euler.x=.85
  sleeve(side,cloth)
  for bone,r in [('thigh',(.102,.08,.018)),('calf',(.08,.05,.014))]:
   p=rig.pose.bones[bone+'_'+side];tube('combat '+bone+' '+side,p.head,p.tail,r,cloth,bone+'_'+side)
  # Footwear is built in anatomical rest, then transported by the foot's full
  # rest-to-pose matrix. A level shoe built in a bent-leg guard carries a false
  # pitch offset into the captured walk. No foot rotations are patched.
  foot='foot_'+side;fp=rig.data.bones[foot].head_local
  deform=rig.pose.bones[foot].matrix @ rig.data.bones[foot].matrix_local.inverted()
  shoes=[sphere('combat boot '+side,(fp.x,fp.y-.05,fp.z+.03),(.071,.135,.075),rubber),box('boot sole '+side,(fp.x,fp.y-.055,fp.z-.037),(.14,.25,.033),rubber,.016)]
  for shoe in shoes:
   bpy.context.view_layer.update();shoe.matrix_world=deform @ shoe.matrix_world;attach(shoe,foot)
 torso=attach(box('body armour carrier',(0,-.015,1.29),(.43,.33,.43),cloth,.07),'spine_03')
 for s in [-1,1]:
  attach(box('armour shoulder strap',(s*.16,-.14,1.48),(.055,.035,.18),linen,.012),'spine_03')
  attach(box('strap buckle',(s*.16,-.165,1.43),(.063,.019,.040),metal,.005),'spine_03')
  for j in range(2):attach(box('magazine pouch',(s*(.06+j*.09),-.198,1.23),(.075,.065,.17),linen,.012),'spine_03')
  attach(box('cargo trouser pocket',(s*.23,.005,.78),(.09,.16,.17),cloth,.018),'thigh_l' if s==1 else 'thigh_r')
 attach(box('combat belt',(0,-.01,1.06),(.40,.34,.052),linen,.012),'pelvis')
 attach(box('belt buckle',(0,-.19,1.07),(.057,.02,.043),metal,.006),'pelvis')
 attach(box('small field pack',(0,.19,1.3),(.31,.18,.36),cloth,.045),'spine_03')
 head=rig.pose.bones['head'];hc=(head.head+head.tail)*.5
 # Ballistic helmet shell follows the skull; no historical crest or wide brim.
 vs=[];fs=[]
 for j in range(13):
  t=j*pi/2/12
  for k in range(48):a=k*2*pi/48;vs.append((hc.x+.129*cos(t)*sin(a),hc.y-.147*cos(t)*cos(a),hc.z+.014+.135*sin(t)))
 for j in range(12):
  for k in range(48):i=j*48+k;n=j*48+(k+1)%48;fs.append((i,n,n+48,i+48))
 attach(bevel(solid(mesh('ballistic helmet',vs,fs,cloth),.009),.003),'head')
 attach(curve('helmet rolled edge',vs[:48]+vs[:1],.006,linen),'head')
 gun=empty('RIG-soldier rifle',(-.05,-.33,1.16));attach(gun,'hand_r')
 start=Vector((-.22,-.35,1.35));end=Vector((.62,-.38,.85));axis=(end-start).normalized()
 for name,a,b,r,ma in [('rifle receiver',start,start.lerp(end,.5),.023,metal),('rifle barrel',start.lerp(end,.5),end,.010,metal),('rifle stock',start-axis*.12,start,.033,rubber)]:parent(curve(name,[a,b],r,ma),gun)
 parent(box('rifle magazine',(.08,-.36,1.07),(.055,.032,.13),metal,.007),gun)
 # Project finished surfaces, not the eight pre-bevel corners of the carrier.
 # Apply geometry in bind space before skinning, preserving the MPFB weights.
 for ob in list(set(bpy.data.objects)-before):
  if ob.type not in {'MESH','CURVE'}:continue
  bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
  if ob.type=='CURVE':bpy.ops.object.convert(target='MESH')
  for modifier in list(ob.modifiers):
   if modifier.type in {'ARMATURE','MASK'}:continue
   bpy.ops.object.modifier_move_to_index(modifier=modifier.name,index=0)
   bpy.ops.object.modifier_apply(modifier=modifier.name)
  bm=bmesh.new();bm.from_mesh(ob.data)
  bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bmesh.ops.triangulate(bm,faces=list(bm.faces))
  edges=[e for e in bm.edges if e.calc_length()>.045]
  if edges:bmesh.ops.subdivide_edges(bm,edges=edges,cuts=3,use_grid_fill=True)
  bm.to_mesh(ob.data);bm.free()
 # Keep local rig coordinates while sampling reference-compensated open motions.
 from retarget import prepare,apply_matrices
 neutral={p.name:p.matrix.copy() for p in rig.pose.bones};motion={};sources={}
 for clip in ['idle','move','hit','death']:
  apply_matrices(rig,neutral)
  motion[clip],sources[clip]=prepare(rig,R,clip,[0.]*24+[i/48 for i in range(49)])
 apply_matrices(rig,neutral)
 objs=set(bpy.data.objects)-before
 for ob in objs:ob['soldier']=True
 # One rigid placement of the whole articulated miniature; captured local gait retained.
 group=empty('RIG-soldier placement',(0,0,0))
 for ob in objs:
  if ob.parent not in objs:parent(ob,group)
 group.scale=(.70,)*3;group.rotation_euler.z=.30
 loc=point(186,178,0);loc+=view*((.15-loc.z)/view.z);group.location=loc
 # Front-facing donor -Y follows the ramp toward the viewer. No foot rotation edits.
 bpy.context.view_layer.update()
 return dict(rig=rig,group=group,motion=motion,sources=sources,neutral=neutral,objects=list(objs),gun=gun)
