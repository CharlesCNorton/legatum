"""Scout: MPFB anatomy and rig, original fitted clothing and equipment. Blender 5.x."""
import bpy,os,sys,json,math,random
from pathlib import Path
from mathutils import Vector,Matrix
from math import sin,cos,pi
R=Path(os.environ['ANIM_ROOT']); M=R/'masters/scout'; A=R/'assets/scout'
random.seed(107)
def mesh(name,vs,fs,mat):
 d=bpy.data.meshes.new(name);d.from_pydata(vs,[],fs);d.update();o=bpy.data.objects.new('GEO-'+name,d);bpy.context.collection.objects.link(o)
 d.materials.append(mat)
 for p in d.polygons:p.use_smooth=True
 return o
def solid(o,t=.006):
 m=o.modifiers.new('Real fabric thickness','SOLIDIFY');m.thickness=t;return o
def bevel(o,w=.005):
 m=o.modifiers.new('Rounded worn edges','BEVEL');m.width=w;m.segments=3;return o
def curve(name,pts,r,mat):
 d=bpy.data.curves.new(name,'CURVE');d.dimensions='3D';s=d.splines.new('POLY');s.points.add(len(pts)-1)
 for p,v in zip(s.points,pts):p.co=(*v,1)
 d.bevel_depth=r;d.bevel_resolution=2;o=bpy.data.objects.new('GEO-'+name,d);bpy.context.collection.objects.link(o);d.materials.append(mat);return o
def attach(o,bone):
 bpy.context.view_layer.update();world=o.matrix_world.copy();o.parent=rig;o.parent_type='BONE';o.parent_bone=bone;bpy.context.view_layer.update();o.matrix_world=world;return o
def sphere(name,loc,scale,mat):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,location=loc);o=bpy.context.object;o.name='GEO-'+name;o.scale=scale;o.data.materials.append(mat)
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 for p in o.data.polygons:p.use_smooth=True
 return o
def material(name,c,rough=.8,metal=0,fill=None):
 m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*c,1);n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
 noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=180;noise.inputs['Detail'].default_value=3
 bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.22;bump.inputs['Distance'].default_value=.0015;l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs['Normal'],p.inputs['Normal'])
 if fill:
  t=n.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(A/(fill+'.png')));t.projection='BOX';t.projection_blend=.3;tc=n.new('ShaderNodeTexCoord');l.new(tc.outputs['Generated'],t.inputs['Vector'])
  mix=n.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=.3;mix.inputs[1].default_value=(*c,1);l.new(t.outputs['Color'],mix.inputs[2]);l.new(mix.outputs[0],p.inputs['Base Color'])
 if fill in ['linen','wool']:p.inputs['Sheen Weight'].default_value=.25
 return m
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.preferences.addon_enable(module='bl_ext.user_default.mpfb')
from bl_ext.user_default.mpfb.services.humanservice import HumanService
from bl_ext.user_default.mpfb.services.targetservice import TargetService
macro=TargetService.get_default_macro_info_dict();macro.update(gender=1.,age=.52,muscle=.72,weight=.48,height=.48,proportions=.65);macro['race']={'caucasian':.8,'african':.1,'asian':.1}
body=HumanService.create_human(macro_detail_dict=macro);body.name='GEO-Scout MPFB anatomy'
bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();zs=[v.co.z for v in me.vertices];ev.to_mesh_clear();s=1.72/(max(zs)-min(zs));body.scale=(s,s,s)
bpy.context.view_layer.objects.active=body;body.select_set(True);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
rig=HumanService.add_builtin_rig(body,'game_engine');rig.name='Scout MPFB game_engine';rig.location.z=.105
system=R/'blender-user/extensions/.user/user_default/mpfb/data'
eyes=HumanService.add_mhclo_asset(str(system/'eyes/high-poly/high-poly.mhclo'),body,asset_type='Eyes',subdiv_levels=1,material_type='MAKESKIN');eyes.name='GEO-Scout eyes'
skin=material('Painted tan skin',(.52,.27,.13),.65,fill='skin');body.data.materials.clear();body.data.materials.append(skin)
sub=body.modifiers.new('Anatomical subdivision','SUBSURF');sub.levels=sub.render_levels=1
linen=material('Ochre woven linen',(.61,.36,.12),.87,fill='linen');wool=material('Olive travelling cloak',(.16,.155,.10),.92,fill='wool');leather=material('Scuffed brown leather',(.15,.064,.028),.7,fill='leather');edge=material('Worn leather edges',(.32,.16,.067));thread=material('Linen stitches',(.54,.35,.17));hair=material('Salt and pepper curls',(.047,.036,.026));grey=material('Grey beard tips',(.20,.17,.135));wood=material('Weathered staff',(.22,.115,.047));brass=material('Worn brass fasteners',(.48,.29,.095),.35,1);stone=material('Cream stone target E9CFA0',(.86,.65,.37),.88)
# Tunic: circumferential folds, cinched waist, flared hem; real shell, not body primitives.
vs=[];fs=[];N=72;J=32
for j in range(J+1):
 t=j/J;z=.72+.70*t
 if z<1.08:rx=.28-.10*(z-.72)/.36;ry=.19-.065*(z-.72)/.36
 else:rx=.18+.045*sin((z-1.08)/.39*pi*.7);ry=.125+.025*sin((z-1.08)/.39*pi)
 if z>1.32:
  f=(z-1.32)/.10;rx=rx*(1-f)+.085*f;ry=ry*(1-f)+.075*f
 for i in range(N):
  a=2*pi*i/N;fold=(.006+.006*(1-t))*sin(a*14+sin(t*8)*.35);vs.append(((rx+fold)*sin(a),-(ry+fold)*cos(a),z+.012*sin(a*5)*(1-t)))
