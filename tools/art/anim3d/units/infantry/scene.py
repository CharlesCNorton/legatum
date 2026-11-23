"""Infantry: MPFB anatomy, tailored 3D kit, frozen camera UVs and five actions."""
import bpy, math, os, sys, json, hashlib, subprocess
from pathlib import Path
from mathutils import Vector, Matrix
from math import sin, cos, pi
from bpy_extras.object_utils import world_to_camera_view
R=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'))
M=R/'masters/infantry'; A=R/'assets/infantry'; V=R/'review/3d-v2'
for p in (M,V,M/'clips',M/'renders'):p.mkdir(parents=True,exist_ok=True)
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from retarget import prepare, apply_matrices
CLIPS={'idle':(8,4,True),'move':(8,6,True),'attack':(10,14,False),'hit':(4,8,False),'death':(10,5,False)}
def log(s):
 with (V/'infantry-log.md').open('a') as f:f.write('- '+s+'\n')
 print(s,flush=True)
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

def configure():
 sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device=os.environ.get('CYCLES_DEVICE','CPU');sc.cycles.samples=int(os.environ.get('SAMPLES','6'));sc.cycles.use_denoising=True;sc.cycles.max_bounces=4;sc.cycles.diffuse_bounces=2
 if sc.cycles.device=='GPU':
  prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices();found=False
  for d in prefs.devices:d.use=d.type=='METAL';found|=d.use
  if not found:raise RuntimeError('Metal GPU required; refusing CPU fallback')
 sc.render.threads_mode='FIXED';sc.render.threads=3;sc.render.resolution_x=sc.render.resolution_y=int(os.environ.get('RESOLUTION','256'));sc.render.resolution_percentage=100;sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.use_file_extension=True
 # Standard is intentional for frozen camera-painted colour, not a photographic preset.
 return sc

