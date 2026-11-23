"""Cavalry round one, true geometry: CC0 Quaternius horse plus MPFB anatomical rider."""
import bpy, os, sys, json, math, ast
from pathlib import Path
from mathutils import Vector, Matrix
from math import sin,cos,pi
ROOT=Path(os.environ['ANIM_ROOT']); MASTER=ROOT/'masters/cavalry'; MASTER.mkdir(parents=True,exist_ok=True)
# Reuse the infantry pipeline's mesh, fitting and joint-solving helpers without running its build.
source=Path('tools/art/anim3d/scene.py').read_text(); tree=ast.parse(source)
for node in tree.body:
 if isinstance(node,ast.FunctionDef) and node.name in {'material','mesh','bevel','solid','curve','sphere','attach','aim_bone','limb','fitted_shell'}:
  exec(compile(ast.Module(body=[node],type_ignores=[]),'<shared mesh helpers>','exec'))
_material=material
def material(*args,**kwargs):
 m=_material(*args,**kwargs);m.use_fake_user=True;return m
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(ROOT/'assets/cavalry/Horse.glb'))
horse=bpy.data.objects['Horse'];hrig=bpy.data.objects['AnimalArmature'];root=bpy.data.objects['RootNode'];root.name='Horse world control';root.scale=(.43,)*3;root.location=(0,.18,.115)
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
for v in horse.data.vertices:
 neck=sum(g.weight for g in v.groups if horse.vertex_groups[g.group].name.startswith('Neck'))
 v.co.x*=1+.12*neck
horse.data.update()
# Preserve the source mesh/weights and smooth the hard low-poly facets.
for p in horse.data.polygons:p.use_smooth=True
sub=horse.modifiers.new('Sculpt surface refinement','SUBSURF');sub.levels=1;sub.render_levels=1
horse['source']='Quaternius Ultimate Animated Animal Pack July 2021, CC0; Horse.glb'
# Rest-space pigment masks remain attached to the skinned surface.
coat=material('Bay coat',(.27,.085,.022),0,.48);hair=material('Black mane and tail',(.016,.012,.009),0,.66)
shadow=material('Bay shaded muscle',(.16,.041,.012),0,.55);muzzle=material('Velvet muzzle',(.034,.025,.019),0,.72)
hoof=material('Horn hooves',(.075,.064,.049),0,.61);lightcoat=material('Bay warm highlights',(.36,.13,.038),0,.53)
black=material('Dark eyes',(.006,.004,.003),0,.25);ivory=material('Ivory markings',(.75,.69,.55),0,.75)
for i,m in enumerate([coat,hair,shadow,muzzle,hoof,lightcoat,black,black]):horse.data.materials[i]=m
horse.data.materials.append(ivory)
# Source local coordinates: -Y is up, -Z points toward the muzzle.
for p in horse.data.polygons:
 c=p.center
 if p.material_index in (0,2,5) and c.y>-.010: p.material_index=1
 if p.material_index in (0,2,5) and abs(c.x)<.00042 and c.y<-.034 and c.z<-.027: p.material_index=8
 # Pale pastern markings on all four legs, retaining the dark horn hooves.
 if abs(c.x)>.002 and -.006<c.y<-.0028 and p.material_index!=4:p.material_index=8
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
skin=material('Skin • warm ochre',(.46,.25,.12),0,.65);linen=material('Warm ivory linen',(.018,.035,.065),0,.88)
bronze=material('Bronze • hammered',(.45,.25,.075),1,.4);gold=material('Bronze • polished edges',(.76,.49,.18),1,.3);dark=material('Incised bronze patina',(.06,.037,.013),.4,.65)
leather=material('Oxide leather',(.105,.039,.017),0,.72);wood=material('Ash spear shaft',(.24,.11,.031),0,.6);iron=material('Forged iron',(.55,.59,.63),1,.32);stone=material('Cream limestone',(.815,.624,.352),0,.85)
body.data.materials.clear();body.data.materials.append(skin)
for p in body.data.polygons:p.use_smooth=True
sub=body.modifiers.new('Anatomical subdivision','SUBSURF');sub.levels=1
system=ROOT/'blender-user/extensions/.user/user_default/mpfb/data';eyes=HumanService.add_mhclo_asset(str(system/'eyes/high-poly/high-poly.mhclo'),body,asset_type='Eyes',subdiv_levels=1,material_type='MAKESKIN');eyes.name='Rider MPFB eyes'
# Uniform shells retain real MPFB anatomy and transferred weights.
fitted_shell('GEO-navy-jacket',lambda v:1.00<v.z<1.475,linen,.020)
pants=material('Navy riding trousers',(.025,.045,.075),0,.88)
boots=material('Black polished riding leather',(.012,.016,.019),0,.44)
buff=material('Buff crossbelt',(.43,.27,.12),0,.75)
fitted_shell('GEO-trousers',lambda v:.46<v.z<1.04,pants,.015)
fitted_shell('GEO-tall-boots',lambda v:v.z<.56,boots,.015)
# Moustache follows the MPFB face; no primitive replacement head.
fitted_shell('GEO-moustache',lambda v:1.545<v.z<1.574 and v.y<-.075 and abs(v.x)<.052,hair,.003)
for j in range(7):
 attach(sphere('GEO-brass-button',(0,-.16,1.12+j*.044),(.009,.008,.009),gold),'spine_03')
