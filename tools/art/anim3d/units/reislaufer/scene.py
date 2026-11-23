"""Reislaufer: MPFB anatomy, tailored 3D kit, frozen camera UVs and five actions."""
import bpy, math, os, sys, json, hashlib, subprocess
from pathlib import Path
from mathutils import Vector, Matrix
from math import sin, cos, pi
from bpy_extras.object_utils import world_to_camera_view
R=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'))
M=R/'masters/reislaufer'; A=R/'assets/reislaufer'; V=R/'review/3d-v2'
for p in (M,V,M/'clips',M/'renders'):p.mkdir(parents=True,exist_ok=True)
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
CLIPS={'idle':(8,10,True),'move':(8,12,True),'attack':(10,14,False),'hit':(4,12,False),'death':(10,10,False)}
def log(s):
 with (V/'reislaufer-log.md').open('a') as f:f.write('- '+s+'\n')
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
 if fill=='steel':
  grey=n.new('ShaderNodeRGBToBW');l.new(t.outputs['Color'],grey.inputs[0]);tone=n.new('ShaderNodeValToRGB');tone.color_ramp.elements[0].color=(.11,.135,.15,1);tone.color_ramp.elements[1].color=(.70,.73,.72,1);l.new(grey.outputs[0],tone.inputs[0]);l.new(tone.outputs[0],p.inputs['Base Color'])
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
 sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0
 return sc

# Camera coordinates in the original 256-pixel token. Positive depth is away from camera.
UP=Vector((0,math.sin(math.radians(12)),math.cos(math.radians(12))))
VIEW=Vector((0,-math.cos(math.radians(12)),math.sin(math.radians(12))))
CENTER=Vector((0,0,1.025));SPAN=2.5

def P(x,y,depth=0):return CENTER+Vector(((x-128)*SPAN/256,0,0))+UP*((128-y)*SPAN/256)-VIEW*depth

