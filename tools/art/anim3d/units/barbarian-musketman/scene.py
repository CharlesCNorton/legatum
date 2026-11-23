"""Barbarian musketman: MPFB anatomy, tailored 3D kit, frozen camera UVs and five actions."""
import bpy, math, os, sys, json, hashlib, subprocess
from pathlib import Path
from mathutils import Vector, Matrix
from math import sin, cos, pi
from bpy_extras.object_utils import world_to_camera_view
R=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'))
M=R/'masters/barbarian-musketman'; A=R/'assets/barbarian-musketman'; V=R/'review/3d-v2'
for p in (M,V,M/'clips',M/'renders'):p.mkdir(parents=True,exist_ok=True)
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
CLIPS={'idle':(8,10,True),'move':(8,12,True),'attack':(10,14,False),'hit':(4,12,False),'death':(10,10,False)}
def log(s):
 with (V/'barbarian-musketman-log.md').open('a') as f:f.write('- '+s+'\n')
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
 p=rig.pose.bones[name];q=p.bone.matrix_local.to_quaternion();v=q@Vector((0,1,0));rot=(v.rotation_difference(Vector(direction).normalized())@q).to_matrix().to_4x4();rot.translation=p.head;p.matrix=rot;bpy.context.view_layer.update()

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
 sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast';sc.view_settings.exposure=.25
 return sc

# Camera coordinates in the original 256-pixel token. Positive depth is away from camera.
UP=Vector((0,math.sin(math.radians(18)),math.cos(math.radians(18))))
VIEW=Vector((0,-math.cos(math.radians(18)),math.sin(math.radians(18))))
CENTER=Vector((.28,0,.67));SPAN=1.75

def P(x,y,depth=0):return CENTER+Vector(((x-128)*SPAN/256,0,0))+UP*((128-y)*SPAN/256)-VIEW*depth

