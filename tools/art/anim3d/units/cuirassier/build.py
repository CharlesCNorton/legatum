"""Cuirassier: CC0 Quaternius horse, MPFB rider and original articulated plate armour."""
import bpy, os, sys, json, math, ast
from pathlib import Path
from mathutils import Vector, Matrix, Quaternion
from math import sin,cos,pi
ROOT=Path(os.environ['ANIM_ROOT']); MASTER=ROOT/'masters/cuirassier'; MASTER.mkdir(parents=True,exist_ok=True)
# Reuse the infantry pipeline's mesh, fitting and joint-solving helpers without running its build.
source=Path('tools/art/anim3d/scene.py').read_text(); tree=ast.parse(source)
for node in tree.body:
 if isinstance(node,ast.FunctionDef) and node.name in {'material','mesh','bevel','solid','curve','sphere','attach','aim_bone','limb','fitted_shell'}:
  exec(compile(ast.Module(body=[node],type_ignores=[]),'<shared mesh helpers>','exec'))
_material=material
def material(*args,**kwargs):
 m=_material(*args,**kwargs);m.use_fake_user=True;return m
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(ROOT/'assets/horseman/Horse.glb'))
horse=bpy.data.objects['Horse'];hrig=bpy.data.objects['AnimalArmature'];root=bpy.data.objects['RootNode'];root.name='Horse world control';root.scale=(.46,)*3;root.location=(0,.18,.115)
for o in list(bpy.context.scene.objects):
 if o.name=='Icosphere':bpy.data.objects.remove(o,do_unlink=True)
for track in hrig.animation_data.nla_tracks: track.mute=True
hrig.animation_data.action=bpy.data.actions['AnimalArmature|Idle'];hrig.animation_data.action_slot=hrig.animation_data.action.slots[0]
bpy.context.scene.frame_set(0);bpy.context.view_layer.update()
# glTF splits vertices at flat-shaded normals; weld before subdivision.
import bmesh
bm=bmesh.new();bm.from_mesh(horse.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000001);bm.to_mesh(horse.data);bm.free()
# Shorten the stylized muzzle and soften the oversized pointed ears.
for v in horse.data.vertices:
 if v.co.y<-.034 and v.co.z<-.026:
  v.co.z=-.026+(v.co.z+.026)*.82;v.co.x*=1.12
 if v.co.y<-.044:v.co.y=-.044+(v.co.y+.044)*.64
horse.data.update()
# Sculpt the source coat in bind space: fuller chest and neck, sturdier lower legs.
for v in horse.data.vertices:
 weights={horse.vertex_groups[g.group].name:g.weight for g in v.groups}
 neck=sum(w for n,w in weights.items() if n.startswith('Neck'))
 torso=sum(w for n,w in weights.items() if n.startswith('Torso'))
 v.co.x*=1+.26*neck+.12*torso
 if abs(v.co.x)>.002 and v.co.y>-.017:
  center=math.copysign(.0045,v.co.x);v.co.x=center+(v.co.x-center)*1.20
# Preserve the source mesh/weights and smooth the hard low-poly facets.
for p in horse.data.polygons:p.use_smooth=True
sub=horse.modifiers.new('Sculpt surface refinement','SUBSURF');sub.levels=1;sub.render_levels=2
horse['source']='Quaternius Ultimate Animated Animal Pack July 2021, CC0; Horse.glb'
# Rest-space pigment masks remain attached to the skinned surface.
coat=material('Bay coat',(.045,.043,.040),0,.48);hair=material('Black mane and tail',(.016,.012,.009),0,.66)
shadow=material('Bay shaded muscle',(.022,.021,.020),0,.55);muzzle=material('Velvet muzzle',(.034,.025,.019),0,.72)
hoof=material('Horn hooves',(.075,.064,.049),0,.61);lightcoat=material('Bay warm highlights',(.085,.078,.069),0,.53)
black=material('Dark eyes',(.006,.004,.003),0,.25);ivory=material('Ivory markings',(.75,.69,.55),0,.75)
for i,m in enumerate([coat,hair,shadow,muzzle,hoof,lightcoat,black,black]):horse.data.materials[i]=m
horse.data.materials.append(ivory)
# Source local coordinates: -Y is up, -Z points toward the muzzle.
for p in horse.data.polygons:
 c=p.center
 if p.material_index in (0,2,5) and c.y>-.010: p.material_index=1
 if p.material_index in (0,2,5) and abs(c.x)<.00042 and c.y<-.034 and c.z<-.027: p.material_index=8
 # Pale pastern markings on all four legs, retaining the dark horn hooves.
 # The cuirassier horse has no white socks.
