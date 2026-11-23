"""MPFB human, fitted hoplite kit, editable rig and review scene. Run in Blender."""
import bpy, sys, os, math, json, random
from pathlib import Path
from mathutils import Vector, Matrix, Quaternion
from math import sin, cos, pi
ROOT = Path(os.environ.get('ANIM_ROOT', str(Path.home()/'LegatumRuns/anim-pilot')))
MASTER = ROOT/'masters/phalangite'
ASSETS = ROOT/'assets'
REVIEW = ROOT/'review/3d-v2'
for p in (MASTER, REVIEW): p.mkdir(parents=True, exist_ok=True)
random.seed(12)

def material(name, color, metal=0, rough=.52):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    s=m.node_tree.nodes.get('Principled BSDF'); s.inputs['Base Color'].default_value=(*color,1)
    s.inputs['Metallic'].default_value=metal; s.inputs['Roughness'].default_value=rough
    return m

def mesh(name, verts, faces, mat, smooth=True):
    d=bpy.data.meshes.new(name); d.from_pydata(verts,[],faces); d.update()
    o=bpy.data.objects.new(name,d); bpy.context.collection.objects.link(o)
    if mat: d.materials.append(mat)
    for p in d.polygons: p.use_smooth=smooth
    return o

def bevel(o, width=.004, segments=2):
    m=o.modifiers.new('Forged rounded edges','BEVEL'); m.width=width; m.segments=segments
    return o

def solid(o,t=.004):
    m=o.modifiers.new('Physical thickness','SOLIDIFY'); m.thickness=t
    return o

def curve(name, pts, radius, mat):
    d=bpy.data.curves.new(name,'CURVE'); d.dimensions='3D'; d.resolution_u=2
    s=d.splines.new('POLY'); s.points.add(len(pts)-1)
    for p,v in zip(s.points,pts): p.co=(*v,1)
    d.bevel_depth=radius; d.bevel_resolution=2
    o=bpy.data.objects.new(name,d); bpy.context.collection.objects.link(o); d.materials.append(mat)
    return o

def sphere(name, loc, scale, mat):
    # Small metal rivets and shield boss only; never anatomy.
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,location=loc)
    o=bpy.context.object; o.name=name; o.scale=scale; o.data.materials.append(mat)
    for p in o.data.polygons:p.use_smooth=True
    return o

def attach(o,bone):
    bpy.context.view_layer.update(); world=o.matrix_world.copy()
    o.parent=rig; o.parent_type='BONE'; o.parent_bone=bone
    bpy.context.view_layer.update(); o.matrix_world=world
    o['attachment']=bone
    return o

def aim_bone(name, direction):
    p=rig.pose.bones[name]; rest=p.bone.matrix_local
    q=rest.to_quaternion(); v=q @ Vector((0,1,0)); delta=v.rotation_difference(Vector(direction).normalized())
    rot=(delta @ q).to_matrix().to_4x4(); rot.translation=p.head.copy()
    p.matrix=rot; bpy.context.view_layer.update()

def limb(upper, lower, target, pole):
    a=rig.pose.bones[upper].head.copy(); t=Vector(target); axis=t-a
    l1=rig.data.bones[upper].length; l2=rig.data.bones[lower].length
    d=min(axis.length,l1+l2-.0001); axis.normalize()
    along=(l1*l1-l2*l2+d*d)/(2*d); h=max(0,l1*l1-along*along)**.5
    side=Vector(pole)-a; side=(side-axis*side.dot(axis)).normalized()
    elbow=a+axis*along+side*h
    aim_bone(upper,elbow-a); aim_bone(lower,t-elbow)

def camera(pos):
    c=bpy.context.scene.camera; c.location=pos
    c.rotation_euler=(Vector((0,0,1.25))-c.location).to_track_quat('-Z','Y').to_euler()

bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
bpy.ops.preferences.addon_enable(module='bl_ext.user_default.mpfb')
from bl_ext.user_default.mpfb.services.humanservice import HumanService
from bl_ext.user_default.mpfb.services.targetservice import TargetService
macro=TargetService.get_default_macro_info_dict()
macro.update(gender=1.0,age=.38,muscle=.85,weight=.57,height=.45,proportions=.65)
macro['race']={'caucasian':.75,'african':.15,'asian':.10}
body=HumanService.create_human(macro_detail_dict=macro)
body.name='MPFB anatomical male • original topology'
from bl_ext.user_default.mpfb.services.locationservice import LocationService
for side in ['l','r']:
    for target,weight in [('upperarm-muscle-incr',.65),('upperarm-shoulder-muscle-incr',.45),('lowerarm-muscle-incr',.45)]:
        TargetService.load_target(body,str(Path(LocationService.get_mpfb_data('targets'))/'arms'/f'{side}-{target}.target.gz'),weight=weight)

# Normalize real evaluated anatomy; no primitive body construction.
bpy.context.view_layer.update(); ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get()); me=ev.to_mesh()
zlo=min(v.co.z for v in me.vertices); zhi=max(v.co.z for v in me.vertices); ev.to_mesh_clear()
body.scale=(1.72/(zhi-zlo)*1.04,1.72/(zhi-zlo)*1.04,1.72/(zhi-zlo))
bpy.context.view_layer.objects.active=body; body.select_set(True)
bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
rig=HumanService.add_builtin_rig(body,'game_engine'); rig.name='Phalangite MPFB game_engine'
rig.location.z=.105
system_data=ROOT/'blender-user/extensions/.user/user_default/mpfb/data'
eyes=HumanService.add_mhclo_asset(str(system_data/'eyes/high-poly/high-poly.mhclo'),body,asset_type='Eyes',subdiv_levels=1,material_type='MAKESKIN')
eyes.name='MPFB system eyes • CC0'

skin=material('Skin • warm ochre',(.44,.235,.115),0,.6)
bronze=material('Bronze • hammered',(.32,.155,.042),.72,.43)
gold=material('Bronze • polished edges',(.62,.335,.075),.78,.34)
dark=material('Incised bronze patina',(.075,.047,.017),.55,.65)
red=material('Cinnabar wool',(.27,.018,.008),0,.83)
linen=material('Warm ivory linen',(.72,.61,.42),0,.88)
leather=material('Oxide leather',(.12,.040,.015),0,.7)
iron=material('Forged iron',(.16,.18,.18),.75,.43)
wood=material('Ash spear shaft',(.19,.072,.018),0,.57)
stone=material('Cream limestone',(.86,.73,.53),0,.86)
body.data.materials.clear(); body.data.materials.append(skin)
sub=body.modifiers.new('Anatomical subdivision','SUBSURF'); sub.levels=1; sub.render_levels=1
for p in body.data.polygons:p.use_smooth=True
# Body-derived shells retain chest, calf and knee topology and rig weights.
def fitted_shell(name, predicate, mat, inflate=.009):
    dg=bpy.context.evaluated_depsgraph_get(); ev=body.evaluated_get(dg); me=ev.to_mesh()
    faces=[p for p in me.polygons if all(predicate(me.vertices[i].co) for i in p.vertices)]
    ids=sorted(set(i for p in faces for i in p.vertices)); mapping={v:i for i,v in enumerate(ids)}
    vs=[tuple(me.vertices[i].co+me.vertices[i].normal*inflate) for i in ids]
    ob=mesh(name,vs,[[mapping[i] for i in p.vertices] for p in faces],mat)
    # Spatially transfer original MPFB skinning before posing.
    from mathutils.kdtree import KDTree
    kd=KDTree(len(body.data.vertices))
    for v in body.data.vertices:kd.insert(v.co,v.index)
    kd.balance()
    for g in body.vertex_groups:
        if g.name in rig.data.bones: ob.vertex_groups.new(name=g.name)
    for j,i in enumerate(ids):
        _, k, _=kd.find(me.vertices[i].co)
        for g in body.data.vertices[k].groups:
            name=body.vertex_groups[g.group].name
            if name in ob.vertex_groups:ob.vertex_groups[name].add([j],g.weight,'REPLACE')
    ev.to_mesh_clear(); ob.parent=rig
    # Rigid armour plates follow one anatomical segment; nearest basis weights
    # can map shaped chest vertices onto clavicles and pull the shell inside skin.
    if 'cuirass' in name:
        for g in ob.vertex_groups: g.remove(list(range(len(vs))))
        ob.vertex_groups['spine_03'].add(list(range(len(vs))),1,'REPLACE')
    ar=ob.modifiers.new('MPFB fitted weights','ARMATURE'); ar.object=rig
    solid(ob,.008); bevel(ob,.003)
    return ob
