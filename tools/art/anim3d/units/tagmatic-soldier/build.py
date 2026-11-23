"""True MPFB infantry, fitted Byzantine kit and frozen-camera painting UVs.

No image planes: shield is a convex closed wooden volume; cloth has thickness;
helmet is a conical metal shell; anatomy and articulation are MPFB CC0.
"""
import bpy, bmesh, math, os, json, random
from pathlib import Path
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view
from math import sin,cos,pi
R=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')))
M=R/'masters/tagmatic-soldier';A=R/'assets/tagmatic-soldier';M.mkdir(parents=True,exist_ok=True)
random.seed(13)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
sc=bpy.context.scene
E=.28;SPAN=2.45;TARGET=Vector((0,0,1.08));D=Vector((0,-cos(E),sin(E)));V=Vector((0,sin(E),cos(E)))
def screen(x,y,depth=0):return TARGET+Vector(((x-128)*SPAN/256,0,0))+V*((128-y)*SPAN/256)+D*depth

def mat(name,color,metal=0,rough=.6,fill=None):
 m=bpy.data.materials.new('MAT-'+name);m.use_nodes=True;m.diffuse_color=(*color,1)
 n=m.node_tree.nodes;l=m.node_tree.links;s=n.get('Principled BSDF')
 s.inputs['Base Color'].default_value=(*color,1);s.inputs['Metallic'].default_value=metal;s.inputs['Roughness'].default_value=rough
 if fill:
  t=n.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(A/f'fill-{fill}.png'),check_existing=True);t.projection='BOX';t.projection_blend=.25
  tc=n.new('ShaderNodeTexCoord');l.new(tc.outputs['Generated'],t.inputs['Vector']);mix=n.new('ShaderNodeMixRGB');mix.inputs[0].default_value=.65;mix.inputs[1].default_value=(*color,1);l.new(t.outputs['Color'],mix.inputs[2]);l.new(mix.outputs[0],s.inputs['Base Color'])
 noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=190 if not metal else 95;noise.inputs['Detail'].default_value=3
 bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.18;bump.inputs['Distance'].default_value=.0015
 l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs['Normal'],s.inputs['Normal'])
 if fill=='cloth':s.inputs['Sheen Weight'].default_value=.22
 return m

def mesh(name,verts,faces,ma,smooth=True):
 d=bpy.data.meshes.new(name);d.from_pydata(verts,[],faces);d.update();o=bpy.data.objects.new('GEO-'+name,d);sc.collection.objects.link(o)
 if ma:d.materials.append(ma)
 for f in d.polygons:f.use_smooth=smooth
 # Recalculate closed/open surface consistency after construction.
 bm=bmesh.new();bm.from_mesh(d);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(d);bm.free()
 return o

def bevel(o,w=.003):
 m=o.modifiers.new('Soft forged edge','BEVEL');m.width=w;m.segments=3
 return o

def solid(o,t=.006):
 m=o.modifiers.new('Physical material thickness','SOLIDIFY');m.thickness=t
 return o

def curve(name,pts,r,ma):
 d=bpy.data.curves.new(name,'CURVE');d.dimensions='3D';d.bevel_depth=r;d.bevel_resolution=2
 sp=d.splines.new('POLY');sp.points.add(len(pts)-1)
 for p,q in zip(sp.points,pts):p.co=(*q,1)
 o=bpy.data.objects.new('GEO-'+name,d);sc.collection.objects.link(o);d.materials.append(ma);return o

def sphere(name,p,scale,ma):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,location=p);o=bpy.context.object;o.name='GEO-'+name;o.scale=scale;o.data.materials.append(ma)
 for f in o.data.polygons:f.use_smooth=True
 return o

def attach(o,bone):
 bpy.context.view_layer.update();w=o.matrix_world.copy();o.parent=rig;o.parent_type='BONE';o.parent_bone=bone;bpy.context.view_layer.update();o.matrix_world=w;o['attachment']=bone;return o

def aim(name,direction):
 p=rig.pose.bones[name];q=p.bone.matrix_local.to_quaternion();delta=(q@Vector((0,1,0))).rotation_difference(Vector(direction).normalized());m=(delta@q).to_matrix().to_4x4();m.translation=p.head;p.matrix=m;bpy.context.view_layer.update()

def limb(upper,lower,world,pole):
 inv=rig.matrix_world.inverted();target=inv@Vector(world);pole=inv@Vector(pole);a=rig.pose.bones[upper].head.copy();v=target-a
 d=min(v.length,rig.data.bones[upper].length+rig.data.bones[lower].length-.0001);v.normalize();l1=rig.data.bones[upper].length;l2=rig.data.bones[lower].length
 along=(l1*l1-l2*l2+d*d)/(2*d);side=pole-a;side=(side-v*side.dot(v)).normalized();elbow=a+v*along+side*max(0,l1*l1-along*along)**.5
 aim(upper,elbow-a);aim(lower,target-elbow)

