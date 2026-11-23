"""MPFB human, fitted hoplite kit, editable rig and review scene. Run in Blender."""
import bpy, sys, os, math, json, random
from pathlib import Path
from mathutils import Vector, Matrix, Quaternion
from math import sin, cos, pi
ROOT = Path(os.environ.get('ANIM_ROOT', str(Path.home()/'LegatumRuns/anim-pilot')))
MASTER = ROOT/'masters/gaesatae'
ASSETS = ROOT/'assets/gaesatae'
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
macro.update(gender=1.0,age=.42,muscle=1.0,weight=.72,height=.42,proportions=.65)
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
body.scale=(1.72/(zhi-zlo)*1.10,1.72/(zhi-zlo)*1.04,1.72/(zhi-zlo))
bpy.context.view_layer.objects.active=body; body.select_set(True)
bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
rig=HumanService.add_builtin_rig(body,'game_engine'); rig.name='Gaesatae • MPFB game_engine'
rig.location=(.10,0,.105)
system_data=ROOT/'blender-user/extensions/.user/user_default/mpfb/data'
eyes=HumanService.add_mhclo_asset(str(system_data/'eyes/high-poly/high-poly.mhclo'),body,asset_type='Eyes',subdiv_levels=1,material_type='MAKESKIN')
eyes.name='MPFB system eyes • CC0'

skin=material('Skin • painted ochre',(.52,.32,.17),0,.7)
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

# Tailored body-derived shells preserve MPFB weights and full three-dimensional anatomy.
cloth=material('Charcoal umber woven trousers',(.095,.073,.046),0,.86)
hair=material('Golden brown swept hair',(.20,.112,.043),0,.72)
strap=material('Worn boot leather',(.20,.115,.055),0,.75)
cream=material('Warm limestone E9CFA0',tuple(((c/255+.055)/1.055)**2.4 for c in (233,207,160)),0,.87)
pants=fitted_shell('GEO-folded wool trousers',lambda v:.16<v.z<.985,cloth,.032)
# Fold relief follows the original curved mesh and deforms with skin weights.
for v in pants.data.vertices:
    if v.co.z<.88:
        v.co += v.normal*(.005*sin(v.co.z*27+v.co.x*16)+.002*sin(v.co.z*51-v.co.y*19))
sub=pants.modifiers.new('Soft woven folds','SUBSURF');sub.levels=sub.render_levels=1
for side,sg in [('l',1),('r',-1)]:
    boot=fitted_shell('GEO-soft leather boot '+side,lambda v,s=sg:v.z<.245 and v.x*s>0,strap,.012)
    # Real ankle bindings. Coordinates are in the unposed body space.
    calf=rig.pose.bones['calf_'+side]; ankle=calf.tail.copy(); ankle.z+=.105
    for k in range(4):
        z=.15+.042*k
        pts=[(ankle.x+.074*cos(a)+.10,ankle.y+.072*sin(a),z+.015*cos(a+pi*k)) for a in [j*2*pi/56 for j in range(57)]]
        attach(curve('GEO-boot binding '+side+str(k),pts,.010,strap),'calf_'+side)
# A thick broad bronze/leather belt, with actual relief bosses, pin holes and edges.
verts=[];faces=[]
for j in range(3):
    for i in range(96):
        a=2*pi*i/96;verts.append((.10+.19*sin(a),-.139*cos(a),1.06+j*.031))
for j in range(2):
    for i in range(96):
        a=j*96+i;b=j*96+(i+1)%96;faces.append((a,b,b+96,a+96))
belt=solid(mesh('GEO-thick bronze belt',verts,faces,gold),.009);bevel(belt,.003);attach(belt,'pelvis')
for z in (1.06,1.122):
    attach(curve('GEO-belt rolled rim',[(.10+.194*sin(a),-.144*cos(a),z) for a in [j*2*pi/96 for j in range(97)]],.004,gold),'pelvis')
for a in (-1.2,-.6,0,.6,1.2):
    attach(sphere('GEO-belt medallion',(.10+.196*sin(a),-.151*cos(a),1.091),(.027,.009,.027),gold),'pelvis')
# Torc sits around the actual neck; its gold terminals are distinct geometry.
head=rig.pose.bones['head']; hc=(head.head+head.tail)*.5+rig.location
neck_z=head.head.z+.105-.035
pts=[]
for i in range(97):
    a=.36+(2*pi-.72)*i/96
    pts.append((.10+.113*sin(a),-.095*cos(a),neck_z-.075*cos(a)))
