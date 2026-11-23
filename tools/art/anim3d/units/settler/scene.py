"""True MPFB anatomy and original tailored traveller kit, in metres. Blender only."""
import bpy, math, os, json, random
from pathlib import Path
from mathutils import Vector, Matrix
from math import sin, cos, pi
ROOT=Path(os.environ.get('ANIM_ROOT',str(Path.home()/'LegatumRuns/anim-pilot')))
MASTER=ROOT/'masters/settler'; ASSETS=ROOT/'assets/settler'; REVIEW=ROOT/'review/3d-v2'
for p in (MASTER,ASSETS,REVIEW): p.mkdir(parents=True,exist_ok=True)
random.seed(71)
def log(s):
    with (REVIEW/'settler-log.md').open('a') as f:f.write('- '+s+'\n')
def mat(name,c,rough=.7,metal=0):
    m=bpy.data.materials.new('MAT-'+name);m.use_nodes=True;m.diffuse_color=(*c,1)
    s=m.node_tree.nodes.get('Principled BSDF');s.inputs['Base Color'].default_value=(*c,1);s.inputs['Roughness'].default_value=rough;s.inputs['Metallic'].default_value=metal
    return m

def mesh(name,vs,fs,m):
    d=bpy.data.meshes.new(name);d.from_pydata(vs,[],fs);d.update();o=bpy.data.objects.new('GEO-'+name,d);bpy.context.collection.objects.link(o)
    if m:d.materials.append(m)
    for p in d.polygons:p.use_smooth=True
    return o

def solid(o,t=.004):
    mod=o.modifiers.new('Physical fabric thickness','SOLIDIFY');mod.thickness=t
    return o

def bevel(o,t=.003):
    mod=o.modifiers.new('Rounded worn edges','BEVEL');mod.width=t;mod.segments=3
    return o

def sub(o):
    mod=o.modifiers.new('Tailored smooth folds','SUBSURF');mod.levels=1;mod.render_levels=1
    return o

def curve(name,pts,r,m):
    d=bpy.data.curves.new(name,'CURVE');d.dimensions='3D';d.resolution_u=2
    s=d.splines.new('POLY');s.points.add(len(pts)-1)
    for p,v in zip(s.points,pts):p.co=(*v,1)
    d.bevel_depth=r;d.bevel_resolution=2;o=bpy.data.objects.new('GEO-'+name,d);bpy.context.collection.objects.link(o);d.materials.append(m)
    return o

def sphere(name,loc,scale,m):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=20,location=loc);o=bpy.context.object;o.name='GEO-'+name;o.scale=scale;o.data.materials.append(m)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    for p in o.data.polygons:p.use_smooth=True
    return o

def attach(o,bone):
    bpy.context.view_layer.update();w=o.matrix_world.copy();o.parent=rig;o.parent_type='BONE';o.parent_bone=bone;bpy.context.view_layer.update();o.matrix_world=w;o['attachment']=bone
    return o

def aim(name,d):
    p=rig.pose.bones[name];q=p.bone.matrix_local.to_quaternion();v=q@Vector((0,1,0));rot=(v.rotation_difference(Vector(d).normalized())@q).to_matrix().to_4x4();rot.translation=p.head.copy();p.matrix=rot;bpy.context.view_layer.update()

def limb(a,b,t,pole):
    h=rig.pose.bones[a].head.copy();t=Vector(t);axis=t-h;l1=rig.data.bones[a].length;l2=rig.data.bones[b].length;dist=min(axis.length,l1+l2-.0001);axis.normalize();along=(l1*l1-l2*l2+dist*dist)/(2*dist);v=Vector(pole)-h;v=(v-axis*v.dot(axis)).normalized();joint=h+axis*along+v*max(0,l1*l1-along*along)**.5
    aim(a,joint-h);aim(b,t-joint)

def cloth_tube(name,rings,m,bone,seg=64):
    vs=[]
    for j,(z,rx,ry,cx,cy) in enumerate(rings):
        for i in range(seg):
            a=2*pi*i/seg;wave=(.008+.008*j/max(1,len(rings)-1))*sin(12*a+j*.35)+.004*sin(23*a)
            vs.append((cx+(rx+wave)*sin(a),cy-(ry+wave)*cos(a),z+.008*sin(7*a)))
    fs=[(j*seg+i,j*seg+(i+1)%seg,(j+1)*seg+(i+1)%seg,(j+1)*seg+i) for j in range(len(rings)-1) for i in range(seg)]
    return attach(sub(solid(mesh(name,vs,fs,m))),bone)

bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.preferences.addon_enable(module='bl_ext.user_default.mpfb')
from bl_ext.user_default.mpfb.services.humanservice import HumanService
from bl_ext.user_default.mpfb.services.targetservice import TargetService
macro=TargetService.get_default_macro_info_dict();macro.update(gender=0,age=.32,muscle=.42,weight=.46,height=.47,proportions=.65);macro['race']={'caucasian':.65,'african':.15,'asian':.20}
body=HumanService.create_human(macro_detail_dict=macro);body.name='GEO-MPFB female traveller'
bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();lo=min(v.co.z for v in me.vertices);hi=max(v.co.z for v in me.vertices);ev.to_mesh_clear();body.scale=(1.72/(hi-lo),)*3
bpy.context.view_layer.objects.active=body;body.select_set(True);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
rig=HumanService.add_builtin_rig(body,'game_engine');rig.name='RIG-Settler MPFB';rig.location.z=.09
system=ROOT/'blender-user/extensions/.user/user_default/mpfb/data'
eyes=HumanService.add_mhclo_asset(str(system/'eyes/high-poly/high-poly.mhclo'),body,asset_type='Eyes',subdiv_levels=1,material_type='MAKESKIN');eyes.name='GEO-MPFB eyes'
skin=mat('painted warm skin',(.55,.30,.17),.63);ivory=mat('ivory flax linen',(.64,.52,.35),.86);olive=mat('sage olive wool',(.20,.22,.145),.9);rust=mat('terracotta woven shawl',(.34,.105,.052),.87);leather=mat('scuffed chestnut leather',(.105,.043,.018),.7);hair=mat('dark chestnut hair',(.055,.022,.009),.74);wood=mat('weathered staff',(.23,.13,.045),.7);wicker=mat('woven pack ochre',(.27,.17,.065),.86);gold=mat('worn brass clasp',(.65,.40,.13),.32,1);stone=mat('warm cream stone E9CFA0',(.92,.66,.36),.87)
body.data.materials.clear();body.data.materials.append(skin);sub(body)
for p in body.data.polygons:p.use_smooth=True
# Natural walking rest pose: narrow civilian stance, staff grip and shoulder-strap grip.
limb('thigh_r','calf_r',(-.12,-.10,.06),(-.15,-.35,.43));limb('thigh_l','calf_l',(.13,.055,.06),(.13,-.25,.43))
limb('upperarm_r','lowerarm_r',(-.34,-.22,1.12),(-.34,-.04,1.10));limb('upperarm_l','lowerarm_l',(.18,-.25,1.37),(.38,-.02,1.12))
for side in ('r','l'):
    aim('hand_'+side,(0,-.01,.09))
    for digit in ['index','middle','ring','pinky']:
        for k in range(1,4):
            p=rig.pose.bones[f'{digit}_{k:02d}_{side}'];p.rotation_mode='XYZ';p.rotation_euler.x=.95
p=rig.pose.bones['head'];w=p.matrix.copy();v=p.head.copy();p.matrix=Matrix.Translation(v)@Matrix.Rotation(.32,4,'Z')@Matrix.Translation(-v)@w
bpy.context.view_layer.update()
# Dress is a full closed-around garment, not a painted relief or image plane.
rings=[]
for j in range(25):
    t=j/24;rings.append((.31+.98*t,.285-.100*t,.195-.045*t,-.025*(1-t),.01))
skirt=cloth_tube('full length linen skirt',rings,ivory,'pelvis')
# Shape-key hem follow-through is authored geometry, not a simulation claim.
skirt.shape_key_add(name='Basis');key=skirt.shape_key_add(name='Hem sway');key.slider_min=-1
for v,base in zip(key.data,skirt.data.vertices):
    w=max(0,min(1,(1.28-base.co.z)/.9));v.co.x+=.035*w*sin(base.co.z*7);v.co.y+=.025*w*cos(base.co.x*13)
