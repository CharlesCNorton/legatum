"""Field cannon: original hard surfaces and MPFB crew, no billboard geometry."""
import bpy, os, math, json, random
from pathlib import Path
from math import sin, cos, pi
from mathutils import Vector, Matrix
ROOT=Path(os.environ['ANIM_ROOT']); MASTER=ROOT/'masters/field-cannon'
MASTER.mkdir(parents=True,exist_ok=True)
random.seed(44)
def mat(name,color,metal=0,rough=.6):
 m=bpy.data.materials.new(name);m.use_fake_user=True;m.diffuse_color=(*color,1);m.use_nodes=True
 p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
 return m

def mesh(name,vs,fs,m):
 d=bpy.data.meshes.new(name);d.from_pydata(vs,[],fs);d.update();o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o)
 if m:d.materials.append(m)
 for p in d.polygons:p.use_smooth=True
 return o

def bevel(o,w=.008):
 b=o.modifiers.new('Soft worn arris','BEVEL');b.width=w;b.segments=3
 return o

def solid(o,w=.008):
 b=o.modifiers.new('Actual cloth thickness','SOLIDIFY');b.thickness=w
 return o

def empty(name,loc=(0,0,0)):
 o=bpy.data.objects.new(name,None);bpy.context.collection.objects.link(o);o.location=loc;return o

def parent(o,p):
 bpy.context.view_layer.update();w=o.matrix_world.copy();o.parent=p;o.matrix_world=w;return o

def cube(name,loc,scale,m,p=None):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m);bevel(o)
 if p:parent(o,p)
 return o

def rod(name,a,b,r,m,p=None,r2=None):
 delta=Vector(b)-Vector(a)
 bpy.ops.mesh.primitive_cone_add(vertices=32,radius1=r,radius2=r if r2 is None else r2,depth=delta.length,location=(Vector(a)+Vector(b))*.5)
 o=bpy.context.object;o.name=name;o.rotation_euler=delta.to_track_quat('Z','Y').to_euler();o.data.materials.append(m);bevel(o,.003)
 for poly in o.data.polygons:poly.use_smooth=True
 if p:parent(o,p)
 return o

def curve(name,pts,r,m,p=None):
 d=bpy.data.curves.new(name,'CURVE');d.dimensions='3D';s=d.splines.new('POLY');s.points.add(len(pts)-1)
 for a,b in zip(s.points,pts):a.co=(*b,1)
 d.bevel_depth=r;d.bevel_resolution=2;o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);d.materials.append(m)
 if p:parent(o,p)
 return o

def ball(name,loc,scale,m,p=None):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=12,location=loc);o=bpy.context.object;o.name=name;o.scale=scale;o.data.materials.append(m)
 for a in o.data.polygons:a.use_smooth=True
 if p:parent(o,p)
 return o

def hoop(name,center,r,width,depth,m,p):
 vs=[];fs=[]
 for rr,yy in [(r-depth,-width/2),(r,-width/2),(r,width/2),(r-depth,width/2)]:
  for i in range(96):
   a=2*pi*i/96;vs.append(tuple(Vector(center)+Vector((rr*cos(a),yy,rr*sin(a)))))
 for j in range(4):
  for i in range(96):fs.append((j*96+i,j*96+(i+1)%96,((j+1)%4)*96+(i+1)%96,((j+1)%4)*96+i))
 o=mesh(name,vs,fs,m);bevel(o,.002);parent(o,p);return o

def ring(name,center,r,thick,m,axis='Y',p=None):
 pts=[]
 for i in range(65):
  a=2*pi*i/64
  v=(r*cos(a),0,r*sin(a)) if axis=='Y' else (0,r*cos(a),r*sin(a)) if axis=='X' else (r*cos(a),r*sin(a),0)
  pts.append(tuple(Vector(center)+Vector(v)))
 return curve(name,pts,thick,m,p)

bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bronze=mat('Siege aged bronze',(.41,.245,.075),.72,.4)
edge=mat('Siege bright worn bronze',(.68,.44,.17),.7,.34)
iron=mat('Siege dark forged iron',(.10,.11,.105),.64,.5)
brightiron=mat('Siege iron arris',(.26,.27,.25),.68,.44)
wood=mat('Siege olive painted oak',(.17,.18,.085),0,.73)
rawwood=mat('Siege exposed oak',(.28,.17,.075),0,.72)
navy=mat('Siege indigo wool',(.027,.055,.105),0,.87)
red=mat('Siege vermilion facings',(.37,.039,.016),0,.83)
linen=mat('Siege ivory linen',(.73,.66,.48),0,.88)
leather=mat('Siege black boot leather',(.025,.023,.018),0,.56)
skin=mat('Siege painted warm skin',(.52,.30,.16),0,.66)
stone=mat('Siege cream limestone',(.82,.70,.49),0,.86)
dark=mat('Siege bore soot',(.012,.009,.006),0,.95)
# Physical gun, forward along +X; axle along Y. Radius is the rolling radius.
gun=empty('Gun travel and recoil');gun['wheel_radius']=.48
ax=.08;wz=.585;radius=.48
rod('Iron axle',(ax,-.61,wz),(ax,.61,wz),.052,iron,gun)
for sy in [-1,1]:
 y=sy*.61;wheel=empty('Wheel '+str(sy),(ax,y,wz));parent(wheel,gun)
 # Broad wooden felloe and iron tyre, with genuine spoke openings.
 for off in [-.037,.037]:
  ring('Oak felloe',(ax,y+off,wz),radius-.035,.029,wood,p=wheel)
 hoop('Flat wrought iron tyre',(ax,y,wz),radius,.105,.014,iron,wheel)
 for off in [-.034,.034]:ring('Tyre polished edge',(ax,y+off,wz),radius-.006,.005,brightiron,p=wheel)
 for i in range(12):
  a=2*pi*i/12;end=Vector((ax+(radius-.054)*cos(a),y,wz+(radius-.054)*sin(a)))
  start=Vector((ax+.072*cos(a),y,wz+.072*sin(a)))
  o=cube('Tapered oak spoke',(start+end)*.5,(.046,.052,(end-start).length),wood,wheel);o.rotation_euler=(end-start).to_track_quat('Z','Y').to_euler()
  ball('Felloe nail',tuple(end+Vector((0,sy*.035,0))),(.009,.005,.009),brightiron,wheel)
 rod('Turned wheel hub',(ax,y-.09,wz),(ax,y+.09,wz),.081,rawwood,wheel,r2=.069)
 for off in [-.073,.073]:ring('Hub iron binding',(ax,y+off,wz),.077,.010,iron,p=wheel)
 rod('Axle end',(ax,y+sy*.09,wz),(ax,y+sy*.13,wz),.042,brightiron,wheel)
# Cheeks narrow at rear, tall around trunnions. Warm cut edges and iron fastenings.
for sy in [-1,1]:
 y=sy*.22
 outline=[(-.79,.16),(-.72,.30),(-.12,.77),(.43,.82),(.53,.63),(.10,.52)]
 vs=[(x,y+off,z) for off in [-.055,.055] for x,z in outline];n=len(outline)
 fs=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 cheek=bevel(mesh('Oak carriage cheek '+str(sy),vs,fs,wood));parent(cheek,gun)
 for x,z in [(-.55,.30),(-.10,.60),(.34,.65)]:
  plate=cube('Iron cheek strap',(x,y+sy*.063,z),(.085,.018,.25),iron,gun)
  for zz in [-.08,.08]:rod('Square bolt', (x,y+sy*.07,z+zz),(x,y+sy*.088,z+zz),.016,brightiron,gun)
 curve('Worn cheek upper edge',[(x,y-sy*.059,z+.004) for x,z in outline[:4]],.006,rawwood,gun)
 ring('Tow eye',(-.70,y,.22),.04,.01,iron,axis='X',p=gun)
