"""True MPFB kneeling composite archer; original fitted costume and recurved bow."""
import bpy, os, sys, math, json
from pathlib import Path
from mathutils import Vector, Matrix
from math import sin, cos, pi
sys.path.insert(0,str(Path(__file__).parent))
import geometry as g
from geometry import material,mesh,curve,sphere,solid,bevel,attach,limb,aim_bone
R=Path(os.environ['ANIM_ROOT']); M=R/'masters/composite-archer';A=R/'assets/composite-archer'
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.preferences.addon_enable(module='bl_ext.user_default.mpfb')
from bl_ext.user_default.mpfb.services.humanservice import HumanService
from bl_ext.user_default.mpfb.services.targetservice import TargetService
macro=TargetService.get_default_macro_info_dict();macro.update(gender=1.,age=.45,muscle=.65,weight=.50,height=.42,proportions=.60)
macro['race']={'caucasian':.55,'african':.05,'asian':.40}
body=HumanService.create_human(macro_detail_dict=macro);body.name='GEO-MPFB anatomical archer'
bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();lo=min(v.co.z for v in me.vertices);hi=max(v.co.z for v in me.vertices);ev.to_mesh_clear()
body.scale=(1.72/(hi-lo),)*3
bpy.context.view_layer.objects.active=body;body.select_set(True);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
rig=HumanService.add_builtin_rig(body,'game_engine');rig.name='RIG-composite-archer';g.rig=rig;g.body=body
system=R/'blender-user/extensions/.user/user_default/mpfb/data'
eyes=HumanService.add_mhclo_asset(str(system/'eyes/high-poly/high-poly.mhclo'),body,asset_type='Eyes',subdiv_levels=1,material_type='MAKESKIN');eyes.name='GEO-MPFB eyes'
# MPFB eye import purges unused materials: create the palette only after that import.
skin=material('MAT-painted skin',(.48,.245,.105),rough=.65)
red=material('MAT-vermilion embroidered wool',(.37,.035,.015),rough=.88)
trousers=material('MAT-ochre patterned trousers',(.50,.31,.11),rough=.85)
leather=material('MAT-scuffed leather',(.16,.065,.023),rough=.72)
gold=material('MAT-worn gilding',(.78,.42,.085),metal=1,rough=.38)
horn=material('MAT-dark horn',(.055,.022,.008),rough=.35)
wood=material('MAT-horn belly golden wood',(.51,.26,.065),rough=.48)
hair=material('MAT-dark beard',(.035,.022,.013),rough=.85)
ivory=material('MAT-feather and string',(.82,.70,.49),rough=.8)
iron=material('MAT-iron arrowhead',(.4,.43,.46),metal=1,rough=.3)
stone=material('MAT-cream limestone E9CFA0',(.82,.63,.36),rough=.9)
body.data.materials.clear();body.data.materials.append(skin)
sub=body.modifiers.new('Anatomical subdivision','SUBSURF');sub.levels=1;sub.render_levels=1
for p in body.data.polygons:p.use_smooth=True
# Full-surface fitted shells preserve original MPFB anatomy/skin weights.
tunic=g.fitted_shell('GEO-tunic fitted chest',lambda v: .94<v.z<1.48 and abs(v.x)<.255,red,.025)
pants=g.fitted_shell('GEO-patterned trousers',lambda v:.16<v.z<.98,trousers,.046)
sleeves=g.fitted_shell('GEO-folded wool sleeves',lambda v:1.04<v.z<1.46 and .20<abs(v.x)<.57,red,.034)
# Add geometric cloth wrinkles before deformation; not texture-only folds.
for o in (tunic,pants,sleeves):
 for v in o.data.vertices:
  n=v.co.normalized();amp=.0055*sin(v.co.z*95+v.co.x*21)*sin(v.co.z*13)**2
  v.co+=n*amp
 for mod in o.modifiers:
  if mod.type=='SOLIDIFY':mod.thickness=.006
# Fitted boots from anatomical feet/lower calves, then leather welts.
boots=g.fitted_shell('GEO-soft leather boots',lambda v:v.z<.22,leather,.012)
# Cap follows real head dimensions; no replacement primitive anatomy.
h=rig.pose.bones['head']; hc=(h.head+h.tail)*.5
vs=[];fs=[]
for j in range(17):
 t=j*pi/32
 for i in range(64):
  a=i*2*pi/64;vs.append((hc.x+.105*cos(t)*sin(a),hc.y-.113*cos(t)*cos(a),hc.z+.045+.125*sin(t)))
