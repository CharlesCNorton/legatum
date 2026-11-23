"""Musketman: MPFB anatomy, tailored 3D kit, frozen camera UVs and five actions."""
import bpy, math, os, sys, json, hashlib, subprocess
from pathlib import Path
from mathutils import Vector, Matrix
from math import sin, cos, pi
from bpy_extras.object_utils import world_to_camera_view
R=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'))
M=R/'masters/musketman'; A=R/'assets/musketman'; V=R/'review/3d-v2'
for p in (M,V,M/'clips',M/'renders'):p.mkdir(parents=True,exist_ok=True)
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
CLIPS={'idle':(8,4,True),'move':(8,8,True),'attack':(10,14,False),'hit':(4,8,False),'death':(10,8,False)}
def log(s):
 with (V/'musketman-log.md').open('a') as f:f.write('- '+s+'\n')
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
 bpy.context.view_layer.update();w=o.matrix_world.copy();o.parent=pa;o.matrix_parent_inverse=pa.matrix_world.inverted();o.matrix_basis=w;bpy.context.view_layer.update();return o

def attach(o,bone):
 # Bone parent includes the tail offset and potentially nonuniform pose scale.
 # Cancel that complete matrix, avoiding lossy shear decomposition of matrix_world.
 bpy.context.view_layer.update();w=o.matrix_world.copy();o.parent=rig;o.parent_type='BONE';o.parent_bone=bone
 o.matrix_parent_inverse=Matrix.Identity(4);o.matrix_basis=Matrix.Identity(4);bpy.context.view_layer.update()
 o.matrix_parent_inverse=o.matrix_world.inverted();o.matrix_basis=w;bpy.context.view_layer.update();return o

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
 sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device=os.environ.get('CYCLES_DEVICE','CPU');sc.cycles.samples=int(os.environ.get('SAMPLES','6'));sc.cycles.use_denoising=True;sc.cycles.max_bounces=4;sc.cycles.diffuse_bounces=2;sc.render.use_persistent_data=True
 if sc.cycles.device=='GPU':
  prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='METAL';prefs.get_devices();found=False
  for d in prefs.devices:d.use=d.type=='METAL';found|=d.use
  if not found:raise RuntimeError('Metal GPU required; refusing CPU fallback')
 sc.render.threads_mode='FIXED';sc.render.threads=3;sc.render.resolution_x=sc.render.resolution_y=int(os.environ.get('RESOLUTION','256'));sc.render.resolution_percentage=100;sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.use_file_extension=True
 # Standard preserves registered painted pigment; this is not a photographic output.
 sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0
 return sc

# Camera coordinates in the original 256-pixel token. Positive depth is away from camera.
UP=Vector((0,math.sin(math.radians(10)),math.cos(math.radians(10))))
VIEW=Vector((0,-math.cos(math.radians(10)),math.sin(math.radians(10))))
CENTER=Vector((.30,0,.81));SPAN=2.0

def P(x,y,depth=0):return CENTER+Vector(((x-128)*SPAN/256,0,0))+UP*((128-y)*SPAN/256)-VIEW*depth

def setbone(name,a,b,yaw=0):
 p=rig.pose.bones[name];a=Vector(a);b=Vector(b);direction=b-a
 # Orient long axis exactly along target; preserve anatomical roll with rest matrix.
 q=p.bone.matrix_local.to_quaternion();r=(q @ Vector((0,1,0))).rotation_difference(direction.normalized()) @ q
 if yaw:r=__import__('mathutils').Quaternion(direction.normalized(),yaw) @ r
 m=r.to_matrix().to_4x4() @ Matrix.Diagonal((1,direction.length/p.bone.length,1,1));m.translation=rig.matrix_world.inverted() @ a;p.matrix=m;bpy.context.view_layer.update()

def ribbon(name,points,width,ma,bone):
 vs=[]
 for i,p in enumerate(points):
  p=Vector(p);v=Vector(points[min(i+1,len(points)-1)])-Vector(points[max(0,i-1)]);side=v.cross(VIEW).normalized()*width/2;vs.extend([p-side,p+side])
 ob=bevel(solid(mesh(name,vs,[(i*2,i*2+1,i*2+3,i*2+2) for i in range(len(points)-1)],ma),.006),.002)
 return attach(ob,bone)

