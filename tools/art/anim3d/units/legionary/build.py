"""MPFB human, fitted legionary kit, editable rig and review scene. Run in Blender."""
import bpy, sys, os, math, json, random
from pathlib import Path
from mathutils import Vector, Matrix, Quaternion
from math import sin, cos, pi
ROOT = Path(os.environ.get('ANIM_ROOT', str(Path.home()/'LegatumRuns/anim-pilot')))
MASTER = ROOT/'masters/legionary'
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
body.scale=(1.78/(zhi-zlo)*1.03,1.78/(zhi-zlo),1.78/(zhi-zlo))
bpy.context.view_layer.objects.active=body; body.select_set(True)
bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
rig=HumanService.add_builtin_rig(body,'game_engine'); rig.name='Legionary MPFB game_engine'
rig.location.z=.105
system_data=ROOT/'blender-user/extensions/.user/user_default/mpfb/data'
eyes=HumanService.add_mhclo_asset(str(system_data/'eyes/high-poly/high-poly.mhclo'),body,asset_type='Eyes',subdiv_levels=1,material_type='MAKESKIN')
eyes.name='MPFB system eyes • CC0'

skin=material('Skin • warm ochre',(.44,.235,.115),0,.6)
bronze=material('Bronze • hammered',(.50,.29,.09),1,.34)
gold=material('Bronze • polished edges',(.83,.56,.20),1,.26)
dark=material('Incised bronze patina',(.075,.047,.017),.55,.65)
red=material('Cinnabar wool',(.27,.018,.008),0,.83)
linen=material('Warm ivory linen',(.72,.61,.42),0,.88)
leather=material('Oxide leather',(.12,.040,.015),0,.7)
iron=material('Forged iron',(.55,.58,.59),1,.32)
wood=material('Ash spear shaft',(.52,.25,.075),0,.57)
stone=material('Cream limestone',(.80,.59,.32),0,.86)
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
    # Evaluated topology carries interpolated skin groups. Nearest *unmorphed*
    # vertices assigned sleeves to the wrong segment and lifted red fabric over
    # the shoulder when the weapon arm bent.
    for g in body.vertex_groups:
        if g.name in rig.data.bones: ob.vertex_groups.new(name=g.name)
    for j,i in enumerate(ids):
        for g in me.vertices[i].groups:
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
# Original Roman equipment, fitted to the human rather than a recoloured hoplite.
def ring(name,z,rx,ry,height,mat,bone='spine_03'):
    vs=[]; fs=[]; n=64
    for k in range(3):
        for i in range(n):
            a=i*2*pi/n; vs.append((rx*sin(a),-ry*cos(a),z+height*k/2))
    for k in range(2):
        for i in range(n):a=k*n+i;b=k*n+(i+1)%n;fs.append((a,b,b+n,a+n))
    o=solid(mesh(name,vs,fs,mat),.008);bevel(o,.003,3);attach(o,bone);return o
for j in range(7):
    z=1.115+j*.052;rx=.205+.053*sin(j/9*pi*.65);ry=.165+.035*sin(j/9*pi*.65)
    ring('GEO-lorica iron band %02d'%j,z,rx,ry,.048,iron)
    attach(curve('GEO-lorica bright rolled edge',[(rx*sin(a),-ry*cos(a)-.002,z+.045) for a in [i*2*pi/96 for i in range(97)]],.0028,iron),'spine_03')
    for x in [-.045,.045]:
        attach(sphere('GEO-lorica brass fastener',(x,-ry-.010,z+.024),(.008,.005,.008),gold),'spine_03')
        attach(curve('GEO-lorica leather hinge',[(x,-ry-.005,z+.012),(x,-ry-.005,z+.040)],.010,leather),'spine_03')
