"""Rifleman: MPFB anatomy, tailored 3D kit, frozen camera UVs and five actions."""
import bpy, math, os, sys, json, hashlib, subprocess
from pathlib import Path
from mathutils import Vector, Matrix
from math import sin, cos, pi
from bpy_extras.object_utils import world_to_camera_view
R=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'))
M=R/'masters/rifleman'; A=R/'assets/rifleman'; V=R/'review/3d-v2'
for p in (M,V,M/'clips',M/'renders'):p.mkdir(parents=True,exist_ok=True)
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from retarget import prepare, apply_matrices
CLIPS={'idle':(8,4,True),'move':(8,6,True),'attack':(10,14,False),'hit':(4,8,False),'death':(10,5,False)}
def log(s):
 with (V/'rifleman-log.md').open('a') as f:f.write('- '+s+'\n')
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
 if fill in ('wool','linen'):p.inputs['Sheen Weight'].default_value=.25
 if name.startswith('cream'):
  pigment=n.new('ShaderNodeEmission');pigment.inputs[0].default_value=(*color,1)
  ray=n.new('ShaderNodeLightPath');weight=n.new('ShaderNodeMath');weight.operation='MULTIPLY';weight.inputs[1].default_value=.65;l.new(ray.outputs['Is Camera Ray'],weight.inputs[0])
  mix=n.new('ShaderNodeMixShader');l.new(weight.outputs[0],mix.inputs[0]);l.new(p.outputs[0],mix.inputs[1]);l.new(pigment.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],n.get('Material Output').inputs['Surface'])
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