def setbone(name,a,b,yaw=0):
 p=rig.pose.bones[name];a=Vector(a);b=Vector(b);direction=b-a
 # Orient long axis exactly along target; preserve anatomical roll with rest matrix.
 q=p.bone.matrix_local.to_quaternion();r=(q@Vector((0,1,0))).rotation_difference(direction.normalized())@q
 if yaw:r=__import__('mathutils').Quaternion(direction.normalized(),yaw)@r
 m=r.to_matrix().to_4x4()@Matrix.Diagonal((1,direction.length/p.bone.length,1,1));m.translation=rig.matrix_world.inverted()@a;p.matrix=m;bpy.context.view_layer.update()

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
 macro=TargetService.get_default_macro_info_dict();macro.update(gender=1.,age=.58,muscle=.72,weight=.56,height=.45,proportions=.6);macro['race']={'caucasian':1.,'african':0.,'asian':0.}
 body=HumanService.create_human(macro_detail_dict=macro);body.name='GEO-MPFB anatomical musketeer'
 bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();lo=min(v.co.z for v in me.vertices);hi=max(v.co.z for v in me.vertices);ev.to_mesh_clear();body.scale=(1.62/(hi-lo),)*3
 bpy.context.view_layer.objects.active=body;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 rig=HumanService.add_builtin_rig(body,'game_engine');rig.name='RIG-Barbarian musketman MPFB'
 for bone in rig.data.bones:bone.inherit_scale='NONE'
 system=R/'blender-user/extensions/.user/user_default/mpfb/data';eyes=HumanService.add_mhclo_asset(str(system/'eyes/high-poly/high-poly.mhclo'),body,asset_type='Eyes',subdiv_levels=1,material_type='MAKESKIN');eyes.name='GEO-MPFB eyes'
 skin=mat('ochre skin',(.49,.265,.12));linen=mat('painted ivory linen',(.73,.60,.39),fill='linen');red=mat('faded vermilion sash',(.42,.065,.029));leather=mat('scuffed brown hide',(.20,.09,.03),fill='coat');steel=mat('worn gun steel',(.55,.57,.56),1,.38);brass=mat('warm polished brass',(.75,.48,.15),1,.32);wood=mat('walnut gunstock',(.25,.1,.025),fill='coat');dark=mat('hair and recesses',(.065,.035,.016),fill='hair');buff=mat('patched ochre coat',(.32,.23,.115),fill='coat');pants=mat('charcoal patched breeches',(.13,.12,.09));stone=mat('cream limestone E9CFA0',(.8148,.57,.255),0,.88)
 body.data.materials.clear();body.data.materials.append(skin)
 sub=body.modifiers.new('Anatomical subdivision','SUBSURF');sub.levels=sub.render_levels=1
 for p in body.data.polygons:p.use_smooth=True
 # Pose the actual human skeleton in the painting's kneeling stance.
 for name,a,b in [('pelvis',P(72,137,.07),P(72,124,.07)),('spine_01',P(72,124,.07),P(69,108,.06)),('spine_02',P(69,108,.06),P(65,91,.055)),('spine_03',P(65,91,.055),P(64,77,.05)),('neck_01',P(64,77,.05),P(66,67,.04)),('head',P(66,67,.04),P(68,47,.04))]:setbone(name,a,b,.65 if name!='head' else .95)
 for side,points in [('r',[(64,131,.05),(78,187,.38),(38,185,.42)]),('l',[(80,131,.07),(124,141,.10),(131,190,.28)])]:
  a,b,c=[P(*p) for p in points];setbone('thigh_'+side,a,b,.25);setbone('calf_'+side,b,c,.2)
  setbone('foot_'+side,c,P(145 if side=='l' else 32,198 if side=='l' else 191,.24 if side=='l' else .40))
 for side,pts in [('r',[(40,79,-.01),(29,96,-.04),(78,74,-.16)]),('l',[(96,80,.08),(119,102,.02),(123,76,-.13)])]:
  a,b,c=[P(*p) for p in pts];setbone('upperarm_'+side,a,b);setbone('lowerarm_'+side,b,c)
  setbone('hand_'+side,c,P(87,72,-.14) if side=='r' else P(122,72,-.13))
 for side in ('r','l'):
  for digit in ('index','middle','ring','pinky'):
   for k in range(1,4):p=rig.pose.bones[f'{digit}_{k:02d}_{side}'];p.rotation_mode='XYZ';p.rotation_euler.x=.7
 bpy.context.view_layer.update()
 # Coat and shirt loft around chest, narrowing to waist; folds are geometry.
 for label,rxs,rys,ma,zmin,zmax in [('ivory shirt',(.145,.21),(.105,.125),linen,126,77),('weathered buff waistcoat',(.16,.235),(.115,.137),buff,130,77)]:
  vs=[];fs=[];ns=64;nr=22
  for j in range(nr+1):
   t=j/nr;center=P(72-7*t,zmin+(zmax-zmin)*t,.055)
   for k in range(ns):
    a=2*pi*k/ns;fold=.008*cos(a*13+t*2)*sin(pi*t);r=rxs[0]*(1-t)+rxs[1]*t;dep=rys[0]*(1-t)+rys[1]*t
    vs.append(tuple(center+Vector(((r+fold)*sin(a),-(dep+fold)*cos(a),0))))
  for j in range(nr):
   for k in range(ns):
    # Open waistcoat in front to reveal ivory shirt.
    if label.startswith('weathered') and (k<5 or k>59):continue
    i=j*ns+k;n=j*ns+(k+1)%ns;fs.append((i,n,n+ns,i+ns))
  attach(bevel(solid(mesh(label,vs,fs,ma),.006),.002),'spine_02')
 # Sleeves gathered at elbows; forearms and hands remain true MPFB skin.
 for side in ('r','l'):
  p=rig.pose.bones['upperarm_'+side];a=rig.matrix_world@p.head;b=rig.matrix_world@p.tail
  tube('billowing ivory sleeve '+side,a,b+(b-a)*.08,(.085,.075,.036),linen,'upperarm_'+side)
  tube('rolled sleeve cuff '+side,b-(b-a)*.12,b+(b-a)*.12,(.083,.080,.012),linen,'upperarm_'+side)
  p=rig.pose.bones['thigh_'+side];a=rig.matrix_world@p.head;b=rig.matrix_world@p.tail
  tube('patched breeches '+side,a,b,(.115,.086,.020),buff,'thigh_'+side)
  p=rig.pose.bones['calf_'+side];a=rig.matrix_world@p.head;b=rig.matrix_world@p.tail
  tube('dark gaiter '+side,a,b,(.079,.047,.012),pants,'calf_'+side)
  # Visible patches and stitch loops, kept on their anatomical segment.
  for t in (.28,.65):
   center=a.lerp(b,t)+Vector((0,-.065,0));patchvs=[center+Vector((x,-.003,z)) for x,z in [(-.035,-.034),(.033,-.028),(.038,.025),(-.026,.035)]]
   attach(bevel(solid(mesh('stitched gaiter patch '+side,patchvs,[(0,1,2,3)],leather),.004),.002),'calf_'+side)
  ankle=rig.matrix_world@rig.pose.bones['foot_'+side].head
  loc=P(137,199,.24) if side=='l' else P(33,191,.40)
  attach(sphere('leather boot '+side,loc,(.09,.11,.052),leather),'foot_'+side)
  for t in (.60,.73,.86):
   c=a.lerp(b,t);pts=[c+Vector((.06*cos(k*pi/24),-.06*sin(k*pi/24),.016*cos(k*pi/12))) for k in range(49)];attach(curve('crossed boot wrap '+side,pts,.009,leather),'calf_'+side)
 # Ragged coat tails and red sash hanging over the kneeling leg.
 for side in (-1,1):
  vs=[];fs=[]
  for j in range(16):
   t=j/15
   for k in range(9):
    u=k/8;x=(54 if side==-1 else 82)+side*18*t+(u-.5)*22;y=124+49*t+3*sin(k*2.4)*t**8;vs.append(P(x,y,.12+.028*sin(k*1.6)))
  for j in range(15):
   for k in range(8):i=j*9+k;fs.append((i,i+1,i+10,i+9))
  attach(solid(mesh('ragged coat tail '+str(side),vs,fs,buff),.007),'pelvis')
 for off in (-4,0,4):
  pts=[P(46+i*6,127+off-3*sin(i*pi/8),-.13) for i in range(9)];ribbon('folded red sash',pts,.024,red,'pelvis')
 for n in range(4):
  vs=[];fs=[]
  for j in range(18):
   t=j/17
   for k in range(3):vs.append(P(45+n*4+4*sin(t*4+n)+(k-1)*3*(1-.35*t),128+(45+n*3)*t+2*(k%2)*t**12,-.17+.015*sin(t*9+n)))
  for j in range(17):
   for k in range(2):i=j*3+k;fs.append((i,i+1,i+4,i+3))
  attach(solid(mesh('torn sash ribbon '+str(n),vs,fs,red),.004),'pelvis')
 # Leather straps, real raised seams, charge flasks, buckles and pouch.
 points=[P(101,84,-.12),P(86,103,-.16),P(65,120,-.17),P(42,135,-.13)]
 ribbon('thick diagonal bandolier',points,.032,leather,'spine_02')
 for d in (-.013,.013):attach(curve('bandolier raised stitching',[p+Vector((d,-.004,0)) for p in points],.0018,linen),'spine_02')
 for i in range(7):
  x=56+i*5;y=122-i*3.5;a=P(x,y,-.18);b=P(x+4,y+11,-.19)
  attach(curve('individual powder flask '+str(i),[a,b],.014,wood),'spine_02')
  for t in (0,.15,.85):attach(curve('flask brass collar',[a.lerp(b,t),a.lerp(b,t+.1)],.0165,brass),'spine_02')
 ribbon('waist belt',[P(46,135,-.13),P(70,139,-.18),P(96,133,-.12)],.032,leather,'pelvis')
 for x,y in [(70,139),(89,102)]:attach(curve('rectangular brass buckle',[P(x-3,y-3,-.2),P(x+3,y-3,-.2),P(x+3,y+3,-.2),P(x-3,y+3,-.2),P(x-3,y-3,-.2)],.004,brass),'pelvis' if y>130 else 'spine_02')
 pouch=attach(sphere('worn leather powder pouch',P(38,139,-.09),(.075,.045,.085),leather),'pelvis')
 attach(curve('pouch sewn border',[P(31,133,-.15),P(30,143,-.15),P(40,148,-.15),P(45,136,-.15)],.003,linen),'pelvis')
 # Wide irregular felt hat, low pinched crown, raised band and feather barbs.
 hc=P(65,47,.04);vs=[];fs=[]
 for j in range(7):
  t=j/6
  for k in range(96):
   a=2*pi*k/96;rad=.095+.19*t;vs.append(hc+Vector((rad*sin(a),rad*.68*cos(a),-.006+.022*sin(a*3)*t+.03*t**3*cos(a)+.17*rad*sin(a))))
 for j in range(6):
  for k in range(96):i=j*96+k;n=j*96+(k+1)%96;fs.append((i,n,n+96,i+96))
 attach(bevel(solid(mesh('broad weathered hat brim',vs,fs,buff),.009),.003),'head');attach(curve('hat worn rolled rim',vs[-96:]+[vs[-96]],.004,leather),'head')
 vs=[];fs=[]
 for j in range(14):
  t=j/13
  for k in range(64):
   a=2*pi*k/64;rad=.103*(1-.22*t);vs.append(hc+Vector((rad*sin(a),rad*.83*cos(a),.10*t+.015*sin(a*2)*t)))
 for j in range(13):
  for k in range(64):i=j*64+k;n=j*64+(k+1)%64;fs.append((i,n,n+64,i+64))
 fs.append(tuple(range(13*64,14*64)));attach(bevel(solid(mesh('pinched felt hat crown',vs,[tuple(reversed(f)) for f in fs],buff),.006),.002),'head')
 attach(curve('hat leather band',[hc+Vector((.106*sin(a),.09*cos(a),.027)) for a in [2*pi*k/96 for k in range(97)]],.012,leather),'head')
 feather=[P(59-34*t,33-12*sin(pi*t)+6*t,.06) for t in [k/32 for k in range(33)]];attach(curve('swept feather quill',feather,.003,linen),'head')
 for k in range(1,31):
  t=k/32;p=feather[k]
  for sg in (-1,1):attach(curve('feather barb',[p,p+Vector((-.035,-.006,sg*.035*(sin(pi*t)**.5)))],.0025,linen),'head')
 # Wavy shoulder-length hair and short beard.
 for k in range(28):
  a=-1.4+k*2.8/27;c=P(61,58,.10);pts=[c+Vector((.105*sin(a)+.008*sin(j*1.3+k),.075*cos(a),-.012*j)) for j in range(13)];attach(curve('wavy hair strand',pts,.006,dark),'head')
 attach(curve('moustache',[P(73,66,-.14),P(78,67,-.14),P(80,69,-.14)],.006,dark),'head')
 # True solid gun, all parts controlled together. Horizontal to match source.
 gun=empty('CTRL-musket',P(86,72,-.16));attach(gun,'hand_r')
 profile=[(42,76),(80,77),(93,73),(210,72),(210,68),(88,68),(75,72),(42,72)]
 vs=[P(x,y,dep) for dep in (-.145,-.195) for x,y in profile];n=len(profile);fs=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 parent(bevel(mesh('carved walnut musket stock',vs,fs,wood),.005),gun)
 parent(curve('long steel barrel',[P(88,67,-.18),P(216,67,-.18)],.011,steel),gun)
 parent(curve('underbarrel ramrod',[P(99,73,-.19),P(209,73,-.19)],.0035,steel),gun)
 for x in (100,154,205):parent(curve('brass barrel band',[P(x,67,-.18),P(x+2,67,-.18)],.014,brass),gun)
 parent(curve('dark muzzle bore',[P(216,67,-.18),P(217,67,-.18)],.007,dark),gun)
 parent(curve('trigger guard',[P(86,75,-.23),P(88,80,-.23),P(94,80,-.23),P(96,75,-.23)],.004,steel),gun)
 parent(curve('flintlock hammer',[P(91,70,-.23),P(89,63,-.23),P(94,61,-.23)],.005,steel),gun)
 parent(sphere('flintlock round plate',P(88,71,-.23),(.020,.007,.020),steel),gun)
 flash=sphere('muzzle flash',P(219,67,-.18),(.04,.024,.026),mat('flash amber',(.9,.4,.03)));parent(flash,gun);flash.hide_render=True
 for i in range(5):
  smoke=sphere('muzzle smoke '+str(i),P(224+(i%2)*3,65+(i-2)*2,-.17+i*.012),(.035,.034,.041),mat('smoke '+str(i),(.55,.54,.50)));parent(smoke,gun);smoke.hide_render=True
 bpy.ops.mesh.primitive_cylinder_add(vertices=96,radius=.51,depth=.074,location=(0,0,.047));base=bpy.context.object;base.name='GEO-stationary cream base';base.data.materials.append(stone);bevel(base,.010)
 sc=configure();sc.world.use_nodes=True;sc.world.node_tree.nodes.get('Background').inputs[0].default_value=(.65,.70,.8,1);sc.world.node_tree.nodes.get('Background').inputs[1].default_value=.3
 bpy.ops.object.camera_add(location=CENTER+VIEW*8);cam=bpy.context.object;cam.name='CAM-painting';cam.rotation_euler=(-VIEW).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=SPAN;sc.camera=cam
 for name,loc,power,size,color in [('key',(-3,-4,5),500,2.2,(1,.88,.72)),('fill',(3,-3,3),130,3.,(.83,.9,1)),('rim',(1,2,4),270,2.,(.72,.83,1))]:
  bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name='LGT-'+name;o.data.energy=power;o.data.size=size;o.data.color=color;o.rotation_euler=(Vector((0,0,.7))-o.location).to_track_quat('-Z','Y').to_euler()
 # Convert props to real meshes before fixed UV projection. No live camera shader.
 for o in list(sc.objects):
  if o.type=='CURVE':
   bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
 sc['unit']='barbarian-musketman';sc['anatomy']='MPFB 2.0.18 CC0';sc['cream_target']='#E9CFA0'
 bpy.context.view_layer.update();rig['rest_pose']=json.dumps({p.name:[list(r) for r in p.matrix_basis] for p in rig.pose.bones});rig['rest_location']=list(rig.location)
 (M/'bones.json').write_text(json.dumps({p.name:{'head':list(p.head),'tail':list(p.tail)} for p in rig.pose.bones},indent=2))
 bpy.ops.wm.save_as_mainfile(filepath=str(M/'plain.blend'));log('Built kneeling MPFB human, tailored ragged kit, feather hat, bandolier and solid horizontal musket.')

