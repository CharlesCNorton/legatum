"""Unit-owned paths, geometry helpers and MPFB pose controls; Blender 5.x."""
import os, json, math
from pathlib import Path
import bpy
from mathutils import Vector, Matrix
ROOT=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'))
SLUG='barbarian-archer'
MASTER=ROOT/'masters'/SLUG
ASSET=ROOT/'assets'/SLUG
REVIEW=ROOT/'review/3d-v2'
CLIPS={'idle':(8,10,True),'move':(8,12,True),'attack':(10,14,False),'hit':(4,12,False),'death':(10,10,False)}
for p in (MASTER,ASSET,REVIEW):p.mkdir(parents=True,exist_ok=True)
def log(s):
    with (REVIEW/f'{SLUG}-log.md').open('a') as f:f.write(s+'\n')
    print(s,flush=True)
def mat(name,col,metal=0,rough=.65):
    m=bpy.data.materials.new(name);m.diffuse_color=(*col,1);m.use_nodes=True
    b=m.node_tree.nodes.get('Principled BSDF');b.inputs['Base Color'].default_value=(*col,1)
    b.inputs['Metallic'].default_value=metal;b.inputs['Roughness'].default_value=rough
    return m

def mesh(name,vs,fs,m):
    d=bpy.data.meshes.new(name);d.from_pydata(vs,[],fs);d.update()
    o=bpy.data.objects.new('GEO-'+name,d);bpy.context.collection.objects.link(o)
    if m:d.materials.append(m)
    for f in d.polygons:f.use_smooth=True
    return o

def solid(o,t=.005):
    mod=o.modifiers.new('Real thickness','SOLIDIFY');mod.thickness=t
    return o

def bevel(o,w=.003):
    mod=o.modifiers.new('Rounded edges','BEVEL');mod.width=w;mod.segments=3
    return o

def curve(name,pts,r,m):
    d=bpy.data.curves.new(name,'CURVE');d.dimensions='3D';d.resolution_u=2
    s=d.splines.new('POLY');s.points.add(len(pts)-1)
    for p,v in zip(s.points,pts):p.co=(*v,1)
    d.bevel_depth=r;d.bevel_resolution=2
    o=bpy.data.objects.new('GEO-'+name,d);bpy.context.collection.objects.link(o);d.materials.append(m)
    return o

def ellipsoid(name,loc,scale,m):
    # Only small equipment/pelt shapes; human anatomy always MPFB.
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=12,location=loc)
    o=bpy.context.object;o.name='GEO-'+name;o.scale=scale;o.data.materials.append(m)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    for p in o.data.polygons:p.use_smooth=True
    return o

def attach(o,rig,bone):
    bpy.context.view_layer.update();world=o.matrix_world.copy()
    o.parent=rig;o.parent_type='BONE';o.parent_bone=bone
    bpy.context.view_layer.update();o.matrix_world=world;o['attachment']=bone
    return o

def aim(rig,name,direction):
    p=rig.pose.bones[name];q=p.bone.matrix_local.to_quaternion()
    delta=(q@Vector((0,1,0))).rotation_difference(Vector(direction).normalized())
    mm=(delta@q).to_matrix().to_4x4();mm.translation=p.head.copy();p.matrix=mm
    bpy.context.view_layer.update()

def limb(rig,upper,lower,target,pole):
    a=rig.pose.bones[upper].head.copy();axis=Vector(target)-a
    l1=rig.data.bones[upper].length;l2=rig.data.bones[lower].length
    d=max(.001,min(axis.length,l1+l2-.0001));axis.normalize()
    along=(l1*l1-l2*l2+d*d)/(2*d);h=max(0,l1*l1-along*along)**.5
    side=Vector(pole)-a;side=(side-axis*side.dot(axis)).normalized()
    elbow=a+axis*along+side*h
    aim(rig,upper,elbow-a);aim(rig,lower,Vector(target)-elbow)

def reset(rig):
    for p in rig.pose.bones:p.matrix_basis=Matrix.Identity(4)
    rig.location=(0,0,-.045);rig.rotation_euler=(0,0,0)
    bpy.context.view_layer.update()

def pose(rig,phase=0,stride=0,draw=1):
    reset(rig)
    # Lower the pelvis, then solve both knees to planted ankle targets.
    rig.pose.bones['pelvis'].location.y=-.14
    rig.pose.bones['pelvis'].location.x=-.13
    bpy.context.view_layer.update()
    limb(rig,'thigh_r','calf_r',(-.36,-.02+stride,.18),(-.38,-.36,.53))
    limb(rig,'thigh_l','calf_l',(.41,.04-stride,.18),(.40,-.32,.54))
    aim(rig,'foot_r',(-.06,-.16,-.06));aim(rig,'foot_l',(.08,-.16,-.06))
    limb(rig,'upperarm_l','lowerarm_l',(.52,-.15,1.43+phase),(.45,-.16,1.34))
    limb(rig,'upperarm_r','lowerarm_r',(-.30+.33*(1-draw),-.235,1.27+phase),(-.55,-.15,1.17))
    aim(rig,'hand_l',(.012,-.015,.085));aim(rig,'hand_r',(.075,0,.02))
    rig.pose.bones['head'].location.y=-.09
    bpy.context.view_layer.update()
    p=rig.pose.bones['head'];mm=p.matrix.copy();pivot=p.head.copy()
    p.matrix=Matrix.Translation(pivot)@Matrix.Rotation(.58,4,'Z')@Matrix.Translation(-pivot)@mm
    for side in ('r','l'):
        for digit in ('index','middle','ring','pinky'):
            for k in range(1,4):
                p=rig.pose.bones[f'{digit}_{k:02d}_{side}'];p.rotation_mode='XYZ';p.rotation_euler.x=1.0 if side=='l' else .8
    bpy.context.view_layer.update()

def settings(res=256,samples=8):
    sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device=os.environ.get('CYCLES_DEVICE','CPU')
    if sc.cycles.device=='GPU':
        pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='METAL';pref.get_devices()
        devices=[d for d in pref.devices if d.type=='METAL']
        if not devices:raise RuntimeError('Metal GPU required; refusing CPU fallback')
        for d in pref.devices:d.use=d.type=='METAL'
    sc.cycles.samples=samples;sc.cycles.use_denoising=True;sc.cycles.max_bounces=5
    sc.render.resolution_x=sc.render.resolution_y=res;sc.render.resolution_percentage=100
    sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA'
    sc.render.threads_mode='FIXED';sc.render.threads=3
    sc.render.use_persistent_data=True
    sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast';sc.view_settings.exposure=0
    return sc

def render(path):
    sc=bpy.context.scene
    if sc.camera is None:raise RuntimeError('Missing camera')
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    sc.render.filepath=str(path);bpy.ops.render.render(write_still=True)