cloth_tube('gathered linen bodice',[(1.25,.195,.16,0,-.01),(1.31,.215,.18,0,-.01),(1.40,.245,.18,0,-.005),(1.49,.23,.15,0,0),(1.56,.115,.10,0,0)],ivory,'spine_03')
# Asymmetric olive overdrape wraps three quarters around the dress with a diagonal hem.
vs=[];fs=[];nx=48;ny=24
for j in range(ny+1):
    t=j/ny
    for i in range(nx+1):
        u=i/nx;a=-.40+u*1.85*pi;hem=.44+.55*max(0,1-(a+.4)/1.65);z=1.29*(1-t)+hem*t;rx=.19+.115*t;ry=.14+.075*t;fold=.016*sin(9*a+t*3)+.007*sin(19*a)
        vs.append(((rx+fold)*sin(a),-(ry+fold)*cos(a)-.005,z+.012*sin(a*5)*t))
for j in range(ny):
    for i in range(nx):a=j*(nx+1)+i;fs.append((a,a+1,a+nx+2,a+nx+1))
over=attach(sub(solid(mesh('olive diagonal overdrape',vs,fs,olive))), 'pelvis')
# Sleeves use a continuous curved sweep between the actual posed shoulder, elbow and cuff.
for side in ('r','l'):
    a=rig.pose.bones['upperarm_'+side].head+rig.location;b=rig.pose.bones['lowerarm_'+side].head+rig.location;c=rig.pose.bones['hand_'+side].head+rig.location
    for part,start,end,rad0,rad1 in [('upperarm',a,b,.10,.09),('lowerarm',b,c*.85+b*.15,.09,.105)]:
        axis=(end-start).normalized();u=axis.cross(Vector((0,1,0))).normalized();v=axis.cross(u);vs=[];fs=[]
        for j in range(13):
            t=j/12;center=start.lerp(end,t)
            for i in range(40):
                ang=i*2*pi/40;rr=(rad0*(1-t)+rad1*t)*(1+.07*sin(t*6*pi+ang*3))+.006*sin(ang*10)
                vs.append(tuple(center+rr*(u*cos(ang)+v*sin(ang))))
        for j in range(12):
            for i in range(40):a0=j*40+i;b0=j*40+(i+1)%40;fs.append((a0,b0,b0+40,a0+40))
        attach(sub(solid(mesh('folded sleeve '+part+' '+side,vs,fs,ivory))),part+'_'+side)
# Hood: open face aperture, full volume around crown/back, thick rolled hem.
h=rig.pose.bones['head'];hc=(h.head+h.tail)*.5+rig.location;hc.z+=.025
vs=[];fs=[];nx=52;ny=18
for j in range(ny+1):
    t=j/ny
    for i in range(nx+1):
        a=-pi*.62+i/nx*pi*1.24;z=hc.z+.135*cos(a)-.07*(1-cos(a));x=hc.x+.135*sin(a);y=hc.y-.10+.23*t
        vs.append((x*(1-.10*t)+.007*sin(a*12+t*3),y,z-.035*t+.006*cos(a*15)))
for j in range(ny):
    for i in range(nx):a=j*(nx+1)+i;fs.append((a,a+1,a+nx+2,a+nx+1))
attach(sub(solid(mesh('open linen hood crown',vs,fs,ivory),.008)),'head')
attach(curve('hood rolled face border',vs[:nx+1],.011,ivory),'head')
for sg in [-1,1]:
    pts=[(sg*(.11+.04*sin(t*pi)), -.075-.045*sin(t*pi), hc.z-.055-.29*t) for t in [i/30 for i in range(31)]]
    attach(curve('hood hanging fold',pts,.027,ivory),'spine_03')
for j in range(5):
    attach(curve('hood collar folds',[(.16*sin(a),-.12-.06*cos(a),1.56-.016*j-.035*cos(a)) for a in [-pi/2+i*pi/32 for i in range(33)]],.015,ivory),'spine_03')
# Linen hood side panels join the crown to the cowl, leaving the face open.
for sg in [-1,1]:
    vs=[];fs=[]
    for j in range(17):
        t=j/16
        for i in range(13):
            u=i/12;x=sg*(.126+.035*sin(t*pi)+.008*sin(u*5*pi));y=hc.y-.095+.21*u;z=hc.z-.01-.22*t-.025*u
            vs.append((x,y,z))
    for j in range(16):
        for i in range(12):a=j*13+i;fs.append((a,a+1,a+14,a+13))
    attach(sub(solid(mesh('hood side drape',vs,fs,ivory),.006)),'head')