def project():
 """Frozen evaluated rest coordinates deform with the real skin/kit geometry."""
 sc=bpy.context.scene;cam=sc.camera;im=bpy.data.images.load(str(A/'projection.png'),check_existing=True);records=[]
 for o in list(sc.objects):
  if o.type!='MESH' or any(x in o.name for x in ('muzzle','eyes')):continue
  mods=[]
  for m in o.modifiers:
   if m.type!='ARMATURE' and m.show_viewport:mods.append(m);m.show_viewport=False
  bpy.context.view_layer.update();ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();assert len(me.vertices)==len(o.data.vertices)
  uv=o.data.uv_layers.get('Painting') or o.data.uv_layers.new(name='Painting');col=o.data.color_attributes.new(name='Projection facing',type='FLOAT_COLOR',domain='CORNER')
  coords=[world_to_camera_view(sc,cam,ev.matrix_world@v.co) for v in me.vertices]
  normalmat=ev.matrix_world.to_3x3().inverted().transposed();facing=[max(0,min(1,((normalmat@v.normal).normalized().dot((cam.location-ev.matrix_world@v.co).normalized())+.02)/.20)) for v in me.vertices]
  for loop in o.data.loops:
   i=loop.vertex_index;uv.data[loop.index].uv=(coords[i].x,coords[i].y);f=facing[i];col.data[loop.index].color=(f,f,f,1)
  ev.to_mesh_clear()
  for m in mods:m.show_viewport=True
  for slot in o.material_slots:
   if not slot.material:continue
   ma=slot.material.copy();slot.material=ma;n=ma.node_tree.nodes;l=ma.node_tree.links;p=n.get('Principled BSDF')
   old=p.inputs['Base Color'].links[0].from_socket if p.inputs['Base Color'].is_linked else None
   if not old:rgb=n.new('ShaderNodeRGB');rgb.outputs[0].default_value=p.inputs['Base Color'].default_value;old=rgb.outputs[0]
   tc=n.new('ShaderNodeUVMap');tc.uv_map='Painting';tex=n.new('ShaderNodeTexImage');tex.image=im;tex.extension='CLIP';l.new(tc.outputs[0],tex.inputs[0]);attr=n.new('ShaderNodeVertexColor');attr.layer_name=col.name;mul=n.new('ShaderNodeMath');mul.operation='MULTIPLY';l.new(attr.outputs[0],mul.inputs[0]);l.new(tex.outputs['Alpha'],mul.inputs[1]);weight=n.new('ShaderNodeMath');weight.operation='MULTIPLY';weight.inputs[1].default_value=.96;l.new(mul.outputs[0],weight.inputs[0]);mix=n.new('ShaderNodeMixRGB');l.new(weight.outputs[0],mix.inputs[0]);l.new(old,mix.inputs[1]);l.new(tex.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],p.inputs['Base Color']);l.new(mix.outputs[0],p.inputs['Emission Color']);p.inputs['Emission Strength'].default_value=.18
  records.append(o.name)
 bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(M/'barbarian-musketman.blend'));(M/'projection.json').write_text(json.dumps({'objects':records,'method':'frozen rest-camera UV plus facing/alpha blend','weight':.96,'hidden_surfaces':'original generated painted fills'},indent=2));log('Camera projection applied to real meshes; hidden surfaces retain generated painted fills.')



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