for x,z in [(-.62,.24),(-.05,.55),(.35,.60)]:cube('Carriage cross bed',(x,0,z),(.12,.49,.11),wood,gun)
cube('Trail shoe',(-.76,0,.145),(.15,.59,.07),iron,gun)
# Hollow lathed bronze barrel with black interior, integral mouldings and cascabel.
barrel=empty('Barrel elevation',(.20,0,.86));parent(barrel,gun)
profile=[(-.40,.055),(-.36,.10),(-.31,.14),(-.25,.153),(-.19,.157),(-.15,.155),(.00,.142),(.035,.147),(.065,.145),(.08,.133),(.42,.105),(.46,.109),(.49,.108),(.51,.102),(.65,.108),(.68,.128),(.73,.128),(.76,.115),(.76,.078),(.55,.078),(.25,.070)]
vs=[];fs=[]
for x,r in profile:
 for j in range(96):a=j*2*pi/96;vs.append((x+.20,r*cos(a),.88+r*sin(a)))
for k in range(len(profile)-1):
 for j in range(96):a=k*96+j;b=k*96+(j+1)%96;fs.append((a,b,b+96,a+96))
o=mesh('Hollow bronze barrel',vs,fs,bronze);o.data.materials.append(dark)
for p in o.data.polygons:
 if p.index>=18*96:p.material_index=1
parent(o,barrel);bevel(o,.002)
rod('Bore shadow stop',(.44,0,.88),(.445,0,.88),.069,dark,barrel)
for x,r in [(-.06,.155),(.24,.148),(.67,.111),(.90,.129),(.95,.116)]:ring('Bronze turned moulding',(x,0,.88),r,.007,edge,axis='X',p=barrel)
ball('Cascabel knob',(-.235,0,.88),(.055,.06,.06),bronze,barrel)
rod('Trunnion',(.16,-.31,.84),(.16,.31,.84),.055,bronze,barrel)
for sy in [-1,1]:
 cube('Trunnion cap',(.16,sy*.22,.865),(.15,.12,.028),iron,gun)
 for xx in [.10,.22]:ball('Trunnion cap bolt',(xx,sy*.22,.89),(.014,.014,.012),brightiron,gun)
cube('Elevation wedge',(-.13,0,.70),(.24,.15,.08),rawwood,gun)
# Discrete nicks and engraved rings read at miniature scale without procedural noise soup.
for i in range(28):
 x=random.uniform(-.10,.83);a=random.uniform(.2,5.7);rr=.142-.035*max(0,x)/.83
 curve('Bronze wear scratch',[(x,rr*cos(a),.88+rr*sin(a)),(x+.018,rr*cos(a+.035),.88+rr*sin(a+.035))],.0015,edge,barrel)