bpy.ops.preferences.addon_enable(module='bl_ext.user_default.mpfb')
from bl_ext.user_default.mpfb.services.humanservice import HumanService
from bl_ext.user_default.mpfb.services.targetservice import TargetService
macro=TargetService.get_default_macro_info_dict();macro.update(gender=1.,age=.4,muscle=.72,weight=.48,height=.5,proportions=.6);macro['race']={'caucasian':.7,'african':.1,'asian':.2}
body=HumanService.create_human(macro_detail_dict=macro);body.name='GEO-MPFB anatomical soldier'
bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();height=max(v.co.z for v in me.vertices)-min(v.co.z for v in me.vertices);ev.to_mesh_clear()
body.scale=(1.89/height,)*3;bpy.context.view_layer.objects.active=body;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
rig=HumanService.add_builtin_rig(body,'game_engine');rig.name='RIG-Tagmatic MPFB';rig.location=(-.13,0,.13);bpy.context.view_layer.update()
system_data=R/'blender-user/extensions/.user/user_default/mpfb/data'
eyes=HumanService.add_mhclo_asset(str(system_data/'eyes/high-poly/high-poly.mhclo'),body,asset_type='Eyes',subdiv_levels=1,material_type='MAKESKIN');eyes.name='GEO-MPFB system eyes CC0'
skin=mat('warm painted skin',(.48,.27,.14),0,.65)
red=mat('crimson woven wool',(.32,.025,.014),0,.86,'cloth')
steel=mat('worn bright lamellar steel',(.58,.52,.39),1,.38,'steel')
gold=mat('polished brass borders',(.72,.43,.13),1,.48,'gold')
leather=mat('scuffed brown leather',(.13,.060,.026),0,.7,'leather')
wood=mat('ash spear shaft',(.18,.070,.022),0,.62,'leather')
mail=mat('dark iron mail',(.19,.18,.14),1,.6,'steel')
black=mat('blackened recess',(.028,.023,.018),0,.85)
# Exact sRGB E9CFA0 converted to linear, with a fine grain bump.
def linear(x):return x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4
stone=mat('cream limestone E9CFA0',tuple(linear(x/255) for x in (233,207,160)),0,.85)

body.data.materials.clear();body.data.materials.append(skin)
# Keep continuous anatomical under-clothing at bent sleeve/trouser joints.
# Real hands/head retain skin; the fitted outer garments still supply folds.
body.data.materials.append(red);body.data.materials.append(leather)
group_names={g.index:g.name for g in body.vertex_groups}
for face in body.data.polygons:
 weights={}
 for index in face.vertices:
  for g in body.data.vertices[index].groups:
   name=group_names[g.group];weights[name]=weights.get(name,0)+g.weight
 dominant=max(weights,key=weights.get) if weights else ''
 if dominant.startswith(('upperarm','lowerarm','thigh','calf','spine','pelvis','clavicle')):face.material_index=1
 elif dominant.startswith(('foot','ball')):face.material_index=2
# Rest stance landmarks: rear leg braced left, near foot under pointed shield.
limb('thigh_r','calf_r',(-.39,.17,.28),screen(88,169,.07));limb('thigh_l','calf_l',(.20,-.20,.29),screen(143,172,.15))
for s in ['l','r']:aim('foot_'+s,(0,-1,-.12));aim('ball_'+s,(0,-1,0))
limb('upperarm_r','lowerarm_r',screen(68,28,.12),screen(63,57,.08))
limb('upperarm_l','lowerarm_l',screen(142,112,.08),screen(151,91,-.03))
aim('hand_r',(.04,-.01,.13));aim('hand_l',(.08,-.06,.05))
rig.pose.bones['hand_r'].scale=(.80,.80,.80)
for name in ['thumb_01_r','thumb_02_r','thumb_03_r']:
 p=rig.pose.bones[name];p.rotation_mode='XYZ';p.rotation_euler.x=.7
# Close fingers around the overhand spear; anatomical finger chains, not spheres.
for p in rig.pose.bones:
 if p.name.endswith('_r') and any(p.name.startswith(n) for n in ['index','middle','ring','pinky']):
  p.rotation_mode='XYZ';p.rotation_euler.x=.85
