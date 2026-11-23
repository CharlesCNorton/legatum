"""Arquebusier: MPFB anatomy, tailored 3D kit, frozen camera UVs and five actions."""
import bpy, math, os, sys, json, hashlib, subprocess
from pathlib import Path
from mathutils import Vector, Matrix
from math import sin, cos, pi
from bpy_extras.object_utils import world_to_camera_view
R=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'))
M=R/'masters/arquebusier'; A=R/'assets/arquebusier'; V=R/'review/3d-v2'
for p in (M,V,M/'clips',M/'renders'):p.mkdir(parents=True,exist_ok=True)
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from retarget import prepare as retarget_motion, apply_matrices
CLIPS={'idle':(8,10,True),'move':(8,12,True),'attack':(10,14,False),'hit':(4,12,False),'death':(10,10,False)}
def log(s):
 with (V/'arquebusier-log.md').open('a') as f:f.write('- '+s+'\n')
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
 # Preserve the saved painted-pigment display calibration.
 return sc

def build():
 global rig,body,linen,red,leather,steel,brass
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
 bpy.ops.preferences.addon_enable(module='bl_ext.user_default.mpfb')
 from bl_ext.user_default.mpfb.services.humanservice import HumanService
 from bl_ext.user_default.mpfb.services.targetservice import TargetService
 macro=TargetService.get_default_macro_info_dict();macro.update(gender=1.,age=.48,muscle=.6,weight=.55,height=.48,proportions=.6);macro['race']={'caucasian':1.,'african':0.,'asian':0.}
 body=HumanService.create_human(macro_detail_dict=macro);body.name='GEO-MPFB arquebusier anatomy'
 bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();lo=min(v.co.z for v in me.vertices);hi=max(v.co.z for v in me.vertices);ev.to_mesh_clear();body.scale=(1.72/(hi-lo),)*3
 bpy.context.view_layer.objects.active=body;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 rig=HumanService.add_builtin_rig(body,'game_engine');rig.name='RIG-Arquebusier MPFB';rig.location.z=.09
 system=R/'blender-user/extensions/.user/user_default/mpfb/data'
 eyes=HumanService.add_mhclo_asset(str(system/'eyes/high-poly/high-poly.mhclo'),body,asset_type='Eyes',subdiv_levels=1,material_type='MAKESKIN');eyes.name='GEO-MPFB eyes'
 skin=mat('warm painted skin',(.5,.29,.14),fill='skin');red=mat('vermilion wool',(.4,.025,.014),fill='red');linen=mat('warm cream linen',(.78,.64,.4),fill='linen');leather=mat('worn leather',(.22,.09,.025),fill='leather');steel=mat('worn bright steel',(.55,.59,.62),1,.36);brass=mat('polished brass',(.71,.4,.09),1,.3);wood=mat('walnut gunstock',(.22,.09,.027));dark=mat('gun bore and facial hair',(.055,.025,.009));stone=mat('cream limestone E9CFA0',(.95,.70,.32),0,.88)
 body.data.materials.clear();body.data.materials.append(skin)
 for p in body.data.polygons:p.use_smooth=True
 sub=body.modifiers.new('Anatomical smoothing','SUBSURF');sub.levels=sub.render_levels=1
 # Rest pose: gun on viewer left, other hand at belt, braced feet.
 limb('thigh_r','calf_r',(-.18,-.025,.085),(-.22,-.4,.5));limb('thigh_l','calf_l',(.21,.015,.085),(.22,-.4,.5))
 limb('upperarm_r','lowerarm_r',(-.30,-.22,1.35),(-.50,-.04,1.13));limb('upperarm_l','lowerarm_l',(.23,-.27,1.05),(.46,-.03,1.20))
 aim('hand_r',(0,0,.10));aim('hand_l',(-.035,-.025,-.09))
 for side in ('r','l'):
  for digit in ('index','middle','ring','pinky'):
   for k in range(1,4):p=rig.pose.bones[f'{digit}_{k:02d}_{side}'];p.rotation_mode='XYZ';p.rotation_euler.x=.85 if side=='r' else .35
 p=rig.pose.bones['head'];p.rotation_mode='XYZ';p.rotation_euler.y=-.30;bpy.context.view_layer.update();hm=p.matrix.copy();hm.translation.z+=.09;p.matrix=hm;bpy.context.view_layer.update()
 # Doublet with actual longitudinal folds and a thick hem.
 vs=[];fs=[]
 for j in range(25):
  t=j/24;z=1.04+.48*t;rx=.17+.073*sin(pi*t*.8);ry=.125+.026*sin(pi*t)
  for k in range(64):a=2*pi*k/64;fold=.009*cos(a*12)*sin(pi*t);vs.append(((rx+fold)*sin(a),-(ry+fold)*cos(a),z+.09))
 for j in range(24):
  for k in range(64):i=j*64+k;n=j*64+(k+1)%64;fs.append((i,n,n+64,i+64))
 coat=solid(mesh('slashed doublet',vs,fs,red),.008);coat.data.materials.append(linen)
 for p in coat.data.polygons:p.material_index=1 if (p.index%64)//4%2 else 0
 attach(coat,'spine_03')
 # Tailored sleeves follow posed anatomical joints; no primitive body replacement.
 for side in ('r','l'):
  for upper in ('upperarm','lowerarm'):
   p=rig.pose.bones[upper+'_'+side];a=rig.matrix_world @ p.head;b=rig.matrix_world @ p.tail
   tube('slashed '+upper+' '+side,a,b,(.072,.065,.037 if upper=='upperarm' else .018),red,upper+'_'+side,True)
  p=rig.pose.bones['lowerarm_'+side];end=rig.matrix_world @ p.tail
  tube('gathered ivory cuff '+side,end+(rig.matrix_world @ p.head-end)*.13,end,(.073,.067,.008),linen,'lowerarm_'+side)
  p=rig.pose.bones['thigh_'+side];a=rig.matrix_world @ p.head;b=rig.matrix_world @ p.tail
  tube('puffed slashed breeches '+side,a,b*.9+a*.1,(.115,.082,.075),red,'thigh_'+side,True)
  p=rig.pose.bones['calf_'+side];a=rig.matrix_world @ p.head;b=rig.matrix_world @ p.tail
  tube('ivory stocking '+side,a,b,(.075,.04,.012),linen,'calf_'+side)
  tube('red knee garter '+side,a,a+(b-a)*.17,(.083,.077,.005),red,'calf_'+side)
  # Shoes are closed lofts over real anatomical feet, broad rounded toes.
  fp=rig.matrix_world @ rig.pose.bones['foot_'+side].head
  shoe=sphere('latchet shoe '+side,(fp.x,fp.y-.075,.145),(.074,.145,.065),leather);attach(shoe,'foot_'+side)
  for z in range(3):
   yy=fp.y-.14+.052*z;pts=[(fp.x+.068*cos(a),yy,.148+.056*sin(a)) for a in [pi*i/20 for i in range(21)]];attach(curve('shoe welt strap '+side,pts,.009,leather),'foot_'+side)
 # Belt, diagonal baldric, buckles and twelve individually modeled powder charges.
 for z in (1.115,1.145):attach(curve('belt piping',[(.185*sin(a),-.145*cos(a),z) for a in [2*pi*i/96 for i in range(97)]],.012,leather),'spine_01')
 strapvs=[(-.16,-.151,1.56),(-.116,-.162,1.56),(.16,-.174,1.16),(.12,-.176,1.15)]
 attach(bevel(solid(mesh('thick diagonal baldric',strapvs,[(0,1,2,3)],leather),.012),.003),'spine_03')
 attach(curve('baldric gold buckle',[(-.015,-.187,1.36),(.02,-.188,1.38),(.046,-.186,1.34),(.011,-.188,1.32),(-.015,-.187,1.36)],.004,brass),'spine_03')
 for i in range(10):
  a=-1.18+i*2.36/9;start=Vector((.223*sin(a),-.175*cos(a),1.13));end=start+Vector((.045*sin(a),-.035*cos(a),-.17))
  attach(curve('powder charge wooden flask %02d'%i,[start,end],.022,wood),'pelvis')
  for t in (.04,.16,.85):attach(curve('powder brass collar', [start.lerp(end,t),start.lerp(end,t+.08)],.025,brass),'pelvis')
 for i in range(7):attach(sphere('doublet brass button',(.015,-.164,1.21+i*.042),(.008,.005,.008),brass),'spine_03')
 # Ruffled linen collar with alternating shallow pleats.
 for i in range(40):
  a=2*pi*i/40;attach(sphere('ruff pleat',(.084*sin(a),-.078*cos(a),1.65+.006*(i%2)),(.012,.016,.025),linen),'neck_01')
 # Morion: bowl, swept boat brim and real high comb ridge, fitted to head.
 head=rig.pose.bones['head'];hc=rig.matrix_world @ ((head.head+head.tail)*.5);cx,cy,cz=hc
 vs=[];fs=[]
 for j in range(17):
  t=(j/16)*pi/2
  for k in range(64):a=2*pi*k/64;vs.append((cx+.119*cos(t)*sin(a),cy-.132*cos(t)*cos(a),cz+.025+.145*sin(t)))
 for j in range(16):
  for k in range(64):i=j*64+k;n=j*64+(k+1)%64;fs.append((i,n,n+64,i+64))
 attach(bevel(solid(mesh('morion steel bowl',vs,fs,steel),.006),.002),'head')
 vs=[];fs=[]
 for j in range(5):
  t=j/4
  for k in range(96):
   a=2*pi*k/96;vs.append((cx+(.116+.045*t)*sin(a),cy-(.13+.068*t)*cos(a),cz+.015+.075*t*abs(cos(a))**5-.018*t*abs(sin(a))))
 for j in range(4):
  for k in range(96):i=j*96+k;n=j*96+(k+1)%96;fs.append((i,n,n+96,i+96))
 attach(bevel(solid(mesh('morion swept brim',vs,fs,steel),.006),.002),'head');attach(curve('morion rolled brass lip',vs[-96:]+[vs[-96]],.0035,brass),'head')
 vs=[];fs=[]
 for i in range(33):
  a=-1.4+2.8*i/32;y=cy+.16*sin(a);z=cz+.025+.145*cos(a)
  vs.extend([(cx-.009,y,z),(cx-.009,y,z+.045*cos(a)),(cx+.009,y,z+.045*cos(a)),(cx+.009,y,z)])
 for i in range(32):
  for k in range(4):fs.append((4*i+k,4*i+(k+1)%4,4*(i+1)+(k+1)%4,4*(i+1)+k))
 attach(bevel(mesh('morion raised comb',vs,fs,steel),.004),'head')
 attach(curve('comb bright edge',[(cx,cy+.16*sin(a),cz+.025+.19*cos(a)) for a in [-1.4+i*2.8/40 for i in range(41)]],.003,brass),'head')
 for i in range(9):
  a=-1.3+i*2.6/8;attach(sphere('morion brass rivet',(cx+.12*sin(a),cy-.134*cos(a),cz+.04),(.005,.004,.005),brass),'head')
 # Turn the complete morion to expose its broad comb, matching the painting.
 pivot=Vector((cx,cy,cz))
 for o in list(bpy.context.scene.objects):
  if 'morion' in o.name or 'comb bright' in o.name:o.matrix_world=Matrix.Translation(pivot) @ Matrix.Rotation(-.65,4,'Z') @ Matrix.Translation(-pivot) @ o.matrix_world
 # Facial hair follows anatomical face rather than being painted on an empty sphere.
 attach(curve('trimmed moustache',[(cx-.045,cy-.094,cz-.075),(cx-.02,cy-.108,cz-.068),(cx,cy-.113,cz-.074),(cx+.024,cy-.109,cz-.069),(cx+.049,cy-.097,cz-.076)],.008,dark),'head')
 attach(sphere('short pointed beard',(cx,cy-.073,cz-.116),(.043,.024,.031),dark),'head')
 # Matchlock control: upright rest orientation, stock/lock/barrel rigidly assembled.
 gun=empty('CTRL-matchlock',(-.30,-.25,1.42));attach(gun,'hand_r')
 pts=[(-.33,-.25,.17),(-.285,-.25,.185),(-.29,-.25,.48),(-.31,-.25,.75),(-.31,-.25,1.60)]
 stockvs=[]
 for y in (-.278,-.222):
  for x,z in [(-.39,.16),(-.29,.19),(-.315,.51),(-.28,.76),(-.285,1.60),(-.325,1.60),(-.34,.69),(-.35,.44)]:stockvs.append((x,y,z))
 fs=[tuple(range(7,-1,-1)),tuple(range(8,16))]+[(i,(i+1)%8,(i+1)%8+8,i+8) for i in range(8)]
 parent(bevel(mesh('walnut matchlock butt and fore-end',stockvs,fs,wood),.009),gun)
 parent(curve('long steel octagonal barrel',[(-.305,-.28,.76),(-.305,-.28,1.81)],.017,steel),gun)
 for z in (.82,1.20,1.49,1.79):parent(curve('barrel brass band',[(-.305,-.28,z),(-.305,-.28,z+.025)],.020,brass),gun)
 parent(curve('muzzle dark bore',[(-.305,-.28,1.808),(-.305,-.28,1.815)],.011,dark),gun)
 parent(curve('ramrod',[(-.335,-.28,.71),(-.335,-.28,1.67)],.005,wood),gun)
 parent(curve('serpentine matchlock',[(-.30,-.302,.80),(-.355,-.308,.84),(-.34,-.31,.90),(-.31,-.307,.92)],.007,steel),gun)
 parent(curve('trigger guard',[(-.31,-.31,.80),(-.365,-.31,.77),(-.36,-.31,.70),(-.315,-.31,.72)],.006,steel),gun)
 parent(curve('slow match cord',[(-.34,-.32,.9),(-.36,-.33,.94),(-.38,-.33,.93)],.003,linen),gun)
 # Effects use visibility keys, always have non-zero real dimensions.
 flash=sphere('muzzle flash',(-.305,-.28,1.84),(.035,.035,.08),mat('flame',(.9,.3,.03)));parent(flash,gun);flash.hide_render=True
 smoke=sphere('muzzle smoke',(-.305,-.28,1.9),(.065,.065,.1),mat('pale smoke',(.5,.48,.43)));parent(smoke,gun);smoke.hide_render=True
 bpy.ops.mesh.primitive_cylinder_add(vertices=96,radius=.51,depth=.075,location=(0,0,.0475));base=bpy.context.object;base.name='GEO-stationary cream base';base.data.materials.append(stone);bevel(base,.012)
 sc=configure();sc.world.use_nodes=True;sc.world.node_tree.nodes.get('Background').inputs[0].default_value=(.65,.70,.8,1);sc.world.node_tree.nodes.get('Background').inputs[1].default_value=.25
 bpy.ops.object.camera_add(location=(.3,-8,3.15));cam=bpy.context.object;cam.name='CAM-painting';cam.rotation_euler=(Vector((0,0,.94))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=2.13;sc.camera=cam
 for name,loc,power,size,color in [('key',(-3,-4,5),450,2.2,(1,.88,.72)),('fill',(3,-3,3),120,3.,(.83,.9,1)),('rim',(1,2,4),240,2.,(.72,.83,1))]:
  bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name='LGT-'+name;o.data.energy=power;o.data.size=size;o.data.color=color;o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
 rig.scale=(.95,.95,.95)
 sc['unit']='arquebusier';sc['anatomy']='MPFB 2.0.18 CC0';sc['reference']='CC BY 4.0 arquebusier-source.png'
 bpy.context.view_layer.update();rig['rest_pose']=json.dumps({p.name:[list(r) for r in p.matrix_basis] for p in rig.pose.bones});rig['rest_location']=list(rig.location);gun['rest_world']=[v for row in gun.matrix_world for v in row]
 bpy.ops.wm.save_as_mainfile(filepath=str(M/'plain.blend'));log('Built MPFB anatomical body, 53-bone rig and original arquebusier kit; plain.blend saved.')


def project():
 """Freeze finished-surface UVs; camera-only pigment avoids double illumination."""
 sc=bpy.context.scene;cam=sc.camera;im=bpy.data.images.load(str(A/'projection.png'),check_existing=True);records=[]
 for o in list(sc.objects):
  if o.type!='MESH' or o.get('skip_painting_projection') or any(x in o.name for x in ('base','muzzle','eyes')):continue
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
   mix=n.new('ShaderNodeMixShader');l.new(strength.outputs[0],mix.inputs[0]);l.new((n.get('Hidden fill surface') or p).outputs[0],mix.inputs[1]);l.new(pigment.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],out.inputs['Surface'])
  records.append(o.name)
 bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(M/'arquebusier.blend'));(M/'projection.json').write_text(json.dumps({'objects':records,'method':'finished rest-camera UV, ray visibility/facing/source-alpha, camera-only painted illumination','weight':.98,'hidden_surfaces':'original generated painted fills'},indent=2));log('Finished-surface camera projection with camera-only pigment; generated hidden fills retained.')