def build():
 global rig,body,linen,red,leather,steel,brass
 # A failed rebuild must never allow an older delivery to pass as current.
 for manifest in (M/'renders').glob('*/render.json'):manifest.unlink(missing_ok=True)
 (M/'grade.json').unlink(missing_ok=True)
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
 bpy.ops.preferences.addon_enable(module='bl_ext.user_default.mpfb')
 from bl_ext.user_default.mpfb.services.humanservice import HumanService
 from bl_ext.user_default.mpfb.services.targetservice import TargetService
 macro=TargetService.get_default_macro_info_dict();macro.update(gender=1.,age=.40,muscle=.65,weight=.52,height=.5,proportions=.6);macro['race']={'caucasian':1.,'african':0.,'asian':0.}
 body=HumanService.create_human(macro_detail_dict=macro);body.name='GEO-MPFB infantry anatomy'
 bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();lo=min(v.co.z for v in me.vertices);hi=max(v.co.z for v in me.vertices);ev.to_mesh_clear();body.scale=(1.72/(hi-lo),)*3
 bpy.context.view_layer.objects.active=body;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 rig=HumanService.add_builtin_rig(body,'game_engine');rig.name='RIG-Infantry MPFB';rig.location.z=.09
 system=R/'blender-user/extensions/.user/user_default/mpfb/data'
 eyes=HumanService.add_mhclo_asset(str(system/'eyes/high-poly/high-poly.mhclo'),body,asset_type='Eyes',subdiv_levels=1,material_type='MAKESKIN');eyes.name='GEO-MPFB eyes'
 skin=mat('warm painted skin',(.5,.29,.14));red=mat('painted olive field uniform',(.24,.26,.13),fill='wool');linen=mat('ochre puttee cloth',(.39,.30,.18),fill='linen');leather=mat('scuffed tan leather',(.30,.14,.055),fill='leather');steel=mat('worn steel',(.26,.28,.31),1,.55);brass=mat('antique brass buttons',(.48,.32,.13),1,.35);wood=mat('walnut rifle stock',(.26,.115,.035));dark=mat('bore and moustache',(.05,.025,.012));stone=mat('cream limestone E9CFA0',(.81485,.62396,.35153),0,.88)
 body.data.materials.clear();body.data.materials.append(skin)
 for p in body.data.polygons:p.use_smooth=True
 sub=body.modifiers.new('Anatomical smoothing','SUBSURF');sub.levels=sub.render_levels=1
 limb('thigh_r','calf_r',(-.24,-.04,.085),(-.26,-.4,.5));limb('thigh_l','calf_l',(.19,.015,.085),(.25,-.4,.5))
 limb('upperarm_r','lowerarm_r',(-.36,-.07,2.00),(-.34,-.16,1.78));limb('upperarm_l','lowerarm_l',(.43,-.10,1.03),(.33,-.02,1.18))
 aim('hand_r',(-.02,0,.10));aim('hand_l',(0,-.01,.10))
 for side in ('r','l'):
  for digit in ('index','middle','ring','pinky'):
   for k in range(1,4):p=rig.pose.bones[f'{digit}_{k:02d}_{side}'];p.rotation_mode='XYZ';p.rotation_euler.x=.85
 p=rig.pose.bones['head'];p.rotation_mode='XYZ';p.rotation_euler.x=-.25;p.rotation_euler.y=-.18;bpy.context.view_layer.update()
 # Closed, folded coat surface: three-dimensional torso, skirt, lining and hem.
 vs=[];fs=[];rings=[(.88,.235,.16),(.94,.225,.16),(1.03,.205,.15),(1.10,.19,.145),(1.23,.20,.15),(1.39,.235,.155),(1.48,.23,.14),(1.53,.12,.10)]
 for j,(z,rx,ry) in enumerate(rings):
  for k in range(96):
   a=2*pi*k/96;fold=.012*cos(a*10+.22*j)*(1 if j<5 else .45);vs.append(((rx+fold)*sin(a),-(ry+fold)*cos(a),z+.09))
 for j in range(len(rings)-1):
  for k in range(96):i=j*96+k;n=j*96+(k+1)%96;fs.append((i,n,n+96,i+96))
 coat=solid(mesh('field jacket folded wool',vs,fs,red),.009)
 # Bind garment to torso and thighs, preserving the authored rest shape.
 bind_weights(coat,lambda v:{'spine_03':max(0,min(1,(v.z-1.10)/.22)),'pelvis':max(0,1-abs(v.z-1.03)/.28),'thigh_l' if v.x>0 else 'thigh_r':max(0,min(.8,(1.03-v.z)/.5))})
 for side in ('r','l'):
  for upper in ('upperarm','lowerarm'):
   p=rig.pose.bones[upper+'_'+side];a=rig.matrix_world @ p.head;b=rig.matrix_world @ p.tail
   tube('wool sleeve '+upper+' '+side,a,b,(.070,.060,.018),red,upper+'_'+side)
  p=rig.pose.bones['lowerarm_'+side];a=rig.matrix_world @ p.head;b=rig.matrix_world @ p.tail
  tube('turned wool cuff '+side,b.lerp(a,.22),b,(.067,.060,.005),red,'lowerarm_'+side)
  p=rig.pose.bones['thigh_'+side];a=rig.matrix_world @ p.head;b=rig.matrix_world @ p.tail
  tube('wool trousers '+side,a,b,(.095,.079,.015),red,'thigh_'+side)
  p=rig.pose.bones['calf_'+side];a=rig.matrix_world @ p.head;b=rig.matrix_world @ p.tail
  tube('folded trousers calf '+side,a,a.lerp(b,.65),(.080,.066,.014),red,'calf_'+side)
  tube('canvas gaiter '+side,a.lerp(b,.65),b,(.058,.043,.005),linen,'calf_'+side)
  for j in range(4):
   t=.68+j*.08;c=a.lerp(b,t);rad=.071*(1-t)+.043*t+.002
   attach(curve('puttee overlap '+side,[(c.x+rad*cos(q),c.y+rad*sin(q),c.z+.008*sin(q)) for q in [2*pi*k/32 for k in range(33)]],.0025,linen),'calf_'+side)
  fp=rig.matrix_world @ rig.pose.bones['foot_'+side].head
  attach(sphere('ankle boot '+side,(fp.x,fp.y-.05,.15),(.068,.135,.075),leather),'foot_'+side)
  attach(sphere('boot sole '+side,(fp.x,fp.y-.055,.092),(.071,.14,.018),dark),'foot_'+side)
  for j in range(5):attach(curve('boot lace '+side,[(fp.x-.027,fp.y-.12+j*.019,.198-j*.005),(fp.x+.027,fp.y-.10+j*.019,.193-j*.005)],.002,linen),'foot_'+side)
 # Thick lapels and shoulder webbing, separate edges and brass fasteners.
 for sign in (-1,1):
  lapel=mesh('folded field jacket lapel',[(sign*.04,-.11,1.64),(sign*.15,-.145,1.58),(sign*.10,-.176,1.48),(sign*.01,-.15,1.55)],[(0,1,2,3)],red);attach(bevel(solid(lapel,.012),.004),'spine_03')
  strap=mesh('pack shoulder strap',[(sign*.19,-.10,1.54),(sign*.145,-.13,1.54),(sign*.12,-.18,1.12),(sign*.16,-.17,1.12)],[(0,1,2,3)],leather);attach(bevel(solid(strap,.014),.004),'spine_03')
  for j in range(4):
   if sign==1:attach(sphere('field jacket brass button',(0,-.173,1.17+j*.10),(.008,.006,.008),brass),'spine_03')
  attach(box('breast pocket',(sign*.12,-.172,1.40),(.11,.025,.13),red,.012),'spine_03')
 attach(bevel(solid(mesh('diagonal leather baldric',[(-.17,-.179,1.15),(-.14,-.186,1.12),(.19,-.174,1.57),(.16,-.17,1.60)],[(0,1,2,3)],leather),.012),.003),'spine_03')
 for z in (1.085,1.13):attach(curve('belt finished edge',[(.20*sin(a),-.16*cos(a),z) for a in [2*pi*k/96 for k in range(97)]],.013,leather),'pelvis')
 for i in range(4):
  x=-.16+i*.105;attach(box('cartridge pouch',(x,-.195,1.10),(.09,.065,.115),leather,.012),'pelvis');attach(box('pouch flap',(x,-.24,1.14),(.089,.018,.047),leather,.009),'pelvis');attach(sphere('pouch brass stud',(x,-.253,1.12),(.009,.006,.009),brass),'pelvis')
 attach(box('canvas backpack',(-.07,.17,1.38),(.36,.23,.40),linen,.045),'spine_03')
 attach(box('canvas haversack',(-.23,.01,1.01),(.17,.13,.23),linen,.025),'pelvis')
 # Adrian-style full-depth helmet with shallow brim, crest and rolled edge.
 head=rig.pose.bones['head'];hc=rig.matrix_world @ ((head.head+head.tail)*.5);cx,cy,cz=hc
 helmetpaint=mat('olive painted helmet',(.22,.24,.12),0,.67,fill='wool')
 vs=[];fs=[]
 for j in range(17):
  t=(j/16)*pi/2
  for k in range(64):a=2*pi*k/64;vs.append((cx+.12*cos(t)*sin(a),cy-.14*cos(t)*cos(a),cz+.025+.13*sin(t)))
 for j in range(16):
  for k in range(64):i=j*64+k;n=j*64+(k+1)%64;fs.append((i,n,n+64,i+64))
 attach(bevel(solid(mesh('steel helmet bowl',vs,fs,helmetpaint),.006),.002),'head')
 vs=[];fs=[]
 for j in range(4):
  t=j/3
  for k in range(64):
   a=2*pi*k/64;vs.append((cx+(.119+.023*t)*sin(a),cy-(.138+.025*t)*cos(a),cz+.02-.016*t))
 for j in range(3):
  for k in range(64):i=j*64+k;n=j*64+(k+1)%64;fs.append((i,n,n+64,i+64))
 attach(bevel(solid(mesh('helmet flared brim',vs,fs,helmetpaint),.005),.002),'head');attach(curve('rolled helmet rim',vs[-64:]+[vs[-64]],.003,helmetpaint),'head')
 # Net cords follow the curved steel shell; real thickness, no painted-only net.
 for k in range(12):
  az=2*pi*k/12
  pts=[(cx+.123*cos(t)*sin(az),cy-.143*cos(t)*cos(az),cz+.027+.134*sin(t)) for t in [j*pi/2/24 for j in range(25)]]
  attach(curve('helmet net meridian',pts,.0018,linen),'head')
 for j in range(1,7):
  t=j*pi/2/8
  attach(curve('helmet net ring',[(cx+.123*cos(t)*sin(a),cy-.143*cos(t)*cos(a),cz+.027+.134*sin(t)) for a in [k*2*pi/64 for k in range(65)]],.0018,linen),'head')
 attach(curve('helmet chin strap',[(cx-.11,cy,cz),(cx-.08,cy-.09,cz-.14),(cx+.02,cy-.11,cz-.17),(cx+.10,cy-.025,cz-.04)],.007,linen),'head')
 # Upright bolt-action rifle and bayonet, with real stock depth and metal fittings.
 gun=empty('CTRL-rifle',(-.32,-.25,1.18));attach(gun,'hand_l')
 vs=[]
 for y in (-.278,-.222):
  for x,z in [(-.375,.10),(-.28,.10),(-.30,.42),(-.29,.72),(-.303,1.48),(-.333,1.48),(-.34,.65),(-.33,.43)]:vs.append((x,y,z))
 fs=[tuple(range(7,-1,-1)),tuple(range(8,16))]+[(i,(i+1)%8,(i+1)%8+8,i+8) for i in range(8)]
 parent(bevel(mesh('walnut rifle stock',vs,fs,wood),.008),gun)
 parent(curve('rifle barrel',[(-.317,-.283,.72),(-.317,-.283,1.58)],.013,steel),gun)
 parent(curve('fixed bayonet',[(-.317,-.283,1.57),(-.317,-.283,1.91)],.005,steel),gun)
 for z in (.65,1.04,1.44,1.56):parent(curve('barrel band',[(-.317,-.283,z),(-.317,-.283,z+.019)],.019,steel),gun)
 parent(curve('bolt handle',[(-.315,-.29,.65),(-.36,-.31,.64)],.008,steel),gun);parent(sphere('bolt knob',(-.36,-.31,.64),(.013,.013,.013),steel),gun)
 parent(curve('trigger guard',[(-.32,-.25,.52),(-.28,-.26,.49),(-.28,-.26,.44),(-.32,-.25,.43)],.005,steel),gun)
 # Rifle is held upright in the left hand, shortened to the source's barrel.
 for o in list(bpy.context.scene.objects):
  if o.parent==gun:
   w=o.matrix_world.copy();w.translation.x+=.76;o.matrix_world=w
   if 'bayonet' in o.name:o.hide_render=True
 # Grenade belongs to the raised right hand until the attack release.
 hand=rig.matrix_world @ rig.pose.bones['hand_r'].tail
 grenade=empty('CTRL-grenade',hand);attach(grenade,'hand_r')
 parent(sphere('segmented grenade',hand+Vector((0,-.025,0)),(.038,.034,.051),steel),grenade)
 for j in range(4):
  z=hand.z-.031+j*.020
  parent(curve('grenade casing groove',[(hand.x+.039*cos(a),hand.y-.025+.035*sin(a),z) for a in [k*2*pi/32 for k in range(33)]],.002,dark),grenade)
 parent(box('grenade lever',hand+Vector((.025,-.01,.045)),(.013,.012,.065),steel,.003),grenade)
 bpy.ops.mesh.primitive_cylinder_add(vertices=96,radius=.49,depth=.075,location=(0,0,.0475));base=bpy.context.object;base.name='GEO-stationary cream base';base.data.materials.append(stone);base.data.materials.append(mat('cream stone darker rim B68A51',(.4678,.2542,.0823),0,.88))
 for face in base.data.polygons:face.material_index=1 if abs(face.normal.z)<.5 else 0
 bevel(base,.012)
 sc=configure();sc.view_settings.view_transform='Standard';sc.world.use_nodes=True;sc.world.node_tree.nodes.get('Background').inputs[0].default_value=(.65,.70,.8,1);sc.world.node_tree.nodes.get('Background').inputs[1].default_value=.25
 bpy.ops.object.camera_add(location=(.22,-8,3.05));cam=bpy.context.object;cam.name='CAM-painting';cam.rotation_euler=(Vector((0,0,1.06))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=2.56;sc.camera=cam
 for name,loc,power,size,color in [('key',(-3,-4,5),300,3.,(1,.88,.72)),('fill',(3,-3,3),65,3.,(.83,.9,1)),('rim',(1,2,4),140,2.,(.72,.83,1))]:
  bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name='LGT-'+name;o.data.energy=power;o.data.size=size;o.data.color=color;o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
 # Fit real surfaces in the camera plane, preserving their full depth.
 bpy.context.view_layer.update()
 right=cam.rotation_euler.to_matrix() @ Vector((1,0,0));up=cam.rotation_euler.to_matrix() @ Vector((0,1,0));metres=cam.data.ortho_scale/256
 for o in list(sc.objects):
  if o.type=='CURVE':
   bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
  if o.type!='MESH':continue
  # Finish rigid shell thickness and curves before calculating projection UVs.
  if not any(m.type=='ARMATURE' for m in o.modifiers):
   bpy.context.view_layer.objects.active=o
   for modifier in list(o.modifiers):
    if modifier.type in ('BEVEL','SOLIDIFY','SUBSURF'):bpy.ops.object.modifier_apply(modifier=modifier.name)
 fit_surfaces(sc,rig,body)
 sc['unit']='infantry';sc['anatomy']='MPFB 2.0.18 CC0';sc['reference']='CC BY 4.0 infantry-source.png'
 bpy.context.view_layer.update();rig['rest_pose']=json.dumps({p.name:[list(r) for r in p.matrix_basis] for p in rig.pose.bones});rig['rest_location']=list(rig.location);gun['rest_world']=[v for row in gun.matrix_world for v in row]
 bpy.ops.wm.save_as_mainfile(filepath=str(M/'plain.blend'));log('Built MPFB anatomical body, 53-bone rig, olive field jacket, netted helmet, webbing, rifle and raised grenade; plain.blend saved.')


def fit_surfaces(sc,rig,body):
 """Fit complete volumes to painted landmarks, inverse skinning preserves weights.
 No camera-facing cards or contour alpha are introduced. Soles keep world Z.
 """
 # Freeze MPFB's mixed macros before editing vertex coordinates.
 if body.data.shape_keys:
  key=body.shape_key_add(name='Frozen anatomical mix',from_mix=True)
  points=[v.co.copy() for v in key.data]
  body.shape_key_clear()
  for v,co in zip(body.data.vertices,points):v.co=co
 cam=sc.camera;right=cam.rotation_euler.to_matrix()@Vector((1,0,0));up=cam.rotation_euler.to_matrix()@Vector((0,1,0));unit=cam.data.ortho_scale/256
 for obj in sc.objects:
  if obj.type!='MESH' or 'stationary' in obj.name:continue
  arm=next((m for m in obj.modifiers if m.type=='ARMATURE'),None)
  for v in obj.data.vertices:
   deform=Matrix.Identity(4)
   if arm:
    deform=Matrix(((0,0,0,0),)*4);total=0
    for g in v.groups:
     name=obj.vertex_groups[g.group].name
     if name not in rig.pose.bones:continue
     dm=obj.matrix_world.inverted()@rig.matrix_world@rig.pose.bones[name].matrix@rig.data.bones[name].matrix_local.inverted()@rig.matrix_world.inverted()@obj.matrix_world
     deform+=dm*g.weight;total+=g.weight
    if total<.001:deform=Matrix.Identity(4)
    else:deform*=1/total
   world=obj.matrix_world@deform@v.co
   uv=world_to_camera_view(sc,cam,world);x=uv.x*256;y=(1-uv.y)*256
   dx=0;dy=0
   # Throwing arm: lengthen shoulder-to-fist in screen space, smooth into torso.
   strength=max(0,min(1,(112-x)/16))*max(0,min(1,(100-y)/25))
   dx-=5*strength;dy-=max(0,(90-y)*.34)*strength
   # Feet/legs spread to the reference's stance rather than a narrow parade pose.
   lower=max(0,min(1,(y-135)/65))
   dx+=(-9 if x<125 else -2)*lower
   dy-=4*lower
   # Supporting palm and upright rifle align to the painted hand.
   if obj.parent and obj.parent.name=='CTRL-rifle':dx=-9;dy=-3+.18*(221-y)
   elif x>151 and y<145:dx-=max(0,min(1,(x-151)/14))*7
   delta=right*dx*unit-up*dy*unit
   # Keep ground-contact height, use camera-depth travel to preserve screen fit.
   if world.z<.25:
    forward=Vector((0,1,0));denom=up.dot(forward)
    wanted=delta.dot(up);delta=right*dx*unit+forward*(wanted/denom)
   v.co=deform.inverted()@obj.matrix_world.inverted()@(world+delta)
 bpy.context.view_layer.update()


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

def bake_surface_maps():
 """Actual Cycles AO and geometry Pointiness bakes on key physical surfaces."""
 sc=configure();old_samples=sc.cycles.samples;sc.cycles.samples=8
 folder=M/'textures/baked';folder.mkdir(parents=True,exist_ok=True)
 report={}
 for name in ['GEO-steel helmet bowl','GEO-field jacket folded wool']:
  ob=bpy.data.objects[name]
  bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
  uv=ob.data.uv_layers.get('SurfaceBake') or ob.data.uv_layers.new(name='SurfaceBake');ob.data.uv_layers.active=uv
  bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(island_margin=.03);bpy.ops.object.mode_set(mode='OBJECT')
  disabled=[m for m in ob.modifiers if m.type=='SOLIDIFY' and m.show_render]
  for m in disabled:m.show_render=False
  maps={}
  for kind in ['AO','CURVATURE']:
   image=bpy.data.images.new(name+' '+kind,width=256,height=256,alpha=False);image.colorspace_settings.name='Non-Color'
   restores=[]
   for slot in ob.material_slots:
    # Do not alter another object sharing this painted fill.
    if kind=='AO':slot.material=slot.material.copy()
    ma=slot.material;n=ma.node_tree.nodes;l=ma.node_tree.links;out=n.get('Material Output')
    tex=n.new('ShaderNodeTexImage');tex.image=image;n.active=tex
    previous=out.inputs['Surface'].links[0].from_socket
    em=None
    if kind=='CURVATURE':
     geom=n.new('ShaderNodeNewGeometry');em=n.new('ShaderNodeEmission');l.new(geom.outputs['Pointiness'],em.inputs[0]);l.new(em.outputs[0],out.inputs['Surface'])
    restores.append((ma,previous,em))
   bpy.ops.object.bake(type='AO' if kind=='AO' else 'EMIT',margin=4,use_clear=True)
   path=folder/(name.removeprefix('GEO-').replace(' ','-')+'-'+kind.lower()+'.png');image.filepath_raw=str(path);image.file_format='PNG';image.save();image.pack();maps[kind]=image
   for ma,previous,em in restores:
    ma.node_tree.links.new(previous,ma.node_tree.nodes.get('Material Output').inputs['Surface'])
  for slot in ob.material_slots:
   n=slot.material.node_tree.nodes;l=slot.material.node_tree.links;p=n.get('Principled BSDF');uvnode=n.new('ShaderNodeUVMap');uvnode.uv_map='SurfaceBake'
   ao=n.new('ShaderNodeTexImage');ao.image=maps['AO'];l.new(uvnode.outputs[0],ao.inputs[0])
   mix=n.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=.25
   if p.inputs['Base Color'].is_linked:l.new(p.inputs['Base Color'].links[0].from_socket,mix.inputs[1])
   else:mix.inputs[1].default_value=p.inputs['Base Color'].default_value
   l.new(ao.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],p.inputs['Base Color'])
   curvature=n.new('ShaderNodeTexImage');curvature.image=maps['CURVATURE'];l.new(uvnode.outputs[0],curvature.inputs[0]);ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(.85,.85,.85,1);ramp.color_ramp.elements[1].color=(.35,.35,.35,1);l.new(curvature.outputs[0],ramp.inputs[0]);l.new(ramp.outputs[0],p.inputs['Roughness'])
  for m in disabled:m.show_render=True
  report[name]={k:im.filepath_raw for k,im in maps.items()}
 sc.cycles.samples=old_samples;(M/'bakes.json').write_text(json.dumps(report,indent=2));log('Baked real 256px Cycles AO and Pointiness curvature for helmet and jacket; physical recess grime and edge roughness applied.')