bpy.context.view_layer.update()
# Fit the grip in depth as well as screen space before building the sleeves.
# The old hand was 14 cm behind the shaft: invisible at rest, obvious on a fall.
hand=rig.pose.bones['hand_r'];hand_matrix=hand.matrix.copy()
palm=rig.matrix_world@hand.head.lerp(hand.tail,.45)
shaft_a=screen(43,14,.27);shaft_b=screen(177,62,.27);axis=(shaft_b-shaft_a).normalized()
grip=shaft_a+axis*(palm-shaft_a).dot(axis)
wrist=rig.matrix_world@rig.pose.bones['lowerarm_r'].tail
pole=rig.matrix_world@rig.pose.bones['lowerarm_r'].head
limb('upperarm_r','lowerarm_r',wrist+D*(grip-palm).dot(D),pole)
hand_matrix.translation=rig.pose.bones['hand_r'].head;rig.pose.bones['hand_r'].matrix=hand_matrix
bpy.context.view_layer.update()
for f in body.data.polygons:f.use_smooth=True
sub=body.modifiers.new('Anatomy smoothness','SUBSURF');sub.levels=1;sub.render_levels=1
# Material shells extracted from the evaluated MPFB anatomy, then rigid fitted by limb.
def body_shell(name,predicate,ma,bone,inflate=.012):
 ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();vsworld=[ev.matrix_world@v.co for v in me.vertices]
 selected=[p for p in me.polygons if all(predicate(vsworld[i]) for i in p.vertices)];ids=sorted({i for p in selected for i in p.vertices});idx={v:j for j,v in enumerate(ids)}
 vs=[vsworld[i]+(ev.matrix_world.to_3x3()@me.vertices[i].normal).normalized()*inflate for i in ids]
 ob=mesh(name,vs,[[idx[i] for i in p.vertices] for p in selected],ma);ev.to_mesh_clear();solid(ob,.005);attach(ob,bone);return ob
# Closed sleeves follow the posed bone endpoints, with actual gathered cloth folds.
def sleeve(name,a,b,r1,r2,ma,bone,fold=.007):
 a=Vector(a);b=Vector(b);axis=(b-a).normalized();u=axis.cross(Vector((0,1,0))).normalized();v=axis.cross(u).normalized();verts=[];faces=[];N=32;L=14
 for j in range(L+1):
  t=j/L;r=r1*(1-t)+r2*t
  for i in range(N):
   th=i*2*pi/N;rr=r+fold*sin(th*6+t*17)*sin(pi*t)+fold*.5*sin(t*45)
   verts.append(a.lerp(b,t)+rr*(u*cos(th)+v*sin(th)))
 for j in range(L):
  for i in range(N):q=j*N+i;n=j*N+(i+1)%N;faces.append((q,n,n+N,q+N))
 ob=solid(mesh(name,verts,faces,ma),.007);bevel(ob,.002);attach(ob,bone);return ob
for s in ['r','l']:
 for bn in ['upperarm','lowerarm']:
  p=rig.pose.bones[bn+'_'+s];a=rig.matrix_world@p.head;b=rig.matrix_world@p.tail
  sleeve('red gathered sleeve '+bn+s,a,b,.097 if bn=='upperarm' else .077,.080 if bn=='upperarm' else .061,red,bn+'_'+s)
 # Gathered trousers remain cloth when the shield reveals the legs.
 for bn in ['thigh','calf']:
  p=rig.pose.bones[bn+'_'+s];a=rig.matrix_world@p.head;b=rig.matrix_world@p.tail
  if bn=='calf':b=a.lerp(b,.42)
  sleeve('gathered crimson trousers '+bn+s,a,b,.112 if bn=='thigh' else .083,.086 if bn=='thigh' else .071,red,bn+'_'+s,.009)
 # Boots fit actual ankle, toe and calf anatomy; skin never becomes a primitive body.
 for bn in ['calf','foot']:
  p=rig.pose.bones[bn+'_'+s];a=rig.matrix_world@p.head;b=rig.matrix_world@p.tail
  if bn=='calf':
   a=a.lerp(b,.35);sleeve('leather wrapped boot '+s,a,b,.080,.060,leather,bn+'_'+s,.003)
   for k in range(7):
    t=k/7;center=a.lerp(b,t);pts=[center+Vector((.072*cos(th),.068*sin(th),.013*sin(th))) for th in [i*2*pi/32 for i in range(33)]];attach(curve('boot winding '+s,pts,.006,leather),bn+'_'+s)
# Closed leather shoes are real equipment volumes around the anatomical feet.
for s,cx,cy in [('r',-.39,.07),('l',.20,-.29)]:
 verts=[];faces=[];N=32;L=10
 for j in range(L+1):
  t=j/L;z=.177+.125*t;fac=max(.05,sin(pi*(.12+.88*t))**.7)
  for i in range(N):
   a=i*2*pi/N;verts.append((cx+.077*fac*cos(a),cy+.155*fac*sin(a)+.045*t,z))
 for j in range(L):
  for i in range(N):a=j*N+i;b=j*N+(i+1)%N;faces.append((a,b,b+N,a+N))
 faces.append(tuple(reversed(range(N))));faces.append(tuple(L*N+i for i in range(N)))
 ob=bevel(mesh('closed leather shoe '+s,verts,faces,leather),.002);attach(ob,'foot_'+s)
 pts=[(cx+.078*cos(a),cy+.158*sin(a),.184) for a in [i*2*pi/64 for i in range(65)]]
 attach(curve('stitched boot sole '+s,pts,.0045,leather),'foot_'+s)