fitted_shell('GEO-lorica upper cuirass',lambda v: 1.32<v.z<1.46 and abs(v.x)<.255,iron,.018)
fitted_shell('GEO-red tunic sleeves',lambda v: 1.32<v.z<1.49 and .18<abs(v.x)<.38,red,.012)
# Layered shoulder lames: thick curved plates, rolled edges, distinct overlaps.
for sg,side in [(-1,'r'),(1,'l')]:
    for j in range(4):
        x=sg*(.18+.035*j);vs=[]
        for k in range(3):
            for i in range(17):
                a=-1.25+2.5*i/16;vs.append((x+sg*k*.017,-.155*sin(a),1.45+.100*cos(a)-j*.023))
        fs=[(k*17+i,k*17+i+1,(k+1)*17+i+1,(k+1)*17+i) for k in range(2) for i in range(16)]
        # The shoulder yoke hangs from the cuirass, not the rotating humerus.
        # Binding this rest-space cap to the A-pose upper arm flipped it upright.
        o=solid(mesh('GEO-shoulder articulated lame '+side,vs,fs,iron),.007);bevel(o,.003);attach(o,'spine_03')
        attach(curve('GEO-shoulder rolled edge '+side,vs[-17:],.003,iron),'spine_03')
# Folded red tunic skirt, continuous volume with thickness and flared hem.
vs=[];fs=[]; n=80
for j in range(9):
    t=j/8
    for i in range(n):
        a=i*2*pi/n;fold=.012*sin(a*14)*(.25+.75*t);vs.append(((.19+.065*t+fold)*sin(a),-(.14+.055*t+fold)*cos(a),1.12-.32*t+.009*cos(a*7)*t))
for j in range(8):
    for i in range(n):a=j*n+i;b=j*n+(i+1)%n;fs.append((a,b,b+n,a+n))
skirt=solid(mesh('GEO-folded red wool tunic',vs,fs,red),.004);attach(skirt,'pelvis')
su=skirt.modifiers.new('Soft cloth folds','SUBSURF');su.levels=1
ring('GEO-leather cingulum belt',1.105,.204,.153,.045,leather,'pelvis')
# Five hanging studded leather apron strips, each truly three dimensional.
for j in range(5):
    x=(j-2)*.034; vs=[]
    for k in range(9):
        t=k/8
        for side in [-1,1]:vs.append((x+side*.013,-.165-.045*t-.008*sin(t*pi),1.11-.28*t))
    fs=[(k*2,k*2+1,k*2+3,k*2+2) for k in range(8)]
    o=solid(mesh('GEO-studded leather apron',vs,fs,leather),.005);bevel(o,.002);attach(o,'pelvis')
    for k in range(6):
        t=k/5;attach(sphere('GEO-apron bronze stud',(x,-.177-.045*t,1.09-.24*t),(.007,.004,.008),gold),'pelvis')
for j in range(20):
    a=j*2*pi/20;attach(sphere('GEO-belt stud',(.207*sin(a),-.158*cos(a),1.13),(.008,.006,.009),gold),'pelvis')
# Open Imperial-style bronze helmet bowl, neck guard and separate cheek pieces.
hc=(rig.pose.bones['head'].head+rig.pose.bones['head'].tail)*.5;cx,cy,cz=hc;cz+=.105
vs=[];fs=[]
for j in range(17):
    t=j/16*pi/2
    for i in range(64):
        a=i*2*pi/64;vs.append((cx+.110*cos(t)*sin(a),cy-.119*cos(t)*cos(a),cz+.022+.133*sin(t)))
for j in range(16):
    for i in range(64):a=j*64+i;b=j*64+(i+1)%64;fs.append((a,b,b+64,a+64))
helmet=solid(mesh('GEO-bronze helmet bowl',vs,fs,bronze),.006);bevel(helmet,.003);attach(helmet,'head')
for z in [cz+.025,cz+.048]:attach(curve('GEO-helmet brow band',[(.112*sin(a),cy-.122*cos(a),z) for a in [-pi+2*pi*i/96 for i in range(97)]],.005,gold),'head')
for sg in [-1,1]:
    vs=[(sg*.100,cy-.056,cz+.025),(sg*.078,cy-.116,cz+.013),(sg*.067,cy-.121,cz-.106),(sg*.105,cy-.045,cz-.081)]
    o=solid(mesh('GEO-hinged bronze cheekguard',vs,[(0,1,2,3)],bronze),.008);bevel(o,.008,3);attach(o,'head')
    attach(curve('GEO-cheekguard border',vs+[vs[0]],.003,gold),'head')
    attach(sphere('GEO-cheekguard hinge',(sg*.110,cy-.055,cz+.018),(.010,.010,.010),gold),'head')
