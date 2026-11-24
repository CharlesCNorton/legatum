"""MPFB human, fitted hoplite kit, editable rig and review scene. Run in Blender."""
import bpy, sys, os, math, json, random
from pathlib import Path
from mathutils import Vector, Matrix, Quaternion
from math import sin, cos, pi
sys.path.insert(0, str(Path(__file__).resolve().parent))
from kit.human import create_body, add_rig
ROOT = Path(os.environ.get('ANIM_ROOT', str(Path.home()/'LegatumRuns/anim-pilot')))
MASTER = ROOT/'masters/spearman-3d-v2'
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
body=create_body(dict(gender=1.0,age=.42,muscle=1.0,weight=.72,height=.42,proportions=.65,
                      race={'caucasian':.75,'african':.15,'asian':.10}),
                 'MPFB anatomical male • original topology')
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
rig=add_rig(body, 'Spearman • MPFB game_engine')
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
# Forged muscle cuirass: a closed fitted shell with deliberately articulated plates.
# This is armour around the MPFB body, never replacement body geometry.
vs=[];fs=[];rings=28;segments=80
for j in range(rings+1):
    t=j/rings;z=1.035+.405*t
    rx=.193+.054*sin(t*pi*.8);ry=.139+.028*sin(t*pi)
    for i in range(segments):
        a=i*2*pi/segments;x=rx*sin(a);front=max(0,cos(a))
        pec=.030*math.exp(-((abs(x)-.102)/.080)**2-((z-1.24)/.075)**2)
        ab=.014*(.5+.5*cos((z-1.10)*55))*math.exp(-(x/.12)**4)
        y=-ry*cos(a)-(pec+ab)*front**3
        # Neck opening dips, armpits cut below the shoulder sleeve.
        zz=z-.055*t**8*(abs(sin(a))**3)-.025*t**8*front
        vs.append((x,y,zz+.105))
for j in range(rings):
    for i in range(segments):a=j*segments+i;b=j*segments+(i+1)%segments;fs.append((a,b,b+segments,a+segments))
cuirass=solid(mesh('Forged bronze muscle cuirass',vs,fs,bronze),.009);bevel(cuirass,.003);attach(cuirass,'spine_03')
for j in [0,rings]:
    pts=vs[j*segments:(j+1)*segments];attach(curve('Cuirass rolled border',pts+[pts[0]],.005,gold),'spine_03')
def cuirass_front(x,z):
    t=max(0,min(1,(z-.105-1.035)/.405));rx=.193+.054*sin(t*pi*.8);ry=.139+.028*sin(t*pi)
    front=math.sqrt(max(.02,1-(x/rx)**2))
    pec=.030*math.exp(-((abs(x)-.102)/.080)**2-((z-.105-1.24)/.075)**2)
    ab=.014*(.5+.5*cos((z-.105-1.10)*55))*math.exp(-(x/.12)**4)
    return -ry*front-(pec+ab)*front**3-.003
for sg in [-1,1]:
    pts=[(sg*(.015+.18*k/24),-.17-.026*sin(k*pi/24),1.385-.045*sin(k*pi/24)) for k in range(25)]
    pts=[(x,cuirass_front(x,z),z) for x,y,z in pts]
    attach(curve('Pectoral chased groove',pts,.003,dark),'spine_03')
    attach(curve('Pectoral bright lip',[(x,y-.003,z-.005) for x,y,z in pts],.002,gold),'spine_03')
for side in ('l','r'):
    sign=1 if side=='l' else -1
    fitted_shell('Contoured greave '+side,lambda v,s=sign: .105<v.z<.48 and v.x*s>.07 and v.y<.025,bronze,.011)
fitted_shell('Linen tunic shoulder sleeves',lambda v: 1.22<v.z<1.48 and .18<abs(v.x)<.35,linen,.008)
for side,sg in [('l',1),('r',-1)]:
    for z in [.30,.40,.50]:
        x=sg*(.185-(z-.1)*.12)
        pts=[(x+.018*cos(a),-.095-.004*sin(a),z+.105+.025*sin(a)) for a in [i*1.8*pi/32 for i in range(33)]]
        attach(curve('Greave chased spiral '+side,pts,.0025,gold),'calf_'+side)