# Tunic and lamellar cuirass: full circumference, flared skirt with vertical folds.
def ring_shell(name,z0,z1,rx0,rx1,ry0,ry1,ma,bone,fold=0,cx=-.13):
 vs=[];fs=[];N=64;L=16
 for j in range(L+1):
  t=j/L;z=z0+(z1-z0)*t;rx=rx0*(1-t)+rx1*t;ry=ry0*(1-t)+ry1*t
  for i in range(N):
   th=i*2*pi/N;w=fold*(.7*sin(th*12+t*2)+.3*sin(th*19-t*4));vs.append((cx+(rx+w)*sin(th),-(ry+w)*cos(th),z+.012*sin(th*7)*(1-t)))
 for j in range(L):
  for i in range(N):a=j*N+i;b=j*N+(i+1)%N;fs.append((a,b,b+N,a+N))
 ob=solid(mesh(name,vs,fs,ma),.008);attach(ob,bone);return ob
skirt=ring_shell('folded red tunic skirt',.66,1.20,.31,.20,.22,.16,red,'pelvis',.018)
cuirass=ring_shell('closed lamellar backing',1.13,1.62,.205,.245,.16,.17,leather,'spine_03')
# Individual bevelled lamellae with overlapping rows and gilded binding.
vs=[];fs=[]
for row in range(7):
 z=1.14+row*.065
 for k in range(26):
  th=k*2*pi/26;rx=.216+.031*row/6;ry=.172
  start=len(vs)
  for dz,da in [(-.031,-.105),(-.031,.105),(.036,.105),(.036,-.105)]:
   vs.append((-.13+rx*sin(th+da),-ry*cos(th+da),z+dz))
  fs.append(tuple(start+i for i in range(4)))
plates=solid(mesh('overlapping steel lamellae',vs,fs,steel),.008);bevel(plates,.003);attach(plates,'spine_03')
for row in range(7):
 z=1.14+row*.065
 attach(curve('lamellar row binding',[( -.13+(.219+.031*row/6)*sin(a),-.175*cos(a),z-.028) for a in [i*2*pi/96 for i in range(97)]],.0045,gold),'spine_03')
# Armour skirt panels keep an articulated separation over the tunic.
for k in range(10):
 a=k*2*pi/10;vs=[]
 for j in range(5):
  t=j/4
  for s in [-1,0,1]:
   th=a+s*.25;vs.append((-.13+(.21+.085*t)*sin(th),-(.175+.04*t)*cos(th),1.15-.34*t))
 fs=[(j*3+i,j*3+i+1,(j+1)*3+i+1,(j+1)*3+i) for j in range(4) for i in range(2)]
 ob=solid(mesh('lamellar skirt panel',vs,fs,steel),.007);bevel(ob,.003);attach(ob,'pelvis')
for z,rx,ry in [(.69,.31,.23),(.72,.30,.225),(1.16,.215,.18)]:
 attach(curve('tunic gold embroidered hem',[( -.13+rx*sin(a),-ry*cos(a),z+.009*sin(a*12)) for a in [i*2*pi/160 for i in range(161)]],.008,gold),'pelvis')
# Leather belt is a thick ribbon with a real metal buckle and pin.
belt=ring_shell('waist belt',1.135,1.18,.219,.219,.183,.183,leather,'pelvis')
attach(curve('belt buckle',[(-.23,-.194,1.132),(-.16,-.194,1.132),(-.16,-.194,1.188),(-.23,-.194,1.188),(-.23,-.194,1.132)],.005,gold),'pelvis')
attach(curve('buckle tongue',[(-.198,-.199,1.16),(-.16,-.199,1.16)],.003,gold),'pelvis')
# Shoulder armour follows the raised arm rather than pinning it to the chest.
for s in ['r','l']:
 p=rig.pose.bones['upperarm_'+s];a=rig.matrix_world@p.head;b=rig.matrix_world@p.tail
 sleeve('lamellar shoulder '+s,a,a.lerp(b,.36),.111,.101,steel,'upperarm_'+s,.003)
 p=rig.pose.bones['lowerarm_'+s];a=rig.matrix_world@p.head;b=rig.matrix_world@p.tail
 sleeve('embroidered cuff '+s,a.lerp(b,.76),b,.081,.074,gold,'lowerarm_'+s,0)
# Head and helmet centered on MPFB face. Helmet dimensions calibrated below.
bpy.context.view_layer.update();hp=rig.pose.bones['head'];hc=rig.matrix_world@((hp.head+hp.tail)*.5)
# Camera-facing cone and mail follow exact source landmark coordinates.
helmet_center=screen(118,40,-.015);helmet_center.y=hc.y;helmet_center.z=1.91
vs=[];fs=[];N=64;L=20
for j in range(L+1):
 t=j/L;radius=.123*(1-t)**.73+.002
 for i in range(N):
  a=i*2*pi/N;vs.append(helmet_center+Vector((radius*sin(a),-radius*1.08*cos(a),.245*t)))
for j in range(L):
 for i in range(N):a=j*N+i;b=j*N+(i+1)%N;fs.append((a,b,b+N,a+N))