def limb_cloth(name,upper,lower,side,material,radii):
 # Continuous weighted cloth across the joint; separate rigid cylinders split at knees.
 a=rig.matrix_world @ rig.pose.bones[upper+'_'+side].head
 b=rig.matrix_world @ rig.pose.bones[lower+'_'+side].head
 c=rig.matrix_world @ rig.pose.bones[lower+'_'+side].tail
 axis=(c-a).normalized();u=axis.cross(Vector((0,1,0))).normalized();v=axis.cross(u).normalized()
 vs=[];fs=[];nr=32;ns=48
 for j in range(nr+1):
  t=j/nr;part=min(1,int(t*2));f=t*2-part;center=a.lerp(b,f) if part==0 else b.lerp(c,f)
  rad=radii[part]*(1-f)+radii[part+1]*f
  for k in range(ns):
   ang=2*pi*k/ns;fold=1+.07*cos(ang*8+sin(t*pi*3))+.035*sin(t*pi*12+ang*2)
   vs.append(tuple(center+(u*cos(ang)+v*sin(ang))*rad*fold))
 for j in range(nr):
  for k in range(ns):i=j*ns+k;n=j*ns+(k+1)%ns;fs.append((i,n,n+ns,i+ns))
 obj=solid(mesh(name,vs,fs,material),.006)
 def weights(point):
  w=max(0,min(1,.5-(point-b).dot(axis)/.18))
  return {upper+'_'+side:w,lower+'_'+side:1-w}
 bind_weights(obj,weights)
 sub=obj.modifiers.new('Cloth joint smoothing','SUBSURF');sub.levels=sub.render_levels=1
 return obj

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
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
 bpy.ops.preferences.addon_enable(module='bl_ext.user_default.mpfb')
 from bl_ext.user_default.mpfb.services.humanservice import HumanService
 from bl_ext.user_default.mpfb.services.targetservice import TargetService
 macro=TargetService.get_default_macro_info_dict();macro.update(gender=1.,age=.40,muscle=.65,weight=.52,height=.5,proportions=.6);macro['race']={'caucasian':1.,'african':0.,'asian':0.}
 body=HumanService.create_human(macro_detail_dict=macro);body.name='GEO-MPFB rifleman anatomy'
 bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();lo=min(v.co.z for v in me.vertices);hi=max(v.co.z for v in me.vertices);ev.to_mesh_clear();body.scale=(1.72/(hi-lo),)*3
 bpy.context.view_layer.objects.active=body;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 rig=HumanService.add_builtin_rig(body,'game_engine');rig.name='RIG-Rifleman MPFB';rig.location.z=.09
 system=R/'blender-user/extensions/.user/user_default/mpfb/data'
 eyes=HumanService.add_mhclo_asset(str(system/'eyes/high-poly/high-poly.mhclo'),body,asset_type='Eyes',subdiv_levels=1,material_type='MAKESKIN');eyes.name='GEO-MPFB eyes'
 skin=mat('warm painted skin',(.5,.29,.14));red=mat('painted indigo wool',(.055,.085,.15),fill='wool');linen=mat('faded blue trousers',(.18,.25,.29),fill='linen');leather=mat('scuffed tan leather',(.10,.075,.045),fill='leather');steel=mat('worn steel',(.26,.28,.31),1,.55);brass=mat('antique brass buttons',(.48,.32,.13),1,.35);wood=mat('walnut rifle stock',(.26,.115,.035));dark=mat('bore and moustache',(.05,.025,.012));stone=mat('cream limestone E9CFA0',(.81485,.62396,.35153),0,.88)
 body.data.materials.clear();body.data.materials.append(skin)
 for p in body.data.polygons:p.use_smooth=True
 sub=body.modifiers.new('Anatomical smoothing','SUBSURF');sub.levels=sub.render_levels=1
 limb('thigh_r','calf_r',(-.29,-.015,.085),(-.31,-.4,.5));limb('thigh_l','calf_l',(.29,.035,.085),(.31,-.4,.5))
 limb('upperarm_r','lowerarm_r',(-.13,-.26,1.12),(-.44,-.12,1.16));limb('upperarm_l','lowerarm_l',(.20,-.25,1.34),(.40,-.09,1.17))
 aim('hand_r',(.06,-.02,-.02));aim('hand_l',(-.025,-.02,.07))
 for side in ('r','l'):
  for digit in ('index','middle','ring','pinky'):
   for k in range(1,4):p=rig.pose.bones[f'{digit}_{k:02d}_{side}'];p.rotation_mode='XYZ';p.rotation_euler.x=.85
 p=rig.pose.bones['head'];p.rotation_mode='XYZ';p.rotation_euler.x=.08;p.rotation_euler.y=.65;bpy.context.view_layer.update()
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
  limb_cloth('continuous wool sleeve '+side,'upperarm','lowerarm',side,red,(.078,.065,.058))
  p=rig.pose.bones['lowerarm_'+side];a=rig.matrix_world @ p.head;b=rig.matrix_world @ p.tail
  tube('turned wool cuff '+side,b.lerp(a,.22),b,(.067,.060,.005),red,'lowerarm_'+side)
  limb_cloth('continuous trousers '+side,'thigh','calf',side,linen,(.099,.080,.068))
  fp=rig.matrix_world @ rig.pose.bones['foot_'+side].head
  attach(sphere('ankle boot '+side,(fp.x,fp.y-.05,.15),(.068,.135,.075),leather),'foot_'+side)
  attach(sphere('boot sole '+side,(fp.x,fp.y-.055,.092),(.071,.14,.018),dark),'foot_'+side)
  for j in range(5):attach(curve('boot lace '+side,[(fp.x-.027,fp.y-.12+j*.019,.198-j*.005),(fp.x+.027,fp.y-.10+j*.019,.193-j*.005)],.002,linen),'foot_'+side)
 # Rounded collar and two substantial crossed leather belts.
 for sign in (-1,1):
  lapel=mesh('folded blue collar',[(sign*.02,-.11,1.65),(sign*.12,-.15,1.61),(sign*.075,-.18,1.53),(sign*.01,-.155,1.57)],[(0,1,2,3)],red);attach(bevel(solid(lapel,.012),.004),'spine_03')
  strap=mesh('crossbelt '+str(sign),[(sign*-.19,-.183,1.22),(sign*-.155,-.193,1.19),(sign*.19,-.15,1.61),(sign*.155,-.14,1.64)],[(0,1,2,3)],leather);attach(bevel(solid(strap,.009),.003),'spine_03')
  for offset in (-.012,.012):
   attach(curve('crossbelt edge stitching',[(sign*(-.17+.34*t)+offset,-.197+.045*t,1.21+.42*t) for t in [i/32 for i in range(33)]],.0013,linen),'spine_03')
 for j in range(5):attach(sphere('coat brass button',(0,-.175,1.17+j*.085),(.010,.006,.010),brass),'spine_03')
 attach(sphere('round crossbelt brass plate',(0,-.204,1.43),(.035,.009,.035),brass),'spine_03')
 for z in (1.085,1.13):attach(curve('belt finished edge',[(.20*sin(a),-.16*cos(a),z) for a in [2*pi*k/96 for k in range(97)]],.017,leather),'pelvis')
 attach(sphere('oval waist buckle',(.015,-.183,1.11),(.033,.008,.022),brass),'pelvis')
 for sign in (-1,1):
  attach(box('cartridge pouch',(sign*.25,-.07,1.05),(.15,.10,.19),leather,.02),'pelvis')
  attach(box('pouch flap',(sign*.25,-.125,1.09),(.145,.018,.10),leather,.015),'pelvis')
  attach(sphere('pouch round brass clasp',(sign*.25,-.14,1.065),(.024,.006,.024),brass),'pelvis')
 # Full volume slouched kepi: soft crown, leather band, short bill, brass fasteners.
 head=rig.pose.bones['head'];hc=rig.matrix_world @ ((head.head+head.tail)*.5);cx,cy,cz=hc
 vs=[];fs=[]
 for j in range(13):
  t=j/12
  for k in range(64):
   a=2*pi*k/64;r=1-.13*t+.04*sin(t*pi*5)
   vs.append((cx+.106*r*sin(a)-.025*t,cy-.115*r*cos(a)+.016*t,cz+.028+.125*t+.012*t*sin(a)))
 for j in range(12):
  for k in range(64):i=j*64+k;n=j*64+(k+1)%64;fs.append((i,n,n+64,i+64))
 fs.append(tuple(range(12*64,13*64)))
 attach(bevel(solid(mesh('kepi folded crown',vs,fs,red),.005),.003),'head')
 attach(curve('kepi welt',vs[-64:]+[vs[-64]],.003,red),'head')
 for z in (cz+.026,cz+.049):attach(curve('kepi leather band',[(cx+.109*sin(a),cy-.117*cos(a),z) for a in [2*pi*k/64 for k in range(65)]],.009,leather),'head')
 vs=[(cx,cy,cz+.02)]+[(cx+.124*sin(a),cy-.168*cos(a),cz+.018-.009*cos(a)) for a in [-pi/2+pi*k/32 for k in range(33)]]
 attach(bevel(solid(mesh('kepi bill',vs,[(0,k,k+1) for k in range(1,33)],leather),.007),.003),'head')
 for sign in (-1,1):attach(sphere('kepi brass fastener',(cx+sign*.082,cy-.078,cz+.045),(.009,.005,.009),brass),'head')
 # Beard and moustache are fitted around the MPFB mouth, then move with the head.
 attach(curve('moustache',[(cx-.038,cy-.100,cz-.071),(cx-.020,cy-.114,cz-.063),(cx,cy-.119,cz-.068),(cx+.024,cy-.112,cz-.064),(cx+.042,cy-.103,cz-.077)],.009,dark),'head')
 for sign in (-1,1):attach(curve('sideburn and beard',[(cx+sign*.075,cy-.045,cz-.02),(cx+sign*.070,cy-.065,cz-.09),(cx+sign*.040,cy-.095,cz-.12),(cx,cy-.10,cz-.135)],.009,leather),'head')
 # Original full-depth rifle, front across the torso: butt, lock, barrel, bands, sling.
 gun=empty('CTRL-rifle',(-.13,-.28,1.12));attach(gun,'hand_r')
 start=Vector((-.195,-.30,.93));end=Vector((.83,-.30,2.05));axis=(end-start).normalized();across=Vector((axis.z,0,-axis.x))
 def gp(t,w=0,y=0):return start+(end-start)*t+across*w+Vector((0,y,0))
 outline=[(0,-.055),(0,.055),(.25,.026),(.36,.025),(.82,.015),(.82,-.015),(.34,-.025),(.24,-.025)]
 vs=[tuple(gp(t,w,y)) for y in (-.025,.025) for t,w in outline];fs=[tuple(range(7,-1,-1)),tuple(range(8,16))]+[(i,(i+1)%8,(i+1)%8+8,i+8) for i in range(8)]
 parent(bevel(mesh('walnut rifle stock',vs,fs,wood),.006),gun)
 parent(curve('rifle barrel',[gp(.30,0,-.034),gp(1,0,-.034)],.012,steel),gun)
 parent(curve('muzzle bore',[gp(.997,0,-.034),gp(1.002,0,-.034)],.006,dark),gun)
 for t in (.50,.76,.92):parent(curve('barrel band',[gp(t,0,-.017),gp(t+.015,0,-.017)],.025,steel),gun)
 parent(curve('hammer lock',[gp(.30,.015,-.057),gp(.31,.052,-.057),gp(.34,.058,-.057)],.008,steel),gun)
 parent(curve('trigger guard',[gp(t,w,-.036) for t,w in [(.27,-.02),(.27,-.065),(.33,-.065),(.35,-.02)]],.0045,steel),gun)
 sling=[]
 for i in range(33):
  t=i/32;point=gp(.32+.40*t,-.018,-.005);point+=Vector((.21*sin(pi*t),0,-.17*sin(pi*t)));sling.append(point)
 vs=[]
 for point in sling:vs.extend([tuple(point+Vector((-.008,0,.006))),tuple(point+Vector((.008,0,-.006)))])
 parent(bevel(solid(mesh('hanging leather rifle sling',vs,[(i*2,i*2+1,i*2+3,i*2+2) for i in range(32)],leather),.004),.0015),gun)
 bpy.ops.mesh.primitive_cylinder_add(vertices=96,radius=.54,depth=.075,location=(0,0,.0475));base=bpy.context.object;base.name='GEO-stationary cream base';base.data.materials.append(stone);base.data.materials.append(mat('cream stone darker rim',(.72,.52,.30),0,.88))
 for face in base.data.polygons:face.material_index=1 if abs(face.normal.z)<.5 else 0
 bevel(base,.012)
 sc=configure();sc.view_settings.view_transform='Standard';sc.world.use_nodes=True;sc.world.node_tree.nodes.get('Background').inputs[0].default_value=(.65,.70,.8,1);sc.world.node_tree.nodes.get('Background').inputs[1].default_value=.25
 bpy.ops.object.camera_add(location=(.16,-8,2.89));cam=bpy.context.object;cam.name='CAM-painting';cam.rotation_euler=(Vector((.16,0,.92))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=2.25;sc.camera=cam
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
 sc['unit']='rifleman';sc['anatomy']='MPFB 2.0.18 CC0';sc['reference']='CC BY 4.0 rifleman-source.png'
 bpy.context.view_layer.update();rig['rest_pose']=json.dumps({p.name:[list(r) for r in p.matrix_basis] for p in rig.pose.bones});rig['rest_location']=list(rig.location);gun['rest_world']=[v for row in gun.matrix_world for v in row]
 bpy.ops.wm.save_as_mainfile(filepath=str(M/'plain.blend'));log('Built MPFB anatomical body, 53-bone rig, blue coat, full-volume kepi, crossed leather belts, diagonal rifle and sling; plain.blend saved.')


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
 for name in ['GEO-kepi folded crown','GEO-field jacket folded wool']:
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
 sc.cycles.samples=old_samples;(M/'bakes.json').write_text(json.dumps(report,indent=2));log('Baked real 256px Cycles AO and Pointiness curvature for kepi and jacket; physical recess grime and edge roughness applied.')


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
 anchor=world_to_camera_view(sc,cam,Vector((0,0,.085)))
 (M/'registration.json').write_text(json.dumps({'ax':anchor.x*160,'ay':(1-anchor.y)*160,'world':[0,0,.085],'meaning':'stationary stone contact center'},indent=2))
 bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(M/'rifleman.blend'));(M/'projection.json').write_text(json.dumps({'objects':records,'method':'finished rest-camera UV, ray visibility/facing/source-alpha, camera-only painted illumination','weight':.98,'hidden_surfaces':'original generated painted fills'},indent=2));log('Finished-surface camera projection with camera-only pigment; generated hidden fills retained.')