# Phalangite-specific layered linothorax and tunic. No hoplite cuirass or cape.
rig.name='Phalangite MPFB game_engine'
bronze.node_tree.nodes.get('Principled BSDF').inputs['Metallic'].default_value=1
bronze.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.57,.31,.08,1)
gold.node_tree.nodes.get('Principled BSDF').inputs['Metallic'].default_value=1
iron.node_tree.nodes.get('Principled BSDF').inputs['Metallic'].default_value=1
stone.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.815,.54,.25,1)
stone.node_tree.nodes.get('Principled BSDF').inputs['Emission Color'].default_value=(.815,.624,.352,1)
stone.node_tree.nodes.get('Principled BSDF').inputs['Emission Strength'].default_value=.25

def ring_shell(name,z0,z1,rx0,rx1,ry0,ry1,mat,fold=.004,bone='spine_03'):
    vs=[]; fs=[]; steps=16; ns=64
    for j in range(steps+1):
        t=j/steps;z=z0+(z1-z0)*t
        for i in range(ns):
            a=i*2*pi/ns;r=fold*sin(a*14+.5*sin(t*6))
            vs.append(((rx0+(rx1-rx0)*t+r)*sin(a),-(ry0+(ry1-ry0)*t+r)*cos(a),z))
    for j in range(steps):
        for i in range(ns):
            a=j*ns+i;b=j*ns+(i+1)%ns;fs.append((a,b,b+ns,a+ns))
    ob=solid(mesh(name,vs,fs,mat),.007);bevel(ob,.003);attach(ob,bone);return ob
cuirass=ring_shell('GEO-linothorax',1.10,1.49,.185,.245,.14,.16,linen,.005)
ring_shell('GEO-red-pleated-tunic',.78,1.15,.27,.18,.20,.135,red,.014,'pelvis')
for side,sg in [('l',1),('r',-1)]:
    fitted_shell('GEO-red-sleeve-'+side,lambda v,s=sg:1.19<v.z<1.49 and .17<v.x*s<.36,red,.018)
    fitted_shell('GEO-bronze-greave-'+side,lambda v,s=sg:.12<v.z<.49 and v.x*s>.065 and v.y<.025,bronze,.014)
    # Sandal straps follow the anatomical feet.
    foot=rig.pose.bones['foot_'+side];x=foot.head.x;y=foot.head.y
    outline=[(x+.055*cos(a),y-.075+.14*sin(a),.112) for a in [2*pi*i/48 for i in range(48)]]
    attach(bevel(solid(mesh('GEO-sandal-sole-'+side,outline,[tuple(range(48))],leather),.018),.006),'foot_'+side)
    for yy in [-.17,-.12,-.06,.01]:
        attach(curve('GEO-sandal-strap-'+side,[(x+.056*cos(a),y+yy,.13+.045*sin(a)) for a in [i*pi/16 for i in range(17)]],.008,leather),'foot_'+side)