helm=solid(mesh('conical spangenhelm steel',vs,fs,steel),.005);bevel(helm,.002);attach(helm,'head')
for j in [0,1]:attach(curve('helmet brass brow',[(helmet_center.x+.127*sin(a),helmet_center.y-.137*cos(a),helmet_center.z+.013*j) for a in [i*2*pi/96 for i in range(97)]],.007,gold),'head')
for a in [0,pi/2,pi,3*pi/2]:
 pts=[helmet_center+Vector(((.125*(1-t)**.73+.003)*sin(a),-(.137*(1-t)**.73+.003)*cos(a),.245*t)) for t in [i/24 for i in range(25)]];attach(curve('helmet raised brass rib',pts,.008,gold),'head')
 for t in [.1,.3,.5,.7,.85]:attach(sphere('helmet rib rivet',helmet_center+Vector(((.128*(1-t)**.73+.003)*sin(a),-(.140*(1-t)**.73+.003)*cos(a),.245*t)),(.004,.004,.004),gold),'head')
attach(sphere('helmet finial',helmet_center+Vector((0,0,.256)),(.012,.012,.015),gold),'head')
# Mail coif surrounds neck and jaw; face opening remains actual negative space.
vs=[];fs=[];N=64;L=16
for j in range(L+1):
 t=j/L;z=1.63+.29*t;rx=.20*(1-t)+.122*t;ry=.17*(1-t)+.115*t
 for i in range(N):
  a=i*2*pi/N;vs.append((helmet_center.x+rx*sin(a),helmet_center.y-ry*cos(a),z))
for j in range(L):
 for i in range(N):
  a=i*2*pi/N
  if j>9 and abs(math.atan2(sin(a),cos(a)))<.65:continue
  q=j*N+i;n=j*N+(i+1)%N;fs.append((q,n,n+N,q+N))
coif=solid(mesh('mail coif open face',vs,fs,mail),.005);attach(coif,'head')
# A joined mesh of interlocked little rings adds actual mail relief.
rv=[];rf=[]
for j in range(14):
 t=(j+.5)/14;z=1.64+.27*t;rx=.20*(1-t)+.123*t;ry=.17*(1-t)+.116*t
 for k in range(46):
  a=(k+.5*(j%2))*2*pi/46
  if j>8 and abs(math.atan2(sin(a),cos(a)))<.70:continue
  center=Vector((helmet_center.x+(rx+.003)*sin(a),helmet_center.y-(ry+.003)*cos(a),z));u=Vector((cos(a),sin(a),0));v=Vector((0,0,1));normal=u.cross(v);start=len(rv)
  for q in range(10):
   th=q*2*pi/10;radial=u*cos(th)+v*sin(th)
   for q2 in range(4):
    ph=q2*2*pi/4;rv.append(center+radial*(.008+.0016*cos(ph))+normal*.0016*sin(ph))
  for q in range(10):
   for q2 in range(4):rf.append((start+q*4+q2,start+((q+1)%10)*4+q2,start+((q+1)%10)*4+(q2+1)%4,start+q*4+(q2+1)%4))
attach(mesh('interlocked coif rings',rv,rf,steel),'head')
# Convex kite shield: exact projected outline, curved front and closed wooden back.
# Catmull-Rom contour interpolates authored landmarks, not an image alpha cutout.
outline=[(136,53),(148,55),(159,68),(165,89),(168,117),(167,145),(163,172),(157,197),(148,219),(139,206),(127,180),(117,151),(109,121),(107,95),(111,75),(121,60)]
def contour(points,steps=6):
 out=[];n=len(points)
 for i in range(n):
  p0=Vector(points[(i-1)%n]);p1=Vector(points[i]);p2=Vector(points[(i+1)%n]);p3=Vector(points[(i+2)%n])
  for j in range(steps):
   t=j/steps;out.append(.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t))
 return out
edge=contour(outline);center=Vector((140,125));vs=[screen(*center,.45)];fs=[];N=len(edge);L=12
for j in range(1,L+1):
 r=j/L
 for xy in edge:
  p=center.lerp(xy,r);vs.append(screen(*p,.35+.10*(1-r*r)))
for i in range(N):fs.append((0,1+i,1+(i+1)%N))
for j in range(L-1):
 for i in range(N):q=1+j*N+i;n=1+j*N+(i+1)%N;fs.append((q,n,n+N,q+N))
shield=solid(mesh('convex wooden kite shield',vs,fs,red),.035);bevel(shield,.003);attach(shield,'lowerarm_l')
shield.data.materials.append(leather)
shield.modifiers['Physical material thickness'].material_offset=1
shield.modifiers['Physical material thickness'].material_offset_rim=1
shield['projection_weight']=.95
# Real enarmes: broad, bevelled leather ribbons on the concave back. Their
# attachment and release are part of the shield assembly, including buckles.
for k,y in enumerate((100,140)):
 pts=[screen(x,y,.35+.10*(1-min(1,((Vector((x,y))-center).length/90))**2)-.044-.055*sin(pi*j/12)) for j,x in enumerate([124+29*j/12 for j in range(13)])]
 verts=[p+V*dz for p in pts for dz in (-.022,.022)]
 strap=bevel(solid(mesh('shield back enarme '+str(k),verts,[(2*j,2*j+1,2*j+3,2*j+2) for j in range(12)],leather),.009),.003)
 attach(strap,'lowerarm_l')
 for j in (0,12):attach(sphere('shield back strap rivet',pts[j]-D*.006,(.007,.007,.007),gold),'lowerarm_l')
 buckle=[pts[3]+Vector((dx,0,0))+V*dz-D*.008 for dx,dz in [(-.018,-.028),(.018,-.028),(.018,.028),(-.018,.028),(-.018,-.028)]]
 attach(curve('shield back buckle',buckle,.004,gold),'lowerarm_l')