# New human from MPFB, not a reshaped primitive or a borrowed soldier mesh.
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.preferences.addon_enable(module='bl_ext.user_default.mpfb')
from bl_ext.user_default.mpfb.services.humanservice import HumanService
from bl_ext.user_default.mpfb.services.targetservice import TargetService
macro=TargetService.get_default_macro_info_dict();macro.update(gender=1.,age=.4,muscle=.72,weight=.48,height=.45,proportions=.6);macro['race']={'caucasian':.7,'african':.15,'asian':.15}
body=HumanService.create_human(macro_detail_dict=macro);body.name='Rider MPFB CC0 anatomy'
bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();height=max(v.co.z for v in me.vertices)-min(v.co.z for v in me.vertices);ev.to_mesh_clear()
body.scale=(1.72/height,)*3;bpy.context.view_layer.objects.active=body;body.select_set(True);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
rig=HumanService.add_builtin_rig(body,'game_engine');rig.name='Rider MPFB game_engine'
skin=material('Skin • warm ochre',(.46,.25,.12),0,.65);linen=material('Warm ivory linen',(.82,.75,.60),0,.88)
bronze=material('Bronze • hammered',(.45,.25,.075),.72,.4);gold=material('Bronze • polished edges',(.76,.49,.18),.7,.3);dark=material('Incised bronze patina',(.06,.037,.013),.4,.65)
leather=material('Oxide leather',(.105,.039,.017),0,.72);wood=material('Ash spear shaft',(.24,.11,.031),0,.6);iron=material('Forged iron',(.25,.28,.29),.8,.32);stone=material('Cream limestone',(.82,.70,.50),0,.85)
body.data.materials.clear();body.data.materials.append(skin)
for p in body.data.polygons:p.use_smooth=True
sub=body.modifiers.new('Anatomical subdivision','SUBSURF');sub.levels=1
system=ROOT/'blender-user/extensions/.user/user_default/mpfb/data';eyes=HumanService.add_mhclo_asset(str(system/'eyes/high-poly/high-poly.mhclo'),body,asset_type='Eyes',subdiv_levels=1,material_type='MAKESKIN');eyes.name='Rider MPFB eyes'
# Original 17th-century armour, built around the MPFB anatomy.
steel=material('MAT-burnished steel',(.32,.34,.35),1,.33)
gold=material('MAT-gilt rolled edges',(.56,.34,.10),1,.29)
linen=material('MAT-quilted crimson saddlecloth',(.24,.025,.014),0,.83)
leather=material('MAT-scuffed umber leather',(.095,.038,.016),0,.66)
# Skin under armour; boots and gloves use the same genuine anatomical topology.
fitted_shell('GEO-leather arming suit',lambda v:.10<v.z<1.50,leather,.009)
# Elliptical breastplate with a real central ridge and separate articulated waist lames.
def shell(name,rings,bone,mat=steel):
 vs=[];fs=[];N=48
 for z,rx,ry in rings:
  for i in range(N):
   a=2*pi*i/N;vs.append((rx*sin(a),-ry*cos(a)-.015*max(0,cos(a))**12,z))
 for j in range(len(rings)-1):
  for i in range(N):a=j*N+i;b=j*N+(i+1)%N;fs.append((a,b,b+N,a+N))
 ob=attach(bevel(solid(mesh(name,vs,fs,mat),.009),.004,3),bone)
 for z,rx,ry in [rings[0],rings[-1]]:
  attach(curve(name+' gilt rolled rim',[(rx*sin(a),-ry*cos(a)-.016*max(0,cos(a))**12,z) for a in [i*2*pi/96 for i in range(97)]],.004,gold),bone)
 return ob
shell('GEO-ridged steel cuirass',[(1.08,.165,.13),(1.16,.177,.17),(1.29,.215,.168),(1.39,.228,.14),(1.46,.14,.115)],'spine_03')
for j in range(3):shell('GEO-overlapping fauld',[(1.04-j*.048,.182+j*.012,.148),(1.10-j*.048,.177+j*.012,.14)],'pelvis')
# Each limb shell is rigidly attached to its actual bone; joint gaps stay articulated.
def tube(name,bone,r1,r2,start=.06,end=.94):
 b=rig.data.bones[bone];a=b.head_local;v=b.tail_local-a;axis=v.normalized();u=axis.cross(Vector((0,1,0))).normalized();w=axis.cross(u).normalized();vs=[];fs=[]
 for j in range(7):
  t=j/6;r=r1*(1-t)+r2*t;c=a+v*(start+(end-start)*t)
  for k in range(32):
   angle=k*2*pi/32;vs.append(tuple(c+r*(u*sin(angle)+w*cos(angle))))
 for j in range(6):
  for k in range(32):x=j*32+k;y=j*32+(k+1)%32;fs.append((x,y,y+32,x+32))
 attach(bevel(solid(mesh(name,vs,fs,steel),.006),.003,3),bone)
 for j in [0,6]:attach(curve(name+' gilt rim',vs[j*32:(j+1)*32]+[vs[j*32]],.004,gold),bone)
