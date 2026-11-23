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
 sc.render.use_persistent_data=False
 sc.render.threads_mode='FIXED';sc.render.threads=3;sc.render.resolution_x=sc.render.resolution_y=int(os.environ.get('RESOLUTION','256'));sc.render.resolution_percentage=100;sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.use_file_extension=True
 sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0
 return sc

# Camera coordinates in the original 256-pixel token. Positive depth is away from camera.
UP=Vector((0,math.sin(math.radians(18)),math.cos(math.radians(18))))
VIEW=Vector((0,-math.cos(math.radians(18)),math.sin(math.radians(18))))
CENTER=Vector((.28,0,.67));SPAN=1.75

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
 macro=TargetService.get_default_macro_info_dict();macro.update(gender=1.,age=.58,muscle=.72,weight=.56,height=.45,proportions=.6);macro['race']={'caucasian':1.,'african':0.,'asian':0.}
 body=HumanService.create_human(macro_detail_dict=macro);body.name='GEO-MPFB anatomical musketeer'
 bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();lo=min(v.co.z for v in me.vertices);hi=max(v.co.z for v in me.vertices);ev.to_mesh_clear();body.scale=(1.62/(hi-lo),)*3
 bpy.context.view_layer.objects.active=body;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 rig=HumanService.add_builtin_rig(body,'game_engine');rig.name='RIG-Barbarian musketman MPFB'
 for bone in rig.data.bones:bone.inherit_scale='NONE'
 system=R/'blender-user/extensions/.user/user_default/mpfb/data';eyes=HumanService.add_mhclo_asset(str(system/'eyes/high-poly/high-poly.mhclo'),body,asset_type='Eyes',subdiv_levels=1,material_type='MAKESKIN');eyes.name='GEO-MPFB eyes'
 skin=mat('ochre skin',(.49,.265,.12));linen=mat('painted ivory linen',(.73,.60,.39),fill='linen');red=mat('faded vermilion sash',(.42,.065,.029));leather=mat('scuffed brown hide',(.20,.09,.03),fill='coat');steel=mat('worn gun steel',(.55,.57,.56),1,.38);brass=mat('warm polished brass',(.75,.48,.15),1,.32);wood=mat('walnut gunstock',(.25,.1,.025),fill='coat');dark=mat('hair and recesses',(.065,.035,.016),fill='hair');buff=mat('patched ochre coat',(.32,.23,.115),fill='coat');pants=mat('charcoal patched breeches',(.13,.12,.09));stone=mat('cream limestone E9CFA0',(.815,.624,.352),0,.88)
 body.data.materials.clear();body.data.materials.append(skin)
 sub=body.modifiers.new('Anatomical subdivision','SUBSURF');sub.levels=sub.render_levels=1
 for p in body.data.polygons:p.use_smooth=True
 # Pose the actual human skeleton in the painting's kneeling stance.
 for name,a,b in [('pelvis',P(72,137,.07),P(72,124,.07)),('spine_01',P(72,124,.07),P(69,108,.06)),('spine_02',P(69,108,.06),P(65,91,.055)),('spine_03',P(65,91,.055),P(64,77,.05)),('neck_01',P(64,77,.05),P(66,67,.04)),('head',P(66,67,.04),P(68,47,.04))]:setbone(name,a,b,.65 if name!='head' else .95)
 for side,points in [('r',[(64,131,.05),(78,191,.38),(38,185,.42)]),('l',[(80,131,.07),(124,141,.10),(131,190,.28)])]:
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
  p=rig.pose.bones['upperarm_'+side];a=rig.matrix_world @ p.head;b=rig.matrix_world @ p.tail
  tube('billowing ivory sleeve '+side,a,b+(b-a)*.08,(.085,.075,.036),linen,'upperarm_'+side)
  tube('rolled sleeve cuff '+side,b-(b-a)*.12,b+(b-a)*.12,(.083,.080,.012),linen,'upperarm_'+side)
  p=rig.pose.bones['thigh_'+side];a=rig.matrix_world @ p.head;b=rig.matrix_world @ p.tail
  tube('patched breeches '+side,a,b,(.115,.086,.020),buff,'thigh_'+side)
  p=rig.pose.bones['calf_'+side];a=rig.matrix_world @ p.head;b=rig.matrix_world @ p.tail
  tube('dark gaiter '+side,a,b,(.079,.047,.012),pants,'calf_'+side)
  # Visible patches and stitch loops, kept on their anatomical segment.
  for t in (.28,.65):
   center=a.lerp(b,t)+Vector((0,-.065,0));patchvs=[center+Vector((x,-.003,z)) for x,z in [(-.035,-.034),(.033,-.028),(.038,.025),(-.026,.035)]]
   attach(bevel(solid(mesh('stitched gaiter patch '+side,patchvs,[(0,1,2,3)],leather),.004),.002),'calf_'+side)
  ankle=rig.matrix_world @ rig.pose.bones['foot_'+side].head
  loc=P(137,199,.24) if side=='l' else P(38,191,.40)
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
 feather=[P(59-36*t,34-7*sin(pi*t)+9*t**3,.06) for t in [k/32 for k in range(33)]];attach(curve('swept feather quill',feather,.003,linen),'head')
 # Real thin feather vanes, with camber and a scalloped margin under the barbs.
 fvs=[];ffs=[]
 for k,pnt in enumerate(feather):
  t=k/32;width=.040*sin(pi*t)**.7
  for side in (-1,0,1):fvs.append(pnt+Vector((-.010*abs(side),.012*abs(side)*sin(pi*t),side*width)))
 for k in range(32):
  for j in range(2):i=k*3+j;ffs.append((i,i+1,i+4,i+3))
 attach(solid(mesh('cambered feather vanes',fvs,ffs,linen),.0015),'head')
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
  nodes=smoke.active_material.node_tree.nodes;links=smoke.active_material.node_tree.links;output=nodes.get('Material Output')
  for link in list(output.inputs['Surface'].links):links.remove(link)
  volume=nodes.new('ShaderNodeVolumePrincipled');volume.inputs['Color'].default_value=(.68,.72,.78,1);volume.inputs['Density'].default_value=9
  links.new(volume.outputs['Volume'],output.inputs['Volume'])
 bpy.ops.mesh.primitive_cylinder_add(vertices=96,radius=.505,depth=.074,location=(.007,.20,.047));base=bpy.context.object;base.name='GEO-stationary cream base';base.data.materials.append(stone);bevel(base,.014)
 # Camera-only stone pigment opens the cream while live AO preserves contact.
 nodes=stone.node_tree.nodes;links=stone.node_tree.links;bs=nodes.get('Principled BSDF');output=nodes.get('Material Output')
 ao=nodes.new('ShaderNodeAmbientOcclusion');ao.inputs['Distance'].default_value=.12
 geometry=nodes.new('ShaderNodeNewGeometry');normal=nodes.new('ShaderNodeSeparateXYZ');links.new(geometry.outputs['Normal'],normal.inputs[0])
 colors=nodes.new('ShaderNodeMixRGB');colors.inputs[1].default_value=(.75,.50,.29,1);colors.inputs[2].default_value=(1,.83,.63,1);links.new(normal.outputs['Z'],colors.inputs[0])
 grain=nodes.new('ShaderNodeTexNoise');grain.inputs['Scale'].default_value=185;grain.inputs['Detail'].default_value=2;links.new(geometry.outputs['Position'],grain.inputs['Vector'])
 grainrange=nodes.new('ShaderNodeMapRange');grainrange.inputs['To Min'].default_value=.94;grainrange.inputs['To Max'].default_value=1.0;links.new(grain.outputs['Fac'],grainrange.inputs['Value'])
 stonecolor=nodes.new('ShaderNodeMixRGB');stonecolor.blend_type='MULTIPLY';stonecolor.inputs[0].default_value=1;links.new(colors.outputs[0],stonecolor.inputs[1]);links.new(grainrange.outputs[0],stonecolor.inputs[2]);links.new(stonecolor.outputs[0],ao.inputs['Color'])
 pigment=nodes.new('ShaderNodeEmission');links.new(ao.outputs['Color'],pigment.inputs['Color'])
 camray=nodes.new('ShaderNodeLightPath');strength=nodes.new('ShaderNodeMath');strength.operation='MULTIPLY';strength.inputs[1].default_value=.78;links.new(camray.outputs['Is Camera Ray'],strength.inputs[0])
 mix=nodes.new('ShaderNodeMixShader');links.new(strength.outputs[0],mix.inputs[0]);links.new(bs.outputs[0],mix.inputs[1]);links.new(pigment.outputs[0],mix.inputs[2]);links.new(mix.outputs[0],output.inputs['Surface'])
 sc=configure();sc.world.use_nodes=True;sc.world.node_tree.nodes.get('Background').inputs[0].default_value=(.65,.70,.8,1);sc.world.node_tree.nodes.get('Background').inputs[1].default_value=.3
 bpy.ops.object.camera_add(location=CENTER+VIEW*8);cam=bpy.context.object;cam.name='CAM-painting';cam.rotation_euler=(-VIEW).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=SPAN;sc.camera=cam
 for name,loc,power,size,color in [('key',(-3,-4,5),280,2.8,(1,.96,.88)),('fill',(3,-3,3),56,3.,(.90,.94,1)),('rim',(1,2,4),84,2.,(.84,.91,1))]:
  bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name='LGT-'+name;o.data.energy=power;o.data.size=size;o.data.color=color;o.rotation_euler=(Vector((0,0,.7))-o.location).to_track_quat('-Z','Y').to_euler()
 # Convert props to real meshes before fixed UV projection. No live camera shader.
 for o in list(sc.objects):
  if o.type=='CURVE':
   bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
 from refine import finish_surfaces, bind_torso
 finish_surfaces();bind_torso(rig)
 sc['unit']='barbarian-musketman';sc['anatomy']='MPFB 2.0.18 CC0';sc['cream_target']='#E9CFA0'
 bpy.context.view_layer.update();rig['rest_pose']=json.dumps({p.name:[list(r) for r in p.matrix_basis] for p in rig.pose.bones});rig['rest_location']=list(rig.location)
 (M/'bones.json').write_text(json.dumps({p.name:{'head':list(p.head),'tail':list(p.tail)} for p in rig.pose.bones},indent=2))
 bpy.ops.wm.save_as_mainfile(filepath=str(M/'plain.blend'));log('Built kneeling MPFB human, tailored ragged kit, feather hat, bandolier and solid horizontal musket.')