def project():
 """Freeze finished-surface UVs; camera-only pigment avoids double illumination."""
 bake_surface_maps()
 sc=bpy.context.scene;cam=sc.camera;im=bpy.data.images.load(str(A/'projection.png'),check_existing=True);records=[]
 for o in list(sc.objects):
  if o.type!='MESH' or any(x in o.name for x in ('muzzle','eyes','stationary cream base')):continue
  mods=[m for m in o.modifiers if m.type!='ARMATURE' and m.show_viewport]
  for m in mods:m.show_viewport=False
  bpy.context.view_layer.update();ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();assert len(me.vertices)==len(o.data.vertices)
  normalmat=ev.matrix_world.to_3x3().inverted().transposed()
  vertices=[(ev.matrix_world @ v.co,(normalmat @ v.normal).normalized()) for v in me.vertices];ev.to_mesh_clear()
  # Restore helper masks before ray casting: hidden MPFB helpers are not occluders.
  for m in mods:m.show_viewport=True
  bpy.context.view_layer.update()
  coords=[world_to_camera_view(sc,cam,w) for w,n in vertices]
  uv=o.data.uv_layers.get('Painting') or o.data.uv_layers.new(name='Painting');col=o.data.color_attributes.new(name='Projection facing',type='FLOAT_COLOR',domain='CORNER')
  facing=[]
  deps=bpy.context.evaluated_depsgraph_get()
  for w,normal in vertices:
   direction=(cam.location-w).normalized()
   f=max(0,min(1,(normal.dot(direction)+.05)/.3))
   hit,loc,n,idx,obj,matr=sc.ray_cast(deps,w+direction*.002,direction,distance=(cam.location-w).length)
   if hit and (obj!=o or (loc-w).length>.015):f=0
   facing.append(f)
  for loop in o.data.loops:
   i=loop.vertex_index;uv.data[loop.index].uv=(coords[i].x,coords[i].y);f=facing[i];col.data[loop.index].color=(f,f,f,1)
  for m in mods:m.show_viewport=True
  for slot in o.material_slots:
   if not slot.material:continue
   ma=slot.material.copy();slot.material=ma;n=ma.node_tree.nodes;l=ma.node_tree.links;p=n.get('Principled BSDF');out=n.get('Material Output')
   if p is None:continue
   tc=n.new('ShaderNodeUVMap');tc.uv_map='Painting';tex=n.new('ShaderNodeTexImage');tex.image=im;tex.extension='CLIP';l.new(tc.outputs[0],tex.inputs[0])
   attr=n.new('ShaderNodeVertexColor');attr.layer_name=col.name
   alpha=n.new('ShaderNodeMath');alpha.operation='MULTIPLY';l.new(attr.outputs[0],alpha.inputs[0]);l.new(tex.outputs['Alpha'],alpha.inputs[1])
   camera=n.new('ShaderNodeLightPath');weight=n.new('ShaderNodeMath');weight.operation='MULTIPLY';l.new(alpha.outputs[0],weight.inputs[0]);l.new(camera.outputs['Is Camera Ray'],weight.inputs[1])
   strength=n.new('ShaderNodeMath');strength.operation='MULTIPLY';strength.inputs[1].default_value=.98;l.new(weight.outputs[0],strength.inputs[0])
   pigment=n.new('ShaderNodeEmission');pigment.name='Camera painted illumination';l.new(tex.outputs['Color'],pigment.inputs['Color'])
   mix=n.new('ShaderNodeMixShader');l.new(strength.outputs[0],mix.inputs[0]);l.new(p.outputs[0],mix.inputs[1]);l.new(pigment.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],out.inputs['Surface'])
  records.append(o.name)
 bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(M/'infantry.blend'));(M/'projection.json').write_text(json.dumps({'objects':records,'method':'finished rest-camera UV, ray visibility/facing/source-alpha, camera-only painted illumination','weight':.98,'hidden_surfaces':'original generated painted fills'},indent=2));log('Finished-surface camera projection with camera-only pigment; generated hidden fills retained.')