for j in range(J):
 for i in range(N):a=j*N+i;b=j*N+(i+1)%N;fs.append((a,b,b+N,a+N))
tunic=solid(mesh('Folded short tunic',vs,fs,linen));tunic.parent=rig
# Weights tie skirt to thighs and bodice to spine; preserve tailored folds.
for name in ['pelvis','spine_01','spine_03','thigh_l','thigh_r']:tunic.vertex_groups.new(name=name)
for i,v in enumerate(vs):
 z=v[2]
 if z<1.02:
  w=max(0,(1.02-z)/.30)*.65;side='thigh_l' if v[0]>0 else 'thigh_r';tunic.vertex_groups[side].add([i],w,'REPLACE');tunic.vertex_groups['pelvis'].add([i],1-w,'REPLACE')
 else:tunic.vertex_groups['spine_03' if z>1.23 else 'spine_01'].add([i],1,'REPLACE')
ar=tunic.modifiers.new('Skinned tailored tunic','ARMATURE');ar.object=rig
# Sleeves follow each upper arm with a scalloped cuff.
for side in ['l','r']:
 b=rig.pose.bones['upperarm_'+side];p0=b.head+rig.location;p1=p0+(b.tail-b.head)*.52;axis=(p1-p0).normalized();u=Vector((0,1,0));v=axis.cross(u).normalized();vs=[];fs=[]
 for j in range(9):
  t=j/8;c=p0.lerp(p1,t);r=.082+.006*sin(t*pi)
  for i in range(40):
   a=2*pi*i/40;vs.append(tuple(c+(u*cos(a)+v*sin(a))*(r+.004*sin(9*a+t*3))))
 for j in range(8):
  for i in range(40):a=j*40+i;b=j*40+(i+1)%40;fs.append((a,b,b+40,a+40))
 o=solid(mesh('Folded sleeve '+side,vs,fs,linen));attach(o,'upperarm_'+side)
 attach(curve('Sleeve stitched hem '+side,vs[-40:]+[vs[-40]],.0028,thread),'upperarm_'+side)