# Pteruges: overlapping curved strips, fitted at waist with lower flared hem.
for j in range(18):
    a=2*pi*j/18; vs=[]
    for k in range(9):
        t=k/8; z=1.025-.29*t; rx=.18+.075*t; ry=.125+.050*t
        for s in (-1,0,1):
            aa=a+s*.17; wave=.005*sin(t*pi*3+j)
            vs.append(((rx+wave)*sin(aa),-(ry+wave)*cos(aa),z+.105))
    fs=[(k*3+i,k*3+i+1,(k+1)*3+i+1,(k+1)*3+i) for k in range(8) for i in range(2)]
    o=mesh('Linen pteruges %02d'%j,vs,fs,linen); solid(o,.004); attach(o,'pelvis')
    # Gold stitch line at each hem.
    attach(curve('Pteruges hem',vs[-3:],.002,linen),'pelvis')
# Waist and shoulder straps.
for side in [-1,1]:
    for z in [1.20,1.29,1.38]:
        pts=[(side*(.075+.026*cos(a)), -.151-.014*sin(a), z+.027*sin(a)) for a in [i*pi*1.6/28 for i in range(29)]]
        pts=[(x,cuirass_front(x,z)-.002,z) for x,y,z in pts]
        attach(curve('Chased cuirass volute',pts,.003,gold),'spine_03')
for z in [1.08,1.105]:
    attach(curve('Cuirass waist rolled edge',[(.19*sin(a),-.14*cos(a),z) for a in [i*2*pi/96 for i in range(97)]],.009,gold),'spine_01')
attach(curve('Leather baldric',[(-.16,-.115,1.46),(-.07,-.17,1.29),(.15,-.14,1.12)],.024,leather),'spine_03')
for z in [1.13,1.20,1.27,1.34]:attach(sphere('Baldric rivet',(.15-(z-1.12)*1.02,-.172,z),(.007,.004,.007),gold),'spine_03')
# Helmet: open bowl plus true negative-space eye openings / separate cheek guards.
head=rig.pose.bones['head']; hz=head.head.z+.105
hc=(head.head+head.tail)*.5; cx=hc.x; cy=hc.y; cz=hc.z+.105
verts=[]; faces=[]
for j in range(13):
    t=(j/12)*pi/2
    for i in range(64):
        a=i*2*pi/64; verts.append((cx+.108*cos(t)*sin(a),cy-.118*cos(t)*cos(a),cz+.020+.13*sin(t)))
for j in range(12):
    for i in range(64):a=j*64+i;b=j*64+(i+1)%64;faces.append((a,b,b+64,a+64))
attach(solid(mesh('Corinthian helmet crown',verts,faces,bronze),.006),'head')
attach(curve('Raised brow',[(cx+.108*sin(a),cy-.120*cos(a),cz+.020) for a in [(-pi+2*pi*i/80) for i in range(81)]],.006,gold),'head')
# Shallow chased bands and rivets follow the bowl, below the horsehair saddle.
for band in [.26,.52]:
    pts=[]
    for i in range(97):
        a=-1.35+2.7*i/96;t=band+.035*sin(a*18)
        pts.append((cx+.110*cos(t)*sin(a),cy-.120*cos(t)*cos(a),cz+.021+.132*sin(t)))
    attach(curve('Helmet chased wave',pts,.0018,dark),'head')
for i in range(11):
    a=-1.25+.25*i;t=.14
    attach(sphere('Helmet brow rivet',(cx+.110*cos(t)*sin(a),cy-.120*cos(t)*cos(a),cz+.021+.132*sin(t)),(.003,.003,.003),gold),'head')
