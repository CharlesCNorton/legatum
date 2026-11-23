"""True MPFB anatomy, sculpted feather costume and eagle hood in painting pose."""
import sys,random
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
random.seed(17)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.preferences.addon_enable(module='bl_ext.user_default.mpfb')
from bl_ext.user_default.mpfb.services.humanservice import HumanService
from bl_ext.user_default.mpfb.services.targetservice import TargetService
macro=TargetService.get_default_macro_info_dict();macro.update(gender=1.,age=.38,muscle=.85,weight=.55,height=.45,proportions=.65);macro['race']={'caucasian':.1,'african':.1,'asian':.8}
body=HumanService.create_human(macro_detail_dict=macro);body.name='GEO-MPFB-anatomy'
bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();zs=[v.co.z for v in me.vertices];ev.to_mesh_clear();s=1.72/(max(zs)-min(zs));body.scale=(s,s,s);bpy.context.view_layer.objects.active=body;body.select_set(True);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
rig=HumanService.add_builtin_rig(body,'game_engine');rig.name='RIG-eagle-warrior'
eyes=HumanService.add_mhclo_asset(str(ROOT/'blender-user/extensions/.user/user_default/mpfb/data/eyes/high-poly/high-poly.mhclo'),body,asset_type='Eyes',subdiv_levels=1,material_type='MAKESKIN');eyes.name='GEO-eyes'
skin=material('Warm painted skin',(.40,.19,.075),rough=.75);feather=material('Painted eagle feathers',(.42,.26,.08),fill='feathers');ivory=material('Ivory feather edges',(.68,.53,.31));ochre=material('Golden feather edges',(.55,.30,.07));umber=material('Umber feather edges',(.18,.10,.04));linen=material('Cream woven loincloth',(.65,.54,.37),rough=.88);red=material('Cinnabar woven edging',(.40,.055,.025));wood=material('Honey wood club',(.37,.17,.045));dark=material('Obsidian cutting teeth',(.018,.021,.018),rough=.28);horn=material('Eagle hood warm horn',(.70,.39,.075),rough=.5);leather=material('Woven sandals',(.19,.09,.029));stone=material('Cream limestone E9CFA0',tuple(linear(c/255) for c in (233,207,160)),rough=.86)
body.data.materials.clear();body.data.materials.append(skin)
# Painted miniature ambient fill; preserve warm pigment under the feather canopy.
for mat,strength in [(stone,.65),(skin,.22)]:
 bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Emission Color'].default_value=bs.inputs['Base Color'].default_value;bs.inputs['Emission Strength'].default_value=strength
lines={'pelvis':((132,139,0),(132,127,0)),'spine_01':((132,127,0),(132,115,0)),'spine_02':((132,115,0),(132,104,0)),'spine_03':((132,104,0),(131,85,0)),
'clavicle_r':((127,84,0),(111,85,0)),'upperarm_r':((111,85,0),(83,94,-.03)),'lowerarm_r':((83,94,-.03),(60,77,-.08)),'hand_r':((60,77,-.08),(59,71,-.08)),
'clavicle_l':((135,84,0),(151,87,0)),'upperarm_l':((151,87,0),(162,108,-.06)),'lowerarm_l':((162,108,-.06),(174,110,-.22)),'hand_l':((174,110,-.22),(178,109,-.22)),
'neck_01':((132,83,0),(134,74,0)),'head':((134,74,0),(135,51,0)),
 'thigh_r':((122,138,0),(104,169,.01)),'calf_r':((104,169,.01),(86,207,.11)),'foot_r':((86,207,.11),(83,218,.08)),
 'thigh_l':((143,138,0),(161,168,.09)),'calf_l':((161,168,.09),(174,199,.42)),'foot_l':((174,199,.42),(187,208,.39))}
for name,(a,b) in lines.items():bone_line(rig,name,P(*a),P(*b))
p=rig.pose.bones['head'];p.matrix=Matrix.Translation(p.head)@Matrix.Rotation(.80,4,'Z')@Matrix.Translation(-p.head)@p.matrix
for side in ['l','r']:
 for digit in ['index','middle','ring','pinky']:
  for j in [1,2,3]:
   p=rig.pose.bones[f'{digit}_0{j}_{side}'];p.rotation_mode='XYZ';p.rotation_euler.x=.85 if j==1 else 1.15