def setbone(name,a,b,yaw=0):
 p=rig.pose.bones[name];inverse=rig.matrix_world.inverted();a=inverse @ Vector(a);b=inverse @ Vector(b);direction=b-a
 # Orient long axis exactly along target; preserve anatomical roll with rest matrix.
 q=p.bone.matrix_local.to_quaternion();r=(q @ Vector((0,1,0))).rotation_difference(direction.normalized()) @ q
 if yaw:r=__import__('mathutils').Quaternion(direction.normalized(),yaw) @ r
 m=r.to_matrix().to_4x4() @ Matrix.Diagonal((1,direction.length/p.bone.length,1,1));m.translation=a;p.matrix=m;bpy.context.view_layer.update()

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
 macro=TargetService.get_default_macro_info_dict();macro.update(gender=1.,age=.52,muscle=.62,weight=.48,height=.5,proportions=.65);macro['race']={'caucasian':1.,'african':0.,'asian':0.}
 body=HumanService.create_human(macro_detail_dict=macro);body.name='GEO-MPFB anatomical reislaufer'
 bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();lo=min(v.co.z for v in me.vertices);hi=max(v.co.z for v in me.vertices);ev.to_mesh_clear();body.scale=(1.72/(hi-lo),)*3
 bpy.context.view_layer.objects.active=body;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 rig=HumanService.add_builtin_rig(body,'game_engine');rig.name='RIG-Reislaufer MPFB'
 for bone in rig.data.bones:bone.inherit_scale='NONE'
 system=R/'blender-user/extensions/.user/user_default/mpfb/data';eyes=HumanService.add_mhclo_asset(str(system/'eyes/high-poly/high-poly.mhclo'),body,asset_type='Eyes',subdiv_levels=1,material_type='MAKESKIN');eyes.name='GEO-MPFB eyes'
 skin=mat('painted ochre skin',(.49,.265,.12),fill='skin');linen=mat('slashed ivory lining',(.73,.60,.39),fill='linen');red=mat('vermilion wool',(.42,.045,.018));yellow=mat('ochre wool',(.66,.39,.035));leather=mat('scuffed brown leather',(.16,.07,.025),fill='coat');steel=mat('bright worn steel',(.55,.57,.56),1,.34,fill='steel');brass=mat('polished brass',(.75,.48,.15),1,.28);wood=mat('ash pike',(.35,.17,.045));dark=mat('chestnut hair',(.095,.045,.02),fill='hair');stone=mat('cream limestone E9CFA0',(.815,.624,.352),0,.88)
 for material,tint in [(red,(.6,.08,.025,1)),(yellow,(.75,.47,.065,1))]:
  n=material.node_tree.nodes;l=material.node_tree.links;tex=n.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(A/'linen-fill.png'),check_existing=True);tex.projection='BOX';tex.projection_blend=.3;tc=n.new('ShaderNodeTexCoord');l.new(tc.outputs['Generated'],tex.inputs[0]);mix=n.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1;mix.inputs[2].default_value=tint;l.new(tex.outputs[0],mix.inputs[1]);l.new(mix.outputs[0],n.get('Principled BSDF').inputs['Base Color']);n.get('Principled BSDF').inputs['Sheen Weight'].default_value=.25
 body.data.materials.clear();body.data.materials.append(skin)
 # Covered torso remains textile when motion exposes a gap between tailored pieces.
 body.data.materials.append(red)
 for poly in body.data.polygons:
  weights=[sum(g.weight for g in body.data.vertices[i].groups if body.vertex_groups[g.group].name.startswith(('spine','pelvis'))) for i in poly.vertices]
  if min(weights)>.45:poly.material_index=1
 sub=body.modifiers.new('Anatomical subdivision','SUBSURF');sub.levels=sub.render_levels=1
 for p in body.data.polygons:p.use_smooth=True
 for name,a,b in [('pelvis',P(128,137,.04),P(127,124,.04)),('spine_01',P(127,124,.04),P(127,111,.04)),('spine_02',P(127,111,.04),P(128,96,.04)),('spine_03',P(128,96,.04),P(128,78,.04)),('neck_01',P(128,78,.04),P(129,69,.04)),('head',P(129,69,.04),P(132,49,.04))]:setbone(name,a,b,.12)
 for side,pts in [('r',[(116,137,.04),(104,173,.02),(99,213,.02),(89,221,-.05)]),('l',[(138,137,.06),(147,174,.04),(157,213,.01),(169,221,-.06)])]:
  a,b,c,d=[P(*v) for v in pts];setbone('thigh_'+side,a,b);setbone('calf_'+side,b,c);setbone('foot_'+side,c,d)
 for side,pts in [('r',[(111,86,.02),(91,99,-.02),(105,81,-.15),(109,77,-.17)]),('l',[(145,87,.03),(151,105,-.02),(117,109,-.16),(109,107,-.18)])]:
  a,b,c,d=[P(*v) for v in pts];setbone('upperarm_'+side,a,b);setbone('lowerarm_'+side,b,c);setbone('hand_'+side,c,d)
 for side in ('r','l'):
  for digit in ('index','middle','ring','pinky'):
   for k in range(1,4):p=rig.pose.bones[f'{digit}_{k:02d}_{side}'];p.rotation_mode='XYZ';p.rotation_euler.x=.95
 bpy.context.view_layer.update()
 # Full circumference breastplate, with flared waist and neck opening.
 vs=[];fs=[];ns=64;nr=24
 for j in range(nr+1):
  t=j/nr;center=P(127,124-46*t,.04);rx=.135+.064*sin(pi*t*.75);dep=.105+.04*sin(pi*t)
  for k in range(ns):
   ang=2*pi*k/ns;zcut=.028*abs(sin(ang))*t**8;vs.append(center+Vector((rx*sin(ang),-dep*cos(ang),-zcut)))
 for j in range(nr):
  for k in range(ns):i=j*ns+k;n=j*ns+(k+1)%ns;fs.append((i,n,n+ns,i+ns))
 attach(bevel(solid(mesh('steel breastplate',vs,fs,steel),.009),.003),'spine_02')
 for y,rx in [(79,.12),(123,.14)]:
  center=P(127,y,.04);pts=[center+Vector((rx*sin(a),-.111*cos(a),0)) for a in [k*2*pi/64 for k in range(65)]];attach(curve('breastplate rolled edge',pts,.005,steel),'spine_02')
 # Puffed, slashed sleeves and breeches. Each band is real cloth with pale lining.
 for side,color in [('r',yellow),('l',red)]:
  for segment,label,radii in [('upperarm','puffed sleeve',(.068,.070,.040)),('lowerarm','slashed fore sleeve',(.071,.045,.020)),('thigh','slashed breeches',(.083,.068,.041)),('calf','hose',(.060,.035,.013))]:
   p=rig.pose.bones[segment+'_'+side];a=rig.matrix_world @ p.head;b=rig.matrix_world @ p.tail
   tube(label+' '+side,a,b,radii,color,segment+'_'+side,striped=segment!='calf')
   if segment in ('thigh','upperarm'):
    axis=(b-a).normalized();u=axis.cross(Vector((0,1,0))).normalized();v=axis.cross(u).normalized()
    for k in range(8):
     ang=2*pi*k/8;pts=[]
     for j in range(17):
      t=j/16;r=radii[0]*(1-t)+radii[1]*t+radii[2]*sin(pi*t)**.8+.003;pts.append(a.lerp(b,t)+(u*cos(ang)+v*sin(ang))*r)
     attach(curve('raised slash piping '+side,pts,.0027,color),segment+'_'+side)
  # Ruffled wrist cuff and garter with tied tails.
  p=rig.pose.bones['lowerarm_'+side];a=rig.matrix_world @ p.head;b=rig.matrix_world @ p.tail
  tube('linen cuff '+side,b-(b-a)*.12,b+(b-a)*.04,(.047,.045,.004),linen,'lowerarm_'+side)
  c=rig.matrix_world @ rig.pose.bones['calf_'+side].head
  pts=[c+Vector((.066*cos(k*pi/24),-.066*sin(k*pi/24),0)) for k in range(49)];attach(curve('blue grey knee garter '+side,pts,.012,steel),'calf_'+side)
  foot=rig.pose.bones['foot_'+side];ankle=rig.matrix_world @ foot.head;toe=rig.matrix_world @ foot.tail
  ob=sphere('leather boot '+side,(ankle+toe)/2-Vector((0,0,.018)),(.065,.100,.046),leather);ob.rotation_euler=(toe-ankle).to_track_quat('Y','Z').to_euler();attach(ob,'foot_'+side)
  for j in range(3):
   center=ankle.lerp(toe,.23+j*.20);attach(curve('shoe seam '+side,[center+Vector((-.049,-.005,.015)),center+Vector((0,-.026,.036)),center+Vector((.049,-.005,.015))],.003,linen),'foot_'+side)
 # Hanging split doublet skirts, weighted to the pelvis; real folds and lining.
 for k in range(10):
  ang=2*pi*k/10;vs=[];fs=[]
  for j in range(13):
   t=j/12;center=P(127,129+28*t,.03);r=.14+.12*sin(pi*t*.75)
   for l in range(5):
    u=(l/4-.5)*.48;a=ang+u;fold=.008*sin(l*pi/2+t*2);vs.append(center+Vector(((r+fold)*sin(a),-(.12+.045*t+fold)*cos(a),.018*sin(pi*t))))
  for j in range(12):
   for l in range(4):i=j*5+l;fs.append((i,i+1,i+6,i+5))
  ob=attach(solid(mesh('split doublet skirt '+str(k),vs,fs,yellow if k>4 else red),.006),'pelvis');ob.data.materials.append(linen)
  for poly in ob.data.polygons:
   if poly.index%4==1:poly.material_index=1
 # Waist straps, buckles, straps on the breastplate and sword scabbard.
 ribbon('waist belt',[P(111,126,-.10),P(125,128,-.14),P(144,130,-.08)],.034,leather,'pelvis')
 ribbon('diagonal sword belt',[P(110,130,-.09),P(126,133,-.17),P(147,141,-.08)],.028,leather,'pelvis')
 for x,y in [(128,128),(146,138)]:attach(curve('brass buckle',[P(x-3,y-2,-.20),P(x+3,y-2,-.20),P(x+3,y+2,-.20),P(x-3,y+2,-.20),P(x-3,y-2,-.20)],.004,brass),'pelvis')
 for side,x in [('r',111),('l',144)]:
  ribbon('armour shoulder strap '+side,[P(x,85,-.05),P(x+(-1 if side=='r' else 1),80,.02)],.030,leather,'spine_03')
 for x,y in [(114,83),(140,82),(114,120),(140,119)]:attach(sphere('armour rivet',P(x,y,-.11),(.006,.006,.006),brass),'spine_02')
 attach(curve('sword scabbard',[P(148,137,.08),P(164,169,.09)],.014,leather),'pelvis');attach(curve('sword guard',[P(143,135,.07),P(154,130,.07)],.005,steel),'pelvis')
 attach(curve('sword grip',[P(148,134,.07),P(146,126,.06)],.009,leather),'pelvis')
 # Soft wide red beret, fluted crown and pale sweeping ostrich feather.
 hc=P(133,48,.035);vs=[];fs=[]
 for j in range(7):
  t=j/6
  for k in range(96):
   ang=2*pi*k/96;rad=.10+.13*t;vs.append(hc+Vector((rad*sin(ang),rad*.64*cos(ang),.018*sin(ang*3)*t+.04*sin(ang)*t)))
 for j in range(6):
  for k in range(96):i=j*96+k;n=j*96+(k+1)%96;fs.append((i,n,n+96,i+96))
 attach(bevel(solid(mesh('red beret brim',vs,fs,red),.008),.003),'head');attach(curve('beret rolled rim',vs[-96:]+[vs[-96]],.004,red),'head')
 attach(sphere('soft beret crown',hc+Vector((.02,0,.035)),(.14,.11,.065),red),'head')
 # Three closed, curved feather lobes retain the source's ivory/navy/ochre fan.
 for label,points,widths,color in [
  ('ivory',[(120,46),(125,39),(135,34),(145,37),(153,43)],[.5,2.5,2.4,2,.3],linen),
  ('navy',[(123,47),(134,41),(145,40),(154,44),(159,53)],[.5,3,3.2,2.5,.3],dark),
  ('gold',[(143,44),(151,47),(156,54),(158,60),(157,65)],[.5,2.5,2.4,1.6,.2],yellow),
 ]:
  vs=[];fs=[];centers=[];sections=49;sides=12
  for j in range(sections):
   t=j/(sections-1)*(len(points)-1);k=min(int(t),len(points)-2);f=t-k
   x=points[k][0]*(1-f)+points[k+1][0]*f;y=points[k][1]*(1-f)+points[k+1][1]*f
   tangent=Vector((points[k+1][0]-points[k][0],points[k+1][1]-points[k][1]));tangent.normalize();width=widths[k]*(1-f)+widths[k+1]*f
   center=P(x,y,.025);centers.append(center)
   for q in range(sides):
    angle=q*2*pi/sides;ridge=1+.09*sin(j*2.2+q)
    vs.append(P(x-tangent.y*width*cos(angle)*ridge,y+tangent.x*width*cos(angle)*ridge,.025+.012*sin(angle)))
  for j in range(sections-1):
   for q in range(sides):i=j*sides+q;z=j*sides+(q+1)%sides;fs.append((i,z,z+sides,i+sides))
  fs.extend([tuple(reversed(range(sides))),tuple((sections-1)*sides+q for q in range(sides))])
  attach(mesh('feather lobe '+label,vs,fs,color),'head')
  attach(curve('feather quill '+label,centers,.0015,linen),'head')
 for k in range(24):
  ang=-1.5+3*k/23;c=P(130,57,.05);pts=[c+Vector((.10*sin(ang)+.006*sin(j*1.2+k),.08*cos(ang),-.012*j)) for j in range(10)];attach(curve('wavy hair',pts,.005,dark),'head')
 attach(curve('moustache',[P(124,64,-.11),P(129,63,-.13),P(135,65,-.12)],.004,dark),'head')
 # One rigid ash pike held at two points; metal socket and true faceted spearhead.
 pike=empty('CTRL-pike',P(108,80,-.19));attach(pike,'hand_r')
 parent(curve('ash pike shaft',[P(118,225,-.19),P(107,29,-.19)],.018,wood),pike)
 parent(curve('steel pike socket',[P(107,32,-.19),P(107,24,-.19)],.012,steel),pike)
 vs=[P(107,12,-.19),P(104.4,23,-.19),P(107,29,-.19),P(109.6,23,-.19),P(107,23,-.215),P(107,23,-.165)]
 fs=[(0,1,4),(1,2,4),(2,3,4),(3,0,4),(1,0,5),(2,1,5),(3,2,5),(0,3,5)];parent(bevel(mesh('faceted pike head',vs,fs,steel),.0007),pike)
 bpy.ops.mesh.primitive_cylinder_add(vertices=96,radius=.53,depth=.13,location=(0,.08,.0125));base=bpy.context.object;base.name='GEO-stationary cream base';base.data.materials.append(stone);bevel(base,.014)
 nodes=stone.node_tree.nodes;links=stone.node_tree.links;bs=nodes.get('Principled BSDF');output=nodes.get('Material Output');ao=nodes.new('ShaderNodeAmbientOcclusion');ao.inputs['Distance'].default_value=.06
 geometry=nodes.new('ShaderNodeNewGeometry');normal=nodes.new('ShaderNodeSeparateXYZ');links.new(geometry.outputs['Normal'],normal.inputs[0]);colors=nodes.new('ShaderNodeMixRGB');colors.inputs[1].default_value=(.94,.57,.265,1);colors.inputs[2].default_value=(1.11,.82,.56,1);links.new(normal.outputs['Z'],colors.inputs[0]);grain=nodes.new('ShaderNodeTexNoise');grain.inputs['Scale'].default_value=145;grain.inputs['Detail'].default_value=2;tc=nodes.new('ShaderNodeTexCoord');links.new(tc.outputs['Generated'],grain.inputs['Vector']);tones=nodes.new('ShaderNodeValToRGB');tones.color_ramp.elements[0].color=(.80,.76,.69,1);tones.color_ramp.elements[1].color=(1,1,1,1);links.new(grain.outputs['Fac'],tones.inputs[0]);grainmix=nodes.new('ShaderNodeMixRGB');grainmix.blend_type='MULTIPLY';grainmix.inputs[0].default_value=.16;links.new(colors.outputs[0],grainmix.inputs[1]);links.new(tones.outputs[0],grainmix.inputs[2]);links.new(grainmix.outputs[0],ao.inputs['Color'])
 pigment=nodes.new('ShaderNodeEmission');links.new(ao.outputs['Color'],pigment.inputs['Color']);camray=nodes.new('ShaderNodeLightPath');strength=nodes.new('ShaderNodeMath');strength.operation='MULTIPLY';strength.inputs[1].default_value=.80;links.new(camray.outputs['Is Camera Ray'],strength.inputs[0]);mix=nodes.new('ShaderNodeMixShader');links.new(strength.outputs[0],mix.inputs[0]);links.new(bs.outputs[0],mix.inputs[1]);links.new(pigment.outputs[0],mix.inputs[2]);links.new(mix.outputs[0],output.inputs['Surface'])
 sc=configure();sc.world.use_nodes=True;sc.world.node_tree.nodes.get('Background').inputs[0].default_value=(.65,.70,.8,1);sc.world.node_tree.nodes.get('Background').inputs[1].default_value=.3
 bpy.ops.object.camera_add(location=CENTER+VIEW*8);cam=bpy.context.object;cam.name='CAM-painting';cam.rotation_euler=(-VIEW).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=SPAN;sc.camera=cam
 for name,loc,power,size,color in [('key',(-3,-4,5),280,2.8,(1,.96,.88)),('fill',(3,-3,3),56,3.,(.90,.94,1)),('rim',(1,2,4),84,2.,(.84,.91,1))]:
  bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name='LGT-'+name;o.data.energy=power;o.data.size=size;o.data.color=color;o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
 for o in list(sc.objects):
  if o.type=='CURVE':
   bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
 from refine import finish_surfaces
 finish_surfaces();sc['unit']='reislaufer';sc['anatomy']='MPFB 2.0.18 CC0';sc['cream_target']='#E9CFA0'
 bpy.context.view_layer.update();rig['rest_pose']=json.dumps({p.name:[list(r) for r in p.matrix_basis] for p in rig.pose.bones});rig['rest_location']=list(rig.location)
 (M/'bones.json').write_text(json.dumps({p.name:{'head':list(p.head),'tail':list(p.tail)} for p in rig.pose.bones},indent=2))
 bpy.ops.wm.save_as_mainfile(filepath=str(M/'plain.blend'));log('Built MPFB standing reislaufer, steel breastplate, slashed two-colour clothing, feathered beret and solid pike.')

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
 bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(M/'reislaufer.blend'))
 (M/'projection.json').write_text(json.dumps({'objects':records,'method':'finished surfaces, frozen UV, facing and ray visibility; camera-only pigment','stone':'physical only; no figure paint','hidden_surfaces':'original generated painted fills'},indent=2))
 log('Finished-surface camera-only projection applied; physical stone excluded and generated fills retained.')