rim=curve('kite shield brass rim',[screen(*p,.357) for p in edge+[edge[0]]],.011,gold);attach(rim,'lowerarm_l')
for i in range(0,N,4):attach(sphere('shield brass nail',screen(*edge[i],.37),(.0045,.0045,.0045),gold),'lowerarm_l')
# Raised gold cross follows the domed shield; it is the supplied painting's device.
def onshield(x,y,extra=.006):
 q=Vector((x,y));r=min(1,((q-center).length/90));return screen(x,y,.35+.10*(1-r*r)+extra)
for name,poly in [('vertical cross',[(137,61),(142,67),(145,69),(141,75),(147,194),(154,199),(148,208),(144,202),(141,198),(135,76),(131,72),(134,68)]),('horizontal cross',[(117,105),(120,110),(135,113),(157,111),(161,106),(162,116),(158,122),(153,119),(125,122),(119,127),(117,121),(112,116)])]:
 ob=solid(mesh(name,[onshield(x,y) for x,y in poly],[tuple(range(len(poly)))],gold),.003);bevel(ob,.001);attach(ob,'lowerarm_l')
attach(sphere('shield boss',screen(145,113,.49),(.066,.036,.080),gold),'lowerarm_l')
# Spear in the raised hand, the broad iron leaf faces the camera.
start=screen(43,14,.27);socket=screen(177,62,.27);tip=screen(213,77,.27)
shaft=curve('overhand ash spear',[start,socket],.012,wood);attach(shaft,'hand_r')
shaft['shaft_axis_local']=json.dumps([list(shaft.matrix_world.inverted()@p) for p in (start,socket)])
attach(curve('iron spear socket',[socket-(tip-socket)*.20,socket+(tip-socket)*.25],.015,steel),'hand_r')
axis=(tip-socket).normalized();wide=Vector((-axis.z,0,axis.x)).normalized();centerleaf=socket.lerp(tip,.35);v=[socket,centerleaf+wide*.034,tip,centerleaf-wide*.034,centerleaf+D*.014,centerleaf-D*.014]
f=[(0,1,4),(1,2,4),(2,3,4),(3,0,4),(1,0,5),(2,1,5),(3,2,5),(0,3,5)]
attach(bevel(mesh('forged iron spear leaf',v,f,steel,False),.001),'hand_r')
# Original sword at the left hip, tucked alongside the armour skirt.
attach(curve('leather scabbard',[screen(91,118,.15),screen(73,156,.13)],.027,leather),'pelvis')
attach(curve('sword brass throat',[screen(88,122,.17),screen(93,113,.17)],.020,gold),'pelvis')
# Stationary warm cream disc, matching source projected size and foot contact.
bpy.ops.mesh.primitive_cylinder_add(vertices=128,radius=.52,depth=.105,location=(-.105,0,.1225));base=bpy.context.object;base.name='GEO-stationary cream stone';base.data.materials.append(stone);bevel(base,.018);base.modifiers[-1].segments=5
for p in base.data.polygons:p.use_smooth=abs(p.normal.z)<.5
# Orthographic product shot; no DOF blur on atlas silhouettes.
bpy.ops.object.camera_add(location=TARGET+D*8);sc.camera=bpy.context.object;sc.camera.name='CAM-painting';sc.camera.rotation_euler=(-D).to_track_quat('-Z','Y').to_euler();sc.camera.data.type='ORTHO';sc.camera.data.ortho_scale=SPAN
sc.world.use_nodes=True;bg=sc.world.node_tree.nodes.get('Background');bg.inputs['Color'].default_value=(.5,.48,.43,1);bg.inputs['Strength'].default_value=.45
for name,loc,power,size,color in [('warm key',(-3,-4,6),340,3,(1,.97,.90)),('soft fill',(4,-3,3),85,4,(.92,.96,1)),('cool rim',(-1,3,4),145,3,(.86,.92,1))]:
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name='LGT-'+name;o.data.energy=power;o.data.shape='DISK';o.data.size=size;o.data.color=color;o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=8;sc.cycles.use_denoising=True
sc.render.resolution_x=sc.render.resolution_y=256;sc.render.resolution_percentage=100;sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA'
sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0
rig['neutral_pose']=json.dumps({p.name:[list(row) for row in p.matrix_basis] for p in rig.pose.bones});rig['source']='MPFB 2.0.18 CC0 anatomy and game_engine rig'
sc['cream_target_srgb']='#E9CFA0';sc['unit_slug']='tagmatic-soldier';sc['round']=3
# The physical stone keeps live contact shadows. Pigment is camera-only: it is
# not a lamp and contains none of the source's feet or baked cast shadows.
n=stone.node_tree.nodes;l=stone.node_tree.links;bs=n.get('Principled BSDF')
noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=155
pig=n.new('ShaderNodeMixRGB');pig.inputs[1].default_value=tuple(linear(x/255) for x in (255,237,199))+(1,);pig.inputs[2].default_value=tuple(linear(x/255) for x in (252,225,174))+(1,);l.new(noise.outputs['Fac'],pig.inputs[0])
ao=n.new('ShaderNodeAmbientOcclusion');ao.inputs['Distance'].default_value=.16;ao.inputs['Color'].default_value=(1,1,1,1)
# Distinct darker vertical stone rim; live AO still supplies moving contacts.
geom=n.new('ShaderNodeNewGeometry');sep=n.new('ShaderNodeSeparateXYZ');l.new(geom.outputs['Normal'],sep.inputs[0])
rimshade=n.new('ShaderNodeMapRange');rimshade.inputs['From Min'].default_value=0;rimshade.inputs['From Max'].default_value=1;rimshade.inputs['To Min'].default_value=.85;rimshade.inputs['To Max'].default_value=1;l.new(sep.outputs['Z'],rimshade.inputs['Value'])
stonecolor=n.new('ShaderNodeMixRGB');stonecolor.blend_type='MULTIPLY';stonecolor.inputs[0].default_value=1;l.new(pig.outputs[0],stonecolor.inputs[1]);l.new(rimshade.outputs[0],stonecolor.inputs[2])
shade=n.new('ShaderNodeMixRGB');shade.blend_type='MULTIPLY';shade.inputs[0].default_value=.28;l.new(stonecolor.outputs[0],shade.inputs[1]);l.new(ao.outputs['Color'],shade.inputs[2])
emit=n.new('ShaderNodeEmission');l.new(shade.outputs[0],emit.inputs['Color'])
lightpath=n.new('ShaderNodeLightPath');weight=n.new('ShaderNodeMath');weight.operation='MULTIPLY';weight.inputs[1].default_value=.75;l.new(lightpath.outputs['Is Camera Ray'],weight.inputs[0])
mixshader=n.new('ShaderNodeMixShader');l.new(weight.outputs[0],mixshader.inputs[0]);l.new(bs.outputs[0],mixshader.inputs[1]);l.new(emit.outputs[0],mixshader.inputs[2]);l.new(mixshader.outputs[0],n.get('Material Output').inputs['Surface'])
# Seat every ornament sample on the evaluated convex shield, rather than
# connecting a few endpoints by planes that cut through its dome.
from mathutils.bvhtree import BVHTree
bpy.context.view_layer.update();ev=shield.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
shield_tree=BVHTree.FromPolygons([ev.matrix_world@v.co for v in me.vertices],[tuple(p.vertices) for p in me.polygons]);ev.to_mesh_clear()
for o in list(sc.objects):
 if not o.name.startswith(('GEO-vertical cross','GEO-horizontal cross')):continue
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.triangulate(bm,faces=list(bm.faces));bmesh.ops.subdivide_edges(bm,edges=list(bm.edges),cuts=5,use_grid_fill=True);bm.to_mesh(o.data);bm.free()
 inv=o.matrix_world.inverted()
 for v in o.data.vertices:
  world=o.matrix_world@v.co;hit,_,_,_=shield_tree.ray_cast(world+D*3,-D,6)
  if hit is None:raise RuntimeError('Shield relief has no support: '+o.name)
  v.co=inv@(hit+D*.004)