def animate(clip):
 global rig
 bpy.ops.wm.open_mainfile(filepath=str(M/'infantry.blend'));rig=bpy.data.objects['RIG-Infantry MPFB'];gun=bpy.data.objects['CTRL-rifle'];sc=configure();count,fps,loop=CLIPS[clip];sc.render.fps=fps;sc.frame_start=1;sc.frame_end=count
 rest={n:Matrix(m) for n,m in json.loads(rig['rest_pose']).items()}
 for p in rig.pose.bones:p.rotation_mode='XYZ';p.matrix_basis=rest[p.name].copy()
 loc=Vector(rig['rest_location']);gw=gun.matrix_world.copy();gb=gun.matrix_basis.copy()
 if clip=='death':gun.parent=None;gun.matrix_world=gw
 grenade=bpy.data.objects['CTRL-grenade'];grw=grenade.matrix_world.copy()
 if clip=='attack':grenade.parent=None;grenade.matrix_world=grw
 right_hand=rig.pose.bones['hand_r'].matrix.copy()
 stock=bpy.data.objects['GEO-walnut rifle stock'];points=[stock.matrix_world @ v.co for v in stock.data.vertices]
 motion_frames=None;motion_source={'provider':'Original weapon-specific grenade throw'}
 if clip!='attack':
  # Full-rate donor samples allow stable contact classification before output resampling.
  phases=[0.0]*24+[i/48 for i in range(49)]
  motion_frames,motion_source=prepare(rig,R,clip,phases)
  for p in rig.pose.bones:p.matrix_basis=rest[p.name].copy()
  bpy.context.view_layer.update()
 # The rifle stays in the left palm; the authored throw releases the right-hand grenade.
 frames=count+1 if loop else count
 for idx in range(frames):
  sc.frame_set(idx+1)
  for p in rig.pose.bones:p.matrix_basis=rest[p.name].copy()
  rig.location=loc.copy();rig.rotation_euler=(0,0,0);gun.matrix_basis=gb.copy() if clip!='death' else gw.copy();bpy.context.view_layer.update();t=idx/count if loop else idx/(count-1);s=sin(2*pi*t)
  if clip!='attack':
   sample=min(72,24+round(t*48))
   motion=motion_frames[sample];rig.location=loc+motion['root'];apply_matrices(rig,motion['matrices'])
   if clip=='death' and idx==0:
    rig.location=loc.copy()
    for bone in rig.pose.bones:bone.matrix_basis=rest[bone.name].copy()
   bpy.context.view_layer.update()
   if clip=='move':
    # Root height correction preserves captured foot rotations and virtual-ground stride.
    flags=motion_source['contact']['planted'].get(str(sample+1),{})
    support=next((side for side in ('l','r') if flags.get(side)),None)
    if support:
     boot=bpy.data.objects['GEO-boot sole '+support];ev=boot.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();lowest=min((ev.matrix_world@v.co).z for v in me.vertices);ev.to_mesh_clear();rig.location.z+=.086-lowest
  elif clip=='attack':
   # Only the weapon-specific throw is authored. Anticipate, release, follow through.
   targets=[(-.36,-.07,2.00),(-.38,.02,2.00),(-.42,.12,1.94),(-.37,-.20,2.00),(-.22,-.44,1.84),(-.15,-.48,1.65),(-.19,-.35,1.51),(-.29,-.22,1.57),(-.35,-.11,1.82),(-.36,-.07,2.00)]
   limb('upperarm_r','lowerarm_r',targets[idx],(-.45,-.10,1.71))
   aim('hand_r',(-.02,-.03,.10))
   bpy.context.view_layer.update()
   if idx<4:
    # Reconstruct the same bone attachment transform without a parent switch midclip.
    hand=rig.matrix_world @ rig.pose.bones['hand_r'].matrix
    hand0=rig.matrix_world @ right_hand
    grenade.matrix_world=hand @ hand0.inverted() @ grw
    release=grenade.matrix_world.copy()
   else:
    grenade.matrix_world=release.copy()
    u=(idx-3)/6
    grenade.location+=Vector((-.2*u,-1.5*u,.7*u-1.1*u*u))
   for obj in grenade.children:
    obj.hide_render=idx>=6;obj.keyframe_insert('hide_render',frame=idx+1)
   grenade.keyframe_insert('location',frame=idx+1);grenade.keyframe_insert('rotation_euler',frame=idx+1)
  if clip=='death':
   from mathutils import Quaternion
   fall=max(0,min(1,t/.65));ease=fall*fall*(3-2*fall)
   center=sum(points,Vector())/len(points);rotation=Quaternion().slerp(Matrix.Rotation(pi/2,4,'Y').to_quaternion(),ease)
   target=center.lerp(Vector((0,-.20,.14)),ease)
   gun.matrix_world=Matrix.Translation(target) @ rotation.to_matrix().to_4x4() @ Matrix.Translation(-center) @ gw
  bpy.context.view_layer.update()
  if clip=='death' and t>0:
   # Settle the evaluated figure on the actual offset disc/world ground.
   base=bpy.data.objects['GEO-stationary cream base'];invbase=base.matrix_world.inverted();deps=bpy.context.evaluated_depsgraph_get();lift=-10
   for obj in sc.objects:
    if obj.type!='MESH' or obj==base or 'muzzle' in obj.name or obj.parent==gun:continue
    ev=obj.evaluated_get(deps);me=ev.to_mesh()
    for v in me.vertices:
     w=ev.matrix_world @ v.co;local=invbase @ w;floor=.085 if local.x**2+local.y**2<.48**2 else .01
     lift=max(lift,floor-w.z)
    ev.to_mesh_clear()
   rig.location.z+=lift*min(1,t/.5)
   bpy.context.view_layer.update()
  for p in rig.pose.bones:
   p.keyframe_insert('location',frame=idx+1)
   p.keyframe_insert('rotation_quaternion' if p.rotation_mode=='QUATERNION' else 'rotation_euler',frame=idx+1);p.keyframe_insert('scale',frame=idx+1)
  rig.keyframe_insert('location',frame=idx+1);rig.keyframe_insert('rotation_euler',frame=idx+1)
  gun.keyframe_insert('location',frame=idx+1);gun.keyframe_insert('rotation_euler' if gun.rotation_mode!='QUATERNION' else 'rotation_quaternion',frame=idx+1)
 # Keep every action editable, with proper loop endpoint and no sampled duplicate endpoint.
 if rig.animation_data:rig.animation_data.action.name='Infantry '+clip
 sc.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(M/'clips'/f'{clip}.blend'))
 (M/'clips'/f'{clip}.json').write_text(json.dumps({'frames':count,'fps':fps,'loop':loop,'source_sha256':hashlib.sha256((M/'infantry.blend').read_bytes()).hexdigest(),'motion':motion_source}));log('Retargeted CC0 / weapon-layer and saved '+clip+' action ('+str(count)+' output frames).')