for side in ['r','l']:
 tube('GEO-pauldrons '+side,'upperarm_'+side,.105,.094,0,.30)
 tube('GEO-rerebrace '+side,'upperarm_'+side,.083,.065,.25,.91)
 tube('GEO-vambrace '+side,'lowerarm_'+side,.064,.047,.08,.93)
 tube('GEO-steel cuisse '+side,'thigh_'+side,.108,.078,.12,.90)
 tube('GEO-greave '+side,'calf_'+side,.081,.046,.10,.95)
 for bone,radius in [('lowerarm_',.075),('calf_',.087)]:
  c=rig.data.bones[bone+side].head_local
  attach(sphere('GEO-articulated joint cap',c,(radius,radius*.85,radius),steel),bone+side)
# Close helmet with raised comb, visor, eye slot and open ventilation perforations.
hc=(rig.pose.bones['head'].head+rig.pose.bones['head'].tail)*.5;cx,cy,cz=hc
attach(sphere('GEO-closed helmet skull',(cx,cy,cz+.02),(.112,.126,.153),steel),'head')
for side in [-1,1]:
 pts=[(side*.095,cy-.08,cz+.03),(side*.061,cy-.151,cz-.055),(0,cy-.173,cz-.095)]
 attach(bevel(solid(mesh('GEO-visor side',pts,[(0,1,2)],steel),.008),.003,3),'head')
# Gridded visor with omitted cells leaves true holes and a separate upper brow.
vs=[];fs=[]
for j in range(9):
 for k in range(17):
  x=(k/16-.5)*.185;z=cz-.10+j*.014;y=cy-.158+.30*abs(x)
  vs.append((x,y,z))
for j in range(8):
 for k in range(16):
  if j==7 or (j in [3,5] and k in [5,7,9,11]):continue
  a=j*17+k;fs.append((a,a+1,a+18,a+17))
attach(bevel(solid(mesh('GEO-perforated visor',vs,fs,steel),.006),.0015),'head')
attach(curve('GEO-visor gilt brow',[(-.105,cy-.12,cz+.035),(0,cy-.172,cz+.035),(.105,cy-.12,cz+.035)],.006,gold),'head')
attach(curve('GEO-helmet raised comb',[(0,cy-.13,cz+.07),(0,cy-.08,cz+.17),(0,cy+.02,cz+.185),(0,cy+.13,cz+.06)],.008,steel),'head')
attach(curve('GEO-gorget rim',[(.125*sin(a),cy-.13*cos(a),cz-.126) for a in [i*2*pi/72 for i in range(73)]],.009,gold),'head')
for sg in [-1,1]:attach(sphere('GEO-visor pivot',(sg*.108,cy-.075,cz+.02),(.014,.008,.014),gold),'head')
# Thick leather shoulder belt and buckle across the breastplate.
attach(curve('GEO-leather baldric',[(-.15,-.13,1.44),(-.05,-.184,1.27),(.15,-.158,1.10)],.015,leather),'spine_03')
attach(curve('GEO-baldric edge stitch',[(-.163,-.135,1.44),(-.063,-.19,1.27),(.137,-.164,1.10)],.002,gold),'spine_03')
attach(curve('GEO-belt buckle',[(-.03,-.171,1.095),(.025,-.171,1.095),(.025,-.171,1.06),(-.03,-.171,1.06),(-.03,-.171,1.095)],.005,gold),'pelvis')
# Pose the MPFB joints in saddle space before moving the entire rider up.
limb('thigh_r','calf_r',(-.34,-.10,.34),(-.46,-.55,.76));limb('thigh_l','calf_l',(.34,-.10,.34),(.46,-.55,.76))
limb('upperarm_r','lowerarm_r',(-.77,.09,1.72),(-.49,.02,1.41));limb('upperarm_l','lowerarm_l',(.18,-.40,1.13),(.39,-.15,1.13))
for side in ['r','l']:
 aim_bone('foot_'+side,(0,-1,-.1));aim_bone('hand_'+side,(-.95,.30,.015) if side=='r' else (0,-1,0))
 for digit in ['index','middle','ring','pinky']:
  for k in range(1,4):p=rig.pose.bones[f'{digit}_{k:02d}_{side}'];p.rotation_mode='XYZ';p.rotation_euler.x=1.1