def render(stage,blend,frames):
 bpy.ops.wm.open_mainfile(filepath=str(blend));sc=configure();assert sc.camera
 out=M/'renders'/stage;out.mkdir(exist_ok=True);manifest=out/'render.json';manifest.unlink(missing_ok=True)
 if stage.startswith('g-feet-'):
  target=Vector((0,0,.30));cam=sc.camera
  cam.location=target+Vector((0,0,5) if stage.endswith('top') else (0,-5,.18));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=1.35
  for obj in sc.objects:
   if obj.type=='MESH':obj.hide_render=not any(word in obj.name for word in ('boot','hose','breeches','stationary cream base','shoe seam'))
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
 bpy.ops.wm.open_mainfile(filepath=str(M/'reislaufer.blend'));sc=bpy.context.scene;rig=bpy.data.objects['RIG-Reislaufer MPFB'];pike=bpy.data.objects['CTRL-pike']
 from motion import Motion,MAP
 from mathutils import Quaternion
 control_world=pike.matrix_world.copy();pike.parent=None;pike.matrix_world=control_world;bpy.context.view_layer.update()
 motion=Motion(R) if clip!='attack' else None
 source0=motion.sample(clip,0) if motion else None
 neutral=motion.sample('neutral',0) if motion else None
 count,fps,loop=CLIPS[clip];sc.render.fps=fps;sc.frame_start=1;sc.frame_end=count
 rest={p.name:p.matrix_basis.copy() for p in rig.pose.bones};rw={p.name:p.matrix.copy() for p in rig.pose.bones};pikerest=pike.matrix_basis.copy();rigrest=rig.matrix_world.copy()
 grips={side:pike.matrix_world.inverted() @ rig.matrix_world @ rig.pose.bones['hand_'+side].matrix for side in ('r','l')}
 for p in rig.pose.bones:p.rotation_mode='QUATERNION'
 def grip_solve():
  for side in ('r','l'):
   target_world=pike.matrix_world @ grips[side];target_matrix=rig.matrix_world.inverted() @ target_world;target=target_matrix.translation;a=rig.pose.bones['upperarm_'+side].head.copy()
   l1=(rw['lowerarm_'+side].translation-rw['upperarm_'+side].translation).length;l2=(rw['hand_'+side].translation-rw['lowerarm_'+side].translation).length
   axis=target-a;distance=min(axis.length,l1+l2-.00001);axis.normalize();along=(l1*l1-l2*l2+distance*distance)/(2*distance)
   pole=rw['lowerarm_'+side].translation-a;sideaxis=(pole-axis*pole.dot(axis)).normalized();elbow=a+along*axis+max(0,l1*l1-along*along)**.5*sideaxis
   setbone('upperarm_'+side,rig.matrix_world @ a,rig.matrix_world @ elbow);setbone('lowerarm_'+side,rig.matrix_world @ elbow,target_world.translation);rig.pose.bones['hand_'+side].matrix=target_matrix;bpy.context.view_layer.update()
 def turn(name,axis,angle):
  p=rig.pose.bones[name];m=p.matrix.copy();pos=m.translation.copy();m=Matrix.Rotation(angle,4,axis) @ m;m.translation=pos;p.matrix=m;bpy.context.view_layer.update()
 flexible=[ob for ob in sc.objects if ob.type=='MESH' and any(word in ob.name for word in ('feather','beret','split doublet','wavy hair'))]
 if clip=='death':
  for ob in flexible:ob.shape_key_add(name='Basis')
 samples=[]
 for i in range(count+(1 if loop else 0)):
  frame=i+1;t=i/count if loop else min(i/(count-2),1)
  rig.matrix_world=rigrest;pike.matrix_basis=pikerest
  for p in rig.pose.bones:p.matrix_basis=rest[p.name]
  bpy.context.view_layer.update()
  if motion:
   phase=([0,.23,.50,1][i] if clip=='hit' else t);source=motion.sample(clip,phase)
   hipdelta=source['DEF-hips'].to_quaternion() @ source0['DEF-hips'].to_quaternion().inverted()
   for name,sn in MAP.items():
    if name=='pelvis' or name.startswith(('thigh','calf','foot','ball')):continue
    # Carry arms are constrained to the two-hand pike grip. Captured upper-body
    # rotation remains, while the left elbow is solved to the rigid second grip.
    delta=hipdelta.inverted() @ source[sn].to_quaternion() @ source0[sn].to_quaternion().inverted()
    p=rig.pose.bones[name];position=p.head.copy();_,q,scale=rw[name].decompose();p.matrix=Matrix.LocRotScale(position,delta @ q,scale);bpy.context.view_layer.update()
  if clip=='move':
   # Rest-pose retarget: source A_TPose and MPFB bind matrices cancel bone rolls.
   # Fixed Y-up -> Z-up conversion maps travel to -Y. No foot-yaw edits follow.
   scale=.95;hip0=source0['DEF-hips'].translation;hip=source['DEF-hips'].translation
   rig.pose.bones['pelvis'].location.z+=scale*(hip.z-hip0.z)
   bpy.context.view_layer.update()
   for side,suffix in [('l','.L'),('r','.R')]:
    offset=Vector((.025 if side=='l' else -.025,-.045,.115))
    for name,srcname,nextname in [('thigh','thigh','shin'),('calf','shin','foot'),('foot','foot','toe')]:
     bn=name+'_'+side;sn='DEF-'+srcname+suffix;a=source[sn].translation*scale+offset;b=source['DEF-'+nextname+suffix].translation*scale+offset
     q=source[sn].to_quaternion() @ neutral[sn].to_quaternion().inverted() @ rig.data.bones[bn].matrix_local.to_quaternion()
     length=(rw[bn] @ Vector((0,rig.data.bones[bn].length,0))-rw[bn].translation).length if name=='foot' else (b-a).length
     # Source joint direction aligns the longitudinal axis in the same reference
     # calibration for ALL limb bones, including the foot, before keying.
     direction=(b-a).normalized();q=(q @ Vector((0,1,0))).rotation_difference(direction) @ q
     p=rig.pose.bones[bn];p.matrix=Matrix.LocRotScale(a,q,Vector((1,length/p.bone.length,1)));bpy.context.view_layer.update()
   # Lock the source's sampled stance intervals in the travelling world frame.
   # This corrects mocap/retarget contact drift through leg IK, never foot yaw.
   # The renderer displays an in-place loop, so stationary world contacts move
   # backward by the corresponding virtual root displacement in display space.
   for side,suffix,start,stop in [('l','.L',0,.25),('r','.R',.5,.75)]:
    if start<=t<=stop:
     reference=motion.sample('move',start)['DEF-foot'+suffix].translation*.95+Vector((.025 if side=='l' else -.025,-.045,.115))
     foot=rig.pose.bones['foot_'+side];fm=foot.matrix.copy();ankle=fm.translation.copy();ankle.x=reference.x;ankle.y=reference.y+1.3015*(t-start)
     upper=rig.pose.bones['thigh_'+side];lower=rig.pose.bones['calf_'+side];a=upper.head.copy();pole=lower.head.copy();l1=(upper.tail-upper.head).length;l2=(lower.tail-lower.head).length;axis=ankle-a;distance=min(axis.length,l1+l2-.00001);axis.normalize();along=(l1*l1-l2*l2+distance*distance)/(2*distance);sideaxis=pole-a;sideaxis=(sideaxis-axis*sideaxis.dot(axis)).normalized();knee=a+axis*along+sideaxis*max(0,l1*l1-along*along)**.5
     setbone('thigh_'+side,a,knee);setbone('calf_'+side,knee,ankle);fm.translation=ankle;foot.matrix=fm;bpy.context.view_layer.update()
   # Stance support is a vertical floor constraint only; foot rotation is unchanged.
   lows=[];dg=bpy.context.evaluated_depsgraph_get()
   for ob in sc.objects:
    if 'leather boot' in ob.name:
     ev=ob.evaluated_get(dg);me=ev.to_mesh();lows.extend((ev.matrix_world @ v.co).z for v in me.vertices);ev.to_mesh_clear()
   rig.location.z+=.085-min(lows)
  elif clip=='attack':
   strike=[0,-.18,-.35,.25,1,.8,.5,.18,.03,0][i]
   turn('spine_02','X',.10*strike);turn('upperarm_r','X',-.18*strike)
   pike.rotation_euler.x+=.90*strike;pike.rotation_euler.y-=.30*strike;pike.location.y-=.08*strike;pike.location.z-=.06*max(0,strike)
  elif clip=='death':
   hip=source['DEF-hips'];h0=source0['DEF-hips'];delta=hip.to_quaternion() @ h0.to_quaternion().inverted();pivot=rw['pelvis'].translation;displacement=(hip.translation-h0.translation)*.85
   yaw=-math.pi/2*min(1,t/.55);rig.matrix_world=Matrix.Translation(pivot+displacement) @ Matrix.Rotation(yaw,4,'Z') @ delta.to_matrix().to_4x4() @ Matrix.Translation(-pivot) @ rigrest
   blend=max(0,min(1,(t-.18)/.42))
   for side,suffix in [('l','.L'),('r','.R')]:
    for name,sn in [('upperarm','upper_arm'),('lowerarm','forearm'),('hand','hand'),('thigh','thigh'),('calf','shin'),('foot','foot')]:
     bn=name+'_'+side;src='DEF-'+sn+suffix;p=rig.pose.bones[bn];pos=p.head.copy();_,q,scale=rw[bn].decompose()
     current=delta.inverted() @ source[src].to_quaternion() @ source0[src].to_quaternion().inverted() @ q
     target=delta.inverted() @ source[src].to_quaternion() @ neutral[src].to_quaternion().inverted() @ rig.data.bones[bn].matrix_local.to_quaternion()
     p.matrix=Matrix.LocRotScale(pos,current.slerp(target,blend),scale);bpy.context.view_layer.update()
   bpy.context.view_layer.update()
   if t>.10:
    zs=[];xs=[];ys=[];dg=bpy.context.evaluated_depsgraph_get()
    for ob in sc.objects:
     if ob.type!='MESH' or ob.name=='GEO-stationary cream base' or ob.parent==pike:continue
     ev=ob.evaluated_get(dg);me=ev.to_mesh();points=[ev.matrix_world @ v.co for v in me.vertices];xs.extend(p.x for p in points);ys.extend(p.y for p in points)
     if any(word in ob.name for word in ('breastplate','leather boot','puffed sleeve','hose')):zs.extend(p.z for p in points)
     ev.to_mesh_clear()
    rig.location.z+=.085-min(zs);settle=min(1,t/.55);rig.location.x-=((min(xs)+max(xs))/2)*settle;rig.location.y+=(.08-(min(ys)+max(ys))/2)*settle
   # Settle the captured fall's heels with positional IK. Preserve captured foot
   # orientation; shorten horizontal reach when necessary instead of stretching.
   if t>.45:
    amount=min(1,(t-.45)/.30);amount=amount*amount*(3-2*amount)
    bpy.context.view_layer.update()
    for side in ('r','l'):
     boot=bpy.data.objects['GEO-leather boot '+side]
     ev=boot.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
     low=min((ev.matrix_world @ v.co).z for v in me.vertices);ev.to_mesh_clear()
     foot=rig.pose.bones['foot_'+side];fm=foot.matrix.copy()
     ankle=rig.matrix_world @ foot.head;ankle.z+=(.085-low)*amount
     upper=rig.pose.bones['thigh_'+side];lower=rig.pose.bones['calf_'+side]
     a=rig.matrix_world @ upper.head;pole=rig.matrix_world @ lower.head
     l1=(upper.tail-upper.head).length;l2=(lower.tail-lower.head).length
     horizontal=Vector((ankle.x-a.x,ankle.y-a.y,0))
     maxreach=max(0,(l1+l2-.001)**2-(ankle.z-a.z)**2)**.5
     if horizontal.length>maxreach:
      horizontal.normalize();ankle.x=a.x+horizontal.x*maxreach;ankle.y=a.y+horizontal.y*maxreach
     axis=ankle-a;distance=axis.length;axis.normalize()
     along=(l1*l1-l2*l2+distance*distance)/(2*distance)
     sideaxis=pole-a;sideaxis=(sideaxis-axis*sideaxis.dot(axis)).normalized()
     knee=a+axis*along+sideaxis*max(0,l1*l1-along*along)**.5
     setbone('thigh_'+side,a,knee);setbone('calf_'+side,knee,ankle)
     fm.translation=rig.matrix_world.inverted() @ ankle;foot.matrix=fm
     bpy.context.view_layer.update()
   # Release the rigid pike to the floor; its entire length stays real and visible.
   release=min(1,t/.6);release=release*release*(3-2*release)
   initial=pike.matrix_world.copy();final=Matrix.Rotation(math.pi/2,4,'Y');final.translation=Vector((.34,-.30,.11))
   loc=initial.translation.lerp(final.translation,release);q=initial.to_quaternion().slerp(final.to_quaternion(),release);pike.matrix_world=Matrix.LocRotScale(loc,q,Vector((1,1,1)))
   bpy.context.view_layer.update();zs=[]
   for ob in pike.children:
    if ob.type=='MESH':zs.extend((ob.matrix_world @ v.co).z for v in ob.data.vertices)
   if zs and min(zs)<.09:pike.location.z+=.09-min(zs)
  bpy.context.view_layer.update()
  if clip!='death':grip_solve()
  if clip=='death':
   for ob in flexible:
    key=ob.shape_key_add(name=f'Floor contact {frame}',from_mix=False)
    for vertex in key.data:
     world=ob.matrix_world @ vertex.co
     if world.z<.08:world.z=.08+(world.z-.08)*.025;vertex.co=ob.matrix_world.inverted() @ world
    key.value=0;key.keyframe_insert('value',frame=frame-1);key.value=1;key.keyframe_insert('value',frame=frame);key.value=0;key.keyframe_insert('value',frame=frame+1)
  for p in rig.pose.bones:
   for prop in ('location','rotation_quaternion','scale'):p.keyframe_insert(prop,frame=frame)
  for ob in [rig,pike]:
   for prop in ('location','rotation_euler','scale'):ob.keyframe_insert(prop,frame=frame)
  samples.append({s:list(rig.matrix_world @ rig.pose.bones['foot_'+s].head) for s in ('l','r')})
 for ob in [rig,pike]:
  if not ob.animation_data:continue
  act=ob.animation_data.action;act.name=clip+' • '+ob.name;act.use_fake_user=True
  for layer in act.layers:
   for strip in layer.strips:
    for bag in strip.channelbags:
     for fc in bag.fcurves:
      for key in fc.keyframe_points:key.interpolation='BEZIER';key.handle_left_type=key.handle_right_type='AUTO_CLAMPED'
 sc.frame_set(1);bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(M/'clips'/f'{clip}.blend'))
 (M/'clips'/f'{clip}.json').write_text(json.dumps({'frames':count,'fps':fps,'loop':loop,'source_sha256':hashlib.sha256((M/'reislaufer.blend').read_bytes()).hexdigest(),'feet':samples,'motion':motion.provenance(clip) if motion else {'method':'authored two-handed pike thrust'}}));log('Saved '+clip+' skeletal action, '+str(count)+' samples.')