# MPFB body and all its native weights; custom period clothes fit that body.
bpy.ops.preferences.addon_enable(module='bl_ext.user_default.mpfb')
from bl_ext.user_default.mpfb.services.humanservice import HumanService
from bl_ext.user_default.mpfb.services.targetservice import TargetService
macro=TargetService.get_default_macro_info_dict();macro.update(gender=1.,age=.5,muscle=.60,weight=.48,height=.45,proportions=.5)
body=HumanService.create_human(macro_detail_dict=macro);body.name='MPFB artillery gunner anatomy'
bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();lo=min(v.co.z for v in me.vertices);hi=max(v.co.z for v in me.vertices);ev.to_mesh_clear()
body.scale=(1.70/(hi-lo),)*3;bpy.context.view_layer.objects.active=body;body.select_set(True);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
rig=HumanService.add_builtin_rig(body,'game_engine');rig.name='Gunner MPFB game_engine';rig['origin']='MPFB 2.0.18 CC0, native body and 53 bone weights'
body.data.materials.clear();body.data.materials.append(skin)
for p in body.data.polygons:p.use_smooth=True
# Capture evaluated anatomy before moving the rig, including MPFB macro targets.
bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
coords=[v.co.copy() for v in me.vertices];normals=[v.normal.copy() for v in me.vertices];polys=[list(p.vertices) for p in me.polygons];ev.to_mesh_clear()
from mathutils.kdtree import KDTree
kd=KDTree(len(body.data.vertices))
for v in body.data.vertices:kd.insert(v.co,v.index)
kd.balance()
def shell(name,predicate,m,inflate):
 fs=[f for f in polys if all(predicate(coords[i]) for i in f)];ids=sorted({i for f in fs for i in f});mp={v:i for i,v in enumerate(ids)}
 # Broad sculpted fabric folds, with the original body's skinning retained.
 def offset(i):
  v=coords[i];fold=0
  if 'breeches' in name: fold=.006*sin(v.z*49+v.x*18)*sin(v.z*8)**2
  if 'sleeves' in name and abs(v.x)>.20: fold=.005*sin(v.x*72+v.z*22)
  if 'gaiters' in name: fold=.0035*sin(v.z*90+v.x*12)
  return v+normals[i]*(inflate+fold)
 o=mesh(name,[offset(i) for i in ids],[[mp[i] for i in f] for f in fs],m)
 for g in body.vertex_groups:
  if g.name in rig.data.bones:o.vertex_groups.new(name=g.name)
 for j,i in enumerate(ids):
  _,k,_=kd.find(coords[i])
  for g in body.data.vertices[k].groups:
   n=body.vertex_groups[g.group].name
   if n in o.vertex_groups:o.vertex_groups[n].add([j],g.weight,'REPLACE')
 o.parent=rig;ar=o.modifiers.new('Native MPFB skinning','ARMATURE');ar.object=rig;solid(o,.006)
 su=o.modifiers.new('Tailored smoothing','SUBSURF');su.levels=1
 return o
shell('White wool breeches',lambda v:.43<v.z<1.01 and abs(v.x)<.32,linen,.013)
shell('Tall fitted black gaiters',lambda v:v.z<.49,leather,.009)
shell('Blue fitted coat and sleeves',lambda v: .95<v.z<1.43 and not(abs(v.x)>.455),navy,.018)
# Hide clothed skin under shells, retaining original anatomy and weights in master.
# Transparent skin under covered regions avoids tiny seams showing through white trousers.
body.data.materials.append(navy);body.data.materials.append(linen);body.data.materials.append(leather)
for p in body.data.polygons:
 c=sum((body.data.vertices[i].co for i in p.vertices),Vector())/len(p.vertices)
 hand_weight=sum(g.weight for i in p.vertices for g in body.data.vertices[i].groups if any(k in body.vertex_groups[g.group].name for k in ['hand_', 'thumb_', 'index_', 'middle_', 'ring_', 'pinky_']))/len(p.vertices)
 if hand_weight>.3:p.material_index=0
 elif c.z<.49:p.material_index=3
 elif c.z<1.0 and abs(c.x)<.32:p.material_index=2
 elif c.z<1.43 and abs(c.x)<.455:p.material_index=1

def attach(o,bone):
 bpy.context.view_layer.update();w=o.matrix_world.copy();o.parent=rig;o.parent_type='BONE';o.parent_bone=bone;bpy.context.view_layer.update();o.matrix_world=w;return o
# Tailored torso, closed fitted coat, central ivory waistcoat and sculpted folds.
vs=[];fs=[]
for j in range(21):
 t=j/20;z=.94+t*.44;rx=.145+.06*sin(t*pi*.68);ry=.150+.025*sin(t*pi)
 for i in range(64):
  a=i*2*pi/64
  # Compression folds radiate from the belt and loaded shoulder, rather than regular ribs.
  fold=(.009*sin(a*9+t*19)+.005*sin(a*17-t*11))*sin(t*pi)
  fold+=.008*sin(t*37+a*3)*max(0,cos(a))*(1-t)
  vs.append(((rx+fold)*sin(a),-(ry+fold)*cos(a),z))