def build():
 global rig,body,linen,red,leather,steel,brass
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
 bpy.ops.preferences.addon_enable(module='bl_ext.user_default.mpfb')
 from bl_ext.user_default.mpfb.services.humanservice import HumanService
 from bl_ext.user_default.mpfb.services.targetservice import TargetService
 macro=TargetService.get_default_macro_info_dict();macro.update(gender=1.,age=.55,muscle=.65,weight=.53,height=.5,proportions=.6);macro['race']={'caucasian':1.,'african':0.,'asian':0.}
 body=HumanService.create_human(macro_detail_dict=macro);body.name='GEO-MPFB anatomical musketeer'
 bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();lo=min(v.co.z for v in me.vertices);hi=max(v.co.z for v in me.vertices);ev.to_mesh_clear();body.scale=(1.55/(hi-lo),)*3
 bpy.context.view_layer.objects.active=body;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 rig=HumanService.add_builtin_rig(body,'game_engine');rig.name='RIG-Musketman MPFB'
 for bone in rig.data.bones:bone.inherit_scale='NONE'
 system=R/'blender-user/extensions/.user/user_default/mpfb/data';eyes=HumanService.add_mhclo_asset(str(system/'eyes/high-poly/high-poly.mhclo'),body,asset_type='Eyes',subdiv_levels=1,material_type='MAKESKIN');eyes.name='GEO-MPFB eyes'
 skin=mat('painted warm skin',(.49,.265,.12));linen=mat('warm ivory stockings',(.73,.60,.39),fill='linen');red=mat('vermilion wool',(.42,.065,.029),fill='red');leather=mat('scuffed brown hide',(.20,.09,.03),fill='leather');steel=mat('worn gun steel',(.55,.57,.56),1,.38);brass=mat('warm polished brass',(.75,.48,.15),1,.32);wood=mat('walnut gunstock',(.25,.1,.025),fill='leather');dark=mat('hair and felt',(.065,.035,.016),fill='hair');buff=mat('buff leather coat',(.55,.34,.13),fill='buff');stone=mat('cream limestone E9CFA0',(.815,.624,.352),0,.88)
 body.data.materials.clear();body.data.materials.append(skin)
 sub=body.modifiers.new('Anatomical subdivision','SUBSURF');sub.levels=sub.render_levels=1
 for p in body.data.polygons:p.use_smooth=True
 for name,a,b in [('pelvis',P(82,141,.05),P(83,124,.05)),('spine_01',P(83,124,.05),P(86,108,.05)),('spine_02',P(86,108,.05),P(88,89,.05)),('spine_03',P(88,89,.05),P(91,67,.05)),('neck_01',P(91,67,.05),P(98,59,.04)),('head',P(98,59,.04),P(107,39,.04))]:setbone(name,a,b,1.0 if name!='head' else 1.40)
 for side,points in [('r',[(72,135,-.01),(52,169,-.03),(30,204,-.01),(37,214,-.06)]),('l',[(93,137,.12),(117,165,.12),(123,204,.13),(139,213,.08)])]:
  a,b,c,d=[P(*p) for p in points];setbone('thigh_'+side,a,b);setbone('calf_'+side,b,c);setbone('foot_'+side,c,d)
 for side,pts in [('r',[(68,67,-.04),(44,87,-.04),(68,101,-.17),(79,103,-.17)]),('l',[(106,70,.09),(118,91,.07),(133,104,-.14),(143,105,-.14)])]:
  a,b,c,d=[P(*p) for p in pts];setbone('upperarm_'+side,a,b);setbone('lowerarm_'+side,b,c);setbone('hand_'+side,c,d)
 for side in ('r','l'):
  for digit in ('index','middle','ring','pinky'):
   for k in range(1,4):p=rig.pose.bones[f'{digit}_{k:02d}_{side}'];p.rotation_mode='XYZ';p.rotation_euler.x=.75
 bpy.context.view_layer.update()
 # Torso is a closed-volume tailored coat with geometric pleats and a linen collar.
 vs=[];fs=[];ns=64;nr=24
 for j in range(nr+1):
  t=j/nr;center=P(82+9*t,136-72*t,.05);rx=.155+.055*sin(pi*t);ry=.10+.027*sin(pi*t)
  for k in range(ns):
   a=2*pi*k/ns;fold=.007*cos(a*11+2*t)*sin(pi*t);vs.append(center+Vector(((rx+fold)*sin(a),-(ry+fold)*cos(a),0)))
 for j in range(nr):
  for k in range(ns):i=j*ns+k;n=j*ns+(k+1)%ns;fs.append((i,n,n+ns,i+ns))
 attach(bevel(solid(mesh('buff tailored coat',vs,fs,buff),.007),.002),'spine_02')
 for side in ('r','l'):
  for part,r0,r1,bulge in [('upperarm',.081,.075,.021),('lowerarm',.070,.054,.012)]:
   p=rig.pose.bones[part+'_'+side];a=rig.matrix_world @ p.head;b=rig.matrix_world @ p.tail;tube('buff sleeve '+part+' '+side,a,b,(r0,r1,bulge),buff,part+'_'+side)
  p=rig.pose.bones['lowerarm_'+side];a=p.head;b=p.tail;tube('linen turned cuff '+side,b.lerp(a,.3),b,(.078,.066,.008),linen,'lowerarm_'+side)
  p=rig.pose.bones['thigh_'+side];a=p.head;b=p.tail;tube('red breeches '+side,a,b,(.108,.075,.044),red,'thigh_'+side)
  p=rig.pose.bones['calf_'+side];a=p.head;b=p.tail;tube('ivory stocking '+side,a,b,(.074,.039,.007),linen,'calf_'+side)
  ankle=rig.pose.bones['foot_'+side].head
  loc=P(31,209,-.02) if side=='r' else P(132,210,.10)
  boot=attach(sphere('leather boot '+side,loc,(.100,.071,.055),leather),'foot_'+side)
  attach(sphere('boot sole '+side,loc-Vector((0,0,.043)),(.104,.073,.016),dark),'foot_'+side)
  tube('boot cuff '+side,a.lerp(b,.73),b,(.049,.048,.003),leather,'calf_'+side)
  for j in range(5):
   c=a.lerp(b,.76+j*.045);attach(curve('boot leather lacing '+side,[c+Vector((-.042,-.037,.008)),c+Vector((.045,-.035,-.003))],.002,linen),'calf_'+side)
 # Buff coat skirts, thick hem, red baldric and fluttering sash.
 for side in (-1,1):
  vs=[];fs=[]
  for j in range(18):
   t=j/17
   for k in range(9):
    u=k/8;x=82+side*(8+18*t)+(u-.5)*27;y=119+27*t-5*abs(u-.5)*t;vs.append(P(x,y,-.06+.019*sin(k*1.7)))
  for j in range(17):
   for k in range(8):i=j*9+k;fs.append((i,i+1,i+10,i+9))
  attach(solid(mesh('folded coat skirt '+str(side),vs,fs,buff),.007),'pelvis')
 ribbon('red shoulder sash',[P(101,62,-.10),P(97,79,-.14),P(75,98,-.18),P(53,112,-.13)],.073,red,'spine_02')
 for n in range(3):
  vs=[];fs=[]
  for j in range(18):
   t=j/17
   for k in range(4):vs.append(P(52-(24+n*3)*t+(k-1.5)*4+2*sin(t*6+n),113+(36+n*3)*t+3*(k%2)*t**9,-.02+.018*sin(t*7+n)))
  for j in range(17):
   for k in range(3):i=j*4+k;fs.append((i,i+1,i+5,i+4))
  attach(solid(mesh('red sash tail '+str(n),vs,fs,red),.005),'pelvis')
 points=[P(104,63,-.145),P(98,87,-.18),P(86,112,-.19),P(68,134,-.13)]
 ribbon('thick bandolier',points,.030,leather,'spine_02')
 for off in (-.012,.012):attach(curve('bandolier edge stitching',[p+Vector((off,-.002,0)) for p in points],.0018,linen),'spine_02')
 for i in range(7):
  x=72+i*4;y=119-i*6;a=P(x,y,-.20);b=P(x-2,y+12,-.20);attach(curve('wood powder flask '+str(i),[a,b],.013,wood),'spine_02')
  for t in (0,.85):attach(curve('flask brass cap',[a.lerp(b,t),a.lerp(b,t+.12)],.015,brass),'spine_02')
 for x,y in [(82,110),(97,78)]:attach(curve('brass buckle',[P(x-3,y-3,-.22),P(x+3,y-3,-.22),P(x+3,y+3,-.22),P(x-3,y+3,-.22),P(x-3,y-3,-.22)],.003,brass),'spine_02')
 for y in (83,94,119,129):attach(sphere('coat brass button',P(90,y,-.12),(.007,.006,.007),brass),'spine_02')
 for x in (93,103):ribbon('linen collar',[P(x,60,-.10),P(x-3,68,-.12),P(x+2,75,-.13)],.024,linen,'spine_03')
 # Full-depth turned felt brim and crown, red feather with physical vanes/barbs.
 hc=P(102,35,.04);vs=[];fs=[]
 for j in range(8):
  t=j/7
  for k in range(96):
   a=2*pi*k/96;rad=.095+.19*t;vs.append(hc+Vector((rad*sin(a),rad*.62*cos(a),.012*sin(a*2)*t+.032*t**3*cos(a))))
 for j in range(7):
  for k in range(96):i=j*96+k;n=j*96+(k+1)%96;fs.append((i,n,n+96,i+96))
 attach(bevel(solid(mesh('broad felt hat brim',vs,fs,dark),.008),.003),'head');attach(curve('hat worn rolled rim',vs[-96:]+[vs[-96]],.004,leather),'head')
 vs=[];fs=[]
 for j in range(14):
  t=j/13
  for k in range(64):
   a=2*pi*k/64;rad=.107*(1-.15*t);vs.append(hc+Vector((rad*sin(a),rad*.77*cos(a),.115*t+.015*sin(a*2)*t)))
 for j in range(13):
  for k in range(64):i=j*64+k;n=j*64+(k+1)%64;fs.append((i,n,n+64,i+64))
 fs.append(tuple(range(13*64,14*64)));attach(bevel(solid(mesh('pinched felt hat crown',vs,[tuple(reversed(f)) for f in fs],dark),.006),.002),'head')
 attach(curve('hat leather band',[hc+Vector((.110*sin(a),.088*cos(a),.028)) for a in [2*pi*k/96 for k in range(97)]],.010,leather),'head')
 feather=[P(94-29*t,28-10*sin(pi*t)+6*t**3,.055) for t in [k/32 for k in range(33)]];attach(curve('swept feather quill',feather,.002,linen),'head');vs=[];fs=[]
 for k,p in enumerate(feather):
  t=k/32;width=.038*sin(pi*t)**.6
  for side in (-1,0,1):vs.append(p+Vector((-.008*abs(side),.008*abs(side),side*width)))
 for k in range(32):
  for j in range(2):i=k*3+j;fs.append((i,i+1,i+4,i+3))
 attach(solid(mesh('red feather vanes',vs,fs,red),.0015),'head')
 for k in range(1,31):
  t=k/32
  for sg in (-1,1):attach(curve('red feather barb',[feather[k],feather[k]+Vector((-.025,-.003,sg*.040*sin(pi*t)**.5))],.0018,red),'head')
 for k in range(18):
  a=-1.2+k*2.4/17;c=P(99,44,.1);attach(curve('hair lock',[c+Vector((.085*sin(a)+.005*sin(j+k),.075*cos(a),-.012*j)) for j in range(9)],.005,dark),'head')
 attach(curve('moustache',[P(111,53,-.10),P(116,54,-.1),P(119,56,-.1)],.005,dark),'head')
 # Carved solid stock, long cylindrical barrel, flintlock, trigger and socket bayonet.
 gun=empty('CTRL-musket',P(82,104,-.18));attach(gun,'hand_r')
 profile=[(64,110),(83,110),(96,106),(190,106),(190,101),(95,101),(83,103),(64,104)]
 vs=[P(x,y,dep) for dep in (-.145,-.195) for x,y in profile];n=len(profile);fs=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 parent(bevel(mesh('carved walnut musket stock',vs,fs,wood),.003),gun)
 parent(curve('long steel barrel',[P(88,101,-.18),P(218,103,-.18)],.010,steel),gun)
 parent(curve('underbarrel ramrod',[P(96,108,-.19),P(212,109,-.19)],.003,steel),gun)
 for x in (97,160,191,211):parent(curve('steel barrel band',[P(x,102,-.18),P(x+1.5,102,-.18)],.013,steel),gun)
 parent(curve('dark muzzle bore',[P(218,103,-.18),P(219,103,-.18)],.006,dark),gun)
 parent(curve('trigger guard',[P(81,107,-.23),P(83,113,-.23),P(89,113,-.23),P(91,107,-.23)],.0035,steel),gun)
 parent(curve('flintlock hammer',[P(88,103,-.23),P(86,96,-.23),P(91,95,-.23)],.004,steel),gun)
 parent(sphere('flintlock plate',P(85,104,-.23),(.025,.007,.013),steel),gun)
 parent(curve('bayonet socket',[P(211,103,-.18),P(211,108,-.18),P(219,108,-.18)],.005,steel),gun)
 v=[P(216,106,-.18),P(216,110,-.18),P(244,108,-.18),P(216,108,-.192)];parent(bevel(mesh('triangular steel bayonet',v,[(0,1,2),(0,2,3),(1,3,2),(0,3,1)],steel),.0005),gun)
 flash=sphere('muzzle flash',P(223,103,-.18),(.035,.020,.022),mat('flash amber',(.9,.4,.03)));parent(flash,gun);flash.hide_render=True
 for i in range(4):
  smoke=sphere('muzzle smoke '+str(i),P(225+(i%2)*2,101+(i-2)*2,-.17+i*.01),(.025,.026,.035),mat('smoke '+str(i),(.55,.54,.50)));parent(smoke,gun);smoke.hide_render=True
  nodes=smoke.active_material.node_tree.nodes;links=smoke.active_material.node_tree.links;output=nodes.get('Material Output')
  for link in list(output.inputs['Surface'].links):links.remove(link)
  volume=nodes.new('ShaderNodeVolumePrincipled');volume.inputs['Color'].default_value=(.68,.72,.78,1);volume.inputs['Density'].default_value=9;links.new(volume.outputs['Volume'],output.inputs['Volume'])
 bpy.ops.mesh.primitive_cylinder_add(vertices=96,radius=.57,depth=.065,location=(-.015,.04,.0675));base=bpy.context.object;base.name='GEO-stationary cream base';base.data.materials.append(stone);bevel(base,.012)
 nodes=stone.node_tree.nodes;links=stone.node_tree.links;bs=nodes.get('Principled BSDF');output=nodes.get('Material Output')
 ao=nodes.new('ShaderNodeAmbientOcclusion');ao.inputs['Distance'].default_value=.09
 geo=nodes.new('ShaderNodeNewGeometry');separate=nodes.new('ShaderNodeSeparateXYZ');links.new(geo.outputs['Normal'],separate.inputs[0])
 colors=nodes.new('ShaderNodeMixRGB');colors.inputs[1].default_value=(.65,.43,.23,1);colors.inputs[2].default_value=(.815,.624,.352,1);links.new(separate.outputs['Z'],colors.inputs[0]);links.new(colors.outputs[0],ao.inputs['Color'])
 pigment=nodes.new('ShaderNodeEmission');links.new(ao.outputs['Color'],pigment.inputs['Color']);camray=nodes.new('ShaderNodeLightPath');strength=nodes.new('ShaderNodeMath');strength.operation='MULTIPLY';strength.inputs[1].default_value=.65;links.new(camray.outputs['Is Camera Ray'],strength.inputs[0]);mix=nodes.new('ShaderNodeMixShader');links.new(strength.outputs[0],mix.inputs[0]);links.new(bs.outputs[0],mix.inputs[1]);links.new(pigment.outputs[0],mix.inputs[2]);links.new(mix.outputs[0],output.inputs['Surface'])
 sc=configure();sc.world.use_nodes=True;sc.world.node_tree.nodes.get('Background').inputs[0].default_value=(.65,.70,.8,1);sc.world.node_tree.nodes.get('Background').inputs[1].default_value=.3
 bpy.ops.object.camera_add(location=CENTER+VIEW*8);cam=bpy.context.object;cam.name='CAM-painting';cam.rotation_euler=(-VIEW).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=SPAN;sc.camera=cam
 for name,loc,power,size,color in [('key',(-3,-4,5),280,2.8,(1,.96,.88)),('fill',(3,-3,3),56,3.,(.90,.94,1)),('rim',(1,2,4),84,2.,(.84,.91,1))]:
  bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name='LGT-'+name;o.data.energy=power;o.data.size=size;o.data.color=color;o.rotation_euler=(Vector((0,0,.8))-o.location).to_track_quat('-Z','Y').to_euler()
 for o in list(sc.objects):
  if o.type=='CURVE':
   bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
 from refine import finish_surfaces
 finish_surfaces()
 sc['unit']='musketman';sc['anatomy']='MPFB 2.0.18 CC0';sc['cream_target']='#E9CFA0'
 bpy.context.view_layer.update();rig['rest_pose']=json.dumps({p.name:[list(r) for r in p.matrix_basis] for p in rig.pose.bones});rig['rest_location']=list(rig.location)
 (M/'bones.json').write_text(json.dumps({p.name:{'head':list(p.head),'tail':list(p.tail)} for p in rig.pose.bones},indent=2))
 bpy.ops.wm.save_as_mainfile(filepath=str(M/'plain.blend'));log('Built standing MPFB human, buff coat, red breeches/sash, feather hat, bandolier, musket and bayonet.')

