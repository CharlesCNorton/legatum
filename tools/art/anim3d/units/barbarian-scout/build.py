"""Original scout kit on CC0 MPFB anatomy. Blender background entry point."""
import bpy, os, sys, math, json, random
from pathlib import Path
from mathutils import Vector, Matrix
from math import sin, cos, pi
ROOT=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'))
M=ROOT/'masters/barbarian-scout'; A=ROOT/'assets/barbarian-scout'
M.mkdir(parents=True,exist_ok=True)
random.seed(21)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
# Reuse the lead's tested anatomy creation, helpers and CC0 game-engine rig.
lead=Path(__file__).resolve().parents[2]/'scene.py'
code=lead.read_text().split("skin=material(")[0]
# No lead paths or output mutations: execute helper + anatomy portion only.
code=code[code.index('def material'):]
exec(compile(code,str(lead),'exec'))
rig.name='Scout • MPFB rig'; body.name='GEO-anatomy'
rig.location.z=-.30
# Bake MPFB morph shape keys before applying the crouched bind pose.
for obj in (body,eyes):
    if obj.data.shape_keys:
        obj.data=bpy.data.meshes.new_from_object(obj.evaluated_get(bpy.context.evaluated_depsgraph_get()))
skin=material('MAT-painted-skin',(.48,.26,.13),0,.67)
cloth=material('MAT-oatmeal-woven-tunic',(.35,.27,.16),0,.88)
pants=material('MAT-charcoal-wool',(.12,.105,.085),0,.89)
leather=material('MAT-worn-leather',(.16,.078,.031),0,.7)
fur=material('MAT-wolf-pelt',(.13,.115,.09),0,.9)
hair=material('MAT-chestnut-hair',(.085,.046,.022),0,.85)
red=material('MAT-ochre-red-scarf',(.37,.035,.012),0,.86)
metal=material('MAT-bright-worn-iron',(.52,.53,.50),1,.38)
brass=material('MAT-worn-brass',(.48,.29,.08),1,.38)
hornmat=material('MAT-ivory-horn',(.65,.48,.27),0,.63)
# sRGB E9CFA0 converted to linear; a shared warm cream stone target.
def linear(x): return ((x+.055)/1.055)**2.4 if x>.04045 else x/12.92
stone=material('MAT-cream-stone-E9CFA0',tuple(linear(v/255) for v in (233,207,160)),0,.85)
body.data.materials.clear();body.data.materials.append(skin)
for p in body.data.polygons:p.use_smooth=True
# Body-derived garment shells preserve MPFB deformation weights.
def shell(name,predicate,mat,inflate):
    def garment_vertex(v):
        if not predicate(v.co):return False
        # Anatomical hands hang beside the hips in MPFB's initial pose. A
        # height-only trouser selection also clothes their palms and fingers.
        if name=='GEO-wool-trousers':
            return not any(body.vertex_groups[g.group].name.startswith(
                ('clavicle','upperarm','lowerarm','hand','index','middle','ring','pinky','thumb'))
                and g.weight>.001 for g in v.groups)
        return True
    ids=[v.index for v in body.data.vertices if garment_vertex(v)]
    valid=set(ids); faces=[p for p in body.data.polygons if all(i in valid for i in p.vertices)]
    ids=sorted({i for p in faces for i in p.vertices}); mp={v:i for i,v in enumerate(ids)}
    vs=[]
    for i in ids:
        v=body.data.vertices[i]; co=v.co+v.normal*inflate
        co+=v.normal*(.0025*sin(co.z*110+co.x*30))
        vs.append(co)
    o=mesh(name,vs,[[mp[i] for i in p.vertices] for p in faces],mat)
    for g in body.vertex_groups:o.vertex_groups.new(name=g.name)
    for j,i in enumerate(ids):
        for g in body.data.vertices[i].groups:o.vertex_groups[g.group].add([j],g.weight,'REPLACE')
    o.parent=rig
    ar=o.modifiers.new('MPFB skin weights','ARMATURE');ar.object=rig
    sub=o.modifiers.new('Tailored organic surface','SUBSURF');sub.levels=1
    solid(o,.006)
    return o
shell('GEO-wool-trousers',lambda v:.12<v.z<1.02,pants,.014)
shell('GEO-linen-shirt',lambda v:.93<v.z<1.45 and abs(v.x)<.30,cloth,.022)
shell('GEO-leather-boots',lambda v:v.z<.34,leather,.018)
sub=body.modifiers.new('Anatomical subdivision','SUBSURF');sub.levels=1
# Kneeling scout rest pose. All target coordinates are armature-local.
def aim(name,direction):
    p=rig.pose.bones[name];q=p.bone.matrix_local.to_quaternion()
    delta=(q@Vector((0,1,0))).rotation_difference(Vector(direction).normalized())
    rot=(delta@q).to_matrix().to_4x4();rot.translation=p.head.copy();p.matrix=rot
    bpy.context.view_layer.update()
