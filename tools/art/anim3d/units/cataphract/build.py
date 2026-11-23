"""True geometry cataphract: CC0 Quaternius horse, MPFB rider and original scale armor."""
import bpy, os, sys, json, math, ast
from pathlib import Path
from mathutils import Vector, Matrix
from math import sin,cos,pi
ROOT=Path(os.environ['ANIM_ROOT']); MASTER=ROOT/'masters/cataphract'; MASTER.mkdir(parents=True,exist_ok=True)
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
horse.data.update()
# Preserve the source mesh/weights and smooth the hard low-poly facets.
for p in horse.data.polygons:p.use_smooth=True
sub=horse.modifiers.new('Sculpt surface refinement','SUBSURF');sub.levels=1;sub.render_levels=2
horse['source']='Quaternius Ultimate Animated Animal Pack July 2021, CC0; Horse.glb'
# Rest-space pigment masks remain attached to the skinned surface.
coat=material('Bay coat',(.12,.065,.029),0,.48);hair=material('Black mane and tail',(.016,.012,.009),0,.66)
shadow=material('Bay shaded muscle',(.16,.041,.012),0,.55);muzzle=material('Velvet muzzle',(.034,.025,.019),0,.72)
hoof=material('Horn hooves',(.075,.064,.049),0,.61);lightcoat=material('Bay warm highlights',(.20,.12,.055),0,.53)
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
skin=material('Skin • warm ochre',(.46,.25,.12),0,.65);linen=material('Warm ivory linen',(.82,.75,.60),0,.88)
bronze=material('Bronze • hammered',(.42,.43,.40),1,.36);gold=material('Bronze • polished edges',(.64,.56,.37),1,.3);dark=material('Incised bronze patina',(.06,.037,.013),.4,.65)
leather=material('Oxide leather',(.105,.039,.017),0,.72);wood=material('Ash spear shaft',(.24,.11,.031),0,.6);iron=material('Forged iron',(.45,.47,.46),1,.32);stone=material('Cream limestone',(.815,.624,.352),0,.85)
body.data.materials.clear();body.data.materials.append(skin)
for p in body.data.polygons:p.use_smooth=True
sub=body.modifiers.new('Anatomical subdivision','SUBSURF');sub.levels=1
system=ROOT/'blender-user/extensions/.user/user_default/mpfb/data';eyes=HumanService.add_mhclo_asset(str(system/'eyes/high-poly/high-poly.mhclo'),body,asset_type='Eyes',subdiv_levels=1,material_type='MAKESKIN');eyes.name='Rider MPFB eyes'
# A short dark beard keeps the painted adult face legible at token size.
fitted_shell('Rider short beard',lambda v:1.49<v.z<1.57 and v.y<-.063 and abs(v.x)<.075,hair,.002)
# Fitted, weighted linen shirt and sleeves, with actual cloth fold geometry.
fitted_shell('Rider lamellar shirt and sleeves',lambda v:1.01<v.z<1.475 and (abs(v.x)<.24 or v.z>1.29),bronze,.018)
fitted_shell('Rider riding trousers',lambda v:.27<v.z<1.02,linen,.012)
for j in range(15):
 a=2*pi*j/15;vs=[]
 for k in range(9):
  t=k/8
  for q in (-1,0,1):
   aa=a+q*.22;r=.005*cos(q*pi)+.004*sin(t*6+j)
   vs.append(((.18+.035*t+r)*sin(aa),-(.13+.04*t+r)*cos(aa),1.04-.30*t))
 fs=[(k*3+i,k*3+i+1,(k+1)*3+i+1,(k+1)*3+i) for k in range(8) for i in range(2)]
 o=solid(mesh('Split riding tunic fold',vs,fs,linen),.004);attach(o,'thigh_l' if sin(a)>0 else 'thigh_r')
# Draped diagonals and bronze-fastened belt.
for j in range(6):attach(curve('Linen chest fold',[(-.18,-.125,1.40-j*.025),(-.08,-.17,1.30-j*.024),(.16,-.14,1.20-j*.023)],.009,linen),'spine_03')
attach(curve('Leather baldric',[(-.16,-.145,1.45),(-.04,-.181,1.28),(.16,-.145,1.08)],.018,leather),'spine_03')
attach(curve('Rider waist belt',[(.18*sin(a),-.14*cos(a),1.055) for a in [i*2*pi/80 for i in range(81)]],.018,leather),'pelvis')
attach(sphere('Belt bronze clasp',(0,-.158,1.055),(.033,.012,.025),gold),'pelvis')
# Open bronze helmet: raised rim, nasal, cheek plates and neck guard.
hc=(rig.pose.bones['head'].head+rig.pose.bones['head'].tail)*.5;cx,cy,cz=hc
vs=[];fs=[]
for j in range(17):
 t=j/16*pi/2
 for i in range(64):
  a=i*2*pi/64;vs.append((cx+.108*cos(t)*sin(a),cy-.12*cos(t)*cos(a),cz+.018+.14*sin(t)))
for j in range(16):
 for i in range(64):a=j*64+i;b=j*64+(i+1)%64;fs.append((a,b,b+64,a+64))
attach(solid(mesh('Rider bronze helmet bowl',vs,fs,bronze),.006),'head')
attach(curve('Helmet rolled rim',[(cx+.108*sin(a),cy-.12*cos(a),cz+.019) for a in [i*2*pi/100 for i in range(101)]],.007,gold),'head')
for sg in [-1,1]:
 vs=[(sg*.092,cy-.04,cz+.02),(sg*.105,cy-.075,cz-.075),(sg*.063,cy-.12,cz-.10),(sg*.062,cy-.12,cz-.015)]
 attach(bevel(solid(mesh('Bronze cheekguard',vs,[(0,1,2,3)],bronze),.007),.004),'head')
 attach(curve('Cheekguard edge',vs+[vs[0]],.003,gold),'head')