def animate(clip):
 global rig
 bpy.ops.wm.open_mainfile(filepath=str(M/'barbarian-musketman.blend'));sc=bpy.context.scene;rig=bpy.data.objects['RIG-Barbarian musketman MPFB'];gun=bpy.data.objects['CTRL-musket']
 count,fps,loop=CLIPS[clip];sc.render.fps=fps;sc.frame_start=1;sc.frame_end=count
 rest={p.name:p.matrix_basis.copy() for p in rig.pose.bones};restworld={p.name:p.matrix.copy() for p in rig.pose.bones};gunrest=gun.matrix_basis.copy();rigrest=rig.matrix_world.copy()
 for p in rig.pose.bones:p.rotation_mode='QUATERNION'
 def turn(name,axis,angle):
  p=rig.pose.bones[name];m=p.matrix.copy();pos=m.translation.copy();m=Matrix.Rotation(angle,4,axis)@m;m.translation=pos;p.matrix=m;bpy.context.view_layer.update()
 for i in range(count+(1 if loop else 0)):
  frame=i+1;t=i/count if loop else min(i/(count-2),1);wave=sin(2*pi*t)
  rig.matrix_world=rigrest;gun.matrix_basis=gunrest
  for p in rig.pose.bones:p.matrix_basis=rest[p.name]
  bpy.context.view_layer.update()
  if clip=='idle':
   turn('spine_02','X',.012*wave);turn('head','Z',.013*sin(2*pi*t+.4));turn('upperarm_r','Y',.007*wave)
  elif clip=='move':
   # Supported kneeling shuffle: right knee stays planted; left boot takes a short step.
   rig.location.x=.012*wave
   for side in ('r','l'):
    a=restworld['thigh_'+side].translation+Vector((.012*wave,0,0))
    b=restworld['calf_'+side].translation.copy();ankle=restworld['foot_'+side].translation.copy()
    if side=='l':
     b+=Vector((.018*wave,0,.006*max(0,wave)));ankle+=Vector((.035*wave,0,.018*max(0,wave)))
    setbone('thigh_'+side,a,b,.25);setbone('calf_'+side,b,ankle,.2)
    foot=restworld['foot_'+side].copy();foot.translation=ankle-Vector((.012*wave,0,0));rig.pose.bones['foot_'+side].matrix=foot
   turn('spine_02','Z',.018*wave)
  elif clip=='attack':
   recoil=[0,0,.02,.10,.85,1,.5,.2,.05,0][i];turn('spine_02','Y',-.10*recoil);turn('head','Y',-.04*recoil)
   turn('upperarm_r','Y',-.04*recoil)
  elif clip=='hit':
   strength=[0,1,.42,0][i];turn('spine_02','Y',-.22*strength);turn('head','X',.14*strength);turn('upperarm_r','Z',.08*strength)
  elif clip=='death':
   fall=min(1,t/0.88);fall=fall*fall*(3-2*fall)
   pivot=P(76,139,.12);dest=Vector((.16,.04,.34))
   rig.matrix_world=Matrix.Translation(pivot.lerp(dest,fall))@Matrix.Rotation(-1.43*fall,4,'Y')@Matrix.Translation(-pivot)@rigrest
   turn('spine_02','X',.10*fall);turn('head','X',.25*fall);turn('thigh_l','Y',1.0*fall);turn('calf_l','Y',.55*fall);turn('calf_r','Y',-1.1*fall)
   bpy.context.view_layer.update()
   # Settle actual evaluated anatomy/boots on the disc, not oversized object bounds.
   # Ragged cloth must not prop up the entire fallen body.
   if fall>.1:
    zs=[];xs=[];dg=bpy.context.evaluated_depsgraph_get()
    for o in sc.objects:
     if o.type!='MESH' or o.name=='GEO-stationary cream base' or 'muzzle' in o.name or o.parent==gun:continue
     ev=o.evaluated_get(dg);me=ev.to_mesh();points=[ev.matrix_world@v.co for v in me.vertices];xs.extend(p.x for p in points)
     if any(word in o.name for word in ('anatomical','boot','sleeve','breeches','gaiter')):zs.extend(p.z for p in points)
     ev.to_mesh_clear()
    rig.location.z+=(.086-min(zs))*fall
    # Camera remains fixed; translate the falling body just enough to retain a feather margin.
    rig.location.x+=max(0,-.525-min(xs))-max(0,max(xs)-1.105)
   bpy.context.view_layer.update()
   release=max(0,min(1,(t-.18)/.50));release=release*release*(3-2*release)
   initial=gun.matrix_world.copy();final=Matrix.Identity(4);final.translation=Vector((-.13,-.30,.14))
   # Rest gun axis remains horizontal. Release is keyed as an actual rigid transform.
   q=initial.to_quaternion().slerp(__import__('mathutils').Quaternion(),release)
   transform=q.to_matrix().to_4x4();transform.translation=initial.translation.lerp(final.translation,release);gun.matrix_world=transform
  bpy.context.view_layer.update()
  if clip=='attack':turn('lowerarm_l','Y',-.04*recoil)
  for p in rig.pose.bones:
   for prop in ('location','rotation_quaternion','scale'):p.keyframe_insert(prop,frame=frame)
  for prop in ('location','rotation_euler','scale'):rig.keyframe_insert(prop,frame=frame)
  for prop in ('location','rotation_euler','scale'):gun.keyframe_insert(prop,frame=frame)
  for o in sc.objects:
   if 'muzzle flash' in o.name or 'muzzle smoke' in o.name:
    visible=clip=='attack' and (i==4 if 'flash' in o.name else i in (4,5,6))
    o.hide_render=not visible;o.keyframe_insert('hide_render',frame=frame)
 # Layered actions in Blender 5; use Bezier on transforms and constant visibility.
 for obj in [rig,gun]+[o for o in sc.objects if 'muzzle' in o.name]:
  if not obj.animation_data or not obj.animation_data.action:continue
  act=obj.animation_data.action;act.name=clip+' • '+obj.name;act.use_fake_user=True
  curves=[]
  for layer in act.layers:
   for strip in layer.strips:
    for bag in strip.channelbags:curves.extend(bag.fcurves)
  for fc in curves:
   for key in fc.keyframe_points:
    key.interpolation='CONSTANT' if fc.data_path=='hide_render' else 'BEZIER'
    key.handle_left_type=key.handle_right_type='AUTO_CLAMPED'
 sc.frame_set(1);bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(M/'clips'/f'{clip}.blend'))
 (M/'clips'/f'{clip}.json').write_text(json.dumps({'frames':count,'fps':fps,'loop':loop,'source_sha256':hashlib.sha256((M/'barbarian-musketman.blend').read_bytes()).hexdigest()}));log('Authored '+clip+' skeletal action, '+str(count)+' samples.')