# Full sculpted hair cap behind the open face plus individual wavy locks.
cap=sphere('chestnut hair cap',(hc.x,hc.y+.04,hc.z+.012),(.111,.105,.135),hair);attach(cap,'head')
for sg in [-1,1]:
    for k in range(5):
        pts=[(sg*(.09+.008*k+.007*sin(t*pi*5+k)),hc.y-.04+.014*k,hc.z+.09-.28*t) for t in [i/24 for i in range(25)]]
        attach(curve('wavy temple lock',pts,.006,hair),'head')
# Shawl across shoulders and chest, broad folded tail down the right/back side.
vs=[];fs=[];nx=48;ny=14
for j in range(ny+1):
    t=j/ny
    for i in range(nx+1):
        u=i/nx;x=-.25+.55*u;z=1.57-.16*(1-u)-.13*t; y=-.16-.055*sin(u*pi)-.008*sin(t*5*pi)
        vs.append((x,y,z+.012*sin(u*pi*4+t*2)))
for j in range(ny):
    for i in range(nx):a=j*(nx+1)+i;fs.append((a,a+1,a+nx+2,a+nx+1))
attach(sub(solid(mesh('rust shawl shoulder folds',vs,fs,rust),.006)),'spine_03')
vs=[];fs=[];nx=20;ny=40
for j in range(ny+1):
    t=j/ny
    for i in range(nx+1):
        u=i/nx;x=.18+.20*u+.08*sin(t*pi);y=.10+.09*sin(u*pi)+.025*sin(t*8+u*12);z=1.49-.98*t-.12*u
        vs.append((x,y,z))
for j in range(ny):
    for i in range(nx):a=j*(nx+1)+i;fs.append((a,a+1,a+nx+2,a+nx+1))
attach(sub(solid(mesh('rust shawl long fringed tail',vs,fs,rust),.006)),'spine_03')
for i in range(21):
    u=i/20;v=Vector(vs[ny*(nx+1)+i]);attach(curve('shawl fringe',[v,v+Vector((.012*sin(i),.007,.0)) + Vector((0,0,-.055))],.003,rust),'spine_03')
# Belt, knotted hanging ends and thickness-bearing shoulder strap.
for z in [1.27,1.295]:attach(curve('leather belt',[(.194*sin(a),-.150*cos(a),z+.006*sin(3*a)) for a in [i*2*pi/96 for i in range(97)]],.014,leather),'pelvis')
for k in [-1,1]:attach(curve('knotted belt tail',[(.09,-.181,1.295),(.11+.015*k,-.195,1.17),(.13+.018*k,-.23,.94)],.014,leather),'pelvis')
strap=attach(curve('pack strap',[(.22,.12,1.48),(.20,-.10,1.50),(.12,-.20,1.35),(.17,-.18,1.10)],.020,leather),'spine_03')
for i in range(17):
    t=i/16;attach(curve('strap saddle stitch',[(.18-.05*t,-.205,1.44-.29*t),(.186-.05*t,-.206,1.437-.29*t)],.0015,ivory),'spine_03')
clasp=attach(sphere('brass shawl pin',(.205,-.181,1.45),(.025,.008,.025),gold),'spine_03')
attach(curve('pin concentric relief',[(.205+.017*cos(a),-.191,1.45+.017*sin(a)) for a in [i*2*pi/40 for i in range(41)]],.002,gold),'spine_03')
pack=attach(sphere('ochre traveller pack',(.24,.19,1.25),(.18,.15,.25),wicker),'spine_03')
for i in range(24):
    a=i*2*pi/24;pts=[]
    for j in range(31):
        t=-1.1+j/30*2.2;pts.append((.24+.182*cos(t)*sin(a),.19+.152*cos(t)*cos(a),1.25+.252*sin(t)))
    attach(curve('pack woven rib',pts,.0035,wicker),'spine_03')
# Rolled blanket has real cylindrical volume and a spiral end visible to the camera.
start=Vector((.10,.18,1.51));end=Vector((.45,.07,1.49));axis=(end-start).normalized();u=Vector((0,0,1));v=axis.cross(u).normalized()
vs=[];fs=[]
for j in range(9):
    for i in range(64):
        a=i*2*pi/64;vs.append(tuple(start.lerp(end,j/8)+(.10+.004*sin(a*9))*(u*cos(a)+v*sin(a))))