for j in range(20):
 for i in range(64):a=j*64+i;b=j*64+(i+1)%64;fs.append((a,b,b+64,a+64))
coat=attach(solid(mesh('Tailored blue coat body',vs,fs,navy)),'spine_02')
su=coat.modifiers.new('Supple tailored folds','SUBSURF');su.levels=1
# Cloth coat tails: real folded mesh, weighted to pelvis.
for sg in [-1,1]:
 vs=[]
 for j in range(11):
  t=j/10
  for i in range(9):
   u=i/8;vs.append((sg*(.045+.16*u+.03*t),.105+.055*t+.012*sin(u*4*pi),.98-.38*t+.025*sin(u*pi)))
 fs=[(j*9+i,j*9+i+1,(j+1)*9+i+1,(j+1)*9+i) for j in range(10) for i in range(8)]
 attach(solid(mesh('Split folded coat tail',vs,fs,navy)),'pelvis')
 attach(curve('Coat tail red piping',[vs[j*9+8] for j in range(11)],.004,red),'pelvis')
# Sewn sleeves have deliberate broad folds visible at token resolution.
for side in ['l','r']:
 for segment,r0,r1 in [('upperarm',.078,.060),('lowerarm',.062,.044)]:
  bone=rig.data.bones[segment+'_'+side];a=bone.head_local;b=bone.tail_local;axis=(b-a).normalized()
  u=axis.cross(Vector((0,1,0))).normalized();v=axis.cross(u).normalized();vs=[];fs=[]
  for j in range(25):
   t=j/24;center=a.lerp(b,t)
   for k in range(40):
    angle=2*pi*k/40;wrinkle=(.006*sin(t*22+2.2*sin(angle*2))+.002*sin(t*43-angle*3))*sin(pi*t)**.6
    radius=r0*(1-t)+r1*t+wrinkle;vs.append(tuple(center+radius*(u*cos(angle)+v*sin(angle))))
  for j in range(24):
   for k in range(40):q=j*40+k;z=j*40+(k+1)%40;fs.append((q,z,z+40,q+40))
  attach(solid(mesh('Folded blue sleeve '+segment+' '+side,vs,fs,navy),.004),segment+'_'+side)
# Broad red cuffs fitted to the forearm bone rather than guessed X cutoffs.
for side in ['l','r']:
 b=rig.data.bones['lowerarm_'+side];a=b.head_local;tip=b.tail_local;v=(tip-a).normalized()
 cuff=rod('Artillery red cuff '+side,tip-v*.092,tip-v*.012,.050,red,r2=.044);attach(cuff,'lowerarm_'+side)
 # Bright cuff seam and two buttons remain readable at 64 px.
 for t in [.025,.066]:
  pos=tip-v*t+Vector((0,-.047,0));attach(ball('Cuff brass button',pos,(.007,.005,.007),edge),'lowerarm_'+side)
def coat_front(x,z):
 t=max(0,min(1,(z-.94)/.44));rx=.145+.06*sin(t*pi*.68);ry=.150+.025*sin(t*pi)
 return -ry*max(.05,1-(x/rx)**2)**.5
# Flat cross belts, fitted over the actual coat surface, not round ropes. Ribbon surface follows the chest.
def ribbon(name,pts,width,m,bone):
 vs=[]
 for i,p in enumerate(pts):
  tangent=Vector(pts[min(i+1,len(pts)-1)])-Vector(pts[max(0,i-1)])
  side=Vector((tangent.z,0,-tangent.x)).normalized()*width/2
  pair=[Vector(p)-side,Vector(p)+side]
  if name=='Ivory cross belt':
   for vertex in pair:vertex.y=coat_front(vertex.x,vertex.z)-.012
  vs.extend(pair)
 fs=[(2*i,2*i+1,2*i+3,2*i+2) for i in range(len(pts)-1)]
 return attach(bevel(solid(mesh(name,vs,fs,m),.006),.002),bone)