def project():
 """Frozen UVs on finished surfaces; original pigment lights camera rays only."""
 sc=bpy.context.scene;cam=sc.camera;im=bpy.data.images.load(str(A/'projection.png'),check_existing=True);records=[]
 dg=bpy.context.evaluated_depsgraph_get()
 for o in list(sc.objects):
  if o.type!='MESH' or any(x in o.name for x in ('muzzle','eyes','stationary cream base')):continue
  ev=o.evaluated_get(dg);me=ev.to_mesh();assert len(me.vertices)==len(o.data.vertices)
  uv=o.data.uv_layers.get('Painting') or o.data.uv_layers.new(name='Painting');col=o.data.color_attributes.new(name='Projection facing',type='FLOAT_COLOR',domain='CORNER')
  incidence=o.data.color_attributes.new(name='Rest incidence',type='FLOAT_COLOR',domain='CORNER')
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
   dot=max(.02,(normalmat @ me.vertices[i].normal).normalized().dot((cam.location-ev.matrix_world @ me.vertices[i].co).normalized()));incidence.data[loop.index].color=(dot,dot,dot,1)
  ev.to_mesh_clear()
  for slot in o.material_slots:
   if not slot.material:continue
   ma=slot.material.copy();slot.material=ma;n=ma.node_tree.nodes;l=ma.node_tree.links;p=n.get('Principled BSDF');out=n.get('Material Output')
   tc=n.new('ShaderNodeUVMap');tc.uv_map='Painting';tex=n.new('ShaderNodeTexImage');tex.image=im;tex.extension='CLIP';l.new(tc.outputs[0],tex.inputs[0])
   attr=n.new('ShaderNodeVertexColor');attr.layer_name=col.name
   mul=n.new('ShaderNodeMath');mul.operation='MULTIPLY';l.new(attr.outputs[0],mul.inputs[0]);l.new(tex.outputs['Alpha'],mul.inputs[1])
   camera=n.new('ShaderNodeLightPath');camera.name='Camera-only pigment'
   # Fade a formerly grazing projected surface into the generated fill when it
   # turns toward camera; frozen UVs remain attached to the real deforming mesh.
   geometry=n.new('ShaderNodeNewGeometry');dot=n.new('ShaderNodeVectorMath');dot.operation='DOT_PRODUCT';l.new(geometry.outputs['Normal'],dot.inputs[0]);l.new(geometry.outputs['Incoming'],dot.inputs[1])
   restangle=n.new('ShaderNodeVertexColor');restangle.layer_name='Rest incidence'
   tolerance=n.new('ShaderNodeMath');tolerance.operation='ADD';tolerance.inputs[1].default_value=.15;l.new(restangle.outputs[0],tolerance.inputs[0])
   divisor=n.new('ShaderNodeMath');divisor.operation='MAXIMUM';divisor.inputs[1].default_value=.05;l.new(dot.outputs['Value'],divisor.inputs[0])
   ratio=n.new('ShaderNodeMath');ratio.operation='DIVIDE';ratio.use_clamp=True;l.new(tolerance.outputs[0],ratio.inputs[0]);l.new(divisor.outputs[0],ratio.inputs[1])
   coverage=n.new('ShaderNodeMath');coverage.operation='MULTIPLY';l.new(mul.outputs[0],coverage.inputs[0]);l.new(ratio.outputs[0],coverage.inputs[1])
   weight=n.new('ShaderNodeMath');weight.operation='MULTIPLY';l.new(coverage.outputs[0],weight.inputs[0]);l.new(camera.outputs['Is Camera Ray'],weight.inputs[1])
   paint=n.new('ShaderNodeEmission');paint.inputs['Strength'].default_value=1;l.new(tex.outputs['Color'],paint.inputs['Color'])
   blend=n.new('ShaderNodeMixShader');l.new(weight.outputs[0],blend.inputs[0]);l.new(p.outputs[0],blend.inputs[1]);l.new(paint.outputs[0],blend.inputs[2]);l.new(blend.outputs[0],out.inputs['Surface'])
  records.append({'object':o.name,'vertices':len(o.data.vertices),'visible_vertices':sum(v>0 for v in facing)})
 bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(M/'barbarian-musketman.blend'))
 (M/'projection.json').write_text(json.dumps({'objects':records,'method':'finished surfaces, frozen UV, facing and ray visibility; camera-only pigment','stone':'physical only; no figure paint','hidden_surfaces':'original generated painted fills'},indent=2))
 log('Finished-surface camera-only projection applied; physical stone excluded and generated fills retained.')