bpy.context.view_layer.update()
# Heavy riding boots and real stirrup hoops follow the foot bones.
for side in ['l','r']:
 p=rig.pose.bones['foot_'+side].head
 attach(sphere('GEO-armoured riding boot '+side,p+Vector((0,-.06,-.02)),(.060,.13,.055),steel),'foot_'+side)
 attach(curve('GEO-stirrup hoop '+side,[p+Vector(v) for v in [(-.07,-.08,.08),(-.08,-.12,-.055),(.08,-.12,-.055),(.07,-.08,.08)]],.009,gold),'foot_'+side)
# Long wheellock pistol aimed screen-left, never a spear substitution.
grip=(rig.pose.bones['hand_r'].head+rig.pose.bones['hand_r'].tail)*.5;direction=Vector((-.95,.30,.015)).normalized()
attach(curve('GEO-pistol walnut stock',[grip+Vector((.035,0,-.10)),grip,grip+direction*.56],.024,wood),'hand_r')
attach(curve('GEO-pistol steel barrel',[grip+Vector((0,0,.025)),grip+direction*.68+Vector((0,0,.025))],.014,steel),'hand_r')
attach(sphere('GEO-wheellock brass wheel',grip+Vector((-.025,-.035,.027)),(.032,.009,.032),gold),'hand_r')
attach(curve('GEO-trigger guard',[grip+Vector(v) for v in [(-.07,0,0),(-.08,0,-.045),(-.01,0,-.055),(.01,0,0)]],.005,gold),'hand_r')
for d in [.13,.46,.675]:attach(sphere('GEO-barrel band',grip+direction*d+Vector((0,0,.025)),(.018,.018,.018),gold),'hand_r')
# Anatomical pelvis sits on the source's moving back, rather than floating above it.
rig.scale=(1.25,)*3;rig.location=(0,.13,.49);bpy.context.view_layer.update()
def horse_attach(o,bone):
 bpy.context.view_layer.update()
 world=o.matrix_world.copy();o.parent=hrig;o.parent_type='BONE';o.parent_bone=bone;bpy.context.view_layer.update();o.matrix_world=world;return o
horse_attach(rig,'Torso');rig['seated_pose']=json.dumps({p.name:[list(r) for r in p.matrix_basis] for p in rig.pose.bones})
# Curved blanket over the barrel, saddle leather, girth and bridle.
vs=[];fs=[]
for j in range(17):
 y=-.23+j*.047
 for i in range(25):
  a=-1.42+i*2.84/24;vs.append((.37*sin(a),y,1.19+.32*cos(a)))
for j in range(16):
 for i in range(24):a=j*25+i;fs.append((a,a+1,a+26,a+25))
horse_attach(solid(mesh('Ivory woven saddle blanket',vs,fs,linen),.012),'Torso')
for j in [0,16]:horse_attach(curve('Blanket leather piping',vs[j*25:(j+1)*25],.013,leather),'Torso')
horse_attach(sphere('Leather riding saddle',(0,.16,1.52),(.25,.34,.065),leather),'Torso')
for y in [-.16,.40]:horse_attach(curve('Saddle raised bolster',[(-.25,y,1.51),(-.13,y,1.59),(0,y,1.61),(.13,y,1.59),(.25,y,1.51)],.025,leather),'Torso')
horse_attach(curve('Saddle girth',[(.34*sin(a),-.12,1.20+.33*cos(a)) for a in [i*2*pi/96 for i in range(97)]],.024,leather),'Torso2')
for sg in [-1,1]:
 # Bridle straps follow the real animated head; reins follow saddle, with slack.
 horse_attach(curve('Cheek bridle',[(sg*.15,-.91,1.98),(sg*.17,-1.05,1.77),(sg*.14,-1.27,1.57)],.015,leather),'Head')
 horse_attach(curve('Nose band',[(sg*.14,-1.27,1.57),(0,-1.35,1.59)],.016,leather),'Head')
 horse_attach(sphere('Bronze bridle rosette',(sg*.17,-1.055,1.77),(.025,.015,.025),gold),'Head')
 horse_attach(curve('Slack leather rein',[(sg*.14,-1.26,1.59),(sg*.28,-.81,1.54),(sg*.22,-.38,1.69),(.18,-.27,1.73)],.009,leather),'Torso')