def turn(name,axis,angle):
    p=rig.pose.bones[name];m=p.matrix.copy();pos=m.translation.copy();m=Matrix.Rotation(angle,4,axis)@m;m.translation=pos;p.matrix=m;bpy.context.view_layer.update()
turn('spine_01','X',.12);turn('spine_03','Z',.20);turn('head','Z',.70)
limb('thigh_l','calf_l',(.30,-.29,.45),(.25,-.65,1.22))
limb('thigh_r','calf_r',(-.29,.05,.46),(-.18,-.50,.20))
aim('foot_l',(.04,-.18,-.045));aim('foot_r',(-.02,-.15,-.08))
limb('upperarm_l','lowerarm_l',(.25,-.22,1.65),(.70,.02,1.45))
limb('upperarm_r','lowerarm_r',(-.17,-.41,.82),(-.38,-.30,1.10))
aim('hand_l',(-.10,-.035,.015));aim('hand_r',(.01,-.05,-.10))
hp=rig.pose.bones['head'];hm=hp.matrix.copy();hm.translation.x+=.065;hp.matrix=hm
bpy.context.view_layer.update()
# Freeze shaped anatomy into a new bind pose; retain real MPFB topology/weights.
for o in list(bpy.context.scene.objects):
    if o.type=='MESH':
        for mod in list(o.modifiers):
            if mod.type=='ARMATURE':
                bpy.context.view_layer.objects.active=o
                bpy.ops.object.modifier_apply(modifier=mod.name)
bpy.context.view_layer.objects.active=rig
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True)
bpy.ops.object.mode_set(mode='POSE');bpy.ops.pose.armature_apply(selected=False);bpy.ops.object.mode_set(mode='OBJECT')
for o in list(bpy.context.scene.objects):
    if o.type=='MESH' and o.vertex_groups:
        ar=o.modifiers.new('Scout rest-pose skinning','ARMATURE');ar.object=rig
        bpy.context.view_layer.objects.active=o
        bpy.ops.object.modifier_move_up(modifier=ar.name)
# Custom kit is built in world coordinates and bone-parented preserving transforms.
def bone(name):return rig.matrix_world@rig.pose.bones[name].head
# Closed folded tunic skirt around pelvis, short enough to expose both knees.
vs=[];fs=[]
for j in range(13):
    t=j/12
    for i in range(64):
        a=2*pi*i/64; wave=.015*sin(11*a+2*t)*t
        vs.append(((.205+.08*t+wave)*sin(a),.01-(.15+.07*t+wave)*cos(a),.72-.29*t+.025*cos(a*7)*t))
for j in range(12):
    for i in range(64):k=j*64+i;n=j*64+(i+1)%64;fs.append((k,n,n+64,k+64))
skirt=mesh('GEO-folded-tunic-hem',vs,fs,cloth);solid(skirt,.009);attach(skirt,'pelvis')
# Tailored wolf pelt: a volumetric shoulder cowl and draped folded back, real fibres.
vs=[];fs=[]
for j in range(15):
    t=j/14
    for i in range(64):
        a=2*pi*i/64
        rx=.15+.20*sin(t*pi*.65); ry=.105+.10*t
        vs.append((rx*sin(a),.045-ry*cos(a),1.28-.31*t-.04*abs(sin(a))))
for j in range(14):
    for i in range(64):k=j*64+i;n=j*64+(i+1)%64;fs.append((k,n,n+64,k+64))
cowl=mesh('GEO-wolf-pelt-cowl',vs,fs,fur);solid(cowl,.017);attach(cowl,'spine_03')
vs=[];fs=[]
for j in range(18):
    t=j/17
    for i in range(25):
        u=i/24;vs.append(((u-.5)*(.54+.15*t),.16+.13*t+.025*sin(u*9*pi),1.17-.79*t+.06*cos(u*5*pi)*t))
for j in range(17):
    for i in range(24):k=j*25+i;fs.append((k,k+1,k+26,k+25))