vs=[]
for rr in [.10,.16]:
    for i in range(33):a=pi/2+i*pi/32;vs.append((rr*sin(a),cy-rr*cos(a),cz-.028-(rr-.1)*.42))
o=solid(mesh('GEO-flared bronze neckguard',vs,[(i,i+1,i+34,i+33) for i in range(32)],bronze),.005);bevel(o,.004);attach(o,'head')

# Linen neck scarf and tied ends, above the metal collar.
for j in range(4):
    attach(curve('GEO-linen scarf fold',[(.105*sin(a),-.105*cos(a)-.015,1.665+.012*j-.025*cos(a)) for a in [i*2*pi/64 for i in range(65)]],.014,linen),'spine_03')
for sg in [-1,1]:
    o=solid(mesh('GEO-linen scarf knot tail',[(sg*.01,-.139,1.68),(sg*.052,-.155,1.62),(sg*.04,-.197,1.52),(sg*.008,-.19,1.55)],[(0,1,2,3)],linen),.008);bevel(o,.006);attach(o,'spine_03')

# Sandals with real soles, crossing straps and ankle straps.
for sg,side in [(1,'l'),(-1,'r')]:
    foot=rig.pose.bones['foot_'+side];x=foot.head.x;y=foot.head.y
    outline=[(x+.060*cos(a),y-.07+.140*sin(a),.112) for a in [i*2*pi/48 for i in range(48)]]
    o=solid(mesh('GEO-sandal sole '+side,outline,[tuple(range(48))],leather),.017);bevel(o,.005);attach(o,'foot_'+side)
    for yy in [-.16,-.12,-.08,-.025,.02]:
        pts=[(x+.057*cos(a),y+yy,.132+.052*sin(a)) for a in [i*pi/20 for i in range(21)]]
        attach(curve('GEO-sandal strap '+side,pts,.005,leather),'foot_'+side)
    for z in [.19,.23]:attach(curve('GEO-ankle strap '+side,[(x+.045*sin(a),y+.045*cos(a),z) for a in [i*2*pi/32 for i in range(33)]],.0045,leather),'foot_'+side)
# Rest: planted feet and right hand holding the long pilum clear of the torso.
rig.location.z=.085
limb('thigh_r','calf_r',(-.16,-.06,.082),(-.22,-.31,.48))
limb('thigh_l','calf_l',(.18,.035,.082),(.23,-.28,.48))
limb('upperarm_r','lowerarm_r',(-.365,-.19,1.28),(-.60,0,.80))
# The fingers need clearance behind the convex shell, not only a wrist behind it.
limb('upperarm_l','lowerarm_l',(.30,-.24,1.10),(.44,-.02,1.12))
for side in ['r','l']:
    aim_bone('hand_'+side,(0,-.025,.09))
    for digit in ['index','middle','ring','pinky']:
        for k in range(1,4):
            p=rig.pose.bones[f'{digit}_{k:02d}_{side}'];p.rotation_mode='XYZ';p.rotation_euler.x=1.05
bpy.context.view_layer.update()
# Oppose the thumb around the shaft; leaving the MPFB rest thumb made an open hand.
for name,target in [('thumb_01_r',(-.357,-.224,1.351)),('thumb_02_r',(-.375,-.232,1.371)),('thumb_03_r',(-.379,-.214,1.374))]:
    aim_bone(name,Vector(target)-rig.pose.bones[name].head)
grip=rig.matrix_world @ rig.pose.bones['hand_r'].head+Vector((.020,-.044,.068))
def control(name,loc,bone):
    o=bpy.data.objects.new(name,None);bpy.context.collection.objects.link(o);o.location=loc;attach(o,bone);return o
def parent_world(o,parent):
    bpy.context.view_layer.update();m=o.matrix_world.copy();o.parent=parent;o.parent_type='OBJECT';o.matrix_world=m;return o