for j in range(16):
 for i in range(64):a=j*64+i;b=j*64+(i+1)%64;fs.append((a,b,b+64,a+64))
attach(solid(mesh('GEO-red embroidered felt cap',vs,fs,red),.006),'head')
for z in [.035,.057]:attach(curve('GEO-cap gold braid',[(hc.x+.107*sin(a),hc.y-.115*cos(a),hc.z+z) for a in [i*2*pi/96 for i in range(97)]],.006,gold),'head')
# Beard is a skin-derived surface, follows actual jaw, with incised hair strands.
beard=g.fitted_shell('GEO-shaped beard',lambda v:hc.z-.115<v.z<hc.z-.008 and v.y<hc.y-.042,hair,.004)
# Pose low enough for one knee to touch the disc, front shin braced.
rig.location=(0,0,-.33)
limb('thigh_r','calf_r',(-.25,.20,.48),(-.38,-.47,.32))
limb('thigh_l','calf_l',(.42,-.14,.46),(.53,-.48,.88))
aim_bone('foot_l',(.18,-.04,-.025));aim_bone('foot_r',(0,.13,-.03))
# Both hands lie on a common arrow axis; right draws at cheek, left holds bow.
limb('upperarm_l','lowerarm_l',(.69,-.16,1.54),(.48,-.18,1.48))
limb('upperarm_r','lowerarm_r',(-.035,-.30,1.60),(-.55,-.26,1.55))
aim_bone('hand_l',(.02,0,.10));aim_bone('hand_r',(.10,0,0))
# Turn face to look along the arrow's line.
p=rig.pose.bones['head'];mat=p.matrix.copy();pivot=p.head.copy();p.matrix=Matrix.Translation(pivot) @ Matrix.Rotation(.9,4,'Z') @ Matrix.Translation(-pivot) @ mat
for side in ('l','r'):
 for digit in ['index','middle','ring','pinky']:
  for k in range(1,4):
   p=rig.pose.bones[f'{digit}_{k:02d}_{side}'];p.rotation_mode='XYZ';p.rotation_euler.x=.95 if side=='l' else .65
bpy.context.view_layer.update()
# World-authored details are bone-parented without changing their placement.
# Tunic skirts: separate thick fitted front/back panels, flared over raised thigh.
for side in [-1,1]:
 vs=[];fs=[]
 for j in range(13):
  t=j/12
  for i in range(33):
   a=-pi/2+i*pi/32 if side==-1 else pi/2+i*pi/32
   rx=.205+.14*t;ry=.145+.065*t
   vs.append((rx*sin(a),-ry*cos(a),.70-.33*t+.040*sin(a*6)*t))
 for j in range(12):
  for i in range(32):a=j*33+i;fs.append((a,a+1,a+34,a+33))
 o=solid(mesh('GEO-split red tunic skirt',vs,fs,red),.008);attach(o,'pelvis')
 attach(curve('GEO-skirt stitched gold hem',vs[-33:],.008,gold),'pelvis')
# Torso belt and diagonal shoulder baldric are thick ribbons with real buckles.
for z in [.704,.742]:attach(curve('GEO-belt edge',[(.212*sin(a),-.164*cos(a),z) for a in [i*2*pi/96 for i in range(97)]],.012,leather),'spine_01')
attach(curve('GEO-belt leather',[(.21*sin(a),-.162*cos(a),.723) for a in [i*2*pi/96 for i in range(97)]],.022,leather),'spine_01')
for x in [-.16,-.08,0,.08,.16]:attach(sphere('GEO-gold belt mount',(x,-.171,.724),(.017,.009,.017),gold),'spine_01')
attach(curve('GEO-diagonal baldric',[(-.15,-.15,.73),(-.08,-.19,.89),(.03,-.17,1.05),(.14,-.11,1.15)],.021,leather),'spine_03')
attach(curve('GEO-baldric buckle',[(-.075,-.216,.88),(-.035,-.216,.90),(-.05,-.216,.945),(-.09,-.216,.925),(-.075,-.216,.88)],.004,gold),'spine_03')
for i in range(16):
 z=.78+i*.021;x=-.15+(z-.73)*.69;attach(sphere('GEO-baldric stitching',(x,-.204,z),(.0025,.002,.003),ivory),'spine_03')