for sg in [-1,1]:
 ribbon('Ivory cross belt',[(sg*(-.14+.27*t),-.125-.029*sin(t*pi),1.39-.40*t) for t in [i/16 for i in range(17)]],.053,linen,'spine_02')
 for z in [1.02,1.09,1.16,1.23,1.30]:attach(ball('Brass uniform button',(sg*.055,coat_front(sg*.055,z)-.013,z),(.011,.008,.011),edge),'spine_02')
# Raised belt plate, central pin and fine stitches: physical detail, not projected substitutes.
attach(curve('Crossbelt brass buckle',[(x,coat_front(x,z)-.027,z) for x,z in [(.077,1.086),(.124,1.086),(.124,1.138),(.077,1.138),(.077,1.086)]],.004,edge),'spine_02')
attach(rod('Crossbelt buckle pin',(.078,coat_front(.10,1.11)-.029,1.11),(.124,coat_front(.10,1.11)-.029,1.11),.0025,edge),'spine_02')
for sg in [-1,1]:
 for edge_side in [-1,1]:
  for j in range(26):
   t=(j+.4)/26;x=sg*(-.14+.27*t)+edge_side*.020;z=1.39-.40*t;y=coat_front(x,z)-.020
   attach(curve('Ivory belt hand stitching',[(x-.002,y,z+.002),(x+.002,y,z-.002)],.0013,rawwood),'spine_02')
attach(curve('Red standing collar',[(.073*sin(a),-.061*cos(a),1.415) for a in [i*2*pi/48 for i in range(49)]],.018,red),'neck_01')
for sg in [-1,1]:
 attach(cube('Red shoulder board',(sg*.185,-.015,1.385),(.105,.07,.018),red),'upperarm_'+('l' if sg>0 else 'r'))
# The painting has a closed navy coat, not a third vertical ivory chest strap.
for sg in [-1,1]:
 attach(curve('Red lapel piping',[(sg*.10,-.155,1.38),(sg*.065,-.172,1.24),(sg*.046,-.155,1.02)],.0035,red),'spine_02')
# Shako fitted to anatomical head; no maker marks or national emblems.
head=rig.data.bones['head'];hc=(head.head_local+head.tail_local)*.5;hz=hc.z+.07
attach(rod('Black felt shako',(0,hc.y,hz),(0,hc.y,hz+.20),.105,leather,r2=.12),'head')
for zz,rr,ma in [(hz,.107,edge),(hz+.19,.121,red)]:attach(ring('Shako piping',(0,hc.y,zz),rr,.009,ma,axis='Z'),'head')
vs=[(0,hc.y-.11,hz-.01)]+[(.117*cos(a),hc.y-.085-.09*sin(a),hz-.025) for a in [i*pi/24 for i in range(25)]]
attach(solid(mesh('Black shako visor',vs,[tuple(range(len(vs)))],leather),.008),'head')
for z in [hz+.045,hz+.12]:attach(ball('Brass shako disc',(0,hc.y-.116,z),(.018,.006,.023),edge),'head')
attach(ball('Red wool pompon',(-.065,hc.y,hz+.235),(.035,.035,.042),red),'head')
for i in range(14):
 a=2*pi*i/14;attach(curve('Pompon fibres',[(-.065+.026*cos(a),hc.y+.026*sin(a),hz+.215),(-.065+.029*cos(a),hc.y+.029*sin(a),hz+.259)],.003,red),'head')