def render(stage,blend,frames):
 bpy.ops.wm.open_mainfile(filepath=str(blend));sc=configure();assert sc.camera
 out=M/'renders'/stage;out.mkdir(exist_ok=True);manifest=out/'render.json';manifest.unlink(missing_ok=True)
 if stage.startswith('g-feet-'):
  target=Vector((0,.08,.22));cam=sc.camera
  cam.location=target+Vector((0,0,5) if stage.endswith('top') else (5,0,.18));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=1.35
  for obj in sc.objects:
   if obj.type=='MESH':obj.hide_render=not any(word in obj.name for word in ('boot','gaiter','breeches','stationary cream base'))
 if stage=='b-plain':
  clay=mat('plain clay',(.45,.4,.32));sc.view_layers[0].material_override=clay
 for i,f in enumerate(frames):
  if 'FRAME_INDEX' in os.environ and i!=int(os.environ['FRAME_INDEX']):continue
  sc.frame_set(f)
  if stage=='e-death' and i==len(frames)-1:
   import shutil;shutil.copyfile(out/f'{i-1:02}.png',out/f'{i:02}.png');continue
  sc.render.filepath=str(out/f'{i:02}.png');bpy.ops.render.render(write_still=True)
 if 'FRAME_INDEX' in os.environ:return
 manifest.write_text(json.dumps({'stage':stage,'engine':sc.render.engine,'device':sc.cycles.device,'samples':sc.cycles.samples,'resolution':sc.render.resolution_x,'blend_sha256':hashlib.sha256(blend.read_bytes()).hexdigest(),'frames':len(frames)}))
 subprocess.run([str(R/'venv/bin/python'),str(HERE/'finish.py'),'review',stage],check=True);log('Posted '+stage+' review ('+sc.cycles.device+', '+str(sc.render.resolution_x)+' px).')