attach(curve('GEO-gold neck torc',pts,.017,gold),'spine_03')
for p in (pts[0],pts[-1]):attach(sphere('GEO-torc terminal',p,(.026,.024,.027),gold),'spine_03')
for i in range(35):
    a=.36+(2*pi-.72)*i/34; c=Vector((.10+.113*sin(a),-.095*cos(a),neck_z-.075*cos(a)))
    ps=[c+Vector((.019*cos(t)*sin(a),-.019*cos(t)*cos(a),.019*sin(t))) for t in [j*2*pi/16 for j in range(17)]]
    attach(curve('GEO-torc twist',ps,.0025,bronze),'spine_03')
# Scalp shell and swept, tapered locks, not a helmet or primitive head.
scalp=fitted_shell('GEO-sculpted scalp hair',lambda v:v.z>1.59 and (v.y>-.018 or v.z>1.68),hair,.010)
# Hair coordinates taken around MPFB head; curls trail behind and below the ears.
for k in range(38):
    a=-pi*.75+k/37*pi*1.5
    pts=[]
    for j in range(15):
        t=j/14;ang=a+.40*t
        pts.append((hc.x+.104*sin(ang)*(1+.17*t),hc.y+.108*cos(ang)+.065*t,hc.z+.09-.20*t+.012*sin(t*3*pi+k)))
    o=attach(curve('GEO-swept hair lock %02d'%k,pts,.010+(k%3)*.002,hair),'head')
# Drooping moustache, shaped on the mouth before the head turns.
for sg in (-1,1):
    ps=[(hc.x+sg*(.006+.057*t),hc.y-.101-.020*sin(pi*t),hc.z-.053-.036*t*t) for t in [j/18 for j in range(19)]]
    attach(curve('GEO-Celtic moustache',ps,.010,hair),'head')
    attach(curve('GEO-moustache highlight',[(x,y-.006,z+.006) for x,y,z in ps],.0025,gold),'head')
# Braced painting pose, with a raised spear hand.
limb('thigh_r','calf_r',(-.50,-.02,.075),(-.45,-.45,.5))
limb('thigh_l','calf_l',(.34,.02,.075),(.40,-.45,.5))
limb('upperarm_r','lowerarm_r',(-.48,-.08,1.64),(-.49,-.05,1.30))
limb('upperarm_l','lowerarm_l',(.37,-.29,1.10),(.45,-.02,1.30))
aim_bone('hand_r',(.03,0,.1))
# World rotation about the neck preserves its connection.
p=rig.pose.bones['head']; pivot=p.head.copy()
p.matrix=Matrix.Translation(pivot+Vector((.065,0,.005)))@Matrix.Rotation(.82,4,'Z')@Matrix.Diagonal((1.12,1.12,1.08,1))@Matrix.Translation(-pivot)@p.matrix
for side in ('r','l'):
    for digit in ('index','middle','ring','pinky'):
        for j in range(1,4):
            p=rig.pose.bones[f'{digit}_{j:02d}_{side}'];p.rotation_mode='XYZ';p.rotation_euler.x=.95 if j>1 else .65
bpy.context.view_layer.update()
# Stationary cream base, one unbroken low disc.
bpy.ops.mesh.primitive_cylinder_add(vertices=128,radius=.66,depth=.10,location=(.055,0,.05))
base=bpy.context.object;base.name='GEO-stationary cream stone';base.data.materials.append(cream);bevel(base,.016,3)
# Orthographic framing is locked for every stage and clip.
sc=bpy.context.scene
camd=bpy.data.cameras.new('CAM-painting');cam=bpy.data.objects.new('CAM-painting',camd);bpy.context.collection.objects.link(cam)
cam.location=(0,-7,3.05);target=Vector((0,0,.95));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();camd.type='ORTHO';camd.ortho_scale=2.25;sc.camera=cam
bpy.context.view_layer.update()
# Inverse orthographic mapping controls equipment composition without flattening it.
def screen(x,y,depth=0):
    q=cam.matrix_world.to_quaternion();right=q@Vector((1,0,0));up=q@Vector((0,1,0));view=q@Vector((0,0,1))
    return target+right*((x/256-.5)*2.25)+up*((.5-y/256)*2.25)+view*depth
# Convex shield: an elongated lenticular wooden body with metal rolled rim.
shield=bpy.data.objects.new('RIG-shield',None);bpy.context.collection.objects.link(shield)
center=screen(190,130,.22);right=cam.matrix_world.to_quaternion()@Vector((1,0,0));up=cam.matrix_world.to_quaternion()@Vector((0,1,0));normal=cam.matrix_world.to_quaternion()@Vector((0,0,1))
rx,rz=.215,.650
verts=[tuple(center+normal*.075)];faces=[]
for j in range(1,13):
    r=j/12
    for i in range(96):
        a=2*pi*i/96;verts.append(tuple(center+right*(rx*r*cos(a))+up*(rz*r*sin(a))+normal*(.075*(1-r*r))))