def audit():
 reports=[];source=hashlib.sha256((M/'reislaufer.blend').read_bytes()).hexdigest()
 bpy.ops.wm.open_mainfile(filepath=str(M/'reislaufer.blend'))
 from refine import audit_surface
 surface=audit_surface()
 master_rig=bpy.data.objects['RIG-Reislaufer MPFB'];lengths={p.name:(p.tail-p.head).length for p in master_rig.pose.bones}
 for clip,(n,fps,loop) in CLIPS.items():
  path=M/'clips'/f'{clip}.blend';meta=json.loads(path.with_suffix('.json').read_text());assert meta['source_sha256']==source
  bpy.ops.wm.open_mainfile(filepath=str(path));sc=bpy.context.scene;rig=bpy.data.objects['RIG-Reislaufer MPFB'];assert len(rig.data.bones)==53
  base=bpy.data.objects['GEO-stationary cream base'];origin=base.matrix_world.copy();counts=[];minz=100;poses=[];feet=[];grips=[];forward=[];heel_contacts=[]
  sc.frame_set(1);bpy.context.view_layer.update();pike=bpy.data.objects['CTRL-pike'];grip=pike.matrix_world.inverted() @ rig.matrix_world @ rig.pose.bones['hand_l'].matrix
  for frame in range(1,n+1):
   sc.frame_set(frame);bpy.context.view_layer.update();assert base.matrix_world==origin
   for bone in rig.pose.bones:
    if bone.name.startswith(('thigh','calf','foot')):assert .85<(bone.tail-bone.head).length/lengths[bone.name]<1.15,(clip,frame,bone.name,'retarget stretch')
   feet.append({side:list((rig.matrix_world @ rig.pose.bones['foot_'+side].matrix).translation) for side in ('l','r')})
   forward.append({side:list(rig.matrix_world.to_3x3() @ (rig.pose.bones['foot_'+side].tail-rig.pose.bones['foot_'+side].head).normalized()) for side in ('l','r')})
   if clip!='death':
    error=((pike.matrix_world @ grip).translation-(rig.matrix_world @ rig.pose.bones['hand_l'].matrix).translation).length;grips.append(error);assert error<.002,(clip,frame,'support hand left pike',error)
   poses.append(tuple(round(v,5) for p in rig.pose.bones for row in p.matrix for v in row)+tuple(round(v,5) for row in rig.matrix_world for v in row))
   for o in sc.objects:
    assert min(abs(v) for v in o.scale)>1e-5,(clip,frame,o.name,'unsafe scale')
    if o.type=='MESH' and not o.hide_render:
     ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());minz=min(minz,min((ev.matrix_world @ Vector(c)).z for c in ev.bound_box))

   if clip=='death' and frame>=n-1:
    for side in ('r','l'):
     boot=bpy.data.objects['GEO-leather boot '+side];ev=boot.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
     low=min((ev.matrix_world @ v.co).z for v in me.vertices);ev.to_mesh_clear()
     heel_contacts.append(low);assert abs(low-.085)<.003,(clip,frame,side,'heel missed support',low)
  assert len(set(poses))>1,(clip,'rig does not animate')
  if clip=='death':assert poses[-1]==poses[-2],'Death skeletal pose is not held'
  gait=None
  if clip=='move':
   # Walk_Loop is in-place. Restore constant -Y root travel to measure planted
   # ankle drift; the static display pedestal is not the walking world frame.
   stride=1.37*.95;drifts=[];angles=[]
   for side,indices in [('l',[0,1,2]),('r',[4,5,6])]:
    points=[Vector((feet[j][side][0],feet[j][side][1]-stride*j/8,0)) for j in indices]
    drifts.extend((p-points[0]).length for p in points)
    for j in indices:
     v=Vector((forward[j][side][0],forward[j][side][1],0)).normalized();angles.append(math.degrees(math.acos(max(-1,min(1,v.dot(Vector((0,-1,0))))))))
   gait={'forward':'-Y','virtual_stride_m':stride,'support_ankle_planar_drift_m':max(drifts),'support_foot_yaw_degrees':max(angles),'scope':'sampled contact windows, not a continuous collision solver'}
   assert max(drifts)<.025,('support ankle sliding',gait)
   assert max(angles)<8,('feet not aligned to travel',gait)
  reports.append({'terminal_heel_heights_m':heel_contacts,'gait':gait,'feet':feet,'maximum_grip_error':max(grips,default=0),'motion':meta.get('motion'),'distinct_skeletal_poses':len(set(poses)),'clip':clip,'frames':n,'bones':len(rig.data.bones),'stationary_base':True,'minimum_bbox_z':minz})
 (V/'reislaufer-audit.json').write_text(json.dumps({'surface':surface,'checks':reports,'limits':'Bounds and rig checks do not establish hand contacts, cloth collision freedom or visual approval.'},indent=2));log('Audit passed: five clips, source hashes, 53-bone rig, fixed base and positive object scales.')