def project():
 """Frozen UVs on finished surfaces; original pigment lights camera rays only."""
 sc=bpy.context.scene;cam=sc.camera;im=bpy.data.images.load(str(A/'projection.png'),check_existing=True);records=[]
 dg=bpy.context.evaluated_depsgraph_get()
 for o in list(sc.objects):
  if o.type!='MESH' or any(x in o.name for x in ('muzzle','eyes','stationary cream base')):continue
  ev=o.evaluated_get(dg);me=ev.to_mesh();assert len(me.vertices)==len(o.data.vertices)
  uv=o.data.uv_layers.get('Painting') or o.data.uv_layers.new(name='Painting');col=o.data.color_attributes.new(name='Projection facing',type='FLOAT_COLOR',domain='CORNER')
  coords=[world_to_camera_view(sc,cam,ev.matrix_world @ v.co) for v in me.vertices]
  normalmat=ev.matrix_world.to_3x3().inverted().transposed();facing=[]
  for vertex in me.vertices:
   world=ev.matrix_world @ vertex.co;direction=(cam.location-world).normalized()
   f=max(0,min(1,((normalmat @ vertex.normal).normalized().dot(direction)+.01)/.14))
   if f:
    # Reject paint from a different visible surface at this camera pixel.
    hit,loc,_,_,hitobj,_=sc.ray_cast(dg,world+direction*.001,direction,distance=8)
    if hit and (loc-world).length>.003:f=0
   facing.append(f)
  for loop in o.data.loops:
   i=loop.vertex_index;uv.data[loop.index].uv=(coords[i].x,coords[i].y);f=facing[i];col.data[loop.index].color=(f,f,f,1)
  ev.to_mesh_clear()
  for slot in o.material_slots:
   if not slot.material:continue
   ma=slot.material.copy();slot.material=ma;n=ma.node_tree.nodes;l=ma.node_tree.links;p=n.get('Principled BSDF');out=n.get('Material Output')
   tc=n.new('ShaderNodeUVMap');tc.uv_map='Painting';tex=n.new('ShaderNodeTexImage');tex.image=im;tex.extension='CLIP';l.new(tc.outputs[0],tex.inputs[0])
   attr=n.new('ShaderNodeVertexColor');attr.layer_name=col.name
   mul=n.new('ShaderNodeMath');mul.operation='MULTIPLY';l.new(attr.outputs[0],mul.inputs[0]);l.new(tex.outputs['Alpha'],mul.inputs[1])
   camera=n.new('ShaderNodeLightPath');camera.name='Camera-only pigment'
   weight=n.new('ShaderNodeMath');weight.operation='MULTIPLY';l.new(mul.outputs[0],weight.inputs[0]);l.new(camera.outputs['Is Camera Ray'],weight.inputs[1])
   paint=n.new('ShaderNodeEmission');paint.inputs['Strength'].default_value=1;l.new(tex.outputs['Color'],paint.inputs['Color'])
   blend=n.new('ShaderNodeMixShader');l.new(weight.outputs[0],blend.inputs[0]);l.new(p.outputs[0],blend.inputs[1]);l.new(paint.outputs[0],blend.inputs[2]);l.new(blend.outputs[0],out.inputs['Surface'])
  records.append({'object':o.name,'vertices':len(o.data.vertices),'visible_vertices':sum(v>0 for v in facing)})
 bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(M/'musketman.blend'))
 (M/'projection.json').write_text(json.dumps({'objects':records,'method':'finished surfaces, frozen UV, facing and ray visibility; camera-only pigment','stone':'physical only; no figure paint','hidden_surfaces':'original generated painted fills'},indent=2))
 log('Finished-surface camera-only projection applied; physical stone excluded and generated fills retained.')