def animate(clip):
 global rig
 bpy.ops.wm.open_mainfile(filepath=str(M/'rifleman.blend'));rig=bpy.data.objects['RIG-Rifleman MPFB'];gun=bpy.data.objects['CTRL-rifle'];sc=configure();count,fps,loop=CLIPS[clip];sc.render.fps=fps;sc.frame_start=1;sc.frame_end=count
 rest={n:Matrix(m) for n,m in json.loads(rig['rest_pose']).items()}
 for p in rig.pose.bones:p.rotation_mode='XYZ';p.matrix_basis=rest[p.name].copy()
 loc=Vector(rig['rest_location']);gw=gun.matrix_world.copy();gb=gun.matrix_basis.copy()
 if clip=='death':gun.parent=None;gun.matrix_world=gw
 # Rifle stays coupled to the right hand; left palm follows its frozen grip.
 right_wrist=rig.matrix_world @ rig.pose.bones['hand_r'].head
 left_wrist=rig.matrix_world @ rig.pose.bones['hand_l'].head
 right_hand=rig.pose.bones['hand_r'].matrix.copy();left_hand=rig.pose.bones['hand_l'].matrix.copy()
 stock=bpy.data.objects['GEO-walnut rifle stock'];points=[stock.matrix_world @ v.co for v in stock.data.vertices];zmin=min(v.z for v in points);bottom=[v for v in points if v.z<zmin+.04];butt=sum(bottom,Vector())/len(bottom)
 motion_frames=None;motion_source={'provider':'Original weapon-specific rifle aim and recoil'}
 if clip!='attack':
  # Full-rate donor samples allow stable contact classification before output resampling.
  phases=[0.0]*24+[i/48 for i in range(49)]
  motion_frames,motion_source=prepare(rig,R,clip,phases)
  for p in rig.pose.bones:p.matrix_basis=rest[p.name].copy()
  bpy.context.view_layer.update()
 # Weapon rests against the right palm. During aim both arms solve toward the weapon.
 frames=count+1 if loop else count
 for idx in range(frames):
  sc.frame_set(idx+1)
  for p in rig.pose.bones:p.matrix_basis=rest[p.name].copy()
  rig.location=loc.copy();rig.rotation_euler=(0,0,0);gun.matrix_basis=gb.copy() if clip!='death' else gw.copy();bpy.context.view_layer.update();t=idx/count if loop else idx/(count-1);s=sin(2*pi*t)
  if clip!='attack':
   sample=min(72,24+round(t*48))
   motion=motion_frames[sample];rig.location=loc+motion['root'];apply_matrices(rig,motion['matrices'])
   bpy.context.view_layer.update()
   if clip=='move':
    # Root height correction preserves captured foot rotations and virtual-ground stride.
    flags=motion_source['contact']['planted'].get(str(sample+1),{})
    support=next((side for side in ('l','r') if flags.get(side)),None)
    if support:
     boot=bpy.data.objects['GEO-boot sole '+support];ev=boot.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();lowest=min((ev.matrix_world @ v.co).z for v in me.vertices);ev.to_mesh_clear();rig.location.z+=.086-lowest
  elif clip=='attack':
   # Aim, settle, fire/recoil, recover. Whole weapon remains attached to the hand.
   amount=[0,.25,.65,1,1,.90,.95,.60,.20,0][idx]
   pivot=right_wrist
   rot=Matrix.Rotation(.65*amount,4,'Y')
   desired=Matrix.Translation(pivot+Vector((.06*amount,0,.35*amount))) @ rot @ Matrix.Translation(-pivot) @ gw
   # Move both hands by the same rigid weapon transform.
   delta=desired @ gw.inverted()
   for side,wrist,pole in [('r',right_wrist,(-.43,-.12,1.18)),('l',left_wrist,(.42,-.10,1.22))]:
    target=delta @ wrist-rig.location
    limb('upperarm_'+side,'lowerarm_'+side,target,pole)
   bpy.context.view_layer.update()
   # The attached gun follows the right-hand aim with a stable rest grip transform.
   hand=rig.pose.bones['hand_r'];handmat=rig.matrix_world.inverted() @ delta @ rig.matrix_world @ right_hand;handmat.translation=hand.head.copy();hand.matrix=handmat
   bpy.context.view_layer.update();gun.matrix_world=desired
  if clip=='death':
   from mathutils import Quaternion
   fall=max(0,min(1,t/.65));ease=fall*fall*(3-2*fall)
   center=sum(points,Vector())/len(points);rotation=Quaternion().slerp(Matrix.Rotation(pi/2,4,'X').to_quaternion(),ease)
   target=center.lerp(Vector((0,-.20,.14)),ease)
   gun.matrix_world=Matrix.Translation(target) @ rotation.to_matrix().to_4x4() @ Matrix.Translation(-center) @ gw
  bpy.context.view_layer.update()
  if clip!='death':
   weapon_delta=gun.matrix_world @ gw.inverted()
   limb('upperarm_l','lowerarm_l',weapon_delta @ left_wrist-rig.location,(.42,-.10,1.18))
   p=rig.pose.bones['hand_l'];hm=rig.matrix_world.inverted() @ weapon_delta @ rig.matrix_world @ left_hand;hm.translation=p.head.copy();p.matrix=hm
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
 if rig.animation_data:rig.animation_data.action.name='Rifleman '+clip
 sc.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(M/'clips'/f'{clip}.blend'))
 (M/'clips'/f'{clip}.json').write_text(json.dumps({'frames':count,'fps':fps,'loop':loop,'source_sha256':hashlib.sha256((M/'rifleman.blend').read_bytes()).hexdigest(),'motion':motion_source}));log('Retargeted CC0 / weapon-layer and saved '+clip+' action ('+str(count)+' output frames).')