# Finish rigid surfaces before projection; bone parenting retains articulation.
for o in list(sc.objects):
 if o.type!='MESH' or any(m.type=='ARMATURE' for m in o.modifiers):continue
 bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
 for mod in list(o.modifiers):
  if mod.type in {'BEVEL','SOLIDIFY','SUBSURF'}:bpy.ops.object.modifier_apply(modifier=mod.name)
sc['finished_surface_projection']=True
# Frozen camera UVs on the real disc preserve the painted limestone. The
# generated top contains no feet/shadows; moving contacts use fresh scene AO.
bpy.context.view_layer.update()
uv=base.data.uv_layers.new(name='StoneRestUV')
for loop in base.data.loops:
 q=world_to_camera_view(sc,sc.camera,base.matrix_world@base.data.vertices[loop.vertex_index].co)
 uv.data[loop.index].uv=(q.x,q.y)
uvn=n.new('ShaderNodeUVMap');uvn.uv_map='StoneRestUV'
tex=n.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(A/'stone-projection.png'));tex.extension='EXTEND';l.new(uvn.outputs[0],tex.inputs['Vector'])
plate=n.new('ShaderNodeMixRGB');l.new(tex.outputs['Alpha'],plate.inputs[0]);l.new(stonecolor.outputs[0],plate.inputs[1]);l.new(tex.outputs['Color'],plate.inputs[2]);l.new(plate.outputs[0],shade.inputs[1])
weight.inputs[1].default_value=.97
bpy.ops.wm.save_as_mainfile(filepath=str(M/'unpainted.blend'))
# Freeze projected UVs at rest. Facing and ray visibility weights reject occluded/back surfaces.
# Convert curves to meshes before projection, preserving real cross section.
for o in list(sc.objects):
 if o.type=='CURVE':
  bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
