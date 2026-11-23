"""Real MPFB archer with fitted linen, laced leather, bronze and a flexing bow."""
import sys,math,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
from math import sin,cos,pi
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.preferences.addon_enable(module='bl_ext.user_default.mpfb')
from bl_ext.user_default.mpfb.services.humanservice import HumanService
from bl_ext.user_default.mpfb.services.targetservice import TargetService
macro=TargetService.get_default_macro_info_dict();macro.update(gender=1.,age=.35,muscle=.94,weight=.60,height=.44,proportions=.65);macro['race']={'caucasian':.8,'african':.1,'asian':.1}
body=HumanService.create_human(macro_detail_dict=macro);body.name='GEO-MPFB archer anatomy'
bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();zs=[v.co.z for v in me.vertices];ev.to_mesh_clear();s=1.72/(max(zs)-min(zs));body.scale=(s*1.03,s,s);bpy.context.view_layer.objects.active=body;body.select_set(True);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
rig=HumanService.add_builtin_rig(body,'game_engine');rig.name='Archer MPFB rig';rig.location.z=.105
system=ROOT/'blender-user/extensions/.user/user_default/mpfb/data'
eyes=HumanService.add_mhclo_asset(str(system/'eyes/high-poly/high-poly.mhclo'),body,asset_type='Eyes',subdiv_levels=1,material_type='MAKESKIN');eyes.name='GEO-MPFB eyes'
skin=mat('MAT-skin',(.49,.265,.13));linen=mat('MAT-linen',(.75,.67,.51),rough=.88);blue=mat('MAT-indigo',(.045,.055,.08),rough=.9);leather=mat('MAT-leather',(.17,.085,.039),rough=.72);edge=mat('MAT-leather-edge',(.37,.22,.10),rough=.72);bronze=mat('MAT-bronze',(.62,.38,.13),1,.38);gold=mat('MAT-bronze-edge',(.85,.59,.25),1,.29);wood=mat('MAT-yew',(.23,.075,.024),rough=.5);string=mat('MAT-bowstring',(.25,.16,.08),rough=.8);iron=mat('MAT-iron',(.40,.43,.44),1,.4)
stone=mat('MAT-cream-E9CFA0',(.76,.49,.23),rough=.86);rim=mat('MAT-cream-rim',(.52,.36,.20),rough=.87)
body.data.materials.clear();body.data.materials.append(skin)
sub=body.modifiers.new('Anatomical subdivision','SUBSURF');sub.levels=1
for p in body.data.polygons:p.use_smooth=True
# Closed ring surfaces with modeled folds; skinning belongs to the MPFB skeleton.
def garment(name,z0,z1,rx0,rx1,ry0,ry1,folds,amp,material,bone):
 vs=[];fs=[];n=96;rows=20
 for j in range(rows+1):
  t=j/rows;z=z0+(z1-z0)*t
  for i in range(n):
   a=i*2*pi/n;fold=amp*(.35+.65*(1-t))*cos(folds*a+.3*sin(t*3))
   zz=z-(.085*abs(sin(a))**3+.025*max(0,cos(a)))*t**6 if name=='Laced leather cuirass' else z
   vs.append(((rx0+(rx1-rx0)*t+fold)*sin(a),-(ry0+(ry1-ry0)*t+fold)*cos(a),zz+.105))
 for j in range(rows):
  for i in range(n):a=j*n+i;b=j*n+(i+1)%n;fs.append((a,b,b+n,a+n))
 o=bevel(solid(mesh(name,vs,fs,material),.007));attach(o,rig,bone);return o
vest=garment('Laced leather cuirass',1.005,1.405,.176,.215,.163,.183,6,.004,leather,'spine_03')
skirt=garment('Pleated ivory tunic',.70,1.04,.295,.178,.205,.126,18,.019,linen,'pelvis')
# Real hem thickness and continuous indigo border follow the folds.
for zz in [.705,.742]:
 pts=[]
 for i in range(193):
  a=i*2*pi/192;t=(zz-.70)/.34;fold=.019*(.35+.65*(1-t))*cos(18*a+.3*sin(t*3));pts.append(((.295+(.178-.295)*t+fold+.002)*sin(a),-(.205+(.126-.205)*t+fold+.002)*cos(a),zz+.105))
 attach(curve('Indigo woven hem',pts,.010 if zz==.742 else .005,blue),rig,'pelvis')