# Layered ivory and leather pteruges, individual hems and bronze fastening studs.
for layer in [0,1]:
    for j in range(16):
        a=2*pi*(j+.5*layer)/16;vs=[]
        for k in range(7):
            t=k/6
            for s in [-1,0,1]:
                aa=a+s*.16;rx=.185+.065*t+.008*layer;ry=.14+.045*t+.008*layer
                vs.append((rx*sin(aa),-ry*cos(aa),1.12-(.29-.08*layer)*t))
        ob=solid(mesh('GEO-pteruges',vs,[(k*3+i,k*3+i+1,(k+1)*3+i+1,(k+1)*3+i) for k in range(6) for i in range(2)],linen if layer else leather),.006)
        bevel(ob,.003);attach(ob,'pelvis')
        attach(curve('GEO-pteruges-hem',vs[-3:],.003,gold),'pelvis')
        q=Vector(vs[-2]);q.z+=.018;q.y-=.004
        attach(sphere('GEO-pteruges-rivet',q,(.009,.006,.009),gold),'pelvis')
ring_shell('GEO-leather-belt',1.095,1.125,.195,.195,.15,.15,leather,0,'pelvis')
for sg in [-1,1]:
    vs=[(sg*.13-.035,-.17,1.34),(sg*.13+.035,-.17,1.34),(sg*.13+.035,-.12,1.53),(sg*.13-.035,-.12,1.53)]
    attach(bevel(solid(mesh('GEO-linen-shoulder-flap',vs,[(0,1,2,3)],linen),.014),.004),'spine_03')
    attach(sphere('GEO-shoulder-buckle',(sg*.13,-.187,1.37),(.013,.008,.013),gold),'spine_03')
for j in range(3):
    pts=[(.22*sin(a),-.18*cos(a),1.52-.013*j-.043*cos(a)) for a in [-pi/2+i*pi/40 for i in range(41)]]
    attach(curve('GEO-folded-red-collar',pts,.018,red),'spine_03')
# Open-faced bronze helmet with real cheek pieces, rolled brow and low bronze crest.
hc=(rig.pose.bones['head'].head+rig.pose.bones['head'].tail)*.5;cx=hc.x;cy=hc.y;cz=hc.z+.105
vs=[];fs=[]
for j in range(17):
    t=j/16*pi/2
    for i in range(64):
        a=i*2*pi/64;vs.append((cx+.111*cos(t)*sin(a),cy-.125*cos(t)*cos(a),cz+.015+.145*sin(t)))
for j in range(16):
    for i in range(64):a=j*64+i;b=j*64+(i+1)%64;fs.append((a,b,b+64,a+64))
attach(bevel(solid(mesh('GEO-helmet-bowl',vs,fs,bronze),.006),.003),'head')
attach(curve('GEO-helmet-brow',[(cx+.113*sin(a),cy-.13*cos(a),cz+.015) for a in [i*2*pi/96 for i in range(97)]],.007,gold),'head')
for sg in [-1,1]:
    vs=[(sg*.099,cy-.055,cz+.018),(sg*.10,cy-.108,cz-.025),(sg*.084,cy-.11,cz-.11),(sg*.09,cy-.035,cz-.12),(sg*.108,cy+.012,cz-.025)]
    attach(bevel(solid(mesh('GEO-helmet-cheek',vs,[(0,1,2,3,4)],bronze),.006),.004),'head')
for j in range(35):
    a=-.85+j/34*2.5
    pts=[(-.017,cy+.13*sin(a),cz+.14*cos(a)),(.017,cy+.13*sin(a),cz+.14*cos(a)),(.017,cy+.195*sin(a),cz+.20*cos(a)),(-.017,cy+.195*sin(a),cz+.20*cos(a))]
    attach(bevel(solid(mesh('GEO-low-bronze-crest',pts,[(0,1,2,3)],bronze),.004),.002),'head')