# Curved faceplate and real apertures are built by helmet.py in the build stage.
# Red horsehair fan with individually ridged tufts, curved front to back.
for i in range(63):
    a=-1.15+i/62*2.95
    y=cy+.142*sin(a); z=cz+.015+.150*cos(a)
    yo=cy+.315*sin(a); zo=cz+.015+.360*cos(a)
    pts=[(-.023,y,z),(.023,y,z),(.018,yo,zo),(-.018,yo,zo)]
    o=mesh('Horsehair crest tuft',pts,[(0,1,2,3)],red,False);solid(o,.006);attach(o,'head')
attach(curve('Crest bronze saddle',[(0,cy+.144*sin(a),cz+.015+.153*cos(a)) for a in [-1.15+i/60*2.95 for i in range(61)]],.014,gold),'head')
# Sandals on real MPFB feet, leather straps over instep.
for s,side in [(1,'l'),(-1,'r')]:
    foot=rig.pose.bones['foot_'+side]; x=foot.head.x; y=foot.head.y
    outline=[(x+.061*cos(a),y-.07+.142*sin(a),.112) for a in [2*pi*i/48 for i in range(48)]]
    sole=mesh('Leather sandal sole '+side,outline,[tuple(range(48))],leather);solid(sole,.018);bevel(sole,.007);attach(sole,'foot_'+side)
    for yy in [-.17,-.12,-.07,.015]:
        pts=[(x+.058*cos(a),y+yy,.127+.048*sin(a)) for a in [i*pi/16 for i in range(17)]]
        attach(curve('Sandal strap '+side,pts,.009,leather),'foot_'+side)
# Set natural guard stance before attaching held kit.
rig.location.z=.085
limb('thigh_r','calf_r',(-.32,-.075,.082),(-.34,-.40,.48))
limb('thigh_l','calf_l',(.32,.035,.082),(.34,-.36,.48))
limb('upperarm_r','lowerarm_r',(-.37,-.31,1.19),(-.55,-.04,1.15))
limb('upperarm_l','lowerarm_l',(.29,-.34,1.12),(.53,-.10,1.13))
for side in ('r','l'):
    aim_bone('hand_'+side,(0,-.03,.09))
    for digit in ['index','middle','ring','pinky']:
        for k in range(1,4):
            p=rig.pose.bones[f'{digit}_{k:02d}_{side}']; p.rotation_mode='XYZ'; p.rotation_euler.x=1.1
bpy.context.view_layer.update()
# Spear aligned through right palm; hand-relative attachment preserves grip.
grip=rig.pose.bones['hand_r'].head+rig.location+Vector((0,-.012,.047))
shaft=curve('Ash dory shaft',[tuple(grip+Vector((0,0,-1.24))),tuple(grip+Vector((0,0,1.06)))],.013,wood);attach(shaft,'hand_r')
for zz in [.98,1.03]: attach(curve('Spear bronze ferrule',[tuple(grip+Vector((0,0,zz))),tuple(grip+Vector((0,0,zz+.035)))],.019,gold),'hand_r')
sv=[tuple(grip+Vector(v)) for v in [(-.045,0,1.06),(0,-.012,1.07),(.045,0,1.06),(0,0,1.25),(0,.012,1.07),(0,0,1.005)]]
attach(mesh('Leaf spearhead with medial ridge',sv,[(0,1,3),(1,2,3),(2,4,3),(4,0,3),(0,5,1),(1,5,2),(2,5,4),(4,5,0)],iron,False),'hand_r')
attach(curve('Iron spear butt',[tuple(grip+Vector((0,0,-1.24))),tuple(grip+Vector((0,0,-1.16)))],.015,iron),'hand_r')
# Aspis curved shell, raised radial sunburst, concentric engraved rim.
center=Vector((.30,-.38,1.19)); rad=.395
vs=[tuple(center+Vector((0,-.085,0)))]; fs=[]
for j in range(1,13):
    r=rad*j/12; depth=-.085*(1-(r/rad)**2)
    for i in range(96):a=2*pi*i/96;vs.append(tuple(center+Vector((r*sin(a),depth,r*cos(a)))))