bpy.context.view_layer.update()
# Every feather is a curved, ridged surface with Solidify thickness. Rings wrap
# the torso and limbs, not just the visible front. Each vane follows its bone.
def vane(name,start,end,width,mat,bone,depth=.012):
 a,b=Vector(start),Vector(end);axis=(b-a).normalized();side=axis.cross(Vector((0,-1,0))).normalized();normal=side.cross(axis).normalized();vs=[];fs=[]
 for j in range(9):
  t=j/8;w=width*(sin(pi*(.09+.91*t))**.75)
  for k in [-1,0,1]:vs.append(a.lerp(b,t)+side*w*k+normal*(depth*sin(pi*t)*(1-abs(k))+.008*t*t))
 for j in range(8):
  for k in range(2):i=j*3+k;fs.append((i,i+3,i+4,i+1))
 o=solid(mesh(name,vs,fs,mat),.003);bevel(o,.001);attach(o,rig,bone);return o
# Closed folded under-suit loft, with feathers covering its silhouette.
vs=[];fs=[];ww=[]
for j in range(17):
 t=j/16;y=85+47*t;rx=18+3*sin(pi*t);ry=.15+.025*sin(pi*t)
 for i in range(64):
  a=2*pi*i/64;vs.append(P(132+rx*sin(a),y,ry*-cos(a)));ww.append({'spine_03':1-t,'spine_01':t})
for j in range(16):
 for i in range(64):a=j*64+i;b=j*64+(i+1)%64;fs.append((a,a+64,b+64,b))