def animate(clip):
 global rig
 bpy.ops.wm.open_mainfile(filepath=str(M/'arquebusier.blend'));rig=bpy.data.objects['RIG-Arquebusier MPFB'];gun=bpy.data.objects['CTRL-matchlock'];sc=configure();count,fps,loop=CLIPS[clip];sc.render.fps=fps;sc.frame_start=1;sc.frame_end=count
 rest={n:Matrix(m) for n,m in json.loads(rig['rest_pose']).items()}
 for p in rig.pose.bones:p.rotation_mode='QUATERNION';p.matrix_basis=rest[p.name].copy()
 bpy.context.view_layer.update()
 loc=Vector(rig['rest_location']);gw=gun.matrix_world.copy();gb=gun.matrix_basis.copy()
 if clip in ('attack','death'):gun.parent=None;gun.matrix_world=gw
 right_wrist=rig.matrix_world @ rig.pose.bones['hand_r'].head
 left_wrist=rig.matrix_world @ rig.pose.bones['hand_l'].head
 right_hand=rig.pose.bones['hand_r'].matrix.copy();left_hand=rig.pose.bones['hand_l'].matrix.copy()
 stock=bpy.data.objects['GEO-walnut matchlock butt and fore-end'];points=[stock.matrix_world @ v.co for v in stock.data.vertices];zmin=min(v.z for v in points);bottom=[v for v in points if v.z<zmin+.04];butt=sum(bottom,Vector())/len(bottom)
 # Weapon rests against the right palm. During aim both arms solve toward the weapon.
 frames=count+1 if loop else count
 motion=None
 if clip!='attack':
  phases=[i/count if loop else min(1,i/(count-2)) if clip=='death' else i/(count-1) for i in range(frames)]
  motion,motion_meta=retarget_motion(rig,R,clip,phases)
  if loop:motion[-1]=motion[0]
  (M/'clips'/f'{clip}-motion.json').write_text(json.dumps(motion_meta,indent=2))
  sc.render.fps=fps
 for idx in range(frames):
  sc.frame_set(idx+1)
  for p in rig.pose.bones:p.matrix_basis=rest[p.name].copy()
  rig.location=loc.copy();rig.rotation_euler=(0,0,0);gun.matrix_basis=gb.copy() if clip not in ('attack','death') else gw.copy();bpy.context.view_layer.update();t=idx/count if loop else idx/(count-1)
  if motion:
   sample=motion[idx];apply_matrices(rig,sample['matrices'])
   weight=min(1,idx/3) if clip=='death' else (0 if idx in (0,count-1) else 1) if clip=='hit' else 1
   if weight<1:
    for p in rig.pose.bones:p.matrix_basis=rest[p.name].lerp(p.matrix_basis,weight)
   rig.location=loc+sample['root']*weight
   bpy.context.view_layer.update()
  if clip=='move':
   # Ground the finished soles, not anatomical ankle heads; keep source foot rotations.
   lows=[];deps=bpy.context.evaluated_depsgraph_get()
   for side in ('l','r'):
    for name in ('GEO-latchet shoe '+side,'GEO-shoe leather sole '+side):
     shoe=bpy.data.objects[name];ev=shoe.evaluated_get(deps);me=ev.to_mesh();lows.append(min((ev.matrix_world @ v.co).z for v in me.vertices));ev.to_mesh_clear()
   base=bpy.data.objects['GEO-stationary cream base'];top=max((base.matrix_world @ Vector(c)).z for c in base.bound_box)
   rig.location.z+=top+.002-min(lows);bpy.context.view_layer.update()
  if clip=='attack':
   # Weapon is a rigid body; hands solve to its trigger and fore-end.
   amount=[0,.28,.72,1,1,1,.92,.65,.27,0][idx]
   direction=Vector((.72,-.69,.05)).normalized()
   q=Vector((0,0,1)).rotation_difference(direction)
   from mathutils import Quaternion
   rot=Quaternion().slerp(q,amount).to_matrix().to_4x4()
   target_butt=butt.lerp(Vector((-.32,-.05,1.42)),amount)
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
  elif clip=='death':
   u=min(1,t/.78)
   # Reorient the captured backward fall onto the disc, retaining source articulation.
   turn=Matrix.Rotation(.65*min(1,idx/4),4,'Z')
   rig.rotation_euler=turn.to_euler();rig.location=loc+turn.to_3x3() @ (rig.location-loc)
   bpy.context.view_layer.update()
   # Covered anatomy is masked, so center the complete visible costume, not
   # the remaining torso alone (which would push the feet outside the cell).
   coords=[];deps=bpy.context.evaluated_depsgraph_get()
   for obj in sc.objects:
    if obj.type!='MESH' or 'base' in obj.name or 'muzzle' in obj.name or obj.parent==gun:continue
    ev=obj.evaluated_get(deps);me=ev.to_mesh();coords.extend(ev.matrix_world @ v.co for v in me.vertices);ev.to_mesh_clear()
   center=Vector(((min(v.x for v in coords)+max(v.x for v in coords))/2,(min(v.y for v in coords)+max(v.y for v in coords))/2,0))
   settle=max(0,min(1,(idx-2)/2));settle=settle*settle*(3-2*settle)
   base=bpy.data.objects['GEO-stationary cream base'];rig.location+=(Vector((base.location.x,base.location.y,0))-center)*settle
   fall=max(0,min(1,(u-.15)/.85));pivot=Vector((-.305,-.25,.17));gun.matrix_world=Matrix.Translation((-.48*fall,0,.01*fall)) @ Matrix.Translation(pivot) @ Matrix.Rotation(1.57*fall,4,'Y') @ Matrix.Translation(-pivot) @ gw
   for digit in ('index','middle','ring','pinky'):
    for k in range(1,4):
     finger=rig.pose.bones[f'{digit}_{k:02d}_r'];finger.matrix_basis=rest[finger.name].lerp(Matrix.Identity(4),fall)
  bpy.context.view_layer.update()
  if clip=='death' and t>0:
   # Settle the evaluated figure on the actual offset disc/world ground.
   base=bpy.data.objects['GEO-stationary cream base'];invbase=base.matrix_world.inverted();top=max((base.matrix_world @ Vector(c)).z for c in base.bound_box);ground=min((base.matrix_world @ Vector(c)).z for c in base.bound_box);deps=bpy.context.evaluated_depsgraph_get();lift=-10
   for obj in sc.objects:
    if obj.type!='MESH' or obj==base or 'muzzle' in obj.name or obj.parent==gun:continue
    ev=obj.evaluated_get(deps);me=ev.to_mesh()
    for v in me.vertices:
     w=ev.matrix_world @ v.co;local=invbase @ w;floor=top if local.x**2+local.y**2<.48**2 else ground
     lift=max(lift,floor-w.z)
    ev.to_mesh_clear()
   rig.location.z+=lift*min(1,t/.5)
   bpy.context.view_layer.update()
   # The released rigid gun settles against the same actual raised disc/ground.
   if t>.25:
    lift=-10
    for obj in sc.objects:
     if obj.type!='MESH' or obj.parent!=gun or 'muzzle' in obj.name:continue
     for v in obj.data.vertices:
      w=obj.matrix_world @ v.co;local=invbase @ w;floor=top if local.x**2+local.y**2<.48**2 else ground
      lift=max(lift,floor-w.z)
    gun.location.z+=lift*min(1,(t-.25)/.35)
    bpy.context.view_layer.update()

  for p in rig.pose.bones:
   p.keyframe_insert('location',frame=idx+1)
   p.keyframe_insert('rotation_quaternion' if p.rotation_mode=='QUATERNION' else 'rotation_euler',frame=idx+1);p.keyframe_insert('scale',frame=idx+1)
  rig.keyframe_insert('location',frame=idx+1);rig.keyframe_insert('rotation_euler',frame=idx+1)
  gun.keyframe_insert('location',frame=idx+1);gun.keyframe_insert('rotation_euler' if gun.rotation_mode!='QUATERNION' else 'rotation_quaternion',frame=idx+1)
  for name in ('GEO-muzzle flash','GEO-muzzle smoke'):
   o=bpy.data.objects[name];o.hide_render=not(clip=='attack' and idx==(4 if 'flash' in name else 5));o.keyframe_insert('hide_render',frame=idx+1)
 # Keep every action editable, with proper loop endpoint and no sampled duplicate endpoint.
 if rig.animation_data:rig.animation_data.action.name='Arquebusier '+clip
 sc.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(M/'clips'/f'{clip}.blend'))
 (M/'clips'/f'{clip}.json').write_text(json.dumps({'frames':count,'fps':fps,'loop':loop,'source_sha256':hashlib.sha256((M/'arquebusier.blend').read_bytes()).hexdigest()}));log(('Retargeted CC0 and saved ' if motion else 'Authored and saved ')+clip+' action ('+str(count)+' output frames).')


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

mode=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'build'
if mode=='build':
 build();render('b-plain',M/'plain.blend',[1]);bpy.ops.wm.open_mainfile(filepath=str(M/'plain.blend'));project();render('c-textured-lit',M/'arquebusier.blend',[1])
elif mode=='project':
 bpy.ops.wm.open_mainfile(filepath=str(M/'plain.blend'));project()
elif mode=='b':
 render('b-plain',M/'plain.blend',[1])
elif mode=='c':
 render('c-textured-lit',M/'arquebusier.blend',[1])
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
 for stage,blend,frames in [('b-plain',M/'plain.blend',[1]),('c-textured-lit',M/'arquebusier.blend',[1]),('d-rig-poses',M/'clips/attack.blend',[1,3,5,7])]:render(stage,blend,frames)
 for clip,(n,_,_) in CLIPS.items():render('e-'+clip,M/'clips'/f'{clip}.blend',list(range(1,n+1)))
else:raise ValueError(mode)