pilum=control('Pilum control',grip,'hand_r')
parent_world(curve('GEO-pilum ash shaft',[grip+Vector((.10,0,-1.26)),grip+Vector((-.035,0,.12))],.014,wood),pilum)
parent_world(curve('GEO-pilum long iron shank',[grip+Vector((-.035,0,.12)),grip+Vector((-.080,0,.50))],.0065,iron),pilum)
parent_world(curve('GEO-pilum socket',[grip+Vector((-.028,0,.05)),grip+Vector((-.040,0,.18))],.017,bronze),pilum)
sv=[grip+Vector(v) for v in [(-.092,-.01,.50),(-.068,-.01,.50),(-.08,.01,.50),(-.083,0,.57)]]
parent_world(mesh('GEO-pilum pyramidal point',sv,[(0,1,3),(1,2,3),(2,0,3),(2,1,0)],iron,False),pilum)
# Convex rectangular scutum, not a flat painted card.
center=Vector((.40,-.36,1.20));shield=control('Scutum control',center,'lowerarm_l')
def shield_point(x,z,depth=0):
    # Rounded end grain and a narrower convex face match the painted scutum.
    rounded=z-math.copysign(.060*(x/.235)**2*(abs(z)/.485)**8,z)
    return center+Vector((x*.95,-.085*(1-(x/.235)**2)-depth,rounded))
vs=[];fs=[];nx=64;nz=100
for j in range(nz+1):
    for i in range(nx+1):
        x=(i/nx-.5)*.47;z=(j/nz-.5)*.97;vs.append(shield_point(x,z))
for j in range(nz):
    for i in range(nx):a=j*(nx+1)+i;fs.append((a,a+1,a+nx+2,a+nx+1))
scutum=solid(mesh('GEO-scutum painted convex wood',vs,fs,red),.016);bevel(scutum,.006);parent_world(scutum,shield)
for z in [-.485,.485]:parent_world(curve('GEO-scutum bronze rim',[shield_point((i/48-.5)*.47,z,.006) for i in range(49)],.010,gold),shield)
for x in [-.235,.235]:parent_world(curve('GEO-scutum bronze rim',[shield_point(x,(i/48-.5)*.97,.006) for i in range(49)],.010,gold),shield)
parent_world(sphere('GEO-scutum iron umbo',shield_point(.105,0,.035),(.075,.049,.09),iron),shield)
# Wing and lightning relief is sampled from the painting in paint.py, matching the brushwork.
# Bone-held sword scabbard, visible on the right hip.
attach(curve('GEO-gladius leather scabbard',[(-.21,.04,1.09),(-.26,-.015,.69)],.026,leather),'pelvis')
attach(curve('GEO-gladius grip',[(-.20,.05,1.09),(-.19,.055,1.20)],.017,linen),'pelvis')
attach(sphere('GEO-gladius pommel',(-.19,.055,1.20),(.029,.023,.024),gold),'pelvis')
# Same warm cream disc across every frame, no podium or extra tier.
bpy.ops.mesh.primitive_cylinder_add(vertices=128,radius=.465,depth=.085,location=(-.018,0,.0425))
base=bpy.context.object;base.name='Stationary cream stone';base.data.materials.append(stone);bevel(base,.012,3)
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=8;sc.cycles.use_denoising=True
sc.render.resolution_x=sc.render.resolution_y=256;sc.render.resolution_percentage=100
sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.fps=24
sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.35,.39,.45,1);sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.35
sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast'
bpy.ops.object.camera_add(location=(1.9,-8,3.44));sc.camera=bpy.context.object;sc.camera.name='CAM-legionary painting';sc.camera.data.type='ORTHO';sc.camera.data.ortho_scale=2.20
sc.camera.rotation_euler=(Vector((0,0,.915))-sc.camera.location).to_track_quat('-Z','Y').to_euler()
for name,loc,power,size,col in [('LGT-warm key',(-3,-4,6),650,2,(1,.89,.73)),('LGT-soft fill',(4,-2,3),170,3,(.86,.92,1)),('LGT-cool rim',(-2,3,4),400,2,(.75,.86,1))]:
    bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name=name;o.data.energy=power;o.data.size=size;o.data.color=col;o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