for i in range(96):fs.append((0,1+(i+1)%96,1+i))
for j in range(11):
    for i in range(96):a=1+j*96+i;b=1+j*96+(i+1)%96;fs.append((a,a+96,b+96,b))
attach(solid(mesh('Convex bronze aspis',vs,fs,bronze),.012),'lowerarm_l')
for rr in [rad,rad-.022,.087]:
    pts=[tuple(center+Vector((rr*sin(a),-.009-.085*(1-(rr/rad)**2),rr*cos(a)))) for a in [2*pi*i/128 for i in range(129)]]
    attach(curve('Aspis turned rim',pts,.005 if rr<rad else .009,gold),'lowerarm_l')
for i in range(12):
    a=2*pi*i/12; r=.315 if i%2==0 else .275
    pts=[tuple(center+Vector((rr*sin(aa),-.099+.07*(rr/rad)**2,rr*cos(aa)))) for rr,aa in [(.081,a-.21),(r,a),(.081,a+.21),(.15,a)]]
    # A raised keel, two distinct facets and side walls catch light at token size.
    pts[3]=tuple(Vector(pts[3])+Vector((0,-.040,0)))
    ray=solid(mesh('Sunburst raised ray',pts,[(0,1,3),(1,2,3),(2,0,3)],gold,False),.009)
    bevel(ray,.0015);attach(ray,'lowerarm_l')
attach(sphere('Aspis central omphalos',tuple(center+Vector((0,-.104,0))),(.072,.035,.072),gold),'lowerarm_l')
for i in range(48):
    a=2*pi*i/48;attach(sphere('Aspis rim stud',tuple(center+Vector((.34*sin(a),-.016,.34*cos(a)))),(.0035,.003,.0035),gold),'lowerarm_l')
for i in range(36):
    a=2*pi*i/36
    pts=[tuple(center+Vector((rr*sin(aa),-.028,rr*cos(aa)))) for rr,aa in [(.367,a-.035),(.375,a),(.367,a+.035)]]
    attach(curve('Aspis chased chevron',pts,.0018,dark),'lowerarm_l')
# Turn the aspis about its center, preserving thickness.
for ob in list(bpy.context.scene.objects):
    if any(x in ob.name for x in ['aspis','Aspis','Sunburst']):
        ob.matrix_world=Matrix.Translation(center+Vector((.12,0,0))) @ Matrix.Rotation(-.40,4,'Z') @ Matrix.Diagonal((.92,1,1.08,1)) @ Matrix.Translation(-center) @ ob.matrix_world
# One editable aspis control, still bone attached, can be released during death.
shield_objects=[ob for ob in list(bpy.context.scene.objects) if any(x in ob.name for x in ['aspis','Aspis','Sunburst'])]
shield_control=bpy.data.objects.new('Aspis control',None);bpy.context.collection.objects.link(shield_control);shield_control.location=center;attach(shield_control,'lowerarm_l')
for ob in shield_objects:
    world=ob.matrix_world.copy();ob.parent=shield_control;ob.parent_type='OBJECT';ob.matrix_world=world
# Real cloth mesh: shoulder-pinned wool, initial broad folds, later baked per clip.
vs=[];fs=[]; nx=24;ny=32
for j in range(ny+1):
    t=j/ny
    for i in range(nx+1):
        u=i/nx; x=(u-.5)*(.46+.46*t); y=.095+.11*t+.026*sin(u*pi*12)*(.2+.8*t)
        z=1.51-1.16*t+.025*cos(u*pi*4)*t
        vs.append((x,y,z))
for j in range(ny):
    for i in range(nx):a=j*(nx+1)+i;fs.append((a,a+1,a+nx+2,a+nx+1))