# Eyes from the installed CC0 MakeHuman system pack.
system=ROOT/'blender-user/extensions/.user/user_default/mpfb/data'
eyes=HumanService.add_mhclo_asset(str(system/'eyes/high-poly/high-poly.mhclo'),body,asset_type='Eyes',subdiv_levels=1,material_type='MAKESKIN');eyes.name='Gunner MPFB system eyes'
# Moustache follows the actual face, modest silhouette.
# Place facial paint against the evaluated facial surface, not the head bone centre.
def face_y(x,z):
 points=[v.y for v in coords if abs(v.x-x)<.012 and abs(v.z-z)<.014]
 return min(points)-.006 if points else hc.y-.15
moustache_z=hc.z-.045
pts=[(x,face_y(x,moustache_z),moustache_z+.007*cos(x*50)) for x in [-.045,-.03,-.015,0,.015,.03,.045]]
attach(curve('Gunner dark painted moustache',pts,.009,leather),'head')
for sg in [-1,1]:
 z=hc.z+.027
 attach(curve('Gunner eyebrow',[(sg*x,face_y(sg*x,z),z+.005*sin(x*50)) for x in [.016,.025,.035,.045]],.004,leather),'head')
# Equipment pouch at hip.
attach(cube('Leather cartridge pouch',(-.19,.035,.95),(.15,.10,.18),rawwood),'pelvis')
attach(cube('Cartridge pouch flap',(-.19,-.022,.985),(.16,.02,.10),leather),'pelvis')
# Sole definition and gaiter closures fitted to real MPFB feet.
for side in ['l','r']:
 foot=rig.data.bones['foot_'+side];x=foot.head_local.x;y=foot.head_local.y
 attach(cube('Boot sole '+side,(x,y-.06,.022),(.115,.25,.035),leather),'foot_'+side)
 for z in [.13,.21,.29,.37,.44]:attach(ball('Gaiter button',(x+.05,-.048,z),(.006,.006,.006),iron),'calf_'+side)
# IK-like two-bone solve, authored end-effector placements in anatomical coordinates.
def aim(name,d):
 p=rig.pose.bones[name];q=p.bone.matrix_local.to_quaternion();v=q @ Vector((0,1,0));rot=(v.rotation_difference(Vector(d).normalized()) @ q).to_matrix().to_4x4();rot.translation=p.head.copy();p.matrix=rot;bpy.context.view_layer.update()
def limb(up,low,t,pole):
 a=rig.pose.bones[up].head.copy();delta=Vector(t)-a;l1=rig.data.bones[up].length;l2=rig.data.bones[low].length;d=min(delta.length,l1+l2-.0001);delta.normalize();along=(l1*l1-l2*l2+d*d)/(2*d);h=max(0,l1*l1-along*along)**.5
 side=Vector(pole)-a;side=(side-delta*side.dot(delta)).normalized();el=a+delta*along+side*h;aim(up,el-a);aim(low,Vector(t)-el)
limb('thigh_r','calf_r',(-.32,-.055,.07),(-.32,-.3,.5));limb('thigh_l','calf_l',(.22,.015,.07),(.23,-.3,.5))
p=rig.pose.bones['spine_01'];pivot=p.head.copy();p.matrix=Matrix.Translation(pivot) @ Matrix.Rotation(.18,4,'Y') @ Matrix.Translation(-pivot) @ p.matrix
bpy.context.view_layer.update()
limb('upperarm_r','lowerarm_r',(-.26,-.23,1.13),(-.44,-.18,1.10));limb('upperarm_l','lowerarm_l',(.40,.16,.82),(.46,-.03,1.10))
aim('hand_r',(0,-.08,.015));aim('hand_l',(.10,0,-.025))
for side in ['r','l']:
 for digit in ['index','middle','ring','pinky']:
  for k in range(1,4):
   p=rig.pose.bones[f'{digit}_{k:02d}_{side}'];p.rotation_mode='XYZ';p.rotation_euler.x=.65 if side=='r' else .25