def audit():
 reports=[];source=hashlib.sha256((M/'barbarian-musketman.blend').read_bytes()).hexdigest()
 for clip,(n,fps,loop) in CLIPS.items():
  path=M/'clips'/f'{clip}.blend';meta=json.loads(path.with_suffix('.json').read_text());assert meta['source_sha256']==source
  bpy.ops.wm.open_mainfile(filepath=str(path));sc=bpy.context.scene;rig=bpy.data.objects['RIG-Barbarian musketman MPFB'];assert len(rig.data.bones)==53
  base=bpy.data.objects['GEO-stationary cream base'];origin=base.matrix_world.copy();counts=[];minz=100;poses=[]
  for frame in range(1,n+1):
   sc.frame_set(frame);bpy.context.view_layer.update();assert base.matrix_world==origin
   poses.append(tuple(round(v,5) for p in rig.pose.bones for row in p.matrix for v in row)+tuple(round(v,5) for row in rig.matrix_world for v in row))
   for o in sc.objects:
    assert min(abs(v) for v in o.scale)>1e-5,(clip,frame,o.name,'unsafe scale')
    if o.type=='MESH' and not o.hide_render:
     ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());minz=min(minz,min((ev.matrix_world@Vector(c)).z for c in ev.bound_box))
   counts.append(sum(not o.hide_render for o in sc.objects if 'muzzle smoke' in o.name))
  assert len(set(poses))>1,(clip,'rig does not animate')
  if clip=='death':assert poses[-1]==poses[-2],'Death skeletal pose is not held'
  reports.append({'distinct_skeletal_poses':len(set(poses)),'clip':clip,'frames':n,'bones':len(rig.data.bones),'stationary_base':True,'minimum_bbox_z':minz,'smoke_objects_visible':counts})
 (V/'barbarian-musketman-audit.json').write_text(json.dumps({'checks':reports,'limits':'Bounds and rig checks do not establish hand contacts, cloth collision freedom or visual approval.'},indent=2));log('Audit passed: five clips, source hashes, 53-bone rig, fixed base and positive object scales.')

mode=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'build'
if mode=='build':
 build();render('b-plain',M/'plain.blend',[1]);bpy.ops.wm.open_mainfile(filepath=str(M/'plain.blend'));configure();from bake import bake;bake();project();render('c-textured-lit',M/'barbarian-musketman.blend',[1])
elif mode=='rest':
 render('b-plain',M/'plain.blend',[1]);render('c-textured-lit',M/'barbarian-musketman.blend',[1])
elif mode.startswith('animate-'):animate(mode[8:])
elif mode.startswith('e-'):render(mode,M/'clips'/(mode[2:]+'.blend'),list(range(1,CLIPS[mode[2:]][0]+1)))
elif mode=='audit':audit()
elif mode=='animate':
 for clip in CLIPS:animate(clip)
elif mode in ('preview','render'):
 if mode=='render':
  render('b-plain',M/'plain.blend',[1]);render('c-textured-lit',M/'barbarian-musketman.blend',[1])
 render('d-rig-poses',M/'clips/attack.blend',[1,3,5,7])
 for clip,(n,_,_) in CLIPS.items():render('e-'+clip,M/'clips'/f'{clip}.blend',list(range(1,n+1)))
else:raise ValueError(mode)