# Embroidered neckline follows the chest with real raised piping.
for sg in [-1,1]:attach(curve('GEO-gold wrap neck border',[(sg*.10,-.12,1.15),(sg*.08,-.17,1.03),(-sg*.02,-.19,.86),(sg*.04,-.17,.75)],.009,gold),'spine_03')
# Quiver on near hip, a closed oval leather container and golden rim.
qc=Vector((-.26,-.21,.52));qaxis=Vector((-.22,0,.95)).normalized();qx=Vector((1,0,.23)).normalized();qy=Vector((0,1,0));vs=[];fs=[]
for j in range(13):
 t=j/12;center=qc+qaxis*(t-.5)*.56;r=.055+.015*t
 for i in range(48):
  a=i*2*pi/48;vs.append(tuple(center+qx*(r*cos(a))+qy*(.037*sin(a))))
for j in range(12):
 for i in range(48):a=j*48+i;b=j*48+(i+1)%48;fs.append((a,b,b+48,a+48))
fs.append(tuple(reversed(range(48))))
attach(solid(mesh('GEO-ornamented leather quiver',vs,fs,leather),.006),'pelvis')
for j in [0,12]:attach(curve('GEO-quiver gilded rim',vs[j*48:(j+1)*48]+[vs[j*48]],.006,gold),'pelvis')
for i in range(6):
 start=qc+qaxis*.20+qx*((i%3-1)*.025)+qy*((i//3)*.02)
 end=start+qaxis*(.19+.016*(i%2))
 attach(curve('GEO-quiver arrow',[start,end],.003,wood),'pelvis')
 for s in [-1,1]:attach(solid(mesh('GEO-quiver fletching',[end-qaxis*.07,end-qaxis*.02+qx*s*.018,end+qx*s*.018,end],[(0,1,2,3)],ivory),.001),'pelvis')
# Real composite bow: swept recurved limbs with horn overlay and red bindings.
grip=rig.matrix_world @ rig.pose.bones['hand_l'].head+Vector((.01,0,.045))
ctrl=bpy.data.objects.new('CTRL-bow',None);bpy.context.collection.objects.link(ctrl);ctrl.location=grip;attach(ctrl,'hand_l')
def bowpart(o):
 bpy.context.view_layer.update();world=o.matrix_world.copy();o.parent=ctrl;o.parent_type='OBJECT';o.matrix_world=world;return o
pts=[(-.20,0,-.52),(-.28,0,-.48),(-.24,0,-.40),(-.08,0,-.33),(.005,0,-.20),(0,0,0),(.005,0,.20),(-.08,0,.33),(-.24,0,.40),(-.28,0,.48),(-.20,0,.52)]
# Smooth Bezier 3D curves, real circular thickness, broad face in token plane.
def smooth_curve(name,points,r,mat):
 d=bpy.data.curves.new(name,'CURVE');d.dimensions='3D';d.resolution_u=12;s=d.splines.new('BEZIER');s.bezier_points.add(len(points)-1)
 for p,v in zip(s.bezier_points,points):p.co=v;p.handle_left_type=p.handle_right_type='AUTO'
 d.bevel_depth=r;d.bevel_resolution=3;o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);d.materials.append(mat);return o
bowpart(smooth_curve('GEO-recurved composite bow',[grip+Vector(v) for v in pts],.019,wood))
bowpart(smooth_curve('GEO-dark horn backing',[grip+Vector((x,y-.012,z)) for x,y,z in pts],.008,horn))
for zz in [-.43,-.20,-.04,.04,.20,.43]:
 xx=min(pts,key=lambda v:abs(v[2]-zz))[0]
 for k in range(5):bowpart(curve('GEO-red sinew binding',[grip+Vector((xx+.023*cos(a),.022*sin(a),zz+(k-2)*.006)) for a in [i*2*pi/24 for i in range(25)]],.003,red))
# String and arrow meshes have editable deformation/visibility during release.
draw=rig.matrix_world @ rig.pose.bones['hand_r'].head+Vector((.04,-.015,.026))
string=curve('GEO-bowstring',[grip+Vector(pts[0]),draw,grip+Vector(pts[-1])],.0023,ivory)
# Convert to mesh then shape-key the middle string; rebuilt by animation to follow hands.
bpy.ops.object.select_all(action='DESELECT');string.select_set(True);bpy.context.view_layer.objects.active=string;bpy.ops.object.convert(target='MESH');string=bpy.context.object
string['rest_points']=json.dumps([list(grip+Vector(pts[0])),list(draw),list(grip+Vector(pts[-1]))])
arrowctrl=bpy.data.objects.new('CTRL-arrow',None);bpy.context.collection.objects.link(arrowctrl);arrowctrl.location=draw
for o in [curve('GEO-nocked arrow shaft',[draw,grip+Vector((.15,0,.026))],.004,wood)]:
 bpy.context.view_layer.update();world=o.matrix_world.copy();o.parent=arrowctrl;o.matrix_world=world
end=grip+Vector((.18,0,.026));arrowhead=solid(mesh('GEO-arrowhead',[end,end+Vector((-.07,-.015,0)),end+Vector((-.07,0,.015)),end+Vector((-.07,.015,0)),end+Vector((-.07,0,-.015))],[(0,1,2),(0,2,3),(0,3,4),(0,4,1)],iron,False),.001)
bpy.context.view_layer.update();world=arrowhead.matrix_world.copy();arrowhead.parent=arrowctrl;arrowhead.matrix_world=world
for sg in [-1,1]:
 o=solid(mesh('GEO-arrow flight feathers',[draw+Vector((.02,0,0)),draw+Vector((.03,0,sg*.018)),draw+Vector((.11,0,sg*.018)),draw+Vector((.13,0,0))],[(0,1,2,3)],ivory),.001);bpy.context.view_layer.update();world=o.matrix_world.copy();o.parent=arrowctrl;o.matrix_world=world
# Stationary single warm cream disc.
bpy.ops.mesh.primitive_cylinder_add(vertices=96,radius=.56,depth=.085,location=(.02,0,.0425));base=bpy.context.object;base.name='GEO-stationary cream base';base.data.materials.append(stone);bevel(base,.014,3)
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=8;sc.cycles.use_denoising=True;sc.cycles.max_bounces=4
sc.render.resolution_x=sc.render.resolution_y=256;sc.render.resolution_percentage=100;sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.threads_mode='FIXED';sc.render.threads=3
sc.world.color=(.15,.15,.15);sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast'
bpy.ops.object.camera_add(location=(1.6,-7,3.7));cam=bpy.context.object;cam.name='CAM-painting';cam.rotation_euler=(Vector((.12,0,.72))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=1.95;sc.camera=cam
for name,loc,power,size,col in [('warm key',(-3,-4,5),550,2.0,(1,.91,.77)),('soft fill',(4,-2,3),130,3,(.88,.93,1)),('cool rim',(1,3,4),300,2,(.78,.87,1))]:
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name='LGT-'+name;o.data.energy=power;o.data.size=size;o.data.color=col;o.rotation_euler=(Vector((0,0,.8))-o.location).to_track_quat('-Z','Y').to_euler()
bpy.context.view_layer.update()
rig['neutral_pose']=json.dumps({p.name:[list(row) for row in p.matrix_basis] for p in rig.pose.bones});rig['neutral_location']=list(rig.location);rig['origin']='MPFB 2.0.18 CC0 anatomy and 53-bone game_engine rig'
sc['unit']='composite-archer';sc['round']=1
bpy.ops.wm.save_as_mainfile(filepath=str(M/'plain.blend'))
(M/'model-info.json').write_text(json.dumps({'body_vertices':len(body.data.vertices),'bones':len(rig.data.bones),'objects':len(sc.objects),'bone_world':{p.name:list(rig.matrix_world @ p.head) for p in rig.pose.bones if p.name in ['head','pelvis','thigh_l','thigh_r','calf_l','calf_r','foot_l','foot_r','hand_l','hand_r']}},indent=2))
sc.render.filepath=str(M/'b-plain.png');bpy.ops.render.render(write_still=True)
print('PLAIN_READY')
