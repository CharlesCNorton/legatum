"""Trench infantry: MPFB anatomy, tailored 3D kit, frozen camera UVs and five actions."""
import bpy, math, os, sys, json, hashlib, subprocess
from pathlib import Path
from mathutils import Vector, Matrix
from math import sin, cos, pi
from bpy_extras.object_utils import world_to_camera_view
R=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'))
M=R/'masters/trench-infantry'; A=R/'assets/trench-infantry'; V=R/'review/3d-v2'
for p in (M,V,M/'clips',M/'renders'):p.mkdir(parents=True,exist_ok=True)
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from retarget import prepare, apply_matrices
import refine
CLIPS={'idle':(8,4,True),'move':(8,6,True),'attack':(10,14,False),'hit':(4,8,False),'death':(10,5,False)}
def log(s):
 with (V/'trench-infantry-log.md').open('a') as f:f.write('- '+s+'\n')
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
  # Hidden-surface pigments have their own brushwork; retain live product light
  # and cavity shade without washing the generated colour to flat grey.
  ao=n.new('ShaderNodeAmbientOcclusion');ao.inputs['Distance'].default_value=.05
  shade=n.new('ShaderNodeMixRGB');shade.blend_type='MULTIPLY';shade.inputs[0].default_value=.3;l.new(t.outputs['Color'],shade.inputs[1]);l.new(ao.outputs['Color'],shade.inputs[2])
  pigment=n.new('ShaderNodeEmission');l.new(shade.outputs[0],pigment.inputs[0])
  ray=n.new('ShaderNodeLightPath');weight=n.new('ShaderNodeMath');weight.operation='MULTIPLY';weight.inputs[1].default_value=.65;l.new(ray.outputs['Is Camera Ray'],weight.inputs[0])
  mix=n.new('ShaderNodeMixShader');l.new(weight.outputs[0],mix.inputs[0]);l.new(p.outputs[0],mix.inputs[1]);l.new(pigment.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],n.get('Material Output').inputs[0])
 if fill in ('wool','linen'):p.inputs['Sheen Weight'].default_value=.25
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