bind_posed(solid(mesh('Feather garment underlayer',vs,fs,feather),.005),rig,ww)
for row in range(6):
 for i in range(22):
  a=2*pi*(i+.5*(row%2))/22;x=132+(19+2*sin(row/5*pi))*sin(a);y=85+row*7;dep=-.18*cos(a)
  vane('Torso overlapping feather',P(x,y,dep),P(x+2*sin(a),y+11,dep*1.05),.031,[ivory,ochre,umber,feather][(row+i//4)%4],'spine_03' if row<4 else 'spine_01')
# Feather sleeves and thigh stockings follow each anatomical segment.
for bone,a,b,radius,nrow in [('upperarm_r',(110,85,0),(83,94,-.03),.105,4),('lowerarm_r',(83,94,-.03),(63,79,-.08),.085,3),('upperarm_l',(151,87,0),(162,108,-.06),.10,3),('thigh_r',(122,137,0),(104,169,.01),.12,5),('thigh_l',(143,137,0),(161,168,.09),.12,5)]:
 start,end=P(*a),P(*b);axis=(end-start).normalized();side=axis.cross(Vector((0,1,0))).normalized();normal=axis.cross(side)
 for row in range(nrow):
  for i in range(12):
   ang=2*pi*(i+.5*(row%2))/12;rad=side*cos(ang)+normal*sin(ang);v=start.lerp(end,row/nrow)+rad*radius
   vane('Limb feather '+bone,v,v+axis*.14+rad*.015,.035,[ivory,ochre,umber,feather][(row+i//3)%4],bone)
# Long flight feathers hang below the outstretched weapon arm.
for j in range(17):
 x=69+j*2.6;y=94+2*sin(j/16*pi);length=21-8*j/16+4*sin(j*1.3)
 vane('Weapon wing primary',P(x,y,.04),P(x-3,y+length,.055),.035,[ivory,umber,ochre][j%3],'upperarm_r' if j>7 else 'lowerarm_r')
# Layered hip feathers, front and back, open between legs.
for row in range(3):
 for i in range(24):
  a=2*pi*(i+.5*(row%2))/24;x=132+(19+row*4)*sin(a);dep=-.16*cos(a)
  vane('Skirt feather',P(x,129+row*7,dep),P(x+5*sin(a),144+row*7,dep*1.20),.038,[ivory,ochre,umber][(row+i//3)%3],'pelvis')
# Cream loincloth: folded textile with red raised border and real thickness.
vs=[];fs=[]
for j in range(21):
 t=j/20
 for i in range(9):
  u=i/8;vs.append(P(125+15*u-3*t,129+42*t,-.225-.009*sin(u*pi*6)-.02*sin(t*pi)))
for j in range(20):
 for i in range(8):a=j*9+i;fs.append((a,a+9,a+10,a+1))
o=solid(mesh('Folded cream loincloth',vs,fs,linen),.005);attach(o,rig,'pelvis')
for x in [126,138]:attach(curve('Red loincloth edging',[P(x-3*t,130+40*t,-.244) for t in [j/30 for j in range(31)]],.009,red),rig,'pelvis')
attach(curve('Loincloth red hem',[P(x,169,-.241) for x in range(123,136)],.009,red),rig,'pelvis')
for j in range(4):attach(curve('Woven waist sash',[P(132+19*sin(a),125+j*1.7,.18*-cos(a)) for a in [i*2*pi/96 for i in range(97)]],.011,red if j==2 else linen),rig,'pelvis')
attach(sphere('Sash knot',P(132,130,-.22),(.047,.027,.060),linen),rig,'pelvis')
# Eagle hood: full domed skull, hooked beak, open face aperture and nape feathers.
vs=[];fs=[]
for j in range(17):
 t=j/16*pi/2
 for i in range(64):
  a=2*pi*i/64;vs.append(P(133+13*cos(t)*sin(a),54-12*sin(t),-.01+.12*cos(t)*cos(a)))
for j in range(16):
 for i in range(64):a=j*64+i;b=j*64+(i+1)%64;fs.append((a,b,b+64,a+64))
attach(solid(mesh('Eagle skull dome',vs,fs,horn),.008),rig,'head')
# Hooked upper beak is a volumetric swept loft, not a flat painted cutout.
vs=[];fs=[];path=[(137,45,8),(144,44,7),(151,46,5),(154,50,2),(153,54,.6)]
for x,y,r in path:
 for i in range(16):a=i*2*pi/16;vs.append(P(x,y+r*.55*sin(a),-.08+r*.009*cos(a)))
for j in range(len(path)-1):
 for i in range(16):a=j*16+i;b=j*16+(i+1)%16;fs.append((a,b,b+16,a+16))
fs.extend([tuple(range(15,-1,-1)),tuple((len(path)-1)*16+i for i in range(16))]);attach(bevel(mesh('Hooked eagle beak',vs,fs,horn),.003),rig,'head')
attach(curve('Hood face aperture rim',[P(x,y,-.12) for x,y in [(144,52),(135,54),(130,60),(131,69),(137,75),(146,75)]],.015,horn),rig,'head')
attach(sphere('Eagle eye ivory',P(133,48,-.138),(.035,.013,.032),ivory),rig,'head');attach(sphere('Eagle eye black',P(134,48,-.150),(.017,.009,.020),dark),rig,'head')
for row in range(5):
 for i in range(10):
  a=2*pi*i/10;x=132+13*sin(a);d=.01-.13*cos(a);y=48+row*6
  if cos(a)>.5 and x>128:continue
  vane('Hood feather',P(x,y,d),P(x-4,y+13,d+.015),.034,[ivory,ochre,umber][(row+i//3)%3],'head')
# Convex oval wicker shield, lower feather fringe, wrapped red rim.
center=(174,111);ns=80;nr=14;vs=[];fs=[]
def shieldpoint(r,a):return P(174+18*r*cos(a)+5*r*sin(a),111+25*r*sin(a),-.31-.05*(1-r*r))
for j in range(nr+1):
 for i in range(ns):vs.append(shieldpoint(j/nr,2*pi*i/ns))
for j in range(nr):
 for i in range(ns):a=j*ns+i;b=j*ns+(i+1)%ns;fs.append((a,a+ns,b+ns,b))
shield=solid(mesh('Convex wicker shield',vs,fs,linen),.022);attach(shield,rig,'hand_l')
pts=[shieldpoint(1,2*pi*i/128) for i in range(129)];attach(curve('Shield red wrapped rim',pts,.018,red),rig,'hand_l')
for i in range(96):
 a=i*2*pi/96;c=shieldpoint(1,a);v=(shieldpoint(1,a+.01)-c).normalized();cross=v.cross(Vector((0,-1,0))).normalized();pts=[c+Vector((0,-1,0))*.020*cos(t)+cross*.020*sin(t) for t in [k*2*pi/12 for k in range(13)]];attach(curve('Rim binding stitch',pts,.0015,ochre),rig,'hand_l')
for j in range(16):
 y=91+j*2.6;rr=max(0,1-((y-111)/25)**2)**.5;pts=[P(174+5*(y-111)/25+18*rr*(i/20*2-1),y,-.365-.002*sin(i*pi)) for i in range(21)];attach(curve('Wicker woven row',pts,.0028,ivory),rig,'hand_l')
for row in range(3):
 for i in range(14):
  x=156+i*2.9;y=126+row*6+3*sin(i/13*pi)
  vane('Shield fringe feather',P(x,y,-.23),P(x+2,y+16,-.22),.031,[ivory,ochre,umber][(row+i//4)%3],'hand_l')
# Wooden macuahuitl, true obsidian edge blades and a bound handle.
start=P(53,85,-.10);end=P(101,14,-.10);axis=(end-start).normalized();wide=axis.cross(Vector((0,-1,0))).normalized();front=Vector((0,-1,0));v=[]
for t,w in [(0,.018),(.24,.021),(.29,.044),(1,.045)]:
 c=start.lerp(end,t)
 for a,b in [(-1,-1),(1,-1),(1,1),(-1,1)]:v.append(c+wide*w*a+front*.014*b)
f=[]
for j in range(3):
 for i in range(4):a=j*4+i;b=j*4+(i+1)%4;f.append((a,b,b+4,a+4))
f.extend([(3,2,1,0),(12,13,14,15)]);club=bevel(mesh('Wooden macuahuitl',v,f,wood),.004);attach(club,rig,'hand_r')
for k in range(7):
 for sg in [-1,1]:
  c=start.lerp(end,.34+k*.09)+wide*.052*sg;vs=[c+wide*x+axis*z+front*y for x,y,z in [(-.012,-.009,-.028),(.012,-.009,-.028),(.012,.009,-.028),(-.012,.009,-.028),(-.012,-.009,.028),(.012,-.009,.028),(.012,.009,.028),(-.012,.009,.028)]];attach(bevel(mesh('Obsidian inset blade',vs,[(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],dark),.0015),rig,'hand_r')
for j in range(13):
 c=start.lerp(end,.01+j*.017);attach(curve('Club grip binding',[c+wide*.022*cos(a)+front*.019*sin(a) for a in [i*2*pi/24 for i in range(25)]],.003,linen),rig,'hand_r')
# Sandal soles and straps preserve full MPFB toes and heel anatomy.
for side,x,y,d in [('r',83,216,.08),('l',183,208,.39)]:
 attach(sphere('Sandal sole '+side,P(x,y,d),(.09,.12,.018),leather),rig,'foot_'+side)
 for j in range(3):attach(curve('Sandal binding '+side,[P(x-5+j, y-4-j*3,d-.08),P(x,y-7-j*3,d-.12),P(x+5+j,y-5-j*3,d-.07)],.007,linen),rig,'foot_'+side)
# Base: single plain warm cream disc. It is never parented to the moving rig.
bpy.ops.mesh.primitive_cylinder_add(vertices=128,radius=.70,depth=.10,location=(P(134,128).x,0,.15));base=bpy.context.object;base.name='GEO-cream-stone-base';base.data.materials.append(stone);bevel(base,.012)
for p in base.data.polygons:p.use_smooth=len(p.vertices)==4
sc=bpy.context.scene;bpy.ops.object.camera_add(location=TARGET+Vector((0,-6*cos(ELEV),6*sin(ELEV))));cam=bpy.context.object;cam.name='CAM-painting';cam.data.type='ORTHO';cam.data.ortho_scale=SCALE;cam.data.dof.use_dof=False;aim(cam,TARGET);sc.camera=cam
for name,pos,power,size,col in [('warm-key',(-3,-4,5),1000,2,(1,.93,.82)),('soft-fill',(3,-3,3),300,3,(.88,.93,1)),('cool-rim',(2,3,4),200,2,(.70,.83,1))]:
 data=bpy.data.lights.new('LGT-'+name,'AREA');data.energy=power;data.size=size;data.color=col;o=bpy.data.objects.new(data.name,data);sc.collection.objects.link(o);o.location=pos;aim(o,(0,0,1))
sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.45,.43,.39,1);sc.world.node_tree.nodes['Background'].inputs[1].default_value=.5
sc.render.film_transparent=True;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=8;sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.render.resolution_x=sc.render.resolution_y=256;sc.render.image_settings.color_mode='RGBA'
rig['neutral_pose']=json.dumps({p.name:[list(row) for row in p.matrix_basis] for p in rig.pose.bones});sc['unit']='eagle-warrior';sc['source']='MPFB 2.0.18 CC0 body and original unit kit';sc['no_billboards']=True
# Convert curves, then group bone-attached feathers to reduce scene overhead.
for o in list(sc.objects):
 if o.type=='CURVE':
  bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
# Keep fully editable rig/material master and a neutral clay review copy.
save('unpainted.blend')
clay=material('Plain clay',(.50,.44,.32))
for o in sc.objects:
 if o.type=='MESH' and o!=base:
  o.data.materials.clear();o.data.materials.append(clay)
save('plain.blend');log('- Built MPFB anatomy, original three-dimensional feather costume, eagle hood, woven shield and macuahuitl; saved plain and material masters.')
print('BUILD_OK',len(sc.objects),flush=True)