def render(stage,blend,frames):
 bpy.ops.wm.open_mainfile(filepath=str(blend));sc=configure();assert sc.camera
 out=M/'renders'/stage;out.mkdir(exist_ok=True);manifest=out/'render.json';manifest.unlink(missing_ok=True)
 if stage=='b-plain':
  clay=mat('plain clay',(.45,.4,.32));sc.view_layers[0].material_override=clay
 for i,f in enumerate(frames):
  sc.frame_set(f)
  if stage=='e-death' and i==len(frames)-1:
   import shutil;shutil.copyfile(out/f'{i-1:02}.png',out/f'{i:02}.png');continue
  sc.render.filepath=str(out/f'{i:02}.png');bpy.ops.render.render(write_still=True)
 manifest.write_text(json.dumps({'stage':stage,'engine':sc.render.engine,'device':sc.cycles.device,'samples':sc.cycles.samples,'resolution':sc.render.resolution_x,'blend_sha256':hashlib.sha256(blend.read_bytes()).hexdigest(),'frames':len(frames)}))
 subprocess.run([str(R/'venv/bin/python'),str(HERE/'finish.py'),'review',stage],check=True);log('Posted '+stage+' review ('+sc.cycles.device+', '+str(sc.render.resolution_x)+' px).')

def feet():
 bpy.ops.wm.open_mainfile(filepath=str(M/'clips/move.blend'));sc=configure();sc.render.resolution_x=sc.render.resolution_y=160
 cam=sc.camera;out=M/'renders/feet';out.mkdir(exist_ok=True)
 for view,loc,target in [('top',(0,0,4),(0,0,.2)),('front',(0,-4,.32),(0,0,.32))]:
  cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=1.2
  # Isolate lower legs for the walk inspection; retain feet/puttees on real rig.
  for o in sc.objects:
   if o.type in ('MESH','CURVE'):o.hide_render=not any(k in o.name for k in ('boot','lace','puttee','gaiter'))
  for i in range(8):
   sc.frame_set(i+1);sc.render.filepath=str(out/f'{view}-{i:02}.png');bpy.ops.render.render(write_still=True)
 (out/'render.json').write_text(json.dumps({'engine':sc.render.engine,'device':sc.cycles.device,'views':['top','front'],'frames_per_view':8,'resolution':160,'blend_sha256':hashlib.sha256((M/'clips/move.blend').read_bytes()).hexdigest()}))
 subprocess.run([str(R/'venv/bin/python'),str(HERE/'finish.py'),'feet'],check=True)