cape=mesh('GEO-folded-pelt-cape',vs,fs,fur);solid(cape,.018);attach(cape,'spine_01')
# Tufts taper as geometry; no billboard cards or alpha cutout anatomy.
for surf in (cowl,cape):
    tv=[];tf=[]
    for p in random.sample(list(surf.data.polygons),min(290,len(surf.data.polygons))):
        c=p.center.copy(); n=p.normal.copy(); tang=Vector((0,0,-1)); wid=random.uniform(.008,.017); length=random.uniform(.025,.058)
        # Mesh polygon centers/normals updated explicitly before sampling below.
        c=sum((surf.data.vertices[i].co for i in p.vertices),Vector())/len(p.vertices)
        n=(surf.data.vertices[p.vertices[1]].co-surf.data.vertices[p.vertices[0]].co).cross(surf.data.vertices[p.vertices[2]].co-surf.data.vertices[p.vertices[0]].co).normalized()
        n=Vector((c.x,c.y-.02,.12 if surf==cowl else 0)).normalized()
        c+=n*.012
        side=n.cross(tang).normalized()*wid; tip=c+tang*length+n*.025
        k=len(tv);tv.extend([c-side,c+side,c+n*.025,tip]);tf.extend([(k,k+2,k+3),(k+2,k+1,k+3),(k,k+1,k+2)])
    o=mesh('GEO-layered-fur-tufts',tv,tf,fur);attach(o,'spine_03' if surf==cowl else 'spine_01')
# Hair follows an ellipsoidal scalp fitted around the posed MPFB head.
h=bone('head'); center=h+Vector((.018,.018,.09))
hv=[];hf=[]
for j in range(15):
    t=.04+j/14*1.85
    for i in range(48):
        a=2*pi*i/48;hv.append(center+Vector((.116*sin(t)*sin(a),.124*sin(t)*cos(a),.133*cos(t))))
for j in range(14):
    for i in range(48):k=j*48+i;n=j*48+(i+1)%48;hf.append((k,n,n+48,k+48))
attach(solid(mesh('GEO-sculpted-scalp',hv,hf,hair),.007),'head')
for j in range(180):
    a=random.uniform(-pi,pi); t=random.uniform(.12,1.50)
    start=center+Vector((.120*sin(t)*sin(a),.129*sin(t)*cos(a),.138*cos(t)))
    end=start+Vector((-.012,.025,-random.uniform(.035,.105)))
    o=curve('GEO-sculpted-hair-lock',[start,start+Vector((.009,.008,-.02)),end],random.uniform(.003,.008),hair);attach(o,'head')
# Beard sculpted from a fitted lower-face shell would follow the face; short locks
# follow the actual head orientation rather than adding a spherical primitive.
for j in range(35):
    a=-1.2+2.4*j/34
    p=center+Vector((.075*sin(a)+.045,-.084*cos(a)-.014,-.084))
    attach(curve('GEO-beard-lock',[p,p+Vector((-.002,.003,-.025))],.004,hair),'head')
# Scarf collar and two cloth tails, modeled folds with thickness.
for z,r in [(1.215,.137),(1.19,.142)]:
    attach(curve('GEO-red-scarf-collar',[(r*sin(a),-.02-r*.76*cos(a),z-.04*cos(a)) for a in [2*pi*i/64 for i in range(65)]],.016,red),'spine_03')
for sg in (-1,1):
    pts=[]
    for j in range(12):
        t=j/11
        for u in (-1,0,1):pts.append((.05+sg*.035*t+u*.025*(1-.6*t),-.16-.018*sin(t*pi),1.17-.23*t+.012*cos(t*9+u)))
    ob=mesh('GEO-red-scarf-tail',pts,[(j*3+i,j*3+i+1,j*3+i+4,j*3+i+3) for j in range(11) for i in range(2)],red);solid(ob,.004);attach(ob,'spine_03')
# Broad belt, rolled rims, buckle and studs.
for zz in (.734,.764):
    attach(curve('GEO-waist-belt-edge',[(.214*sin(a),-.158*cos(a),zz) for a in [2*pi*i/80 for i in range(81)]],.012,leather),'pelvis')