# Belt as thick ribbon and rectangular buckles.
def ribbon(name,pts,width,mat,bone):
 vs=[(x,y,z+sg*width/2) for x,y,z in pts for sg in [-1,1]];fs=[(i*2,i*2+1,i*2+3,i*2+2) for i in range(len(pts)-1)];return attach(bevel(solid(mesh(name,vs,fs,mat),.007),.002),bone)
ribbon('Waist belt',[(.19*sin(a),-.143*cos(a),1.17) for a in [i*2*pi/96 for i in range(97)]],.042,leather,'spine_01')
attach(curve('Belt buckle',[(-.035,-.155,1.145),(.027,-.155,1.145),(.027,-.155,1.195),(-.035,-.155,1.195),(-.035,-.155,1.145)],.006,brass),'spine_01')
# Long diagonal shoulder strap, with offset edge stitches.
strap=[(.17-.40*t,-.171-.018*sin(t*pi),1.55-.50*t) for t in [i/32 for i in range(33)]]
ribbon('Satchel shoulder strap',strap,.046,leather,'spine_03')
for sign in [-1,1]:attach(curve('Strap sewn edge',[(x,y-.007,z+sign*.017) for x,y,z in strap],.0017,thread),'spine_03')
for k in range(4):attach(curve('Strap buckle',[(.07-k*.012,-.194,1.43-k*.015),(.11-k*.012,-.194,1.43-k*.015)],.003,brass),'spine_03')
bag=attach(sphere('Leather satchel',(-.24,-.17,1.01),(.125,.062,.145),leather),'pelvis')
flap=attach(sphere('Satchel overlapping flap',(-.24,-.224,1.08),(.119,.019,.075),leather),'pelvis')
attach(curve('Satchel stitched flap',[(-.35+.22*t,-.241,1.09-.065*sin(t*pi)) for t in [i/32 for i in range(33)]],.0025,thread),'pelvis')
attach(sphere('Satchel brass stud',(-.24,-.247,1.018),(.009,.005,.009),brass),'pelvis')
ribbon('Belt hanging end',[(.06,-.17,1.15),(.08,-.19,.97),(.05,-.20,.84)],.033,leather,'pelvis')
# Broad folded cape with weighted hems and authored secondary shape-key motion.
vs=[];fs=[];NX=28;NY=30
for j in range(NY+1):
 t=j/NY
 for i in range(NX+1):
  u=i/NX;x=(u-.5)*(.46+.65*t)-.20*t;y=.10+.13*t+.065*sin(u*pi*9)*(.15+.85*t);z=1.55-1.18*t+.10*sin(u*pi)*t
  vs.append((x,y,z))
for j in range(NY):
 for i in range(NX):a=j*(NX+1)+i;fs.append((a,a+1,a+NX+2,a+NX+1))