for sg in [-1,1]:
 attach(curve('GEO-jacket-piping',[(sg*.10,-.14,1.40),(sg*.12,-.17,1.28),(sg*.10,-.15,1.07)],.004,gold),'spine_03')
 for j in range(4):
  attach(curve('GEO-jacket-fold',[(sg*.17,-.12,1.18+j*.05),(sg*.11,-.164,1.16+j*.05),(sg*.06,-.17,1.17+j*.05)],.005,linen),'spine_03')
# Thick, bevelled flat straps and a real buckle, fitted to the torso.
for sg in [-1,1]:
 vs=[(sg*x+q*.018,y,z) for x,y,z in [(-.16,-.10,1.45),(-.10,-.168,1.36),(.02,-.175,1.23),(.15,-.15,1.08)] for q in [-1,1]]
 attach(bevel(solid(mesh('GEO-buff-crossbelt',vs,[(0,1,3,2),(2,3,5,4),(4,5,7,6)],buff),.008),.003),'spine_03')
attach(curve('GEO-waist-belt',[(.19*sin(a),-.145*cos(a),1.065) for a in [i*2*pi/80 for i in range(81)]],.018,boots),'pelvis')
attach(curve('GEO-belt-buckle',[(-.026,-.165,1.04),(.026,-.165,1.04),(.026,-.165,1.085),(-.026,-.165,1.085),(-.026,-.165,1.04)],.005,gold),'pelvis')
# Tailored navy kepi with crown, band, curved black visor and brass chin cord.
hc=(rig.pose.bones['head'].head+rig.pose.bones['head'].tail)*.5;cx,cy,cz=hc
vs=[];fs=[]
for j,(rx,ry,z) in enumerate([(.106,.116,cz+.020),(.108,.12,cz+.045),(.100,.109,cz+.120),(.085,.095,cz+.134)]):
 for i in range(64):
  a=i*2*pi/64;vs.append((cx+rx*sin(a),cy-ry*cos(a),z+.012*cos(a)))
for j in range(3):
 for i in range(64):a=j*64+i;b=j*64+(i+1)%64;fs.append((a,b,b+64,a+64))