for j in range(8):
    for i in range(64):a=j*64+i;b=j*64+(i+1)%64;fs.append((a,b,b+64,a+64))
attach(solid(mesh('rolled wool blanket',vs,fs,olive),.008),'spine_03')
pts=[]
for i in range(181):
    a=i/180*6*pi;r=.01+.09*i/180;pts.append(tuple(end+axis*.005+r*(u*cos(a)+v*sin(a))))
attach(curve('blanket visible spiral',pts,.009,ivory),'spine_03')
# Staff runs through the right palm; all its parts share the same bone attachment.
grip=rig.pose.bones['hand_r'].head+rig.location+Vector((0,-.013,.045));staff=[]
for i in range(65):
    t=i/64;staff.append((grip.x-.025*(1-t)+.003*sin(t*22),grip.y+.005*sin(t*17),.09+1.38*t))
attach(curve('walking staff',staff,.013,wood),'hand_r')
for k in range(7):attach(curve('staff carved grain',[(x+.012*cos(k),y+.012*sin(k),z) for x,y,z in staff],.0012,leather),'hand_r')
# Sandals with soles and overlapping leather cross-straps on real anatomical feet.
for side in ('r','l'):
    foot=rig.pose.bones['foot_'+side];x=foot.head.x;y=foot.head.y
    pts=[(x+.052*cos(a),y-.065+.12*sin(a),.095) for a in [i*2*pi/48 for i in range(48)]]
    attach(bevel(solid(mesh('sandal sole '+side,pts,[tuple(range(48))],leather),.016),.005),'foot_'+side)
    for k in range(3):
        pts=[(x-.055+.11*t,y-.15+.045*k+.045*t,.11+.04*sin(t*pi)) for t in [i/20 for i in range(21)]]
        attach(curve('sandal cross strap '+side,pts,.009,leather),'foot_'+side)
# Stationary, single warm cream disc.
bpy.ops.mesh.primitive_cylinder_add(vertices=128,radius=.48,depth=.075,location=(0,0,.0375));base=bpy.context.object;base.name='GEO-stationary cream base';base.data.materials.append(stone);bevel(base,.012)
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=8;sc.cycles.use_denoising=True;sc.cycles.max_bounces=4
sc.render.resolution_x=sc.render.resolution_y=256;sc.render.resolution_percentage=100;sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA'
sc.world.color=(.17,.17,.17);sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast'
bpy.ops.object.camera_add(location=(.45,-7,2.47));sc.camera=bpy.context.object;sc.camera.name='CAM-painting';sc.camera.data.type='ORTHO';sc.camera.data.ortho_scale=2.04;sc.camera.rotation_euler=(Vector((0,0,.88))-sc.camera.location).to_track_quat('-Z','Y').to_euler()
for name,pos,power,size,col in [('warm key',(-3,-4,6),650,2,(1,.90,.76)),('soft fill',(4,-3,3),180,3,(.9,.94,1)),('cool rim',(1,3,4),260,2,(.76,.85,1))]:
    bpy.ops.object.light_add(type='AREA',location=pos);o=bpy.context.object;o.name='LGT-'+name;o.data.energy=power;o.data.size=size;o.data.color=col;o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
sc.render.fps=24
rig['neutral_pose']=json.dumps({p.name:[list(r) for r in p.matrix_basis] for p in rig.pose.bones});rig['source']='MPFB 2.0.18 CC0 game_engine, 53 bones'
from cloth_mask import apply_mask
apply_mask()
sc['unit']='settler';sc['cloth_method']='Authored folds and hem follow-through; no cloth simulation claimed'
bpy.ops.wm.save_as_mainfile(filepath=str(MASTER/'settler-plain.blend'))
(MASTER/'model-info.json').write_text(json.dumps({'body_vertices':len(body.data.vertices),'bones':len(rig.data.bones),'objects':len(sc.objects),'source':'MPFB 2.0.18 female CC0','cloth':sc['cloth_method']},indent=2))
log('Built MPFB female, full folded robes, open hood, shawl/fringe, pack/spiral bedroll, staff, straps and sandals; plain master saved.')