def render(stage,blend,frames):
 bpy.ops.wm.open_mainfile(filepath=str(blend));sc=configure();assert sc.camera
 out=M/'renders'/stage;out.mkdir(exist_ok=True);manifest=out/'render.json';manifest.unlink(missing_ok=True)
 if stage=='b-plain':
  frames=[1,1,1]
  clay=mat('plain clay',(.45,.4,.32));sc.view_layers[0].material_override=clay
 for i,f in enumerate(frames):
  if stage=='b-plain' and i>0:
   sc.camera.location=(4,-4,2.0) if i==1 else (4,1,1.8)
   sc.camera.rotation_euler=(Vector((0,0,1.03))-sc.camera.location).to_track_quat('-Z','Y').to_euler()
   sc.camera.data.ortho_scale=2.50
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
  # Isolate lower legs for the walk inspection; retain feet and trouser hems on real rig.
  for o in sc.objects:
   if o.type in ('MESH','CURVE'):o.hide_render=not any(k in o.name for k in ('boot','lace'))
  for i in range(8):
   sc.frame_set(i+1);sc.render.filepath=str(out/f'{view}-{i:02}.png');bpy.ops.render.render(write_still=True)
 subprocess.run([str(R/'venv/bin/python'),str(HERE/'finish.py'),'feet'],check=True)

mode=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'build'
if mode=='feet':feet()
elif mode=='build':
 build();render('b-plain',M/'plain.blend',[1]);bpy.ops.wm.open_mainfile(filepath=str(M/'plain.blend'));project();render('c-textured-lit',M/'rifleman.blend',[1])
elif mode=='project':
 bpy.ops.wm.open_mainfile(filepath=str(M/'plain.blend'));project()
elif mode=='b':
 render('b-plain',M/'plain.blend',[1])
elif mode=='c':
 render('c-textured-lit',M/'rifleman.blend',[1])
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
 for stage,blend,frames in [('b-plain',M/'plain.blend',[1]),('c-textured-lit',M/'rifleman.blend',[1]),('d-rig-poses',M/'clips/attack.blend',[1,3,5,7])]:render(stage,blend,frames)
 for clip,(n,_,_) in CLIPS.items():render('e-'+clip,M/'clips'/f'{clip}.blend',list(range(1,n+1)))
else:raise ValueError(mode)