def sleeve(side):
 # One continuous skinned sleeve, with shared elbow rings and real fold volume.
 a=rig.matrix_world @ rig.pose.bones['upperarm_'+side].head
 b=rig.matrix_world @ rig.pose.bones['lowerarm_'+side].head
 c=rig.matrix_world @ rig.pose.bones['lowerarm_'+side].tail
 vs=[];fs=[];rings=33;segments=48
 for j in range(rings):
  t=j/(rings-1)
  if t<.5:center=a.lerp(b,t*2);axis=(b-a).normalized()
  else:center=b.lerp(c,(t-.5)*2);axis=(c-b).normalized()
  # Blend ring frames near elbow; overlapping primitives are not needed.
  blend=max(0,min(1,(t-.36)/.28));axis=(b-a).normalized().lerp((c-b).normalized(),blend).normalized()
  u=axis.cross(Vector((0,1,0))).normalized();v=axis.cross(u).normalized()
  radius=.075+.012*sin(pi*t)-.007*t
  for k in range(segments):
   angle=2*pi*k/segments
   fold=1+.07*cos(angle*7+t*9)+.05*cos(t*35+angle*2)*sin(pi*t)**2
   vs.append(tuple(center+(u*cos(angle)+v*sin(angle))*radius*fold))
 for j in range(rings-1):
  for k in range(segments):i=j*segments+k;n=j*segments+(k+1)%segments;fs.append((i,n,n+segments,i+segments))
 o=solid(mesh('continuous wool sleeve '+side,vs,fs,red),.006)
 # Determine weights before inverse skinning, by known ring membership.
 weights={}
 for j in range(rings):
  t=j/(rings-1);w=max(0,min(1,(t-.38)/.24));weights[j]={'upperarm_'+side:1-w,'lowerarm_'+side:w}
 index=iter(range(len(vs)))
 bind_weights(o,lambda v:weights[next(index)//segments])
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
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
 bpy.ops.preferences.addon_enable(module='bl_ext.user_default.mpfb')
 from bl_ext.user_default.mpfb.services.humanservice import HumanService
 from bl_ext.user_default.mpfb.services.targetservice import TargetService
 macro=TargetService.get_default_macro_info_dict();macro.update(gender=1.,age=.55,muscle=.55,weight=.52,height=.5,proportions=.6);macro['race']={'caucasian':1.,'african':0.,'asian':0.}
 body=HumanService.create_human(macro_detail_dict=macro);body.name='GEO-MPFB trench-infantry anatomy'
 bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();lo=min(v.co.z for v in me.vertices);hi=max(v.co.z for v in me.vertices);ev.to_mesh_clear();body.scale=(1.72/(hi-lo),)*3
 bpy.context.view_layer.objects.active=body;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 rig=HumanService.add_builtin_rig(body,'game_engine');rig.name='RIG-Trench infantry MPFB';rig.location.z=.09
 system=R/'blender-user/extensions/.user/user_default/mpfb/data'
 eyes=HumanService.add_mhclo_asset(str(system/'eyes/high-poly/high-poly.mhclo'),body,asset_type='Eyes',subdiv_levels=1,material_type='MAKESKIN');eyes.name='GEO-MPFB eyes'
 skin=mat('warm painted skin',(.5,.29,.14));red=mat('weathered horizon blue wool',(.22,.25,.28),fill='wool');linen=mat('ochre puttee cloth',(.39,.30,.18),fill='linen');leather=mat('scuffed tan leather',(.30,.14,.055),fill='leather');steel=mat('worn steel',(.26,.28,.31),1,.55);brass=mat('antique brass buttons',(.48,.32,.13),1,.35);wood=mat('walnut rifle stock',(.26,.115,.035));dark=mat('bore and moustache',(.05,.025,.012));stone=mat('cream limestone E9CFA0',(.815,.624,.352),0,.88)
 body.data.materials.clear();body.data.materials.append(skin)
 for p in body.data.polygons:p.use_smooth=True
 sub=body.modifiers.new('Anatomical smoothing','SUBSURF');sub.levels=sub.render_levels=1
 limb('thigh_r','calf_r',(-.17,-.025,.085),(-.22,-.4,.5));limb('thigh_l','calf_l',(.19,.015,.085),(.22,-.4,.5))
 limb('upperarm_r','lowerarm_r',(-.30,-.24,1.13),(-.46,-.03,1.05));limb('upperarm_l','lowerarm_l',(.20,-.26,1.275),(.45,-.03,1.11))
 aim('hand_r',(0,0,.10));aim('hand_l',(-.03,0,.10))
 for side in ('r','l'):
  for digit in ('index','middle','ring','pinky'):
   for k in range(1,4):p=rig.pose.bones[f'{digit}_{k:02d}_{side}'];p.rotation_mode='XYZ';p.rotation_euler.x=.85
 p=rig.pose.bones['head'];p.rotation_mode='XYZ';p.rotation_euler.y=-.35;bpy.context.view_layer.update()
 # Closed, folded coat surface: three-dimensional torso, skirt, lining and hem.
 vs=[];fs=[];rings=[(.46,.325,.17),(.55,.315,.17),(.73,.28,.165),(.91,.225,.15),(1.08,.185,.145),(1.23,.20,.15),(1.39,.235,.155),(1.48,.23,.14),(1.53,.13,.10)]
 for j,(z,rx,ry) in enumerate(rings):
  for k in range(96):
   a=2*pi*k/96;fold=.012*cos(a*10+.22*j)*(1 if j<5 else .45);vs.append(((rx+fold)*sin(a),-(ry+fold)*cos(a),z+.09))
 for j in range(len(rings)-1):
  for k in range(96):i=j*96+k;n=j*96+(k+1)%96;fs.append((i,n,n+96,i+96))
 coat=solid(mesh('greatcoat folded wool',vs,fs,red),.009)
 # Bind garment to torso and thighs, preserving the authored rest shape.
 bind_weights(coat,lambda v:{'spine_03':max(0,min(1,(v.z-1.10)/.22)),'pelvis':max(0,1-abs(v.z-1.03)/.28),'thigh_l' if v.x>0 else 'thigh_r':max(0,min(.8,(1.03-v.z)/.5))})
 for side in ('r','l'):
  sleeve(side)
  p=rig.pose.bones['lowerarm_'+side];a=rig.matrix_world @ p.head;b=rig.matrix_world @ p.tail
  tube('turned wool cuff '+side,b.lerp(a,.22),b,(.087,.077,.005),red,'lowerarm_'+side)
  p=rig.pose.bones['thigh_'+side];a=rig.matrix_world @ p.head;b=rig.matrix_world @ p.tail
  tube('wool trousers '+side,a,b,(.095,.079,.015),red,'thigh_'+side)
  p=rig.pose.bones['calf_'+side];a=rig.matrix_world @ p.head;b=rig.matrix_world @ p.tail
  tube('wrapped puttees '+side,a,b,(.071,.043,.006),linen,'calf_'+side)
  for j in range(11):
   t=.13+j*.073;c=a.lerp(b,t);rad=.071*(1-t)+.043*t+.002
   attach(curve('puttee overlap '+side,[(c.x+rad*cos(q),c.y+rad*sin(q),c.z+.008*sin(q)) for q in [2*pi*k/32 for k in range(33)]],.0025,linen),'calf_'+side)
  fp=rig.matrix_world @ rig.pose.bones['foot_'+side].head
  attach(sphere('ankle boot '+side,(fp.x,fp.y-.05,.15),(.068,.135,.075),leather),'foot_'+side)
  attach(sphere('boot sole '+side,(fp.x,fp.y-.055,.092),(.071,.14,.018),dark),'foot_'+side)
  for j in range(5):attach(curve('boot lace '+side,[(fp.x-.027,fp.y-.12+j*.019,.198-j*.005),(fp.x+.027,fp.y-.10+j*.019,.193-j*.005)],.002,linen),'foot_'+side)
 # Thick lapels and shoulder webbing, separate edges and brass fasteners.
 for sign in (-1,1):
  lapel=mesh('folded greatcoat lapel',[(sign*.04,-.11,1.64),(sign*.15,-.145,1.58),(sign*.10,-.176,1.48),(sign*.01,-.15,1.55)],[(0,1,2,3)],red);attach(bevel(solid(lapel,.012),.004),'spine_03')
  strap=mesh('pack shoulder strap',[(sign*.19,-.10,1.54),(sign*.145,-.13,1.54),(sign*.12,-.18,1.12),(sign*.16,-.17,1.12)],[(0,1,2,3)],leather);attach(bevel(solid(strap,.014),.004),'spine_03')
  for j in range(5):attach(sphere('greatcoat brass button',(sign*.067,-.168,1.08+j*.105),(.012,.008,.012),brass),'spine_03')
 attach(bevel(solid(mesh('diagonal leather baldric',[(-.17,-.179,1.15),(-.14,-.186,1.12),(.19,-.174,1.57),(.16,-.17,1.60)],[(0,1,2,3)],leather),.012),.003),'spine_03')
 for z in (1.085,1.13):attach(curve('belt finished edge',[(.20*sin(a),-.16*cos(a),z) for a in [2*pi*k/96 for k in range(97)]],.013,leather),'pelvis')
 for i in range(3):
  x=-.135+i*.135;attach(box('cartridge pouch',(x,-.195,1.10),(.12,.075,.115),leather,.012),'pelvis');attach(box('pouch flap',(x,-.24,1.14),(.119,.018,.047),leather,.009),'pelvis');attach(sphere('pouch brass stud',(x,-.253,1.12),(.009,.006,.009),brass),'pelvis')
 pack=box('canvas backpack',(.05,.195,1.37),(.39,.24,.45),linen,.045);attach(pack,'spine_03')
 roll=tube('blanket roll',(-.12,.21,1.64),(.28,.21,1.64),(.096,.096,0),linen);attach(roll,'spine_03')
 for x in (-.12,.28):attach(sphere('blanket rolled end',(x,.21,1.64),(.018,.094,.094),linen),'spine_03')
 for x in (-.08,.23):attach(curve('blanket binding',[(x,.21+.101*cos(a),1.64+.101*sin(a)) for a in [2*pi*k/40 for k in range(41)]],.009,leather),'spine_03')
 # Visible rolled layers and stitched edges survive when projection turns away.
 for x in (-.139,.299):
  pts=[]
  for k in range(145):
   a=k*6*pi/144;rad=.012+.077*k/144;pts.append((x,.21+rad*cos(a),1.64+rad*sin(a)))
  attach(curve('blanket spiral seam',pts,.0025,leather),'spine_03')
 for sign in (-1,1):
  pts=[(sign*.145,-.192,1.39),(sign*.18,-.192,1.39),(sign*.18,-.192,1.43),(sign*.145,-.192,1.43),(sign*.145,-.192,1.39)]
  attach(curve('strap buckle',pts,.003,brass),'spine_03')
 attach(box('haversack',(.24,.08,1.02),(.17,.13,.23),linen,.025),'pelvis')
 # Adrian-style full-depth helmet with shallow brim, crest and rolled edge.
 head=rig.pose.bones['head'];hc=rig.matrix_world @ ((head.head+head.tail)*.5);cx,cy,cz=hc
 vs=[];fs=[]
 for j in range(17):
  t=(j/16)*pi/2
  for k in range(64):a=2*pi*k/64;vs.append((cx+.12*cos(t)*sin(a),cy-.14*cos(t)*cos(a),cz+.025+.13*sin(t)))
 for j in range(16):
  for k in range(64):i=j*64+k;n=j*64+(k+1)%64;fs.append((i,n,n+64,i+64))
 attach(bevel(solid(mesh('steel helmet bowl',vs,fs,steel),.006),.002),'head')
 vs=[];fs=[]
 for j in range(4):
  t=j/3
  for k in range(64):
   a=2*pi*k/64;vs.append((cx+(.119+.023*t)*sin(a),cy-(.138+.025*t)*cos(a),cz+.02-.016*t))
 for j in range(3):
  for k in range(64):i=j*64+k;n=j*64+(k+1)%64;fs.append((i,n,n+64,i+64))
 attach(bevel(solid(mesh('helmet flared brim',vs,fs,steel),.005),.002),'head');attach(curve('rolled helmet rim',vs[-64:]+[vs[-64]],.003,steel),'head')
 attach(curve('helmet raised crest',[(cx,cy+.115*sin(a),cz+.03+.144*cos(a)) for a in [-1.2+i*2.4/40 for i in range(41)]],.009,steel),'head')
 attach(curve('painted moustache',[(cx-.04,cy-.108,cz-.065),(cx-.017,cy-.12,cz-.058),(cx,cy-.125,cz-.065),(cx+.025,cy-.114,cz-.059),(cx+.045,cy-.10,cz-.067)],.007,dark),'head')
 # Upright bolt-action rifle and bayonet, with real stock depth and metal fittings.
 gun=empty('CTRL-rifle',(-.32,-.25,1.18));attach(gun,'hand_r')
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
 for name,loc,sz in [('muzzle flash',(-.317,-.283,1.61),(.025,.025,.045)),('muzzle smoke',(-.317,-.283,1.64),(.045,.045,.06))]:
  o=sphere(name,loc,sz,linen);parent(o,gun);o.hide_render=True
 bpy.ops.mesh.primitive_cylinder_add(vertices=96,radius=.48,depth=.075,location=(0,0,.0475));base=bpy.context.object;base.name='GEO-stationary cream base';base.data.materials.append(stone);bevel(base,.012)
 sc=configure();sc.view_settings.view_transform='Standard';sc.world.use_nodes=True;sc.world.node_tree.nodes.get('Background').inputs[0].default_value=(.65,.70,.8,1);sc.world.node_tree.nodes.get('Background').inputs[1].default_value=.25
 bpy.ops.object.camera_add(location=(.3,-8,2.89));cam=bpy.context.object;cam.name='CAM-painting';cam.rotation_euler=(Vector((0,0,.89))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=2.13;sc.camera=cam
 for name,loc,power,size,color in [('key',(-3,-4,5),300,3.,(1,.88,.72)),('fill',(3,-3,3),65,3.,(.83,.9,1)),('rim',(1,2,4),140,2.,(.72,.83,1))]:
  bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name='LGT-'+name;o.data.energy=power;o.data.size=size;o.data.color=color;o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
 # Fit real surfaces in the camera plane, preserving their full depth.
 bpy.context.view_layer.update()
 right=cam.rotation_euler.to_matrix() @ Vector((1,0,0));up=cam.rotation_euler.to_matrix() @ Vector((0,1,0));metres=cam.data.ortho_scale/256
 for o in list(sc.objects):
  if o.type=='CURVE':
   bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
  if o.type!='MESH':continue
  if 'helmet' in o.name:
   for v in o.data.vertices:
    w=o.matrix_world @ v.co;uv=world_to_camera_view(sc,cam,w);y=(1-uv.y)*256;delta=(y-13)*.24
    v.co=o.matrix_world.inverted() @ (w+up*delta*metres)
  if o.parent==gun:
   w=o.matrix_world.copy();w.translation+=right*(4*metres);o.matrix_world=w
  # Finish rigid shell thickness and curves before calculating projection UVs.
  if not any(m.type=='ARMATURE' for m in o.modifiers):
   bpy.context.view_layer.objects.active=o
   for modifier in list(o.modifiers):
    if modifier.type in ('BEVEL','SOLIDIFY','SUBSURF'):bpy.ops.object.modifier_apply(modifier=modifier.name)
 refine.finish(rig,body)
 sc['unit']='trench-infantry';sc['anatomy']='MPFB 2.0.18 CC0';sc['reference']='CC BY 4.0 trench-infantry-source.png'
 bpy.context.view_layer.update();rig['rest_pose']=json.dumps({p.name:[list(r) for r in p.matrix_basis] for p in rig.pose.bones});rig['rest_location']=list(rig.location);gun['rest_world']=[v for row in gun.matrix_world for v in row]
 bpy.ops.wm.save_as_mainfile(filepath=str(M/'plain.blend'));log('Built MPFB anatomical body, 53-bone rig, folded greatcoat, puttees, helmet, webbing and bayonet rifle; plain.blend saved.')


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

def project():
 """Freeze finished-surface UVs; camera-only pigment avoids double illumination."""
 sc=bpy.context.scene;cam=sc.camera;im=bpy.data.images.load(str(A/'projection.png'),check_existing=True);records=[]
 cloth=bpy.data.images.load(str(A/'cloth-projection.png'),check_existing=True)
 refine.stone(sc,bpy.data.images.load(str(A/'stone-projection.png'),check_existing=True))
 view=cam.matrix_world.to_quaternion() @ Vector((0,0,1))
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
   direction=view
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
   substrate=out.inputs['Surface'].links[0].from_socket
   tc=n.new('ShaderNodeUVMap');tc.uv_map='Painting';tex=n.new('ShaderNodeTexImage');tex.image=cloth if 'greatcoat folded' in o.name or 'shoulder strap' in o.name else im;tex.extension='CLIP';l.new(tc.outputs[0],tex.inputs[0])
   attr=n.new('ShaderNodeVertexColor');attr.layer_name=col.name
   alpha=n.new('ShaderNodeMath');alpha.operation='MULTIPLY';l.new(attr.outputs[0],alpha.inputs[0]);l.new(tex.outputs['Alpha'],alpha.inputs[1])
   camera=n.new('ShaderNodeLightPath');weight=n.new('ShaderNodeMath');weight.operation='MULTIPLY';l.new(alpha.outputs[0],weight.inputs[0]);l.new(camera.outputs['Is Camera Ray'],weight.inputs[1])
   strength=n.new('ShaderNodeMath');strength.operation='MULTIPLY';strength.inputs[1].default_value=.98;l.new(weight.outputs[0],strength.inputs[0])
   pigment=n.new('ShaderNodeEmission');pigment.name='Camera painted illumination';l.new(tex.outputs['Color'],pigment.inputs['Color'])
   mix=n.new('ShaderNodeMixShader');l.new(strength.outputs[0],mix.inputs[0]);l.new(substrate,mix.inputs[1]);l.new(pigment.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],out.inputs['Surface'])
  records.append(o.name)
 bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(M/'trench-infantry.blend'));(M/'projection.json').write_text(json.dumps({'objects':records,'method':'finished rest-camera UV, ray visibility/facing/source-alpha, camera-only painted illumination','weight':.98,'hidden_surfaces':'original generated painted fills'},indent=2));log('Finished-surface camera projection with camera-only pigment; generated hidden fills retained.')


def animate(clip):
 global rig
 bpy.ops.wm.open_mainfile(filepath=str(M/'trench-infantry.blend'));rig=bpy.data.objects['RIG-Trench infantry MPFB'];gun=bpy.data.objects['CTRL-rifle'];sc=configure();count,fps,loop=CLIPS[clip];sc.render.fps=fps;sc.frame_start=1;sc.frame_end=count
 rest={n:Matrix(m) for n,m in json.loads(rig['rest_pose']).items()}
 for p in rig.pose.bones:p.rotation_mode='XYZ';p.matrix_basis=rest[p.name].copy()
 loc=Vector(rig['rest_location']);gw=gun.matrix_world.copy();gb=gun.matrix_basis.copy()
 if clip in ('attack','death'):gun.parent=None;gun.matrix_world=gw
 right_wrist=rig.matrix_world @ rig.pose.bones['hand_r'].head
 left_wrist=rig.matrix_world @ rig.pose.bones['hand_l'].head
 right_hand=rig.pose.bones['hand_r'].matrix.copy();left_hand=rig.pose.bones['hand_l'].matrix.copy()
 stock=bpy.data.objects['GEO-walnut rifle stock'];points=[stock.matrix_world @ v.co for v in stock.data.vertices];zmin=min(v.z for v in points);bottom=[v for v in points if v.z<zmin+.04];butt=sum(bottom,Vector())/len(bottom)
 motion_frames=None;motion_source={'provider':'Original weapon-specific bolt-action attack'}
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
  rig.location=loc.copy();rig.rotation_euler=(0,0,0);gun.matrix_basis=gb.copy() if clip not in ('attack','death') else gw.copy();bpy.context.view_layer.update();t=idx/count if loop else idx/(count-1);s=sin(2*pi*t)
  if clip!='attack':
   # Sample the complete impact and recovery instead of stopping in a crouch.
   sample=min(72,24+round(t*48))
   motion=motion_frames[sample];rig.location=loc+motion['root'];apply_matrices(rig,motion['matrices'])
   if clip=='death':
    # Blend from carrying stance into the source's anatomical fall. Keeping the
    # painting's bent elbows/knees as offsets leaves a boot in the air at rest.
    amount=min(1,t/.28)
    for p in rig.pose.bones:
     if p.name.startswith(('thigh_','calf_','foot_','ball_','clavicle_','upperarm_','lowerarm_','hand_')):
      a=rest[p.name];b=p.matrix_basis.copy();p.matrix_basis=a.lerp(b,amount)
   if clip=='hit' and idx==count-1:
    for p in rig.pose.bones:p.matrix_basis=rest[p.name].copy()
    rig.location=loc.copy()
   bpy.context.view_layer.update()
   if clip=='move':
    # Root height correction preserves captured foot rotations and virtual-ground stride.
    flags=motion_source['contact']['planted'].get(str(sample+1),{})
    support=next((side for side in ('l','r') if flags.get(side)),None)
    if support:
     boot=bpy.data.objects['GEO-boot sole '+support];ev=boot.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();lowest=min((ev.matrix_world @ v.co).z for v in me.vertices);ev.to_mesh_clear();rig.location.z+=.086-lowest
  elif clip=='attack':
   # Weapon is a rigid body; hands solve to its trigger and fore-end.
   amount=[0,.28,.72,1,1,1,.92,.65,.27,0][idx]
   direction=Vector((.65,-.73,.18)).normalized()
   q=Vector((0,0,1)).rotation_difference(direction)
   from mathutils import Quaternion
   rot=Quaternion().slerp(q,amount).to_matrix().to_4x4()
   target_butt=butt.lerp(Vector((-.30,.08,1.50)),amount)
   # Tilt before lifting: simultaneous linear lift sends the fixed bayonet
   # through the top of the cell in the two transition samples.
   target_butt.z=butt.z+(1.50-butt.z)*amount*amount
   if idx==5:target_butt-=direction*.035
   transform=Matrix.Translation(target_butt) @ rot @ Matrix.Translation(-butt)
   gun.matrix_world=transform @ gw
   if amount>0:
    # Regrip along the barrel while raising; all coordinates share the gun transform.
    rw=transform @ right_wrist.lerp(butt+Vector((0,-.03,.50)),amount)
    lw=left_wrist.lerp(transform @ (butt+Vector((0,-.03,.78))),amount)
    inv=rig.matrix_world.inverted()
    for side,target,pole,hand in [('r',rw,(-.50,-.10,1.15),right_hand),('l',lw,(.46,-.12,1.18),left_hand)]:
     limb('upperarm_'+side,'lowerarm_'+side,inv @ target,pole)
     p=rig.pose.bones['hand_'+side];pose=hand.copy();orientation=rot.to_3x3() @ hand.to_3x3();pose=orientation.to_4x4();pose.translation=p.head;p.matrix=pose
    bpy.context.view_layer.update()
  if clip=='death':
   from mathutils import Quaternion
   fall=max(0,min(1,t/.65));ease=fall*fall*(3-2*fall)
   center=Vector((-.317,-.25,1.0));rotation=Quaternion().slerp(Matrix.Rotation(pi/2,4,'Y').to_quaternion(),ease)
   target=center.lerp(Vector((0,-.36,.14)),ease)
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
  for name in ('GEO-muzzle flash','GEO-muzzle smoke'):
   o=bpy.data.objects[name];o.hide_render=not(clip=='attack' and idx==(4 if 'flash' in name else 5));o.keyframe_insert('hide_render',frame=idx+1)
 # Keep every action editable, with proper loop endpoint and no sampled duplicate endpoint.
 if rig.animation_data:rig.animation_data.action.name='Trench infantry '+clip
 sc.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(M/'clips'/f'{clip}.blend'))
 (M/'clips'/f'{clip}.json').write_text(json.dumps({'frames':count,'fps':fps,'loop':loop,'source_sha256':hashlib.sha256((M/'trench-infantry.blend').read_bytes()).hexdigest(),'motion':motion_source}));log('Retargeted CC0 / weapon-layer and saved '+clip+' action ('+str(count)+' output frames).')


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
  cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=1.0
  # Isolate lower legs for the walk inspection; retain feet/puttees on real rig.
  for o in sc.objects:
   if o.type in ('MESH','CURVE'):o.hide_render=not any(k in o.name for k in ('boot','lace','puttee'))
  for i in range(8):
   sc.frame_set(i+1);sc.render.filepath=str(out/f'{view}-{i:02}.png');bpy.ops.render.render(write_still=True)
 subprocess.run([str(R/'venv/bin/python'),str(HERE/'finish.py'),'feet'],check=True)

mode=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'build'
if mode=='feet':feet()
elif mode=='build':
 build();render('b-plain',M/'plain.blend',[1]);bpy.ops.wm.open_mainfile(filepath=str(M/'plain.blend'));project();render('c-textured-lit',M/'trench-infantry.blend',[1])
elif mode=='project':
 bpy.ops.wm.open_mainfile(filepath=str(M/'plain.blend'));project()
elif mode=='b':
 render('b-plain',M/'plain.blend',[1])
elif mode=='c':
 render('c-textured-lit',M/'trench-infantry.blend',[1])
elif mode=='d':
 render('d-rig-poses',M/'clips/attack.blend',[1,3,5,7])
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
 for stage,blend,frames in [('b-plain',M/'plain.blend',[1]),('c-textured-lit',M/'trench-infantry.blend',[1]),('d-rig-poses',M/'clips/attack.blend',[1,3,5,7])]:render(stage,blend,frames)
 for clip,(n,_,_) in CLIPS.items():render('e-'+clip,M/'clips'/f'{clip}.blend',list(range(1,n+1)))
else:raise ValueError(mode)