for i in range(96):faces.append((0,1+i,1+(i+1)%96))
for j in range(11):
    for i in range(96):
        a=1+j*96+i;b=1+j*96+(i+1)%96;faces.append((a,b,b+96,a+96))
face=solid(mesh('GEO-convex painted oval shield',verts,faces,red),.026);bevel(face,.004)
for o in [face]:o.parent=shield
rimpts=[center+right*(rx*cos(a))+up*(rz*sin(a)) for a in [i*2*pi/128 for i in range(129)]]
rim=curve('GEO-shield iron rim',rimpts,.013,iron);rim.parent=shield
for i in range(16):
    a=i*2*pi/16;p=center+right*((rx-.012)*cos(a))+up*((rz-.018)*sin(a))+normal*.018
    o=sphere('GEO-shield rim rivet',p,(.015,.015,.015),iron);o.parent=shield
boss=sphere('GEO-forged shield boss',center+normal*.095,(.076,.034,.102),iron);boss.rotation_euler=cam.rotation_euler;boss.parent=shield
# Real back handle, attached to hand along with entire convex assembly.
handle=curve('GEO-shield back grip',[center-right*.07-normal*.05,center-normal*.09,center+right*.07-normal*.05],.018,strap);handle.parent=shield
attach(shield,'hand_l')
# Spear lies diagonally above the hair, matching the painting's full silhouette.
weapon=bpy.data.objects.new('RIG-spear',None);bpy.context.collection.objects.link(weapon)
a=screen(44,65,.02);b=screen(162,23,.02);tip=screen(186,12,.02)
shaft=curve('GEO-ash spear shaft',[a,b],.009,wood);shaft.parent=weapon
v=(tip-b).normalized();cross=normal.cross(v).normalized()
vs=[tuple(b),tuple(b+(tip-b)*.36+cross*.047),tuple(tip),tuple(b+(tip-b)*.36-cross*.047),tuple(b+(tip-b)*.44+normal*.012),tuple(b+(tip-b)*.44-normal*.012)]
fs=[(0,1,4),(1,2,4),(2,3,4),(3,0,4),(1,0,5),(2,1,5),(3,2,5),(0,3,5)]
blade=mesh('GEO-iron leaf spearhead',vs,fs,iron,False);bevel(blade,.0015);blade.parent=weapon
socket=curve('GEO-spear socket',[b-v*.07,b+v*.025],.015,iron);socket.parent=weapon
attach(weapon,'hand_r')
# Move the grip to meet the actual shaft, preserving the overhead pose.
grip=screen(75,50,.02)
weapon_world=weapon.matrix_world.copy()
hand=rig.pose.bones['hand_r'];delta=grip-(rig.matrix_world@((hand.head+hand.tail)*.5))
limb('upperarm_r','lowerarm_r',rig.pose.bones['lowerarm_r'].tail+delta+Vector((.10,0,-.055)),(-.5,-.05,1.30))
# Restore weapon to its authored world-space line after that small hand correction.
bpy.context.view_layer.update()
weapon.matrix_world=weapon_world
bpy.context.view_layer.update()
# Area lights: warm upper-left key, soft cool fill, restrained cool rim.
for name,loc,power,size,color in [('key',(-3,-4,6),450,3,(1,.88,.70)),('fill',(3,-3,3),110,4,(.80,.88,1)),('rim',(2,3,4),210,2,(.76,.84,1))]:
    d=bpy.data.lights.new('LGT-'+name,'AREA');o=bpy.data.objects.new('LGT-'+name,d);bpy.context.collection.objects.link(o);o.location=loc;d.energy=power;d.shape='DISK';d.size=size;d.color=color;o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.65,.72,.85,1);sc.world.node_tree.nodes['Background'].inputs[1].default_value=.25
sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=8;sc.cycles.use_denoising=True;sc.cycles.max_bounces=4
sc.render.film_transparent=True;sc.render.resolution_x=sc.render.resolution_y=256;sc.render.resolution_percentage=100
sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.view_settings.view_transform='Standard'
sc.view_settings.look='None';sc.view_settings.exposure=0
# Materials are finished in the projection stage; preserve this plain checkpoint.
rig['neutral_pose']=json.dumps({p.name:[list(row) for row in p.matrix_basis] for p in rig.pose.bones})
sc['unit']='gaesatae';sc['method']='MPFB anatomy, full-depth clothes and shield, fixed rest camera'
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(MASTER/'plain.blend'))
(MASTER/'bones.json').write_text(json.dumps({p.name:{'head':list(p.head),'tail':list(p.tail)} for p in rig.pose.bones},indent=2))
print('GAESATAE_PLAIN_READY')