cloak=mesh('Cloak • simulated wool',vs,fs,red)
pin=cloak.vertex_groups.new(name='Shoulder pins');pin.add(list(range(nx+1)),1,'REPLACE')
vg=cloak.vertex_groups.new(name='spine_03');vg.add(list(range(len(vs))),1,'REPLACE')
cloak.parent=rig;ar=cloak.modifiers.new('Follow shoulders','ARMATURE');ar.object=rig
cloth=cloak.modifiers.new('Cloth per clip','CLOTH'); cloth.settings.quality=6;cloth.settings.mass=.24
cloth.settings.vertex_group_mass=pin.name;cloth.settings.tension_stiffness=25;cloth.settings.compression_stiffness=25;cloth.settings.shear_stiffness=10;cloth.settings.bending_stiffness=.4
cloth.collision_settings.use_self_collision=True;cloth.collision_settings.self_distance_min=.008
cloth.collision_settings.distance_min=.012
solid(cloak,.004);su=cloak.modifiers.new('Wool smoothness','SUBSURF');su.levels=1
# Body is a cloth collider; baked output is retained outside git.
body.modifiers.new('Cloak collision','COLLISION')
for x in [-.16,.16]:attach(sphere('Cloak clasp',(x,-.09,1.53),(.022,.01,.022),gold),'spine_03')
# Collar folds connect the shoulder pins around the neck.
for j in range(4):
    pts=[(.18*sin(a),-.18*cos(a),1.60-.012*j-.034*cos(a)) for a in [-pi/2+i*pi/32 for i in range(33)]]
    attach(curve('Crimson collar fold',pts,.014,red),'spine_03')
# Base is one immutable pale cream stone disc.
bpy.ops.mesh.primitive_cylinder_add(vertices=128,radius=.60,depth=.09,location=(0,0,.045))
base=bpy.context.object;base.name='Stationary cream stone';base.data.materials.append(stone);bevel(base,.015,3)
base.modifiers.new('Stone cloth collision','COLLISION')
# Lighting and lens.
sc=bpy.context.scene;sc.render.threads_mode='FIXED';sc.render.threads=3;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=12;sc.cycles.use_denoising=True
sc.render.resolution_x=sc.render.resolution_y=256;sc.render.resolution_percentage=100
sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA'
sc.world.color=(.13,.13,.13)
sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast';sc.view_settings.exposure=.1
bpy.ops.object.camera_add();sc.camera=bpy.context.object;sc.camera.data.type='ORTHO';sc.camera.data.ortho_scale=2.90
camera((2.5,-7,3.0))
for name,loc,power,size,col in [('Warm upper-left key',(-3,-4,6),800,1.5,(1,.91,.75)),('Soft cool fill',(4,-2,3),310,3,(.88,.92,1)),('Warm back rim',(-2,3,4),700,1.7,(1,.83,.57))]:
    bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name=name;o.data.energy=power;o.data.shape='DISK';o.data.size=size;o.data.color=col;o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
sc.render.fps=24
p=rig.pose.bones['head'];mat=p.matrix.copy();pivot=p.head.copy()
p.matrix=Matrix.Translation(pivot) @ Matrix.Rotation(-.42,4,'Z') @ Matrix.Translation(-pivot) @ mat
bpy.context.view_layer.update()

rig['origin']='MPFB 2.0.18 game_engine, CC0 base topology and weights'
rig['neutral_pose'] = json.dumps({p.name:list(p.matrix_basis) if False else [list(row) for row in p.matrix_basis] for p in rig.pose.bones})
sc['kit_source']='Original procedural hard-surface kit fitted to MPFB anatomy'
bpy.ops.wm.save_as_mainfile(filepath=str(MASTER/'spearman.blend'))
(MASTER/'model-info.json').write_text(json.dumps({'body_vertices':len(body.data.vertices),'body_source':'MPFB 2.0.18 CC0','bones':len(rig.data.bones),'objects':len(sc.objects),'head_center':list(hc)},indent=2))
print('MODEL_READY',MASTER/'spearman.blend')