fs.append(tuple(range(192,256)))
attach(bevel(solid(mesh('GEO-kepi-crown',vs,fs,linen),.006),.004),'head')
for z in [cz+.025,cz+.049]:attach(curve('GEO-kepi-gold-piping',[(cx+.108*sin(a),cy-.12*cos(a),z+.012*cos(a)) for a in [i*2*pi/96 for i in range(97)]],.003,gold),'head')
vs=[(cx+rx*sin(a),cy-ry*cos(a),cz+.020-.024*cos(a)) for rx,ry in [(.106,.12),(.125,.177)] for a in [-1.3+i*2.6/32 for i in range(33)]]
attach(bevel(solid(mesh('GEO-kepi-visor',vs,[(i,i+1,i+34,i+33) for i in range(32)],boots),.006),.003),'head')
attach(sphere('GEO-kepi-brass-stud',(cx,cy-.124,cz+.068),(.009,.006,.012),gold),'head')
# Pose the MPFB joints in saddle space before moving the entire rider up.
limb('thigh_r','calf_r',(-.34,-.10,.34),(-.46,-.55,.76));limb('thigh_l','calf_l',(.34,-.10,.34),(.46,-.55,.76))
limb('upperarm_r','lowerarm_r',(-.85,.08,1.62),(-.52,.08,1.43));limb('upperarm_l','lowerarm_l',(.18,-.40,1.13),(.39,-.15,1.13))
for side in ['r','l']:
 aim_bone('foot_'+side,(0,-1,-.1));aim_bone('hand_'+side,(0,0,1))
 for digit in ['index','middle','ring','pinky']:
  for k in range(1,4):p=rig.pose.bones[f'{digit}_{k:02d}_{side}'];p.rotation_mode='XYZ';p.rotation_euler.x=1.1
bpy.context.view_layer.update()
# Curved steel cavalry sabre, solid diamond section and brass knuckle bow.
grip=rig.pose.bones['hand_r'].head+Vector((0,-.025,.035))
direction=Vector((0,-.70,.72)).normalized();wide=Vector((1,0,0));thin=direction.cross(wide).normalized()
attach(curve('GEO-sabre-grip',[grip-direction*.055,grip+direction*.08],.016,boots),'hand_r')
start=grip+direction*.10;vs=[];fs=[]
for j in range(25):
 t=j/24;c=start+direction*(.55*t)+wide*(.15*t*t);w=.033*(1-.88*t)
 for v in [wide*w,thin*.005,-wide*w,-thin*.005]:vs.append(tuple(c+v))
for j in range(24):
 for k in range(4):a=j*4+k;b=j*4+(k+1)%4;fs.append((a,b,b+4,a+4))
fs.extend([(0,3,2,1),(96,97,98,99)])
attach(bevel(mesh('GEO-sabre-blade',vs,fs,iron),.0015,2),'hand_r')
attach(curve('GEO-sabre-guard',[grip+direction*.09-wide*.065,grip+direction*.09+wide*.055,grip+wide*.075-direction*.025,grip-direction*.065],.007,gold),'hand_r')
# Anatomical pelvis sits on the source's moving back, rather than floating above it.
rig.scale=(1.13,)*3;rig.location=(0,.13,.432);bpy.context.view_layer.update()
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
horse_attach(solid(mesh('GEO-navy-saddle-blanket',vs,fs,linen),.012),'Torso')
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
horse_attach(curve('Leather breast strap',[(-.33,-.40,1.38),(-.27,-.59,1.20),(0,-.67,1.12),(.27,-.59,1.20),(.33,-.40,1.38)],.024,leather),'Torso3')
for sg in [-1,1]:horse_attach(sphere('Breast strap bronze disc',(sg*.27,-.59,1.20),(.043,.016,.043),gold),'Torso3')
# Bronze studs and stitched blanket edging are geometrical, not camera-facing paint.
for sg in [-1,1]:
 for i in range(12):
  y=-.20+i*.055
  horse_attach(sphere('Blanket bronze stitch',(sg*.365,y,1.25),(.007,.013,.007),gold),'Torso')