p=rig.pose.bones['head']; mat=p.matrix.copy(); pivot=p.head.copy(); p.matrix=Matrix.Translation(pivot) @ Matrix.Rotation(.65,4,'Z') @ Matrix.Translation(-pivot) @ mat
mat=p.matrix.copy();mat.translation.z-=.060;p.matrix=mat
bpy.context.view_layer.update()
shield.matrix_world=Matrix.Translation(center) @ Matrix.Rotation(-.13,4,'Y') @ Matrix.Translation(-center) @ shield.matrix_world
for side in ['r','l']:
    aim_bone('foot_'+side,(0,-.12,-.025));aim_bone('ball_'+side,(0,-1,0))
rig.location.z+=.018
bpy.context.view_layer.update()
# Fit straps to the actual posed skin rather than assumed anatomical coordinates.
# Freeze their local mesh points after this fit; future motion remains skeletal.
from mathutils.bvhtree import BVHTree
dg=bpy.context.evaluated_depsgraph_get();ev=body.evaluated_get(dg);me=ev.to_mesh()
verts=[ev.matrix_world @ v.co for v in me.vertices]
tree=BVHTree.FromPolygons(verts,[list(p.vertices) for p in me.polygons])
for ob in list(bpy.context.scene.objects):
    if not ob.name.startswith(('GEO-sandal strap','GEO-ankle strap')):continue
    inverse=ob.matrix_world.inverted()
    for spline in ob.data.splines:
        for point in spline.points:
            world=ob.matrix_world @ Vector(point.co[:3]);hit,normal,_,distance=tree.find_nearest(world)
            if hit is not None:
                local=inverse @ (hit+normal*.004);point.co=(*local,1)
# Sandal leather follows the same calf/foot/toe skin weights as the anatomy.
# A rigid foot-parent left toe straps floating as the captured toes rolled.
from mathutils.kdtree import KDTree
kd=KDTree(len(verts))
for i,v in enumerate(verts):kd.insert(v,i)
kd.balance()
for ob in list(bpy.context.scene.objects):
    if not ob.name.startswith(('GEO-sandal','GEO-ankle strap')):continue
    bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
    if ob.type=='CURVE':bpy.ops.object.convert(target='MESH');ob=bpy.context.object
    for mod in list(ob.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
    world=ob.matrix_world.copy();positions=[world @ v.co for v in ob.data.vertices]
    weights=[]
    for position in positions:
        _,idx,_=kd.find(position)
        w={body.vertex_groups[g.group].name:g.weight for g in me.vertices[idx].groups if body.vertex_groups[g.group].name in rig.data.bones and g.weight>1e-5}
        total=sum(w.values());assert total>0,'Missing anatomical sandal weights';weights.append({n:v/total for n,v in w.items()})
    ob.parent=rig;ob.parent_type='OBJECT';ob.matrix_parent_inverse=Matrix.Identity(4);ob.matrix_basis=Matrix.Identity(4)
    for name in sorted({n for w in weights for n in w}):ob.vertex_groups.new(name=name)
    for v,position,w in zip(ob.data.vertices,positions,weights):
        transform=Matrix([[0.0]*4 for _ in range(4)])
        for name,weight in w.items():
            transform+=(rig.pose.bones[name].matrix @ rig.data.bones[name].matrix_local.inverted())*weight
            ob.vertex_groups[name].add([v.index],weight,'REPLACE')
        v.co=transform.inverted() @ (rig.matrix_world.inverted() @ position)
    mod=ob.modifiers.new('Anatomical sandal toe and ankle weights','ARMATURE');mod.object=rig
body.evaluated_get(dg).to_mesh_clear()
rig['neutral_pose']=json.dumps({p.name:[list(row) for row in p.matrix_basis] for p in rig.pose.bones})
sc['unit']='legionary';sc['source']='MPFB 2.0.18 CC0 anatomy; original Roman kit; project painting'
(MASTER/'model-info.json').write_text(json.dumps({'body_vertices':len(body.data.vertices),'bones':len(rig.data.bones),'objects':len(sc.objects),'head_center':[cx,cy,cz]},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(MASTER/'legionary-plain.blend'))
print('MODEL_READY',MASTER)