def render(stage,blend,frames):
 bpy.ops.wm.open_mainfile(filepath=str(blend));sc=configure();assert sc.camera
 out=M/'renders'/stage;out.mkdir(exist_ok=True);manifest=out/'render.json';manifest.unlink(missing_ok=True)
 if stage.startswith('g-feet-'):
  target=Vector((0,.08,.22));cam=sc.camera
  cam.location=target+Vector((0,0,5) if stage.endswith('top') else (5,0,.18));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=1.35
  for obj in sc.objects:
   if obj.type=='MESH':obj.hide_render=not any(word in obj.name for word in ('boot','stocking','breeches','stationary cream base'))
 if stage=='b-plain':
  clay=mat('plain clay',(.45,.4,.32));sc.view_layers[0].material_override=clay
 for i,f in enumerate(frames):
  sc.frame_set(f)
  if stage=='e-death' and i==len(frames)-1:
   import shutil;shutil.copyfile(out/f'{i-1:02}.png',out/f'{i:02}.png');continue
  sc.render.filepath=str(out/f'{i:02}.png');bpy.ops.render.render(write_still=True)
 manifest.write_text(json.dumps({'stage':stage,'engine':sc.render.engine,'device':sc.cycles.device,'samples':sc.cycles.samples,'resolution':sc.render.resolution_x,'blend_sha256':hashlib.sha256(blend.read_bytes()).hexdigest(),'frames':len(frames)}))
 subprocess.run([str(R/'venv/bin/python'),str(HERE/'finish.py'),'review',stage],check=True);log('Posted '+stage+' review ('+sc.cycles.device+', '+str(sc.render.resolution_x)+' px).')