def animate(clip):
 global rig
 bpy.ops.wm.open_mainfile(filepath=str(M/'barbarian-musketman.blend'));sc=bpy.context.scene;rig=bpy.data.objects['RIG-Barbarian musketman MPFB'];gun=bpy.data.objects['CTRL-musket']
 from motion import Motion, MAP
 motion=Motion(R) if clip!='attack' else None
 source0=motion.sample(clip,0) if motion else None
 count,fps,loop=CLIPS[clip];sc.render.fps=fps;sc.frame_start=1;sc.frame_end=count
 rest={p.name:p.matrix_basis.copy() for p in rig.pose.bones};restworld={p.name:p.matrix.copy() for p in rig.pose.bones};gunrest=gun.matrix_basis.copy();rigrest=rig.matrix_world.copy()
 grip=gun.matrix_world.inverted() @ rig.pose.bones['hand_l'].matrix
 cloth=[o for o in sc.objects if any(word in o.name for word in ('ragged coat tail','torn sash ribbon'))]
 if clip=='death':
  for obj in cloth:obj.shape_key_add(name='Basis')
 for p in rig.pose.bones:p.rotation_mode='QUATERNION'
 def constrain_grip():
  target_matrix=gun.matrix_world @ grip;target=target_matrix.translation;a=rig.pose.bones['upperarm_l'].head.copy()
  l1=(restworld['lowerarm_l'].translation-restworld['upperarm_l'].translation).length;l2=(restworld['hand_l'].translation-restworld['lowerarm_l'].translation).length
  axis=target-a;distance=min(axis.length,l1+l2-.00001);axis.normalize();along=(l1*l1-l2*l2+distance*distance)/(2*distance)
  pole=rig.pose.bones['lowerarm_l'].head-a;side=(pole-axis*pole.dot(axis)).normalized();elbow=a+along*axis+max(0,l1*l1-along*along)**.5*side
  setbone('upperarm_l',a,elbow);setbone('lowerarm_l',elbow,target);rig.pose.bones['hand_l'].matrix=target_matrix;bpy.context.view_layer.update()
 def turn(name,axis,angle):
  p=rig.pose.bones[name];m=p.matrix.copy();pos=m.translation.copy();m=Matrix.Rotation(angle,4,axis) @ m;m.translation=pos;p.matrix=m;bpy.context.view_layer.update()
 def settle_hand(side,weight):
  # Ground contact adapts the source fall, preserving limb lengths and elbow pole.
  upper=rig.pose.bones['upperarm_'+side];lower=rig.pose.bones['lowerarm_'+side];hand=rig.pose.bones['hand_'+side]
  handmatrix=hand.matrix.copy();world=rig.matrix_world @ hand.head;contact=world.copy()
  center=Vector((.007,.20,0));radius=Vector((contact.x-center.x,contact.y-center.y,0))
  if radius.length>.43:radius*=.43/radius.length
  contact.x=center.x+radius.x;contact.y=center.y+radius.y;contact.z=.13
  target=rig.matrix_world.inverted() @ world.lerp(contact,weight);a=upper.head.copy()
  l1=(upper.tail-upper.head).length;l2=(lower.tail-lower.head).length
  axis=target-a;distance=max(abs(l1-l2)+.0001,min(axis.length,l1+l2-.0001));axis.normalize();target=a+axis*distance
  along=(l1*l1-l2*l2+distance*distance)/(2*distance);pole=lower.head-a;pole-=axis*pole.dot(axis)
  if pole.length<.0001:pole=axis.cross(Vector((0,0,1)))
  elbow=a+axis*along+pole.normalized()*max(0,l1*l1-along*along)**.5
  for name,start,end,length in [('upperarm_'+side,a,elbow,l1),('lowerarm_'+side,elbow,target,l2)]:
   p=rig.pose.bones[name];q=p.bone.matrix_local.to_quaternion();rotation=(q @ Vector((0,1,0))).rotation_difference((end-start).normalized()) @ q
   p.matrix=Matrix.LocRotScale(start,rotation,Vector((1,length/p.bone.length,1)));bpy.context.view_layer.update()
  handmatrix.translation=target;hand.matrix=handmatrix;bpy.context.view_layer.update()
 for i in range(count+(1 if loop else 0)):
  frame=i+1;t=i/count if loop else min(i/(count-2),1);wave=sin(2*pi*t)
  rig.matrix_world=rigrest;gun.matrix_basis=gunrest
  for p in rig.pose.bones:p.matrix_basis=rest[p.name]
  bpy.context.view_layer.update()
  if clip in ('idle','move','hit','death'):
   phase=([0,1,.45,0][i] if clip=='hit' else t)
   source=motion.sample(clip,phase)
   # Source world deltas cancel source rest rolls. Preserve target bind lengths.
   for name,source_name in MAP.items():
    if name=='pelvis':continue
    if clip in ('idle','move','hit') and name.startswith(('thigh','calf','foot','ball')):continue
    delta=source[source_name].to_quaternion() @ source0[source_name].to_quaternion().inverted()
    if clip!='death':
     hipdelta=source['DEF-hips'].to_quaternion() @ source0['DEF-hips'].to_quaternion().inverted()
     delta=hipdelta.inverted() @ delta
    if clip=='death':
     hipdelta=source['DEF-hips'].to_quaternion() @ source0['DEF-hips'].to_quaternion().inverted();delta=hipdelta.inverted() @ delta
    p=rig.pose.bones[name];position=p.head.copy();_,q,scale=restworld[name].decompose()
    p.matrix=Matrix.LocRotScale(position,delta @ q,scale);bpy.context.view_layer.update()
  if clip=='move':
   # Retain the source's crouched rhythm, constrained to this unit's kneeling support.
   # The planted right knee/boot never translates. Left boot moves only while lifted.
   foot_delta=source['DEF-foot.L'].translation-source0['DEF-foot.L'].translation
   lift=max(0,foot_delta.z-.006)*.28;gate=min(1,lift/.010)
   for side in ('r','l'):
    a=restworld['thigh_'+side].translation.copy();b=restworld['calf_'+side].translation.copy();ankle=restworld['foot_'+side].translation.copy()
    if side=='l':
     b+=Vector((foot_delta.x*.035*gate,0,lift*.4));ankle+=Vector((foot_delta.x*.075*gate,0,lift))
    setbone('thigh_'+side,a,b,.25);setbone('calf_'+side,b,ankle,.2)
    # Source delta retains ankle articulation; reference rig owns foot forward direction.
    foot=restworld['foot_'+side].copy();foot.translation=ankle
    if side=='l' and gate:
     delta=source['DEF-foot.L'].to_quaternion() @ source0['DEF-foot.L'].to_quaternion().inverted()
     q=__import__('mathutils').Quaternion().slerp(delta,.20*gate)
     foot=Matrix.LocRotScale(ankle,q @ foot.to_quaternion(),foot.to_scale())
    rig.pose.bones['foot_'+side].matrix=foot;bpy.context.view_layer.update()
  elif clip=='attack':
   recoil=[0,0,.02,.10,.85,1,.5,.2,.05,0][i];turn('spine_02','Y',-.10*recoil);turn('head','Y',-.04*recoil)
   turn('upperarm_r','Y',-.04*recoil)
  elif clip=='death':
   fall=min(1,t/.55)
   source_hip=source['DEF-hips'];origin_hip=source0['DEF-hips']
   delta=source_hip.to_quaternion() @ origin_hip.to_quaternion().inverted()
   # The source's timed backward fall drives the root; contact/framing solve its placement.
   pivot=restworld['pelvis'].translation
   displacement=(source_hip.translation-origin_hip.translation)*.48
   rig.matrix_world=Matrix.Translation(pivot+displacement) @ delta.to_matrix().to_4x4() @ Matrix.Translation(-pivot) @ rigrest
   # Transition the kneeling reference legs into the source's actual terminal
   # leg directions. Keeping kneeling offsets at full fall left both boots airborne.
   blend=max(0,min(1,(t-.20)/.45))
   for side,suffix in (('l','.L'),('r','.R')):
    for target_bone,source_a,source_b in [('thigh','thigh','shin'),('calf','shin','foot'),('foot','foot','toe'),('upperarm','upper_arm','forearm'),('lowerarm','forearm','hand')]:
     name=target_bone+'_'+side;p=rig.pose.bones[name];a=p.head.copy();current=(p.tail-p.head).normalized()
     direction=delta.inverted() @ (source['DEF-'+source_b+suffix].translation-source['DEF-'+source_a+suffix].translation).normalized()
     amount=blend*.25 if target_bone in ('upperarm','lowerarm') else blend
     desired=current.lerp(direction,amount).normalized();length=(restworld[name] @ Vector((0,p.bone.length,0))-restworld[name].translation).length
     rest_rotation=p.bone.matrix_local.to_quaternion();orientation=(rest_rotation @ Vector((0,1,0))).rotation_difference(desired) @ rest_rotation
     p.matrix=Matrix.LocRotScale(a,orientation,Vector((1,length/p.bone.length,1)));bpy.context.view_layer.update()
   bpy.context.view_layer.update()
   # Settle actual evaluated anatomy/boots on the disc, not oversized object bounds.
   # Ragged cloth must not prop up the entire fallen body.
   if fall>.1:
    zs=[];xs=[];dg=bpy.context.evaluated_depsgraph_get()
    for o in sc.objects:
     if o.type!='MESH' or o.name=='GEO-stationary cream base' or 'muzzle' in o.name or o.parent==gun:continue
     ev=o.evaluated_get(dg);me=ev.to_mesh();points=[ev.matrix_world @ v.co for v in me.vertices];xs.extend(p.x for p in points)
     if any(word in o.name for word in ('anatomical','boot','sleeve','breeches','gaiter')):zs.extend(p.z for p in points)
     ev.to_mesh_clear()
    rig.location.z+=.086-min(zs)
    # Camera remains fixed; translate the falling body just enough to retain a feather margin.
    rig.location.x+=max(0,-.525-min(xs))-max(0,max(xs)-1.105)
   bpy.context.view_layer.update()
   release=max(0,min(1,t/.32));release=release*release*(3-2*release)
   initial=gun.matrix_world.copy();final=Matrix.Identity(4);final.translation=Vector((-.13,-.30,.14))
   # Rest gun axis remains horizontal. Release is keyed as an actual rigid transform.
   q=initial.to_quaternion().slerp(__import__('mathutils').Quaternion(),release)
   transform=q.to_matrix().to_4x4();transform.translation=initial.translation.lerp(final.translation,release);gun.matrix_world=transform
   contact=max(0,min(1,(t-.40)/.35));contact=contact*contact*(3-2*contact)
   for side in ('r','l'):settle_hand(side,contact)
   gun.matrix_world=transform
  bpy.context.view_layer.update()
  if clip!='death':constrain_grip()
  if clip=='death':
   # Correct true cloth vertices against the stone, preserving thickness and UVs.
   base=bpy.data.objects['GEO-stationary cream base']
   for obj in cloth:
    key=obj.shape_key_add(name=f'Contact {frame}',from_mix=False)
    for vert in key.data:
     world=obj.matrix_world @ vert.co;local=base.matrix_world.inverted() @ world
     floor=.087 if local.x*local.x+local.y*local.y<.505**2 else .012
     if world.z<floor:world.z=floor+(world.z-floor)*.03;vert.co=obj.matrix_world.inverted() @ world
    key.value=0;key.keyframe_insert('value',frame=max(0,frame-1));key.value=1;key.keyframe_insert('value',frame=frame);key.value=0;key.keyframe_insert('value',frame=frame+1)
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
 (M/'clips'/f'{clip}.json').write_text(json.dumps({'frames':count,'fps':fps,'loop':loop,'source_sha256':hashlib.sha256((M/'barbarian-musketman.blend').read_bytes()).hexdigest(),'motion':motion.provenance(clip) if motion else {'method':'authored weapon-specific recoil'}}));log('Authored '+clip+' skeletal action, '+str(count)+' samples.')