cloak=mesh('Wind folded olive cloak',vs,fs,wool);attach(cloak,'spine_03');cloak.shape_key_add(name='Basis');k=cloak.shape_key_add(name='Breeze')
for i,v in enumerate(k.data):
 t=(i//(NX+1))/NY;v.co.y+=.09*t*t*sin(i%29*.27);v.co.x-=.05*t*t
solid(cloak);sub=cloak.modifiers.new('Soft wool folds','SUBSURF');sub.levels=sub.render_levels=1
attach(curve('Cloak worn hem',vs[-NX-1:],.004,thread),'spine_03')
vs=[];fs=[]
for j in range(9):
 t=j/8
 for i in range(64):
  a=2*pi*i/64;r=.10+.10*t
  vs.append((r*sin(a),-r*.78*cos(a),1.66-.10*t-.065*max(0,cos(a))*t+.009*sin(4*a+t*6)))
for j in range(8):
 for i in range(64):a=j*64+i;b=j*64+(i+1)%64;fs.append((a,b,b+64,a+64))
attach(solid(mesh('Draped shoulder cowl',vs,fs,wool)),'spine_03')
attach(sphere('Cloak clasp',(-.14,-.17,1.50),(.027,.010,.027),brass),'spine_03')
# Traveller's broad hat slung behind shoulders.
hat=sphere('Travellers felt hat brim',(-.10,.22,1.49),(.27,.027,.27),leather);attach(hat,'spine_03');attach(sphere('Hat crown',(-.10,.25,1.49),(.16,.07,.16),wool),'spine_03')
# Hair follows the anatomical skull, with real curled strands and jaw beard.
h=rig.pose.bones['head'];hc=(h.head+h.tail)*.5+rig.location;hc.z-=.035
for i in range(90):
 a=random.uniform(0,2*pi);t=random.uniform(.15,1.9);x=hc.x+.096*sin(t)*sin(a);y=hc.y+.105*sin(t)*cos(a);z=hc.z+.015+.123*cos(t)
 if cos(a)<-.3 and t>1.2:continue
 pts=[(x+.011*cos(q),y+.007*sin(q),z+.007*sin(q*1.7)) for q in [j*1.8*pi/12 for j in range(13)]];attach(curve('Hair curl',pts,.007,hair),'head')
for i in range(48):
 a=-1.2+2.4*i/47;x=hc.x+.078*sin(a);y=hc.y-.115*cos(a);z=hc.z-.060-.035*cos(a)
 pts=[(x+.003*sin(t*9+i),y-.006*sin(t*pi),z-.025*t) for t in [j/8 for j in range(9)]];attach(curve('Beard curl',pts,.008,hair if i%4 else grey),'head')
attach(curve('Leather headband',[(hc.x+.099*sin(a),hc.y-.106*cos(a),hc.z+.05) for a in [i*2*pi/96 for i in range(97)]],.008,leather),'head')
# Sandals built in rest coordinates before limb posing.
for side in ['l','r']:
 foot=rig.pose.bones['foot_'+side];x=foot.head.x;y=foot.head.y
 pts=[(x+.055*cos(a),y-.07+.135*sin(a),.112) for a in [i*2*pi/48 for i in range(48)]];attach(bevel(solid(mesh('Sandal sole '+side,pts,[tuple(range(48))],leather),.016)), 'foot_'+side)
 for yy in [-.17,-.12,-.07,.01]:
  pts=[(x+.054*cos(a),y+yy,.128+.052*sin(a)) for a in [i*pi/20 for i in range(21)]];attach(curve('Sandal strap '+side,pts,.008,leather),'foot_'+side)
 for z in [.19,.23,.27]:attach(curve('Ankle lacing '+side,[(x+.043*sin(a),y+.045*cos(a),z+.01*sin(2*a)) for a in [i*2*pi/48 for i in range(49)]],.005,leather),'calf_'+side)
# Pose with analytic two-bone placement. The shading hand remains visibly above the brow.
def aim(name,d):
 p=rig.pose.bones[name];q=p.bone.matrix_local.to_quaternion();dq=(q@Vector((0,1,0))).rotation_difference(Vector(d).normalized());m=(dq@q).to_matrix().to_4x4();m.translation=p.head;p.matrix=m;bpy.context.view_layer.update()
def limb(upper,lower,target,pole):
 a=rig.pose.bones[upper].head.copy();t=Vector(target);axis=t-a;l1=rig.data.bones[upper].length;l2=rig.data.bones[lower].length;d=min(axis.length,l1+l2-.0001);axis.normalize();along=(l1*l1-l2*l2+d*d)/(2*d);height=max(0,l1*l1-along*along)**.5;side=Vector(pole)-a;side=(side-axis*side.dot(axis)).normalized();elbow=a+axis*along+side*height;aim(upper,elbow-a);aim(lower,t-elbow)
rig.location=(.08,0,.015)
p=rig.pose.bones['spine_03'];pivot=p.head.copy();p.matrix=Matrix.Translation(pivot)@Matrix.Rotation(.30,4,'Y')@Matrix.Translation(-pivot)@p.matrix
bpy.context.view_layer.update()
limb('thigh_r','calf_r',(-.26,-.18,.16),(-.32,-.38,.52));limb('thigh_l','calf_l',(.43,.13,.16),(.53,-.40,.65))
limb('upperarm_r','lowerarm_r',(-.62,-.19,1.10),(-.43,-.22,1.25));limb('upperarm_l','lowerarm_l',(.42,-.18,1.71),(.61,-.08,1.50))
aim('hand_l',(-.095,-.035,.005));aim('hand_r',(-.015,-.01,.09))
p=rig.pose.bones['head'];pivot=p.head.copy();p.matrix=Matrix.Translation(pivot)@Matrix.Rotation(.95,4,'Z')@Matrix.Translation(-pivot)@p.matrix
for digit in ['index','middle','ring','pinky']:
 for j in range(1,4):p=rig.pose.bones[f'{digit}_{j:02d}_r'];p.rotation_mode='XYZ';p.rotation_euler.x=1.15
bpy.context.view_layer.update()
grip=rig.pose.bones['hand_r'].head+rig.location+Vector((0,-.015,.045));direction=Vector((-.36,0,.93)).normalized();points=[grip+direction*t for t in [-1.04,-.5,0,.5,.70]]
staff=curve('Forked walking staff',[tuple(p) for p in points],.015,wood);attach(staff,'hand_r')
attach(curve('Staff fork',[tuple(grip+direction*.48),tuple(grip+direction*.57+Vector((-.10,0,-.01))),tuple(grip+direction*.64+Vector((-.13,.01,-.025)))],.012,wood),'hand_r')
for j in range(7):attach(curve('Staff grain ridge',[(p.x+.012*cos(j),p.y+.012*sin(j),p.z) for p in points],.0013,edge),'hand_r')
bpy.ops.mesh.primitive_cylinder_add(vertices=128,radius=.58,depth=.095,location=(.03,0,.0475));base=bpy.context.object;base.name='GEO-Stationary cream stone';base.data.materials.append(stone);bevel(base,.012)
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=8;sc.cycles.use_denoising=True;sc.cycles.max_bounces=4;sc.render.threads_mode='FIXED';sc.render.threads=3;sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.resolution_x=sc.render.resolution_y=256;sc.render.resolution_percentage=100;sc.render.fps=24
sc.world.color=(.15,.15,.15);sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast'
bpy.ops.object.camera_add(location=(.6,-7,3.2));sc.camera=bpy.context.object;sc.camera.name='Scout painting camera';sc.camera.data.type='ORTHO';sc.camera.data.ortho_scale=2.14;sc.camera.rotation_euler=(Vector((-.04,0,.85))-sc.camera.location).to_track_quat('-Z','Y').to_euler()
for name,loc,power,size,col in [('Warm upper left',(-3,-4,6),650,3,(1,.87,.67)),('Soft fill',(4,-2,3),180,4,(.86,.91,1)),('Cool rim',(1,3,4),400,2,(.76,.84,1))]:
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name=name;o.data.energy=power;o.data.size=size;o.data.color=col;o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
# Place anatomical feet just above the single stone disc.
bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();floor=min((body.matrix_world@v.co).z for v in me.vertices);ev.to_mesh_clear();rig.location.z+=.100-floor;bpy.context.view_layer.update()
rig['neutral_pose']=json.dumps({p.name:[list(row) for row in p.matrix_basis] for p in rig.pose.bones});sc['source']='MPFB 2.0.18 CC0 anatomy; original scout kit and authored poses'
bpy.ops.wm.save_as_mainfile(filepath=str(M/'scout-built.blend'))
(M/'model-info.json').write_text(json.dumps({'body_vertices':len(body.data.vertices),'bones':len(rig.data.bones),'objects':len(sc.objects)},indent=2))
print('SCOUT_MODEL_READY',flush=True)