def animate(clip):
 global rig
 bpy.ops.wm.open_mainfile(filepath=str(M/'musketman.blend'));sc=bpy.context.scene;rig=bpy.data.objects['RIG-Musketman MPFB'];gun=bpy.data.objects['CTRL-musket']
 from motion import Motion, MAP
 from mathutils import Quaternion
 motion=Motion(R) if clip!='attack' else None
 source0=motion.sample(clip,0) if motion else None
 reference=motion.sample('reference',0) if motion else None
 count,fps,loop=CLIPS[clip];sc.render.fps=fps;sc.frame_start=1;sc.frame_end=count
 rest={p.name:p.matrix_basis.copy() for p in rig.pose.bones};restworld={p.name:p.matrix.copy() for p in rig.pose.bones};gunrest=gun.matrix_basis.copy();rigrest=rig.matrix_world.copy()
 grip=gun.matrix_world.inverted() @ rig.pose.bones['hand_l'].matrix
 cloth=[o for o in sc.objects if any(word in o.name for word in ('folded coat skirt','red sash tail'))]
 for p in rig.pose.bones:p.rotation_mode='QUATERNION'
 # Captured source transforms are evaluated in hierarchy order. Target leg axes
 # are matched to the source T pose once, with the MPFB roll retained.
 # Foot references use the authored flat boot contact pose: aligning their
 # ankle-to-ball bone axis would tilt the already flat boot. This is a fixed
 # rest-space offset, not an animation-time foot orientation patch.
 calibrated={}
 for name,origin in MAP.items():
  if not name.startswith(('thigh','calf','foot','ball')):continue
  target=restworld[name].to_quaternion();targetaxis=target @ Vector((0,1,0));sourceaxis=reference[origin].to_quaternion() @ Vector((0,1,0)) if motion else targetaxis
  calibrated[name]=target if name.startswith(('foot','ball')) else targetaxis.rotation_difference(sourceaxis) @ target
 def constrain_grip():
  target_matrix=gun.matrix_world @ grip;target=rig.matrix_world.inverted() @ target_matrix.translation;a=rig.pose.bones['upperarm_l'].head.copy()
  l1=(restworld['lowerarm_l'].translation-restworld['upperarm_l'].translation).length;l2=(restworld['hand_l'].translation-restworld['lowerarm_l'].translation).length
  axis=target-a;distance=min(axis.length,l1+l2-.00001);axis.normalize();along=(l1*l1-l2*l2+distance*distance)/(2*distance)
  pole=rig.pose.bones['lowerarm_l'].head-a;side=(pole-axis*pole.dot(axis)).normalized();elbow=a+along*axis+max(0,l1*l1-along*along)**.5*side
  setbone('upperarm_l',a,elbow);setbone('lowerarm_l',elbow,target);rig.pose.bones['hand_l'].matrix=rig.matrix_world.inverted() @ target_matrix;bpy.context.view_layer.update()
 def turn(name,axis,angle):
  p=rig.pose.bones[name];m=p.matrix.copy();pos=m.translation.copy();m=Matrix.Rotation(angle,4,axis) @ m;m.translation=pos;p.matrix=m;bpy.context.view_layer.update()
 def floor_body(words):
  zs=[];dg=bpy.context.evaluated_depsgraph_get()
  for o in sc.objects:
   if o.type!='MESH' or o.hide_render or not any(w in o.name for w in words):continue
   ev=o.evaluated_get(dg);me=ev.to_mesh();zs.extend((ev.matrix_world @ v.co).z for v in me.vertices);ev.to_mesh_clear()
  if zs:rig.location.z+=.104-min(zs);bpy.context.view_layer.update()
 for i in range(count+(1 if loop else 0)):
  frame=i+1;t=i/count if loop else min(i/(count-2),1)
  rig.matrix_world=rigrest;gun.matrix_basis=gunrest
  for p in rig.pose.bones:p.matrix_basis=rest[p.name]
  bpy.context.view_layer.update()
  if motion:
   phase=([0,.45,.8,1][i] if clip=='hit' else t)
   source=motion.sample(clip,phase);hipdelta=source['DEF-hips'].to_quaternion() @ source0['DEF-hips'].to_quaternion().inverted()
   carry=motion.sample('idle',phase) if clip=='move' else source;carry0=motion.sample('idle',0) if clip=='move' else source0
   for name,origin in MAP.items():
    if name=='pelvis':continue
    leg=name.startswith(('thigh','calf','foot','ball'))
    if leg and clip in ('idle','hit'):continue
    p=rig.pose.bones[name];position=p.head.copy();_,q,scale=restworld[name].decompose()
    if clip=='move' and leg:
     if name.startswith('thigh'):
      midpoint=(restworld['thigh_l'].translation+restworld['thigh_r'].translation)*.5
      position=midpoint+Vector((0,.08 if name.endswith('l') else -.08,0))
     delta=source[origin].to_quaternion() @ reference[origin].to_quaternion().inverted();q=delta @ calibrated[name]
    else:
     delta=carry[origin].to_quaternion() @ carry0[origin].to_quaternion().inverted()
     if clip=='death':delta=hipdelta.inverted() @ delta
     q=delta @ q
     if clip=='death' and leg:
      captured=hipdelta.inverted() @ source[origin].to_quaternion() @ reference[origin].to_quaternion().inverted() @ calibrated[name]
      q=q.slerp(captured,max(0,min(1,(t-.15)/.40)))
    p.matrix=Matrix.LocRotScale(position,q,scale);bpy.context.view_layer.update()
   if clip=='move':
    hip=source['DEF-hips'].translation-source0['DEF-hips'].translation;rig.location+=hip*.65;floor_body(('boot',))
  if clip=='attack':
   recoil=[0,0,.02,.1,.85,1,.5,.2,.05,0][i];turn('spine_02','Y',-.10*recoil);turn('head','Y',-.04*recoil);turn('upperarm_r','Y',-.035*recoil)
  elif clip=='death':
   pivot=restworld['pelvis'].translation;displacement=(source['DEF-hips'].translation-source0['DEF-hips'].translation)*.58
   rig.matrix_world=Matrix.Translation(pivot+displacement) @ hipdelta.to_matrix().to_4x4() @ Matrix.Translation(-pivot) @ rigrest
   # Give the captured backward fall a fixed diagonal heading within the token.
   # Whole-body yaw preserves source articulation and avoids horizontal cropping.
   heading=.48*max(0,min(1,(t-.2)/.4))
   worldpivot=rig.matrix_world @ pivot
   rig.matrix_world=Matrix.Translation(worldpivot) @ Matrix.Rotation(heading,4,'Z') @ Matrix.Translation(-worldpivot) @ rig.matrix_world
   bpy.context.view_layer.update()
   if t>.1:floor_body(('anatomical','boot','sleeve','breeches','stocking'))
   # Framing correction translates the complete fallen body, never stretches it.
   if t>.2:
    dg=bpy.context.evaluated_depsgraph_get();xs=[]
    for o in sc.objects:
     if o.type!='MESH' or o.hide_render or o.parent==gun or o.name=='GEO-stationary cream base':continue
     ev=o.evaluated_get(dg);me=ev.to_mesh();xs.extend((ev.matrix_world @ v.co).x for v in me.vertices);ev.to_mesh_clear()
    low=-.63-min(xs);high=1.23-max(xs)
    rig.location.x+=max(low,min(0,high)) if low<=high else .30-(min(xs)+max(xs))*.5
   bpy.context.view_layer.update();release=max(0,min(1,t/.35));release=release*release*(3-2*release)
   initial=gun.matrix_world.copy();final=Matrix.Identity(4);final.translation=Vector((-.12,-.28,.14));q=initial.to_quaternion().slerp(Quaternion(),release)
   transform=q.to_matrix().to_4x4();transform.translation=initial.translation.lerp(final.translation,release);gun.matrix_world=transform
  bpy.context.view_layer.update()
  if clip!='death':constrain_grip()
  if clip=='death':
   for obj in cloth:
    if not obj.data.shape_keys:obj.shape_key_add(name='Basis')
    key=obj.shape_key_add(name=f'Contact {frame}',from_mix=False)
    for vert in key.data:
     world=obj.matrix_world @ vert.co
     if world.z<.11:world.z=.11+(world.z-.11)*.03;vert.co=obj.matrix_world.inverted() @ world
    key.value=0;key.keyframe_insert('value',frame=max(0,frame-1));key.value=1;key.keyframe_insert('value',frame=frame);key.value=0;key.keyframe_insert('value',frame=frame+1)
  for p in rig.pose.bones:
   for prop in ('location','rotation_quaternion','scale'):p.keyframe_insert(prop,frame=frame)
  for prop in ('location','rotation_euler','scale'):rig.keyframe_insert(prop,frame=frame);gun.keyframe_insert(prop,frame=frame)
  for o in sc.objects:
   if 'muzzle flash' in o.name or 'muzzle smoke' in o.name:
    visible=clip=='attack' and (i==4 if 'flash' in o.name else i in (4,5,6));o.hide_render=not visible;o.keyframe_insert('hide_render',frame=frame)
 for obj in [rig,gun]+[o for o in sc.objects if 'muzzle' in o.name]:
  if not obj.animation_data or not obj.animation_data.action:continue
  act=obj.animation_data.action;act.name=clip+' • '+obj.name;act.use_fake_user=True
  for layer in act.layers:
   for strip in layer.strips:
    for bag in strip.channelbags:
     for fc in bag.fcurves:
      for key in fc.keyframe_points:key.interpolation='CONSTANT' if fc.data_path=='hide_render' else 'BEZIER';key.handle_left_type=key.handle_right_type='AUTO_CLAMPED'
 sc.frame_set(1);bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(M/'clips'/f'{clip}.blend'))
 (M/'clips'/f'{clip}.json').write_text(json.dumps({'frames':count,'fps':fps,'loop':loop,'source_sha256':hashlib.sha256((M/'musketman.blend').read_bytes()).hexdigest(),'motion':motion.provenance(clip) if motion else {'method':'authored weapon-specific recoil'}}));log('Saved '+clip+' skeletal action, '+str(count)+' samples; '+('CC0 Quaternius' if motion else 'authored musket recoil')+'.')