# Short shoulder caps, sewn piping and a slanted back quiver strap.
for sg,side in [(1,'l'),(-1,'r')]:
 pts=[]
 for j in range(17):
  t=j/16;pts.append((sg*(.17+.11*t),-.025,1.48-.11*t))
 # Caps use a curved thick patch rather than a primitive tube.
 vs=[]
 for p in pts:
  for a in [-pi/2+k*pi/16 for k in range(17)]:vs.append((p[0],p[1]-.10*sin(a),p[2]+.085*cos(a)))
 fs=[(j*17+k,j*17+k+1,(j+1)*17+k+1,(j+1)*17+k) for j in range(16) for k in range(16)]
 attach(solid(mesh('Ivory sleeve '+side,vs,fs,linen),.006),rig,'upperarm_'+side)
# Lacing eyelets and overlapping leather side panels.
for sg in [-1,1]:
 pts=[(sg*(.145-.28*t),-.188+.017*abs(t-.5),1.44-.31*t) for t in [i/32 for i in range(33)]]
 verts=[(x+d*.012,y,z-d*sg*.011) for x,y,z in pts for d in [-1,1]]
 fs=[(i*2,i*2+1,i*2+3,i*2+2) for i in range(len(pts)-1)]
 attach(bevel(solid(mesh('Broad crossed leather strap',verts,fs,leather),.006),.002),rig,'spine_03')
 for dx in [-.014,.014]:attach(curve('Strap sewn edge',[(x+dx,y-.004,z) for x,y,z in pts],.002,edge),rig,'spine_03')
 attach(ball('Shoulder bronze rosette',(sg*.145,-.19,1.44),(.023,.006,.023),gold),rig,'spine_03')
for i in range(7):attach(ball('Belt bronze stud',(-.14+i*.046,-.155,1.12),(.008,.005,.008),gold),rig,'spine_01')
for z in [1.09,1.12]:attach(curve('Waist leather belt',[(.186*sin(a),-.138*cos(a),z) for a in [i*2*pi/96 for i in range(97)]],.016,leather),rig,'spine_01')
attach(curve('Belt buckle',[(-.025,-.158,1.075),(.025,-.158,1.075),(.025,-.158,1.125),(-.025,-.158,1.125),(-.025,-.158,1.075)],.004,gold),rig,'spine_01')
for sg in [-1,1]:
 pts=[(sg*(.15-.07*t),-.15-.015*sin(t*pi),1.16+.26*t) for t in [i/30 for i in range(31)]]
 attach(curve('Cuirass shoulder binding',pts,.013,edge),rig,'spine_03')
 for i in range(16):
  t=i/15;attach(curve('Linen saddle stitch',[(sg*(.151-.07*t)-.004,-.166,1.16+.26*t),(sg*(.151-.07*t)+.004,-.166,1.165+.26*t)],.0016,linen),rig,'spine_03')
# Open-faced bronze cap with cheek pieces. The face is real MPFB anatomy.
h=rig.pose.bones['head'];hc=(h.head+h.tail)*.5;cx,cy,cz=hc.x,hc.y,hc.z+.105
vs=[];fs=[]
for j in range(17):
 t=j*pi/2/16
 for i in range(64):a=i*2*pi/64;vs.append((cx+.105*cos(t)*sin(a),cy-.116*cos(t)*cos(a),cz+.022+.125*sin(t)))
for j in range(16):
 for i in range(64):a=j*64+i;b=j*64+(i+1)%64;fs.append((a,b,b+64,a+64))