attach(curve('Helmet nasal',[(0,cy-.122,cz+.025),(0,cy-.135,cz-.045)],.009,bronze),'head')
# Pose the MPFB joints in saddle space before moving the entire rider up.
limb('thigh_r','calf_r',(-.34,-.10,.34),(-.46,-.55,.76));limb('thigh_l','calf_l',(.34,-.10,.34),(.46,-.55,.76))
limb('upperarm_r','lowerarm_r',(-.34,-.29,1.23),(-.48,-.12,1.17));limb('upperarm_l','lowerarm_l',(.18,-.40,1.13),(.39,-.15,1.13))
for side in ['r','l']:
 aim_bone('foot_'+side,(0,-1,-.1));aim_bone('hand_'+side,(0,0,1))
 for digit in ['index','middle','ring','pinky']:
  for k in range(1,4):p=rig.pose.bones[f'{digit}_{k:02d}_{side}'];p.rotation_mode='XYZ';p.rotation_euler.x=1.1
bpy.context.view_layer.update()
for side in ['l','r']:
 foot=rig.pose.bones['foot_'+side];p=foot.head
 attach(curve('Rider sandal '+side,[tuple(p+Vector((-.045,-.07,-.025))),tuple(p+Vector((.045,-.07,-.025)))],.025,leather),'foot_'+side)
 for d in [0,.045,.09]:attach(curve('Sandal straps '+side,[tuple(p+Vector((-.045,-d,0))),tuple(p+Vector((0,-d,.024))),tuple(p+Vector((.045,-d,0)))],.009,leather),'foot_'+side)
grip=rig.pose.bones['hand_r'].head+Vector((0,-.014,.04))
attach(curve('Spear ash shaft',[grip+Vector((0,0,-1.46)),grip+Vector((0,0,1.30))],.013,wood),'hand_r')
sv=[tuple(grip+Vector(v)) for v in [(-.022,0,1.30),(0,-.012,1.30),(.022,0,1.30),(0,0,1.46),(0,.012,1.30),(0,0,1.26)]]
attach(mesh('Iron spear blade',sv,[(0,1,3),(1,2,3),(2,4,3),(4,0,3),(0,5,1),(1,5,2),(2,5,4),(4,5,0)],iron,False),'hand_r')
# Anatomical pelvis sits on the source's moving back, rather than floating above it.
rig.scale=(1.07,)*3;rig.location=(0,.13,.432);bpy.context.view_layer.update()
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
 horse_attach(curve('Tail flowing fibre',[(dx,.83+dy,1.45),(dx-.035,1.04+dy,1.16),(dx-.07,1.13+dy,.74),(dx-.10,1.07+dy,.44+.035*sin(i))],.012,hair),'Tail3')
horse_attach(curve('Leather breast strap',[(-.33,-.40,1.38),(-.27,-.59,1.20),(0,-.67,1.12),(.27,-.59,1.20),(.33,-.40,1.38)],.024,leather),'Torso3')
for sg in [-1,1]:horse_attach(sphere('Breast strap bronze disc',(sg*.27,-.59,1.20),(.043,.016,.043),gold),'Torso3')
# Bronze studs and stitched blanket edging are geometrical, not camera-facing paint.
for sg in [-1,1]:
 for i in range(12):
  y=-.20+i*.055
  horse_attach(sphere('Blanket bronze stitch',(sg*.365,y,1.25),(.007,.013,.007),gold),'Torso')
exec(compile(Path('tools/art/anim3d/units/cataphract/kit.py').read_text(), 'cataphract kit', 'exec'))
# Constant base and light rig.
bpy.ops.mesh.primitive_cylinder_add(vertices=128,radius=1.02,depth=.10,location=(0,0,.05));base=bpy.context.object;base.name='Stationary cream stone';base.data.materials.append(stone);bevel(base,.018,3)
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=8;sc.cycles.use_denoising=True;sc.render.threads_mode='FIXED';sc.render.threads=3
sc.render.resolution_x=sc.render.resolution_y=256;sc.render.resolution_percentage=100;sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA'
sc.world.color=(.24,.24,.24);sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast';sc.view_settings.exposure=0
bpy.ops.object.camera_add(location=(-9,-4.4,3.6));sc.camera=bpy.context.object;sc.camera.rotation_euler=(Vector((0,0,1.55))-sc.camera.location).to_track_quat('-Z','Y').to_euler();sc.camera.data.type='ORTHO';sc.camera.data.ortho_scale=3.65
for name,loc,power,size,col in [('Warm key',(-3,-4,6),650,3,(1,.83,.65)),('Cool fill',(4,-2,4),250,4,(.76,.85,1)),('Cool rim',(0,4,5),360,3,(.73,.84,1))]:
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name=name;o.data.energy=power;o.data.shape='DISK';o.data.size=size;o.data.color=col;o.rotation_euler=(Vector((0,0,1.2))-o.location).to_track_quat('-Z','Y').to_euler()
sc['source_horse']='Quaternius CC0 July 2021';sc['source_rider']='MPFB 2.0.18 CC0';sc['sample_frames']='[0]'
bpy.ops.wm.save_as_mainfile(filepath=str(MASTER/'unpainted.blend'))
print('CATAPHRACT_BUILD_READY')