bpy.context.view_layer.update()
painting=bpy.data.images.load(str(A/'painting-aligned.png'));records=[]
# Orthographic visibility rejects painting pixels belonging to foreground equipment.
from mathutils.bvhtree import BVHTree
allverts=[];allfaces=[];dg=bpy.context.evaluated_depsgraph_get()
for ob in sc.objects:
 if ob.type!='MESH' or ob.hide_render:continue
 ev=ob.evaluated_get(dg);me=ev.to_mesh();offset=len(allverts)
 allverts.extend(ev.matrix_world@v.co for v in me.vertices)
 allfaces.extend(tuple(offset+i for i in p.vertices) for p in me.polygons)
 ev.to_mesh_clear()
visibility=BVHTree.FromPolygons(allverts,allfaces)

for o in list(sc.objects):
 if o.type!='MESH' or o==base:continue
 # Keep topology identical during UV evaluation, retaining armature only.
 states=[(m,m.show_viewport) for m in o.modifiers]
 for m,_ in states:
  if m.type!='ARMATURE':m.show_viewport=False
 bpy.context.view_layer.update();ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
 if len(me.vertices)!=len(o.data.vertices):raise RuntimeError('Projection topology mismatch '+o.name)
 coords=[];weights=[]
 for v in me.vertices:
  world=ev.matrix_world@v.co;q=world_to_camera_view(sc,sc.camera,world);coords.append((q.x,q.y));normal=(ev.matrix_world.to_3x3().inverted().transposed()@v.normal).normalized()
  w=max(0,min(1,(normal.dot(D)+.05)/.55));hit,_,_,_=visibility.ray_cast(world+D*5,-D,6);visible=hit is not None and abs((hit-world).dot(D))<.022;weights.append(w if visible else 0)
 ev.to_mesh_clear()
 for m,state in states:m.show_viewport=state
 uv=o.data.uv_layers.new(name='PaintingRestUV');at=o.data.color_attributes.new(name='PaintFacing',type='FLOAT_COLOR',domain='CORNER')
 for i,l in enumerate(o.data.loops):uv.data[i].uv=coords[l.vertex_index];at.data[i].color=(weights[l.vertex_index],)*3+(1,)
 for idx,old in enumerate(list(o.data.materials)):
  ma=old.copy();ma.name=old.name+' projected '+o.name;o.data.materials[idx]=ma;n=ma.node_tree.nodes;l=ma.node_tree.links;s=n.get('Principled BSDF')
  uvn=n.new('ShaderNodeUVMap');uvn.uv_map='PaintingRestUV';t=n.new('ShaderNodeTexImage');t.image=painting;t.extension='CLIP';l.new(uvn.outputs[0],t.inputs['Vector'])
  attr=n.new('ShaderNodeVertexColor');attr.layer_name='PaintFacing';alpha=n.new('ShaderNodeMath');alpha.operation='MULTIPLY';l.new(attr.outputs[0],alpha.inputs[0]);l.new(t.outputs['Alpha'],alpha.inputs[1])
  strength=n.new('ShaderNodeMath');strength.name='Frozen pigment coverage';strength.operation='MULTIPLY';strength.inputs[1].default_value=.97;l.new(alpha.outputs[0],strength.inputs[0])
  # The painting already contains illumination. Preserve it for camera rays;
  # physical rays and unpainted backs keep the generated fill/PBR material.
  emit=n.new('ShaderNodeEmission');emit.name='Source painted illumination';l.new(t.outputs['Color'],emit.inputs['Color'])
  lightpath=n.new('ShaderNodeLightPath');weight=n.new('ShaderNodeMath');weight.name='Camera only painted pigment';weight.operation='MULTIPLY';l.new(lightpath.outputs['Is Camera Ray'],weight.inputs[0]);l.new(strength.outputs[0],weight.inputs[1])
  mixshader=n.new('ShaderNodeMixShader');l.new(weight.outputs[0],mixshader.inputs[0]);l.new(s.outputs[0],mixshader.inputs[1]);l.new(emit.outputs[0],mixshader.inputs[2]);l.new(mixshader.outputs[0],n.get('Material Output').inputs['Surface'])
 records.append({'name':o.name,'vertices':len(o.data.vertices)})
sc['projection_method']='Frozen rest UVs on MPFB and true volumetric equipment; incidence/alpha blend into generated hidden-surface fills'
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(M/'tagmatic-soldier.blend'))
(M/'model.json').write_text(json.dumps({'rig_bones':len(rig.data.bones),'body_vertices':len(body.data.vertices),'objects':records,'camera_span':SPAN,'camera_elevation':E,'cream':'#E9CFA0'},indent=2))
print('MODEL_READY',M)