# Initial pose and camera registration. Weapon deliberately extends into depth.
rig.location.z=.10
limb('thigh_r','calf_r',(-.30,-.04,.04),(-.28,-.38,.48))
limb('thigh_l','calf_l',(.30,-.02,.04),(.34,-.31,.48))
limb('upperarm_r','lowerarm_r',(-.27,-.33,.81),(-.48,-.26,1.15))
limb('upperarm_l','lowerarm_l',(.30,-.34,1.27),(.38,-.12,1.06))
for side in ['l','r']:
    aim_bone('hand_'+side,(.04,-.02,.10))
    for digit in ['index','middle','ring','pinky']:
        for k in range(1,4):
            p=rig.pose.bones[f'{digit}_{k:02d}_{side}'];p.rotation_mode='XYZ';p.rotation_euler.x=1.15
p=rig.pose.bones['head'];mat=p.matrix.copy();pivot=p.head.copy();p.matrix=Matrix.Translation(pivot)@Matrix.Rotation(.65,4,'Z')@Matrix.Translation(-pivot)@mat
bpy.context.view_layer.update()
# One continuous shaft controlled separately; hands will be solved to its grips each frame.
gr=rig.matrix_world@rig.pose.bones['hand_r'].head+Vector((.015,-.025,.035))
gl=rig.matrix_world@rig.pose.bones['hand_l'].head+Vector((.015,-.025,.035))
direction=(gl-gr).normalized();start=gr-direction*.70;end=gl+direction*1.48
weapon=bpy.data.objects.new('CTRL-sarissa',None);bpy.context.collection.objects.link(weapon);weapon.location=gr
weapon['grip_r']=list(gr);weapon['grip_l']=list(gl);weapon['start']=list(start);weapon['end']=list(end)
def weapon_parent(ob):
    bpy.context.view_layer.update();world=ob.matrix_world.copy();ob.parent=weapon;ob.matrix_world=world
weapon_parent(curve('GEO-sarissa-continuous-shaft',[start,end],.011,wood))
# Tiny four-sided iron point, not the spearman's broad leaf head.
u=direction.cross(Vector((0,1,0))).normalized()*.019;v=direction.cross(u.normalized())*.009
verts=[end+u,end+v,end-u,end-v,end+direction*.12]
weapon_parent(mesh('GEO-sarissa-iron-point',verts,[(i,(i+1)%4,4) for i in range(4)]+[(3,2,1,0)],iron,False))
weapon_parent(curve('GEO-iron-butt',[start,start+direction*.07],.013,iron))
# Small bronze pelta strapped to left forearm, rear-facing interior visible.
center=Vector((.37,-.20,1.17));rad=.235;vs=[tuple(center+Vector((0,.055,0)))];fs=[]
for j in range(1,10):
    r=rad*j/9
    for i in range(64):
        a=i*2*pi/64;vs.append(tuple(center+Vector((r*sin(a)*.50,.055*(1-(r/rad)**2)+.4*r*sin(a),r*cos(a)))))
for i in range(64):fs.append((0,1+(i+1)%64,1+i))
for j in range(8):
    for i in range(64):a=1+j*64+i;b=1+j*64+(i+1)%64;fs.append((a,a+64,b+64,b))
attach(bevel(solid(mesh('GEO-small-bronze-shield',vs,fs,bronze),.009),.003),'lowerarm_l')
attach(curve('GEO-shield-rolled-rim',vs[-64:]+[vs[-64]],.009,gold),'lowerarm_l')
for z in [1.10,1.22]:
    attach(curve('GEO-forearm-shield-strap',[(.22,-.29,z),(.32,-.31,z),(.43,-.20,z)],.012,leather),'lowerarm_l')
    attach(curve('GEO-shield-strap-buckle',[(.27,-.32,z-.015),(.31,-.32,z-.015),(.31,-.32,z+.015),(.27,-.32,z+.015),(.27,-.32,z-.015)],.003,gold),'lowerarm_l')