def audit():
 reports=[];source=hashlib.sha256((M/'barbarian-musketman.blend').read_bytes()).hexdigest()
 bpy.ops.wm.open_mainfile(filepath=str(M/'barbarian-musketman.blend'))
 from refine import audit_surface
 surface=audit_surface()
 master_rig=bpy.data.objects['RIG-Barbarian musketman MPFB'];lengths={p.name:(p.tail-p.head).length for p in master_rig.pose.bones}
 for clip,(n,fps,loop) in CLIPS.items():
  path=M/'clips'/f'{clip}.blend';meta=json.loads(path.with_suffix('.json').read_text());assert meta['source_sha256']==source
  bpy.ops.wm.open_mainfile(filepath=str(path));sc=bpy.context.scene;rig=bpy.data.objects['RIG-Barbarian musketman MPFB'];assert len(rig.data.bones)==53
  base=bpy.data.objects['GEO-stationary cream base'];origin=base.matrix_world.copy();counts=[];minz=100;poses=[];feet=[];grips=[]
  sc.frame_set(1);bpy.context.view_layer.update();gun=bpy.data.objects['CTRL-musket'];grip=gun.matrix_world.inverted() @ rig.matrix_world @ rig.pose.bones['hand_l'].matrix
  for frame in range(1,n+1):
   sc.frame_set(frame);bpy.context.view_layer.update();assert base.matrix_world==origin
   for bone in rig.pose.bones:
    if bone.name.startswith(('thigh','calf','foot','upperarm','lowerarm')):assert .85<(bone.tail-bone.head).length/lengths[bone.name]<1.15,(clip,frame,bone.name,'retarget stretch')
   feet.append({side:list((rig.matrix_world @ rig.pose.bones['foot_'+side].matrix).translation) for side in ('l','r')})
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
  if clip=='move':
   for positions in feet:
    assert (Vector(positions['r'])-Vector(feet[0]['r'])).length<.0001,'Kneeling support foot slid'
    if abs(positions['l'][2]-feet[0]['l'][2])<.001:assert abs(positions['l'][0]-feet[0]['l'][0])<.004,'Planted lead foot slid'
  reports.append({'feet':feet,'maximum_grip_error':max(grips,default=0),'motion':meta.get('motion'),'distinct_skeletal_poses':len(set(poses)),'clip':clip,'frames':n,'bones':len(rig.data.bones),'stationary_base':True,'minimum_bbox_z':minz,'smoke_objects_visible':counts})
 (V/'barbarian-musketman-audit.json').write_text(json.dumps({'surface':surface,'checks':reports,'limits':'Bounds and rig checks do not establish hand contacts, cloth collision freedom or visual approval.'},indent=2));log('Audit passed: five clips, source hashes, 53-bone rig, fixed base and positive object scales.')