helmet=attach(bevel(solid(mesh('Bronze helmet',vs,fs,bronze),.006)),rig,'head')
attach(curve('Helmet rolled brow',[(cx+.106*sin(a),cy-.118*cos(a),cz+.022) for a in [i*2*pi/96 for i in range(97)]],.005,gold),rig,'head')
for sg in [-1,1]:
 vs=[(sg*.097,cy-.034,cz+.028),(sg*.103,cy-.065,cz-.075),(sg*.065,cy-.105,cz-.102),(sg*.073,cy-.109,cz-.015)]
 attach(bevel(solid(mesh('Bronze cheekpiece',vs,[(0,1,2,3)],bronze),.006)),rig,'head')
# Small pale crest with dark side band, built from real front-to-back tufts.
for i in range(51):
 a=-1.08+i/50*2.45;y=cy+.126*sin(a);z=cz+.02+.136*cos(a);yo=cy+.178*sin(a);zo=cz+.023+.265*cos(a)
 o=solid(mesh('Pale horsehair crest', [(-.019,y,z),(.019,y,z),(.016,yo,zo),(-.016,yo,zo)],[(0,1,2,3)],linen if i>13 else blue),.004);attach(o,rig,'head')
attach(curve('Crest bronze ridge',[(0,cy+.128*sin(a),cz+.024+.14*cos(a)) for a in [-1.08+i/60*2.45 for i in range(61)]],.012,gold),rig,'head')
# Sandals and calf laces built in the unposed frame and attached to leg bones.
for side in ['l','r']:
 f=rig.pose.bones['foot_'+side];x,y=f.head.x,f.head.y
 outline=[(x+.056*cos(a),y-.065+.136*sin(a),.115) for a in [i*2*pi/48 for i in range(48)]]
 attach(bevel(solid(mesh('Sandal sole '+side,outline,[tuple(range(48))],leather),.017),.005),rig,'foot_'+side)
 for yy in [-.15,-.09,-.02]:attach(curve('Sandal straps '+side,[(x+.056*cos(a),y+yy,.132+.047*sin(a)) for a in [i*pi/20 for i in range(21)]],.008,leather),rig,'foot_'+side)
 c=rig.pose.bones['calf_'+side];v=c.tail-c.head
 for winding in [-1,1]:
  pts=[]
  for j in range(100):
   t=j/99;a=winding*t*pi*7;center=c.tail-v*(.08+.78*t);r=.045+.016*t;pts.append((center.x+r*sin(a),center.y-r*cos(a),center.z+.105))
  attach(curve('Crossed calf lacing '+side,pts,.005,leather),rig,'calf_'+side)