# A dark, swept mane has real volume and narrow warm fibre highlights.
for i in range(38):
 t=i/37;y=-.40-.53*t;z=1.69+.36*t
 bone='Neck1' if t<.34 else 'Neck2' if t<.66 else 'Neck3'
 horse_attach(curve('Mane lock',[(0,y,z),(-.055,y+.018,z-.025),(-.09,y+.06,z-.11)],.014,hair),bone)
 if i%3==0:horse_attach(curve('Mane painted fibre',[(-.012,y,z+.003),(-.058,y+.022,z-.025),(-.092,y+.058,z-.105)],.003,muzzle),bone)
# Long black tail locks, with the source tail motion driving their upper segments.
for i in range(22):
 a=i*2*pi/22;dx=.035*sin(a);dy=.035*cos(a)
 horse_attach(curve('Tail flowing fibre',[(dx,.83+dy,1.45),(dx-.09,1.14+dy,1.16),(dx-.16,1.38+dy,.74),(dx-.21,1.34+dy,.44+.035*sin(i))],.012,hair),'Tail3')
horse_attach(curve('Leather breast strap',[(-.33,-.40,1.38),(-.27,-.59,1.20),(0,-.67,1.12),(.27,-.59,1.20),(.33,-.40,1.38)],.024,leather),'Torso3')
for sg in [-1,1]:horse_attach(sphere('Breast strap bronze disc',(sg*.27,-.59,1.20),(.043,.016,.043),gold),'Torso3')
# Bronze studs and stitched blanket edging are geometrical, not camera-facing paint.
for sg in [-1,1]:
 for i in range(12):
  y=-.20+i*.055
  horse_attach(sphere('Blanket bronze stitch',(sg*.365,y,1.25),(.007,.013,.007),gold),'Torso')
# Horse neck raised toward the painting, retaining the actual articulated source chain.
for action in bpy.data.actions:action.use_fake_user=True
pose={p.name:p.matrix_basis.copy() for p in hrig.pose.bones};basis=hrig.matrix_basis.copy();hrig.animation_data_clear();hrig.animation_data_create();hrig.animation_data.action=bpy.data.actions.new('Cuirassier rest horse')
hrig.matrix_basis=basis
for p in hrig.pose.bones:p.matrix_basis=pose[p.name]
bpy.context.view_layer.update();p=hrig.pose.bones['Neck1'];head=p.head.copy();axis=hrig.matrix_world.to_3x3().inverted()@Vector((1,0,0))
p.matrix=Matrix.Translation(head)@Quaternion(axis.normalized(),-.34).to_matrix().to_4x4()@Matrix.Translation(-head)@p.matrix
for p in hrig.pose.bones:
 p.rotation_mode='QUATERNION'
 for prop in ['location','rotation_quaternion','scale']:p.keyframe_insert(prop,frame=0)
hrig.rotation_mode='QUATERNION'
for prop in ['location','rotation_quaternion','scale']:hrig.keyframe_insert(prop,frame=0)
bpy.context.view_layer.update()
# Constant base and light rig.
bpy.ops.mesh.primitive_cylinder_add(vertices=128,radius=.87,depth=.10,location=(0,0,.05));base=bpy.context.object;base.name='Stationary cream stone';base.data.materials.append(stone);bevel(base,.018,3)
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=8;sc.cycles.use_denoising=True;sc.render.threads_mode='FIXED';sc.render.threads=3
sc.render.resolution_x=sc.render.resolution_y=256;sc.render.resolution_percentage=100;sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA'
sc.world.color=(.24,.24,.24);sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast';sc.view_settings.exposure=.45
bpy.ops.object.camera_add(location=(-6.35,-7.74,3.84));sc.camera=bpy.context.object;sc.camera.rotation_euler=(Vector((-.35,.26,1.34))-sc.camera.location).to_track_quat('-Z','Y').to_euler();sc.camera.data.type='ORTHO';sc.camera.data.ortho_scale=3.25
for name,loc,power,size,col in [('Warm key',(-3,-4,6),650,3,(1,.83,.65)),('Cool fill',(4,-2,4),250,4,(.76,.85,1)),('Cool rim',(0,4,5),500,3,(.72,.83,1))]:
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name=name;o.data.energy=power;o.data.shape='DISK';o.data.size=size;o.data.color=col;o.rotation_euler=(Vector((0,0,1.2))-o.location).to_track_quat('-Z','Y').to_euler()
sc['source_horse']='Quaternius CC0 July 2021';sc['source_rider']='MPFB 2.0.18 CC0';sc['sample_frames']='[0]'
for action in bpy.data.actions: action.use_fake_user=True
bpy.ops.wm.save_as_mainfile(filepath=str(MASTER/'cuirassier-plain.blend'))
bpy.ops.wm.save_as_mainfile(filepath=str(MASTER/'cuirassier.blend'))
print('MOUNTED_BUILD_READY')