mode=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'build'
if mode=='feet':feet()
elif mode=='build':
 build();render('b-plain',M/'plain.blend',[1]);bpy.ops.wm.open_mainfile(filepath=str(M/'plain.blend'));project();render('c-textured-lit',M/'infantry.blend',[1])
elif mode=='project':
 bpy.ops.wm.open_mainfile(filepath=str(M/'plain.blend'));project()
elif mode=='b':
 render('b-plain',M/'plain.blend',[1])
elif mode=='c':
 render('c-textured-lit',M/'infantry.blend',[1])
elif mode=='animate':
 for clip in CLIPS:animate(clip)
elif mode.startswith('animate-'):
 animate(mode.removeprefix('animate-'))
elif mode.startswith('e-'):
 clip=mode.removeprefix('e-');n=CLIPS[clip][0];render(mode,M/'clips'/f'{clip}.blend',list(range(1,n+1)))
elif mode=='preview':
 render('d-rig-poses',M/'clips/attack.blend',[1,3,5,7])
 for clip,(n,_,_) in CLIPS.items():render('e-'+clip,M/'clips'/f'{clip}.blend',list(range(1,n+1)))
elif mode=='render':
 for stage,blend,frames in [('b-plain',M/'plain.blend',[1]),('c-textured-lit',M/'infantry.blend',[1]),('d-rig-poses',M/'clips/attack.blend',[1,3,5,7])]:render(stage,blend,frames)
 for clip,(n,_,_) in CLIPS.items():render('e-'+clip,M/'clips'/f'{clip}.blend',list(range(1,n+1)))
else:raise ValueError(mode)