# Stirrups hang from the saddle beside the boots, with real leather thickness.
for sg in [-1,1]:
 horse_attach(curve('GEO-stirrup-leather',[(sg*.26,.04,1.52),(sg*.39,-.05,.77)],.014,boots),'Torso')
 horse_attach(curve('GEO-steel-stirrup',[(sg*.39,-.05,.79),(sg*.46,-.09,.65),(sg*.46,-.24,.64),(sg*.39,-.24,.79),(sg*.39,-.05,.79)],.012,iron),'Torso')
 horse_attach(sphere('GEO-leather-saddle-bag',(sg*.32,.48,1.34),(.12,.15,.15),leather),'Torso')
# Source idle foreleg lifted from walk, preserving real joint geometry.
for action in bpy.data.actions:action.use_fake_user=True
hrig.animation_data.action=bpy.data.actions['AnimalArmature|Walk'];hrig.animation_data.action_slot=hrig.animation_data.action.slots[0];bpy.context.scene.frame_set(19)
raised={p.name:p.matrix_basis.copy() for p in hrig.pose.bones if p.name.endswith('.R') and p.name.split('.')[0] in ['FrontShoulder','FrontUpperLeg','FrontLowerLeg','IKFrontLeg','FF','PoleTarget']}
hrig.animation_data.action=bpy.data.actions['AnimalArmature|Idle'];hrig.animation_data.action_slot=hrig.animation_data.action.slots[0];bpy.context.scene.frame_set(0)
rest={p.name:p.matrix_basis.copy() for p in hrig.pose.bones};rest.update(raised);obmat=hrig.matrix_basis.copy();hrig.animation_data_clear();hrig.animation_data_create();hrig.animation_data.action=bpy.data.actions.new('Cavalry rest')
hrig.matrix_basis=obmat
for p in hrig.pose.bones:
 p.matrix_basis=rest[p.name];p.rotation_mode='QUATERNION'
 for prop in ['location','rotation_quaternion','scale']:p.keyframe_insert(prop,frame=0)
hrig['raised_idle_foreleg']=json.dumps({n:[list(row) for row in v] for n,v in raised.items()})
bpy.context.scene.frame_set(0);bpy.context.view_layer.update()
# Constant base and light rig.
bpy.ops.mesh.primitive_cylinder_add(vertices=128,radius=.90,depth=.10,location=(0,0,.05));base=bpy.context.object;base.name='Stationary cream stone';base.data.materials.append(stone);bevel(base,.018,3)
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=8;sc.cycles.use_denoising=True;sc.render.threads_mode='FIXED';sc.render.threads=3
sc.render.resolution_x=sc.render.resolution_y=256;sc.render.resolution_percentage=100;sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA'
sc.world.color=(.24,.24,.24);sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast';sc.view_settings.exposure=.45
bpy.ops.object.camera_add(location=(-8,-6,3.2));sc.camera=bpy.context.object;sc.camera.rotation_euler=(Vector((0,0,1.26))-sc.camera.location).to_track_quat('-Z','Y').to_euler();sc.camera.data.type='ORTHO';sc.camera.data.ortho_scale=3.20;sc.camera.data.shift_x=-.04
for name,loc,power,size,col in [('Warm key',(-3,-4,6),650,3,(1,.83,.65)),('Cool fill',(4,-2,4),250,4,(.76,.85,1)),('Cool rim',(0,4,5),350,3,(.75,.85,1))]:
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name=name;o.data.energy=power;o.data.shape='DISK';o.data.size=size;o.data.color=col;o.rotation_euler=(Vector((0,0,1.2))-o.location).to_track_quat('-Z','Y').to_euler()
sc['source_horse']='Quaternius CC0 July 2021';sc['source_rider']='MPFB 2.0.18 CC0';sc['sample_frames']='[0]';sc['cavalry_sabre_length']=.55
bpy.ops.wm.save_as_mainfile(filepath=str(MASTER/'cavalry-plain.blend'))
bpy.ops.wm.save_as_mainfile(filepath=str(MASTER/'cavalry.blend'))
print('MOUNTED_BUILD_READY')