def audit():
 reports=[];source=hashlib.sha256((M/'musketman.blend').read_bytes()).hexdigest()
 bpy.ops.wm.open_mainfile(filepath=str(M/'musketman.blend'))
 from refine import audit_surface
 surface=audit_surface()
 master_rig=bpy.data.objects['RIG-Musketman MPFB'];lengths={p.name:(p.tail-p.head).length for p in master_rig.pose.bones}
 for clip,(n,fps,loop) in CLIPS.items():
  path=M/'clips'/f'{clip}.blend';meta=json.loads(path.with_suffix('.json').read_text());assert meta['source_sha256']==source;assert (meta['frames'],meta['fps'],meta['loop'])==(n,fps,loop)
  bpy.ops.wm.open_mainfile(filepath=str(path));sc=bpy.context.scene;rig=bpy.data.objects['RIG-Musketman MPFB'];assert len(rig.data.bones)==53
  base=bpy.data.objects['GEO-stationary cream base'];origin=base.matrix_world.copy();counts=[];minz=100;poses=[];feet=[];grips=[];footchecks=[]
  sc.frame_set(1);bpy.context.view_layer.update();gun=bpy.data.objects['CTRL-musket'];grip=gun.matrix_world.inverted() @ rig.matrix_world @ rig.pose.bones['hand_l'].matrix
  for frame in range(1,n+1):
   sc.frame_set(frame);bpy.context.view_layer.update();assert base.matrix_world==origin
   for bone in rig.pose.bones:
    if bone.name.startswith(('thigh','calf','foot')):assert .85<(bone.tail-bone.head).length/lengths[bone.name]<1.15,(clip,frame,bone.name,'retarget stretch')
   feet.append({side:list((rig.matrix_world @ rig.pose.bones['foot_'+side].matrix).translation) for side in ('l','r')})
   if clip=='move':
    check={};deps=bpy.context.evaluated_depsgraph_get()
    for side in ('l','r'):
     boot=bpy.data.objects['GEO-leather boot '+side];direction=boot.matrix_world.to_3x3() @ Vector((1,0,0));direction.z=0;direction.normalize()
     assert direction.x>.70,(frame,side,'boot points away from travel',list(direction))
     lows=[]
     for name in ('GEO-leather boot '+side,'GEO-boot sole '+side):
      obj=bpy.data.objects[name];ev=obj.evaluated_get(deps);me=ev.to_mesh();lows.extend((ev.matrix_world @ v.co).z for v in me.vertices);ev.to_mesh_clear()
     check[side]={'forward_xy':list(direction),'sole_min_z':min(lows)}
    assert abs(min(v['sole_min_z'] for v in check.values())-.104)<.003,(frame,'no planted foot',check)
    footchecks.append(check)
   if clip!='death':
    error=((gun.matrix_world @ grip).translation-(rig.matrix_world @ rig.pose.bones['hand_l'].matrix).translation).length;grips.append(error);assert error<.002,(clip,frame,'support hand left gun',error)
   poses.append(tuple(round(v,5) for p in rig.pose.bones for row in p.matrix for v in row)+tuple(round(v,5) for row in rig.matrix_world for v in row))
   for o in sc.objects:
    assert min(abs(v) for v in o.scale)>1e-5,(clip,frame,o.name,'unsafe scale')
    if o.type=='MESH' and not o.hide_render:
     ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());minz=min(minz,min((ev.matrix_world @ Vector(c)).z for c in ev.bound_box))
   counts.append(sum(not o.hide_render for o in sc.objects if 'muzzle smoke' in o.name))
  assert len(set(poses))>1,(clip,'rig does not animate')
  if clip=='death':assert poses[-1]==poses[-2],'Death skeletal pose is not held'
  reports.append({'foot_direction_and_contact':footchecks,'feet':feet,'maximum_grip_error':max(grips,default=0),'motion':meta.get('motion'),'distinct_skeletal_poses':len(set(poses)),'clip':clip,'frames':n,'bones':len(rig.data.bones),'stationary_base':True,'minimum_bbox_z':minz,'smoke_objects_visible':counts})
 (V/'musketman-audit.json').write_text(json.dumps({'surface':surface,'checks':reports,'limits':'Bounds and rig checks do not establish hand contacts, cloth collision freedom or visual approval.'},indent=2));log('Audit passed: five clips, source hashes, 53-bone rig, fixed base and positive object scales.')