mode=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'build'
if mode=='preflight':
 configure();print('GPU preflight passed',flush=True)
elif mode=='build':
 build();render('b-plain',M/'plain.blend',[1]);bpy.ops.wm.open_mainfile(filepath=str(M/'plain.blend'));configure();from bake import bake;bake();project();render('c-textured-lit',M/'reislaufer.blend',[1])
elif mode=='rest':
 render('b-plain',M/'plain.blend',[1]);render('c-textured-lit',M/'reislaufer.blend',[1])
elif mode.startswith('animate-'):animate(mode[8:])
elif mode.startswith('e-'):render(mode,M/'clips'/(mode[2:]+'.blend'),list(range(1,CLIPS[mode[2:]][0]+1)))
elif mode=='audit':audit()
elif mode=='feet':
 for view in ('top','front'):render('g-feet-'+view,M/'clips/move.blend',list(range(1,9)))
elif mode=='animate':
 for clip in CLIPS:animate(clip)
elif mode in ('preview','render'):
 if mode=='render':
  render('b-plain',M/'plain.blend',[1]);render('c-textured-lit',M/'reislaufer.blend',[1])
 render('d-rig-poses',M/'clips/attack.blend',[1,3,5,7])
 for clip,(n,_,_) in CLIPS.items():render('e-'+clip,M/'clips'/f'{clip}.blend',list(range(1,n+1)))
 for view in ('top','front'):render('g-feet-'+view,M/'clips/move.blend',list(range(1,9)))
else:raise ValueError(mode)