# One stationary cream disc.
bpy.ops.mesh.primitive_cylinder_add(vertices=96,radius=.57,depth=.09,location=(0,0,.045))
base=bpy.context.object;base.name='GEO-stationary-cream-base';base.data.materials.append(stone);bevel(base,.012,3)
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=8;sc.cycles.use_denoising=True
sc.render.resolution_x=sc.render.resolution_y=256;sc.render.resolution_percentage=100;sc.render.film_transparent=True
sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA'
sc.world.color=(.22,.22,.22);sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast'
bpy.ops.object.camera_add();sc.camera=bpy.context.object;sc.camera.name='CAM-painting';sc.camera.data.type='ORTHO';sc.camera.data.ortho_scale=2.55
look=Vector((.42,0,1.08));sc.camera.location=look+Vector((1.3,-7,2.0));sc.camera.rotation_euler=(look-sc.camera.location).to_track_quat('-Z','Y').to_euler()
for name,loc,power,size,col in [('LGT-warm-key',(-3,-4,6),600,2,(1,.90,.74)),('LGT-soft-fill',(4,-2,3),170,3,(.88,.92,1)),('LGT-cool-rim',(-2,3,4),450,2,(.78,.86,1))]:
    bpy.ops.object.light_add(type='AREA',location=loc);ob=bpy.context.object;ob.name=name;ob.data.energy=power;ob.data.size=size;ob.data.color=col;ob.rotation_euler=(Vector((0,0,1))-ob.location).to_track_quat('-Z','Y').to_euler()
# Register the continuous sarissa to the painting after the orthographic camera is fixed.
bpy.context.view_layer.update()
right=sc.camera.matrix_world.to_quaternion()@Vector((1,0,0));up=sc.camera.matrix_world.to_quaternion()@Vector((0,1,0));forward=sc.camera.matrix_world.to_quaternion()@Vector((0,0,-1))
def screen_point(x,y,world_y):
    p=look+right*((x/256-.5)*2.55)+up*((.5-y/256)*2.55)
    return p+forward*((world_y-p.y)/forward.y)
gr=screen_point(72,139.849,-.20);gl=screen_point(118,106,-.10)
direction=(gl-gr).normalized();delta=gl-gr;start=gr+delta*((13-72)/46);end=gr+delta*((234-72)/46)
for ob in list(weapon.children):bpy.data.objects.remove(ob,do_unlink=True)
weapon.location=gr;weapon['grip_r']=list(gr);weapon['grip_l']=list(gl);weapon['start']=list(start);weapon['end']=list(end)
weapon_parent(curve('GEO-sarissa-continuous-shaft',[start,end],.010,wood))
u=direction.cross(Vector((0,1,0))).normalized()*.016;v=direction.cross(u.normalized())*.008
verts=[end+u,end+v,end-u,end-v,end+direction*.12]
weapon_parent(mesh('GEO-sarissa-iron-point',verts,[(i,(i+1)%4,4) for i in range(4)]+[(3,2,1,0)],iron,False))
weapon_parent(curve('GEO-iron-butt',[start,start+direction*.07],.012,iron))
for side,g in [('r',gr),('l',gl)]:
    target=rig.matrix_world.inverted()@(g-Vector((.015,-.025,.035)))
    limb('upperarm_'+side,'lowerarm_'+side,target,(-.49,-.26,1.12) if side=='r' else (.15,-.28,.85))
    aim_bone('hand_'+side,(.04,-.02,.10))
bpy.context.view_layer.update()
for ob in list(sc.objects):
    if any(key in ob.name for key in ['small-bronze-shield','shield-rolled-rim','forearm-shield-strap','shield-strap-buckle']):ob.matrix_world=Matrix.Identity(4)
bpy.context.view_layer.update()
rig['neutral_pose']=json.dumps({p.name:[list(row) for row in p.matrix_basis] for p in rig.pose.bones})
sc['unit']='phalangite';sc['body_source']='MPFB 2.0.18 CC0, real topology and weights';sc['stage']='plain'
bpy.ops.wm.save_as_mainfile(filepath=str(MASTER/'plain.blend'))
(MASTER/'model-info.json').write_text(json.dumps({'body_vertices':len(body.data.vertices),'bones':len(rig.data.bones),'objects':len(sc.objects),'sarissa_length':(end-start).length+.12},indent=2))
print('PHALANGITE_PLAIN_READY')