bpy.context.view_layer.update()
grip=rig.pose.bones['hand_r'].head+Vector((0,-.055,.015))
rammer=empty('Rammer hand control',grip);attach(rammer,'hand_r')
rod('Wooden rammer',grip+Vector((.08,0,-1.11)),grip+Vector((-.05,0,.34)),.013,rawwood,rammer)
rod('Rammer sponge',grip+Vector((-.05,0,.32)),grip+Vector((-.065,0,.48)),.037,dark,rammer)
p=rig.pose.bones['head'];p.matrix_basis=p.matrix_basis @ Matrix.Rotation(-.14,4,'Z')
rig.pose.bones['head'].scale=(1.12,1.12,1.12)
rig.location=(-.60,.06,.105);rig.scale=(1.16,1.03,1.0)
# Stationary cream stone base, matched to the painting's low plain disc.
bpy.ops.mesh.primitive_cylinder_add(vertices=128,radius=1.05,depth=.095,location=(0,0,.0475));base=bpy.context.object;base.name='Stationary cream base';base.data.materials.append(stone);bevel(base,.022)
# Camera and warm painterly lighting.
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=12;sc.cycles.use_denoising=True;sc.render.threads_mode='FIXED';sc.render.threads=3
sc.render.resolution_x=sc.render.resolution_y=256;sc.render.resolution_percentage=100;sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA'
sc.world.color=(.23,.23,.23);sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast';sc.view_settings.exposure=.65
bpy.ops.object.camera_add(location=(3,-7,3.0));sc.camera=bpy.context.object;sc.camera.name='Painting camera';sc.camera.data.type='ORTHO';sc.camera.data.ortho_scale=2.70
sc.camera.rotation_euler=(Vector((0,0,.95))-sc.camera.location).to_track_quat('-Z','Y').to_euler()
for name,loc,power,size,col in [('Warm left key',(-3,-4,6),520,3,(1,.82,.62)),('Cool fill',(4,-2,4),180,4,(.75,.84,1)),('Gold rim',(-2,3,4),280,3,(1,.78,.52))]:
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name=name;o.data.energy=power;o.data.shape='DISK';o.data.size=size;o.data.color=col;o.rotation_euler=(Vector((0,0,.8))-o.location).to_track_quat('-Z','Y').to_euler()
gun.rotation_euler.z=-.55;gun.location.x=.12;gun['rest_location']=[.12,0,0];gun['rest_yaw']=-.55
barrel.scale.x=1.40;barrel.location.x+=.10;barrel.rotation_euler.y=-.10
# Solve the weight-bearing wrist against the final transformed barrel crown.
bpy.context.view_layer.update()
contact=barrel.matrix_world @ Vector((-.25,-.025,.171))
# End of the hand bone is the palm contact; the wrist is one hand length behind it.
target=rig.matrix_world.inverted() @ contact-Vector((.11,-.015,-.03)).normalized()*rig.data.bones['hand_l'].length
limb('upperarm_l','lowerarm_l',target,(.56,-.24,1.14))
aim('hand_l',(.11,-.015,-.03))
rig['barrel_contact_local']=[-.25,-.025,.171]
rig['neutral_pose']=json.dumps({p.name:[list(row) for row in p.matrix_basis] for p in rig.pose.bones})
sc['source']='Field cannon painting: one visible MPFB gunner, original hard surface artillery';sc['wheel_radius']=radius
bpy.ops.wm.save_as_mainfile(filepath=str(MASTER/'field-cannon-plain.blend'))
bpy.ops.wm.save_as_mainfile(filepath=str(MASTER/'field-cannon.blend'))
(MASTER/'model-info.json').write_text(json.dumps({'body_vertices':len(body.data.vertices),'bones':len(rig.data.bones),'objects':len(sc.objects),'crew':1,'wheel_radius':radius},indent=2))
print('FIELD_CANNON_MODEL_READY')