attach(curve('GEO-belt-buckle',[(-.035,-.172,.72),(.035,-.172,.72),(.035,-.172,.78),(-.035,-.172,.78),(-.035,-.172,.72)],.006,brass),'pelvis')
# Axe on the belt: beveled iron wedge and wooden handle.
axe=curve('GEO-axe-haft',[(-.29,-.20,.42),(.025,-.19,.86)],.018,leather);attach(axe,'pelvis')
v=[(-.03,-.21,.87),(.14,-.21,.83),(.11,-.21,.70),(.035,-.21,.75),(-.03,-.18,.87),(.14,-.18,.83),(.11,-.18,.70),(.035,-.18,.75)]
axehead=mesh('GEO-forged-axe-head',v,[(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],metal);bevel(axehead,.004,3);attach(axehead,'pelvis')
# Curved horn with a real mouth opening, ivory walls and bronze bands.
pts=[Vector((-.36-.12*sin(t*pi/2),.11, .90+.25*t)) for t in [i/16 for i in range(17)]]
vs=[];fs=[]
for j,p in enumerate(pts):
    r=.015+.035*j/16
    for i in range(24):a=2*pi*i/24;vs.append(p+Vector((r*cos(a),r*sin(a),0)))
for j in range(16):
    for i in range(24):k=j*24+i;n=j*24+(i+1)%24;fs.append((k,n,n+24,k+24))
ob=mesh('GEO-hollow-drinking-horn',vs,fs,hornmat);solid(ob,.006);attach(ob,'spine_03')
for j in (2,14,16):
    r=.015+.035*j/16;p=pts[j]
    attach(curve('GEO-horn-bronze-band',[p+Vector((r*cos(a),r*sin(a),0)) for a in [2*pi*i/48 for i in range(49)]],.006,brass),'spine_03')
# Bracers and boot wraps conform to the skeletal segment, with raised stitches.
for side in ('l','r'):
    for name,count in [('lowerarm_',6),('calf_',8)]:
        pb=rig.pose.bones[name+side];p=rig.matrix_world@pb.head;q=rig.matrix_world@pb.tail
        axis=(q-p).normalized();u=axis.cross(Vector((0,1,0))).normalized();v=axis.cross(u)
        for j in range(count):
            t=.30+.62*j/count;c=p.lerp(q,t);r=(.046 if name=='lowerarm_' else .058)
            coords=[c+r*(u*cos(a)+v*sin(a))+axis*(.010*a/(2*pi)) for a in [2*pi*i/48 for i in range(49)]]
            attach(curve('GEO-wrapped-leather',coords,.006,leather),name+side)
# Closed footwear covers anatomical toes; separate stitched leather soles.
for side in ('l','r'):
    foot=rig.pose.bones['foot_'+side]
    a=rig.matrix_world@foot.head;b=rig.matrix_world@foot.tail
    center=(a+b)*.5;center.z=.147
    verts=[];faces=[]
    for j in range(13):
        t=pi*j/12
        for i in range(48):
            ang=2*pi*i/48
            verts.append((center.x+.067*sin(t)*cos(ang),center.y+.125*sin(t)*sin(ang),center.z+.052*cos(t)))
    for j in range(12):
        for i in range(48):k=j*48+i;n=j*48+(i+1)%48;faces.append((k,n,n+48,k+48))
    attach(mesh('GEO-closed-boot-'+side,verts,faces,leather),'foot_'+side)
    attach(curve('GEO-boot-stitched-welt-'+side,[(center.x+.065*cos(a),center.y+.124*sin(a),.111) for a in [2*pi*i/64 for i in range(65)]],.006,leather),'foot_'+side)
# One stationary cream disc, no rubble or extra tiers.
bpy.ops.mesh.primitive_cylinder_add(vertices=96,radius=.54,depth=.095,location=(0,0,.048))
base=bpy.context.object;base.name='GEO-stationary-cream-base';base.data.materials.append(stone);bevel(base,.014,3)
for p in base.data.polygons:p.use_smooth=True
# Camera calibration against 256 token: low three-quarter elevation, ample margins.
bpy.ops.object.camera_add(location=(0,-6,2.46));cam=bpy.context.object;cam.name='CAM-painting'
target=Vector((0,0,.67));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=1.65
sc=bpy.context.scene;sc.camera=cam
sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.7,.76,.85,1);sc.world.node_tree.nodes['Background'].inputs[1].default_value=.35
for name,pos,energy,size,color in [('key',(-3,-4,5),450,3,(1,.88,.70)),('fill',(3,-2,3),100,4,(.8,.88,1)),('rim',(2,3,4),220,2,(.76,.85,1))]:
    d=bpy.data.lights.new('LGT-'+name,'AREA');d.energy=energy;d.size=size;d.color=color;o=bpy.data.objects.new('LGT-'+name,d);sc.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector((0,0,.8))-o.location).to_track_quat('-Z','Y').to_euler()
sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=8;sc.cycles.use_denoising=True
sc.cycles.max_bounces=4;sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.resolution_x=sc.render.resolution_y=256;sc.render.resolution_percentage=100
sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0
sc['unit']='barbarian-scout';sc['anatomy']='MPFB 2.0.18 CC0';sc['rest_pose']='kneeling lookout'
# Keep plain review as a separate editable scene checkpoint.
bpy.ops.wm.save_as_mainfile(filepath=str(M/'plain.blend'))
bpy.ops.wm.save_as_mainfile(filepath=str(M/'barbarian-scout.blend'))
(M/'bones.json').write_text(json.dumps({p.name:{'head':list(rig.matrix_world@p.head),'tail':list(rig.matrix_world@p.tail)} for p in rig.pose.bones},indent=2))
print('SCOUT_BUILD_READY',M)