mode=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'build'
if mode=='preflight':
 configure();print('GPU preflight passed',flush=True)
elif mode=='build':
 build();render('b-plain',M/'plain.blend',[1]);bpy.ops.wm.open_mainfile(filepath=str(M/'plain.blend'));configure();from bake import bake;bake();project();render('c-textured-lit',M/'musketman.blend',[1])
elif mode=='rest':
 render('b-plain',M/'plain.blend',[1]);render('c-textured-lit',M/'musketman.blend',[1])
elif mode.startswith('animate-'):animate(mode[8:])
elif mode.startswith('e-'):render(mode,M/'clips'/(mode[2:]+'.blend'),list(range(1,CLIPS[mode[2:]][0]+1)))
elif mode=='audit':audit()
elif mode=='feet':
 for view in ('top','front'):render('g-feet-'+view,M/'clips/move.blend',list(range(1,9)))
elif mode=='animate':
 for clip in CLIPS:animate(clip)
elif mode in ('preview','render'):
 if mode=='render':
  render('b-plain',M/'plain.blend',[1]);render('c-textured-lit',M/'musketman.blend',[1])
 render('d-rig-poses',M/'clips/attack.blend',[1,3,5,7])
 for clip,(n,_,_) in CLIPS.items():render('e-'+clip,M/'clips'/f'{clip}.blend',list(range(1,n+1)))
 for view in ('top','front'):render('g-feet-'+view,M/'clips/move.blend',list(range(1,9)))
else:raise ValueError(mode)