# Back quiver, lip, straps and six feathered shafts (all physical geometry).
q0=Vector((-.15,.14,1.05));q1=Vector((-.25,.17,1.48));axis=q1-q0
bpy.ops.mesh.primitive_cone_add(vertices=32,radius1=.047,radius2=.060,depth=axis.length,location=(q0+q1)/2);q=bpy.context.object;q.name='GEO-Leather quiver';q.rotation_euler=axis.to_track_quat('Z','Y').to_euler();q.data.materials.append(leather);bevel(q);attach(q,rig,'spine_03')
for i in range(6):
 p=q1+Vector(((i%3-1)*.025,(i//3-.5)*.025,0));end=p+Vector((-.045,0,.19));attach(curve('Quiver arrow',[p,end],.003,wood),rig,'spine_03')
 attach(solid(mesh('Quiver feather',[end,end+Vector((.02,0,-.06)),end+Vector((0,0,-.09))],[(0,1,2)],linen),.002),rig,'spine_03')
# Fitted left forearm leather bracer follows the lower-arm bone.
b=rig.pose.bones['lowerarm_l'];axis=(b.tail-b.head).normalized();u=axis.cross(Vector((0,0,1))).normalized();v=axis.cross(u);vs=[];fs=[]
for j in range(9):
 t=.38+j/8*.53;center=b.head+(b.tail-b.head)*t+Vector((0,0,.105));radius=.056-.014*t
 for i in range(32):
  a=i*2*pi/32;vs.append(tuple(center+radius*(u*cos(a)+v*sin(a))))
for j in range(8):
 for i in range(32):a=j*32+i;c=j*32+(i+1)%32;fs.append((a,c,c+32,a+32))
attach(bevel(solid(mesh('Leather bow bracer',vs,fs,leather),.006)),rig,'lowerarm_l')
# Pose before fitting the bow. Held gear is attached to the palm.
pose(rig)
grip=rig.matrix_world@rig.pose.bones['hand_l'].head+Vector((0,-.013,.045));draw=rig.matrix_world@rig.pose.bones['hand_r'].tail
control=bpy.data.objects.new('Bow grip',None);bpy.context.collection.objects.link(control);control.location=grip;attach(control,rig,'hand_l')
# Bow curves back toward the archer at either tip; nock remains attached to the draw hand.
pts=[]
for i in range(65):
 t=-1+2*i/64;pts.append(tuple(grip+Vector((-.36*(1-math.sqrt(max(0,1-t*t))),0,.66*t))))
bow=curve('Yew bow',pts,.012,wood)
def parent_control(o):
 bpy.context.view_layer.update();w=o.matrix_world.copy();o.parent=control;o.matrix_world=w;return o
parent_control(bow)
parent_control(curve('Bow belly highlight',[(x,y-.008,z) for x,y,z in pts],.003,edge))
for i in range(15):
 z=(i-7)*.007;parent_control(curve('Bow grip winding',[tuple(grip+Vector((.014*cos(a),.014*sin(a),z))) for a in [j*2*pi/24 for j in range(25)]],.0025,leather))
bs=curve('Bowstring',[pts[0],draw,pts[-1]],.0014,string);bs['dynamic']='nock follows draw hand; tips follow bow'
arrow=curve('Nocked arrow',[draw,grip+Vector((.13,-.005,.025))],.0035,wood);arrow['dynamic']='arrow follows string and bow'
# Shared one-step cream base.
bpy.ops.mesh.primitive_cylinder_add(vertices=96,radius=.57,depth=.09,location=(0,0,.045));base=bpy.context.object;base.name='GEO-Stationary cream base';base.data.materials.append(stone);base.data.materials.append(rim);bevel(base,.012)
for p in base.data.polygons:p.material_index=0 if p.normal.z>.5 else 1
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=8;sc.cycles.use_denoising=True;sc.cycles.max_bounces=5;sc.render.threads_mode='FIXED';sc.render.threads=3
sc.render.resolution_x=sc.render.resolution_y=256;sc.render.resolution_percentage=100;sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.world.color=(.1,.1,.1);sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast';sc.view_settings.exposure=.25
bpy.ops.object.camera_add(location=(.15,-8,3.2));cam=bpy.context.object;cam.name='CAM-painting';cam.rotation_euler=(Vector((.15,0,1.04))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=2.5;sc.camera=cam
for name,loc,power,size,color in [('warm key',(-3,-4,6),650,2,(1,.9,.74)),('soft fill',(3,-4,3),140,3,(.9,.94,1)),('cool rim',(2,3,4),430,2,(.73,.84,1))]:
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name='LGT-'+name;o.data.energy=power;o.data.size=size;o.data.color=color;o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
rig['rest_pose']=json.dumps({p.name:[list(row) for row in p.matrix_basis] for p in rig.pose.bones});sc['source']='MPFB 2.0.18 CC0 anatomy, original archer geometry; no billboards';sc['cream_target_srgb']='#E9CFA0'
save(MASTER/'archer-plain.blend');save(MASTER/'archer.blend')
(MASTER/'model.json').write_text(json.dumps({'vertices':len(body.data.vertices),'bones':len(rig.data.bones),'objects':len(sc.objects)},indent=2));log('- Built MPFB archer, thick folded garments, lacing, bronze helmet, pale crest, sandals, quiver and bow; rest needs visual review.')