mode=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'build'
if mode=='preflight':
 configure();print('GPU preflight passed',flush=True)
elif mode=='build':
 build();render('b-plain',M/'plain.blend',[1]);bpy.ops.wm.open_mainfile(filepath=str(M/'plain.blend'));configure();from bake import bake;bake();project();render('c-textured-lit',M/'barbarian-musketman.blend',[1])
elif mode=='build-only':
 build();configure();from bake import bake;bake();project()
elif mode.startswith('frame-'):
 stage=mode[6:]
 blend=M/('plain.blend' if stage=='b-plain' else 'barbarian-musketman.blend' if stage=='c-textured-lit' else 'clips/move.blend' if stage.startswith('g-feet-') else 'clips/attack.blend' if stage=='d-rig-poses' else f'clips/{stage[2:]}.blend')
 frames=[1] if stage in ('b-plain','c-textured-lit') else [1,3,5,7] if stage=='d-rig-poses' else list(range(1,9)) if stage.startswith('g-feet-') else list(range(1,CLIPS[stage[2:]][0]+1))
 render(stage,blend,frames)
elif mode=='rest':
 render('b-plain',M/'plain.blend',[1]);render('c-textured-lit',M/'barbarian-musketman.blend',[1])
elif mode.startswith('animate-'):animate(mode[8:])
elif mode.startswith('e-'):render(mode,M/'clips'/(mode[2:]+'.blend'),list(range(1,CLIPS[mode[2:]][0]+1)))
elif mode=='audit':audit()
elif mode=='feet':
 for view in ('top','front'):render('g-feet-'+view,M/'clips/move.blend',list(range(1,9)))
elif mode=='animate':
 for clip in CLIPS:animate(clip)
elif mode in ('preview','render'):
 if mode=='render':
  render('b-plain',M/'plain.blend',[1]);render('c-textured-lit',M/'barbarian-musketman.blend',[1])
 render('d-rig-poses',M/'clips/attack.blend',[1,3,5,7])
 for clip,(n,_,_) in CLIPS.items():render('e-'+clip,M/'clips'/f'{clip}.blend',list(range(1,n+1)))
 for view in ('top','front'):render('g-feet-'+view,M/'clips/move.blend',list(range(1,9)))
else:raise ValueError(mode)
