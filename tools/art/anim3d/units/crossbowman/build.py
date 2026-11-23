"""Original quilted infantry kit on a CC0 MPFB body; fixed painting UVs on real geometry."""
import ast, bpy, json, math, os, sys
from pathlib import Path
from mathutils import Vector, Matrix
from math import sin, cos, pi
from bpy_extras.object_utils import world_to_camera_view
ROOT=Path(os.environ['ANIM_ROOT']); M=ROOT/'masters/crossbowman'; A=ROOT/'assets/crossbowman'
M.mkdir(parents=True,exist_ok=True)
# Reuse the lead's geometry/IK routines, without executing its spearman scene.
for node in ast.parse(Path('tools/art/anim3d/scene.py').read_text()).body:
    if isinstance(node,ast.FunctionDef) and node.name in {'material','mesh','solid','bevel','curve','sphere','attach','aim_bone','limb'}:
        exec(compile(ast.Module(body=[node],type_ignores=[]),'<infantry helpers>','exec'))
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.preferences.addon_enable(module='bl_ext.user_default.mpfb')
from bl_ext.user_default.mpfb.services.humanservice import HumanService
from bl_ext.user_default.mpfb.services.targetservice import TargetService
macro=TargetService.get_default_macro_info_dict();macro.update(gender=1.,age=.5,muscle=.65,weight=.48,height=.5,proportions=.65)
body=HumanService.create_human(macro_detail_dict=macro);body.name='GEO-MPFB anatomical crossbowman'
bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();height=max(v.co.z for v in me.vertices)-min(v.co.z for v in me.vertices);ev.to_mesh_clear()
body.scale=(1.78/height*.96,1.78/height,1.78/height);bpy.context.view_layer.objects.active=body;body.select_set(True);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
rig=HumanService.add_builtin_rig(body,'game_engine');rig.name='RIG-crossbowman';rig.location.z=.10
eyes_path=ROOT/'blender-user/extensions/.user/user_default/mpfb/data/eyes/high-poly/high-poly.mhclo'
eyes=HumanService.add_mhclo_asset(str(eyes_path),body,asset_type='Eyes',subdiv_levels=1,material_type='MAKESKIN');eyes.name='GEO-CC0 anatomical eyes'
skin=material('Skin ochre painted',(.42,.24,.13),0,.73)
linen=material('Quilted oatmeal linen',(.53,.40,.23),0,.86)
wool=material('Vermilion shoulder wool',(.38,.035,.014),0,.9)
olive=material('Olive wool trousers',(.12,.13,.055),0,.88)
leather=material('Scuffed brown leather',(.10,.046,.019),0,.72)
wood=material('Crossbow walnut',(.24,.10,.025),0,.62)
steel=material('Worn bright steel',(.30,.25,.19),1,.46)
brass=material('Brass buckle edges',(.64,.38,.12),1,.34)
string=material('Hemp bowstring',(.51,.40,.23),0,.8)
stone=material('Cream stone E9CFA0',(.815,.624,.352),0,.88)
body.data.materials.clear();body.data.materials.append(skin)
for poly in body.data.polygons:poly.use_smooth=True
# Copy body-derived garments in neutral coordinates with genuine MPFB weights.
def garment(name,pred,mat,inflate):
    ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
    polys=[p for p in me.polygons if all(pred(me.vertices[i].co) for i in p.vertices)]
    ids=sorted({i for p in polys for i in p.vertices});idx={v:i for i,v in enumerate(ids)}
    ob=mesh(name,[tuple(me.vertices[i].co+me.vertices[i].normal*inflate) for i in ids],[[idx[i] for i in p.vertices] for p in polys],mat)
    from mathutils.kdtree import KDTree
    kd=KDTree(len(body.data.vertices))
    for v in body.data.vertices:kd.insert(v.co,v.index)
    kd.balance()
    for g in body.vertex_groups:ob.vertex_groups.new(name=g.name)
    for j,i in enumerate(ids):
        _,k,_=kd.find(me.vertices[i].co)
        for g in body.data.vertices[k].groups:ob.vertex_groups[g.group].add([j],g.weight,'REPLACE')
    ev.to_mesh_clear();ob.parent=rig
    ar=ob.modifiers.new('MPFB garment skin weights','ARMATURE');ar.object=rig
    solid(ob,.006);su=ob.modifiers.new('Tailored surface subdivision','SUBSURF');su.levels=1
    return ob
trousers=garment('GEO-olive wool trousers',lambda v:.16<v.z<1.02 and abs(v.x)<.30,olive,.015)
boots=garment('GEO-leather boots',lambda v:v.z<.15,leather,.017)

# Pose: upright rather than spearman guard. World points account for rig elevation.
limb('upperarm_r','lowerarm_r',(-.325,-.20,1.06),(-.29,-.80,1.18))
limb('upperarm_l','lowerarm_l',(.455,-.25,1.40),(.30,-.80,1.44))
aim_bone('hand_r',(0,0,-1));aim_bone('hand_l',(0,-.25,-1))
for side in ['r','l']:
    for digit in ['index','middle','ring','pinky']:
        for k in [1,2,3]:
            p=rig.pose.bones[f'{digit}_{k:02d}_{side}'];p.rotation_mode='XYZ';p.rotation_euler.x=.65 if side=='r' else .18
# Three-quarter head orientation follows the source painting.
p=rig.pose.bones['head'];m=p.matrix.copy();pivot=m.translation.copy();m=Matrix.Rotation(.65,4,'Z') @ m;m.translation=pivot;p.matrix=m;bpy.context.view_layer.update()
# Lift head to register painted face; helmet dome is reduced correspondingly.
p=rig.pose.bones['head'];m=p.matrix.copy();m.translation.z+=.06;p.matrix=m;bpy.context.view_layer.update()
# Feet slightly apart, stable on the base.
limb('thigh_r','calf_r',(-.12,-.015,.10),(-.14,-.25,.48))
limb('thigh_l','calf_l',(.17,.015,.10),(.17,-.20,.48))
for side in ['l','r']:aim_bone('foot_'+side,(.04 if side=='l' else -.02,-1,0))
bpy.context.view_layer.update()
# Continuous quilted sleeves: inverse skin the fitted rest surface, then let
# both arm bones deform the elbow. No separate rigid shoulder/elbow tube seams.
for side in ['l','r']:
    names=['upperarm_'+side,'lowerarm_'+side]
    bones=[rig.pose.bones[n] for n in names]
    points=[bones[0].head.copy(),bones[0].tail.copy(),bones[1].tail.copy()]
    deform=[p.matrix @ p.bone.matrix_local.inverted() for p in bones]
    vs=[];fs=[];weights=[];N=40;J=48
    for j in range(J+1):
        t=j/J;section=min(1,int(t*2));local=t*2-section
        center=points[section].lerp(points[section+1],local)
        axis=(points[section+1]-points[section]).normalized()
        # Blend the tangent around the elbow to keep one continuous ring grid.
        if abs(t-.5)<.12:
            blend=(t-.38)/.24
            axis=(points[1]-points[0]).normalized().lerp((points[2]-points[1]).normalized(),blend).normalized()
        u=axis.cross(Vector((0,1,0))).normalized();v=axis.cross(u)
        w=max(0,min(1,(t-.38)/.24));w=w*w*(3-2*w)
        inv=(deform[0]*(1-w)+deform[1]*w).inverted()
        for k in range(N):
            angle=2*pi*k/N
            radius=(.079*(1-t)+.046*t)+.006*sin(pi*t)+.002*cos(angle*10)*cos(t*pi*38)
            vs.append(tuple(inv @ (center+radius*(u*cos(angle)+v*sin(angle)))))
            weights.append(w)
    for j in range(J):
        for k in range(N):
            q=j*N+k;n=j*N+(k+1)%N;fs.append((q,n,n+N,q+N))
    ob=mesh('GEO-continuous quilted sleeve '+side,vs,fs,linen);ob.parent=rig
    groups=[ob.vertex_groups.new(name=n) for n in names]
    for i,w in enumerate(weights):
        groups[0].add([i],1-w,'REPLACE');groups[1].add([i],w,'REPLACE')
    arm=ob.modifiers.new('Continuous MPFB sleeve weights','ARMATURE');arm.object=rig
    solid(ob,.007)
    sub=ob.modifiers.new('Soft quilt folds','SUBSURF');sub.levels=1
for side in ['l','r']:
    fp=rig.matrix_world @ rig.pose.bones['foot_'+side].head
    shoe=sphere('GEO-rounded leather shoe '+side,(fp.x,fp.y-.065,.145),(.074,.12,.054),leather);attach(shoe,'foot_'+side)
# Torso/skirt: shaped cloth with broad folds and real thickness, not a body primitive.
def cloth_rings(name,rings,mat,bone,folds=.004):
    vs=[];fs=[];N=64
    for j,(z,rx,ry) in enumerate(rings):
        for i in range(N):
            a=i*2*pi/N;f=folds*(sin(a*12+j*.4)+.3*sin(a*23))
            vs.append(((rx+f)*sin(a),-(ry+f)*cos(a),z+.008*cos(a*5)))
    for j in range(len(rings)-1):
        for i in range(N):a=j*N+i;b=j*N+(i+1)%N;fs.append((a,b,b+N,a+N))
    o=mesh(name,vs,fs,mat);solid(o,.009);bevel(o,.003);attach(o,bone);return o
cloth_rings('GEO-quilted gambeson',[(.87,.235,.16),(.98,.22,.16),(1.17,.18,.14),(1.26,.19,.15),(1.38,.21,.16),(1.49,.205,.14),(1.56,.17,.12)],linen,'spine_02')
# Stitched quilting channels: visible material relief instead of painted lines alone.
for i in range(25):
    a=-1.45+i*2.9/24;pts=[]
    for k in range(18):
        t=k/17;z=.87+.65*t;rx=.225-.045*sin(t*pi);ry=.164-.018*sin(t*pi)
        pts.append((rx*sin(a),-ry*cos(a)-.004,z))
    attach(curve('GEO-gambeson stitched channel',pts,.0015,string),'spine_02')
cloth_rings('GEO-waist leather belt',[(1.205,.192,.157),(1.245,.194,.158)],leather,'spine_02',.001)
# Buckle is a real open brass rectangle, with tongue and leather tail.
attach(curve('GEO-open belt buckle',[(.04,-.169,1.209),(.09,-.169,1.209),(.09,-.169,1.247),(.04,-.169,1.247),(.04,-.169,1.209)],.004,brass),'spine_02')
attach(curve('GEO-buckle tongue',[(.065,-.175,1.21),(.065,-.175,1.249)],.0025,brass),'spine_02')
# Cowl has thick fabric, sloped front and concentric sculpted folds.
vs=[];fs=[];N=80;J=18
for j in range(J+1):
    t=j/J
    for i in range(N):
        a=2*pi*i/N;rx=.095+.17*t;ry=.10+.095*t
        z=1.68-.14*t-.10*t*max(0,cos(a))+.008*sin(t*pi*10)
        vs.append((rx*sin(a),-ry*cos(a),z))
for j in range(J):
    for i in range(N):k=j*N+i;n=j*N+(i+1)%N;fs.append((k,n,n+N,k+N))
cowl=solid(mesh('GEO-red draped cowl',vs,[tuple(reversed(f)) for f in fs],wool),.008);attach(cowl,'spine_03')
attach(curve('GEO-cowl stitched hem',vs[-N:]+[vs[-N]],.0025,string),'spine_03')
# Steel kettle helmet: closed domed bowl, flared brim, rolled rim and rivets.
hp=rig.matrix_world @ ((rig.pose.bones['head'].head+rig.pose.bones['head'].tail)*.5)
vs=[];fs=[];N=64;J=20
for j in range(J+1):
    t=j/J*pi/2
    for i in range(N):
        a=i*2*pi/N;vs.append((hp.x+.112*cos(t)*sin(a),hp.y-.128*cos(t)*cos(a),hp.z+.018+.115*sin(t)))
for j in range(J):
    for i in range(N):k=j*N+i;n=j*N+(i+1)%N;fs.append((k,n,n+N,k+N))
attach(bevel(solid(mesh('GEO-kettle helmet bowl',vs,fs,steel),.005),.002),'head')
vs=[];fs=[]
for j in range(5):
    t=j/4
    for i in range(N):
        a=i*2*pi/N;vs.append((hp.x+(.112+.040*t)*sin(a),hp.y-(.128+.040*t)*cos(a),hp.z+.017-.042*t+.008*sin(a)))
for j in range(4):
    for i in range(N):k=j*N+i;n=j*N+(i+1)%N;fs.append((k,n,n+N,k+N))
attach(bevel(solid(mesh('GEO-kettle helmet brim',vs,fs,steel),.005),.002),'head')
attach(curve('GEO-helmet rolled rim',vs[-N:]+[vs[-N]],.003,steel),'head')
for i in range(12):
    a=i*2*pi/12;attach(sphere('GEO-helmet rivet',(hp.x+.114*sin(a),hp.y-.130*cos(a),hp.z+.032),(.0035,.0035,.0035),brass),'head')
# Kettle brim slopes across the face like the source painting.
for ob in list(bpy.context.scene.objects):
    if any(key in ob.name for key in ['kettle helmet','helmet rolled','helmet rivet']):
        ob.matrix_world=Matrix.Translation(hp) @ Matrix.Rotation(-.18,4,'Y') @ Matrix.Translation(-hp) @ ob.matrix_world
# Real beard surface fitted onto lower face.
beard=garment('GEO-short beard',lambda v:1.60<v.z<1.69 and v.y<-.045 and abs(v.x)<.075,leather,.004)
# Diagonal leather strap with open brass buckle, stitching, and hip pouch.
strapvs=[(-.12,-.156,1.19),(-.16,-.156,1.19),(.105,-.17,1.57),(.145,-.17,1.57)]
attach(bevel(solid(mesh('GEO-thick baldric',strapvs,[(0,1,2,3)],leather),.009),.003),'spine_02')
attach(curve('GEO-baldric buckle',[(.005,-.18,1.39),(.035,-.18,1.37),(.058,-.18,1.40),(.028,-.18,1.42),(.005,-.18,1.39)],.003,brass),'spine_02')
# Crossbow: stock vertical at rest, steel prod across the lower shins, real string and stirrup.
weapon=bpy.data.objects.new('CTRL-crossbow',None);bpy.context.collection.objects.link(weapon);weapon.location=(-.325,-.26,1.12)
def weaponize(o):
    bpy.context.view_layer.update();w=o.matrix_world.copy();o.parent=weapon;o.matrix_world=w;return o
def box(name,loc,scale,mat):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(mat);bevel(o,.006,3);return o
weaponize(box('GEO-crossbow walnut tiller',(-.275,-.26,.71),(.047,.055,.97),wood))
weaponize(box('GEO-crossbow trigger mechanism',(-.275,-.30,1.21),(.068,.018,.10),steel))
weaponize(curve('GEO-steel bow prod',[(-.565,-.28,.55),(-.50,-.25,.50),(-.40,-.245,.46),(-.275,-.24,.445),(-.15,-.245,.46),(-.05,-.25,.50),(.015,-.28,.55)],.013,steel))
weaponize(curve('GEO-taut bowstring',[(-.565,-.28,.55),(-.275,-.305,.55),(.015,-.28,.55)],.0027,string))
weaponize(curve('GEO-steel foot stirrup',[(-.31,-.26,.29),(-.325,-.26,.19),(-.225,-.26,.19),(-.24,-.26,.29)],.009,steel))
weaponize(curve('GEO-loaded bolt',[(-.275,-.30,.97),(-.275,-.30,.39)],.004,wood))
for z in [.32,.72,1.02]:weaponize(box('GEO-stock steel band',(-.275,-.26,z),(.063,.067,.021),steel))
for z in [.78,.81,.84,.87]:weaponize(curve('GEO-stock binding', [(-.305,-.30,z),(-.245,-.30,z)],.0025,string))
# Register lower bow hardware to the painted shins without moving the grip.
for part in list(weapon.children):
    if any(key in part.name for key in ['bow prod','bowstring']):
        part.location.z-=.070
        for v in part.data.splines[0].points if part.type=='CURVE' and part.data.splines[0].type=='POLY' else []:v.co.x=-.275+(v.co.x+.275)*.90
    elif 'foot stirrup' in part.name:part.location.z-=.035
weapon.location.x-=.05
# Side bolt case, leather straps, brass studs.
case=cloth_rings('GEO-bolt leather case',[(.72,.063,.051),(1.01,.063,.051)],leather,'pelvis',.001)
case.location.x+=.27
for i in range(5):attach(curve('GEO-spare bolt',[(.25+i*.011,.02,.87),(.25+i*.011,.02,1.13)],.0035,wood),'pelvis')
# Shift figure to the painting's right-biased silhouette.
rig.location.x-=.075
weapon.location.x-=.075
# Pavise is a convex timber shield with leather-bound edges, held upright at rest.
shield=bpy.data.objects.new('CTRL-pavise',None);bpy.context.collection.objects.link(shield);shield.location=(.405,-.17,.10)
def shieldize(ob):
    bpy.context.view_layer.update();w=ob.matrix_world.copy();ob.parent=shield;ob.matrix_world=w;return ob
vs=[];fs=[];N=24;J=40
for j in range(J+1):
    t=j/J
    for i in range(N+1):
        u=i/N;x=.405+(u-.5)*.44;y=-.17-.055*(1-(2*u-1)**2);z=.105+1.31*t-.025*abs(2*u-1)**6
        vs.append((x,y,z))
for j in range(J):
    for i in range(N):k=j*(N+1)+i;fs.append((k,k+1,k+N+2,k+N+1))
pavise=bevel(solid(mesh('GEO-painted pavise convex timber',vs,fs,wool),.035),.008);shieldize(pavise)
for edge in [0,N]:shieldize(curve('GEO-pavise leather side rim',[vs[j*(N+1)+edge] for j in range(J+1)],.018,leather))
for edge in [0,J]:shieldize(curve('GEO-pavise leather end rim',[vs[edge*(N+1)+i] for i in range(N+1)],.018,leather))
for side in [0,N]:
    for j in range(2,J,6):
        pos=Vector(vs[j*(N+1)+side])+Vector((0,-.019,0));shieldize(sphere('GEO-pavise brass rivet',pos,(.009,.005,.009),brass))
# Back handle has real thickness and remains available during motion.
shieldize(curve('GEO-pavise rear grip',[(.37,-.12,.85),(.37,-.03,.85),(.44,-.03,.85),(.44,-.12,.85)],.012,leather))
shield.location.z+=.045
# Cream base is stationary for all poses.
bpy.ops.mesh.primitive_cylinder_add(vertices=96,radius=.635,depth=.075,location=(.025,0,.0375));base=bpy.context.object;base.name='GEO-stationary cream stone';base.data.materials.append(stone);base.data.materials.append(material('Stone darker cream rim',(.72,.46,.23),0,.88));
for poly in base.data.polygons:poly.material_index=0 if poly.normal.z>.5 else 1
bevel(base,.020,5)
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=8;sc.cycles.use_denoising=True
sc.render.resolution_x=sc.render.resolution_y=256;sc.render.resolution_percentage=100;sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA'
sc.world.color=(.15,.15,.15);sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0
bpy.ops.object.camera_add(location=(0,-7,2.90));sc.camera=bpy.context.object;sc.camera.name='CAM-painting';sc.camera.data.type='ORTHO';sc.camera.data.ortho_scale=2.25;sc.camera.rotation_euler=(Vector((0,0,.925))-sc.camera.location).to_track_quat('-Z','Y').to_euler()
for name,loc,power,size,col in [('Warm key',(-3,-4,7),450,4,(1,.96,.88)),('Soft fill',(3,-3,3),90,4,(.92,.96,1)),('Cool rim',(2,3,4),135,3,(.85,.92,1))]:
    bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name=name;o.data.energy=power;o.data.size=size;o.data.color=col;o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
# Compress the figure/base stack around the helmet to match source frame height.
for root_obj in [rig,weapon,shield,base]:
    root_obj.scale.z*=.97;root_obj.location.z=root_obj.location.z*.97+.05
bpy.context.view_layer.update()
# Save genuine untextured geometry for the first review.
bpy.ops.wm.save_as_mainfile(filepath=str(M/'plain.blend'))
# Generated painted linen from the mounted family, tinted for unseen cloth.
fill=bpy.data.images.load(str(A/'fill-linen.png'))
for mat in [linen,wool,olive]:
    n=mat.node_tree.nodes;l=mat.node_tree.links;s=n.get('Principled BSDF');tc=n.new('ShaderNodeTexCoord');tex=n.new('ShaderNodeTexImage');tex.image=fill;tex.projection='BOX';tex.projection_blend=.35;l.new(tc.outputs['Generated'],tex.inputs[0]);mix=n.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=.45;mix.inputs[1].default_value=s.inputs['Base Color'].default_value;l.new(tex.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],s.inputs['Base Color'])
# Fine grain, weave, pointiness edge wear and AO cavities are physical shader detail.
for mat in [skin,linen,wool,olive,leather,wood,steel,brass,stone]:
    n=mat.node_tree.nodes;l=mat.node_tree.links;s=n.get('Principled BSDF')
    tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=170 if mat in [linen,wool,olive] else 95;tex.inputs['Detail'].default_value=3
    bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.18;bump.inputs['Distance'].default_value=.001 if mat==stone else .003;l.new(tex.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],s.inputs['Normal'])
    ao=n.new('ShaderNodeAmbientOcclusion');ao.inputs['Distance'].default_value=.08
    mix=n.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=.3;mix.inputs[1].default_value=s.inputs['Base Color'].default_value;
    if s.inputs['Base Color'].is_linked:l.new(s.inputs['Base Color'].links[0].from_socket,mix.inputs[1])
    l.new(ao.outputs['Color'],mix.inputs[2]);l.new(mix.outputs[0],s.inputs['Base Color'])
    if mat in [steel,brass]:
        geo=n.new('ShaderNodeNewGeometry');r=n.new('ShaderNodeMapRange');r.inputs['From Min'].default_value=.35;r.inputs['From Max'].default_value=.6;r.inputs['To Min'].default_value=.65;r.inputs['To Max'].default_value=.23;l.new(geo.outputs['Pointiness'],r.inputs['Value']);l.new(r.outputs[0],s.inputs['Roughness'])
# Stone retains live shadows, with camera-only cream pigment to open its rim.
for mat in base.data.materials:
    n=mat.node_tree.nodes;l=mat.node_tree.links;s=n.get('Principled BSDF')
    pigment=n.new('ShaderNodeEmission');pigment.inputs['Color'].default_value=s.inputs['Base Color'].default_value
    camera=n.new('ShaderNodeLightPath');fac=n.new('ShaderNodeMath');fac.operation='MULTIPLY';fac.inputs[1].default_value=.42;l.new(camera.outputs['Is Camera Ray'],fac.inputs[0])
    mix=n.new('ShaderNodeMixShader');l.new(fac.outputs[0],mix.inputs[0]);l.new(s.outputs[0],mix.inputs[1]);l.new(pigment.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],n.get('Material Output').inputs['Surface'])
# Freeze visibility in the rest pose, including occlusion by shield and clothing.
from mathutils.bvhtree import BVHTree
for ob in list(sc.objects):
    if ob.type=='CURVE':
        bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob;bpy.ops.object.convert(target='MESH')
# Freeze actual finished rigid surfaces before recording camera UVs. Weighted
# anatomy and garments retain their native topology and armature deformation.
for ob in list(sc.objects):
    if ob.type!='MESH' or any(m.type=='ARMATURE' for m in ob.modifiers):continue
    bpy.context.view_layer.objects.active=ob
    for modifier in list(ob.modifiers):
        if modifier.type in {'SOLIDIFY','BEVEL','SUBSURF'}:
            bpy.ops.object.modifier_apply(modifier=modifier.name)
verts=[];faces=[];dg=bpy.context.evaluated_depsgraph_get()
for ob in sc.objects:
    if ob.type!='MESH':continue
    ev=ob.evaluated_get(dg);me=ev.to_mesh();off=len(verts);verts.extend(ev.matrix_world @ v.co for v in me.vertices);faces.extend(tuple(off+i for i in poly.vertices) for poly in me.polygons);ev.to_mesh_clear()
visibility_bvh=BVHTree.FromPolygons(verts,faces)
# Fix painting UVs in the posed mesh, disabling topology-changing modifiers for registration.
painting=bpy.data.images.load(str(A/'painting-aligned.png'));view=(sc.camera.location-Vector((0,0,1))).normalized();records=[]
for obj in list(sc.objects):
    if obj.type=='CURVE':
        bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj;bpy.ops.object.convert(target='MESH');obj=bpy.context.object
    if obj.type!='MESH' or obj==eyes:continue
    states=[(m,m.show_viewport) for m in obj.modifiers]
    for m,_ in states:
        if m.type!='ARMATURE':m.show_viewport=False
    bpy.context.view_layer.update();ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
    uv=obj.data.uv_layers.new(name='Painting fixed UV');att=obj.data.color_attributes.new(name='Painting incidence',type='FLOAT_COLOR',domain='CORNER');coords=[];weights=[]
    for v in me.vertices:
        q=world_to_camera_view(sc,sc.camera,ev.matrix_world @ v.co);coords.append((q.x,q.y));normal=(ev.matrix_world.to_3x3().inverted().transposed() @ v.normal).normalized();hit=visibility_bvh.ray_cast(ev.matrix_world @ v.co+view*.018,view,20)[0];weights.append(max(0,min(1,normal.dot(view)*2.5)) if hit is None else 0)
    assert len(me.vertices)==len(obj.data.vertices),obj.name
    for i,loop in enumerate(obj.data.loops):uv.data[i].uv=coords[loop.vertex_index];att.data[i].color=(weights[loop.vertex_index],)*3+(1,)
    ev.to_mesh_clear()
    for m,on in states:m.show_viewport=on
    for i,old in enumerate(list(obj.data.materials)):
        mat=old.copy();obj.data.materials[i]=mat;n=mat.node_tree.nodes;l=mat.node_tree.links;s=n.get('Principled BSDF');tex=n.new('ShaderNodeTexImage');tex.image=painting;tex.extension='CLIP';u=n.new('ShaderNodeUVMap');u.uv_map=uv.name;l.new(u.outputs[0],tex.inputs[0]);attr=n.new('ShaderNodeVertexColor');attr.layer_name=att.name
        mult=n.new('ShaderNodeMath');mult.operation='MULTIPLY';l.new(attr.outputs[0],mult.inputs[0]);l.new(tex.outputs['Alpha'],mult.inputs[1])
        if obj==base:
            # Only the clean lower stone rim: no feet, weapon or painted contact
            # shadows. Top keeps the physical product lighting and live AO.
            split=n.new('ShaderNodeSeparateXYZ');l.new(u.outputs[0],split.inputs[0])
            mask=n.new('ShaderNodeMapRange');mask.clamp=True;mask.inputs['From Min'].default_value=.105;mask.inputs['From Max'].default_value=.145;mask.inputs['To Min'].default_value=1;mask.inputs['To Max'].default_value=0;l.new(split.outputs['Y'],mask.inputs['Value'])
            masked=n.new('ShaderNodeMath');masked.operation='MULTIPLY';l.new(mult.outputs[0],masked.inputs[0]);l.new(mask.outputs[0],masked.inputs[1]);mult=masked
        # The painting already has illumination. Camera-only pigment preserves
        # it without turning the character into a lamp for indirect rays.
        camera=n.new('ShaderNodeLightPath');factor=n.new('ShaderNodeMath');factor.operation='MULTIPLY';l.new(mult.outputs[0],factor.inputs[0]);l.new(camera.outputs['Is Camera Ray'],factor.inputs[1])
        strength=n.new('ShaderNodeMath');strength.operation='MULTIPLY';strength.inputs[1].default_value=.97;l.new(factor.outputs[0],strength.inputs[0])
        pigment=n.new('ShaderNodeEmission');pigment.name='Frozen painting pigment';l.new(tex.outputs['Color'],pigment.inputs['Color'])
        mix=n.new('ShaderNodeMixShader');l.new(strength.outputs[0],mix.inputs[0]);l.new(s.outputs[0],mix.inputs[1]);l.new(pigment.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],n.get('Material Output').inputs['Surface'])
    records.append({'name':obj.name,'vertices':len(obj.data.vertices)})
bowstring=bpy.data.objects.get('GEO-taut bowstring')
if bowstring and bowstring.type=='MESH':
    bowstring.shape_key_add(name='Basis');draw=bowstring.shape_key_add(name='Draw')
    for v in draw.data:v.co.z+=.17*max(0,1-abs(v.co.x+.275)/.29)
sub=body.modifiers.new('Anatomical subdivision','SUBSURF');sub.levels=1
rig['neutral']=json.dumps({p.name:[list(row) for row in p.matrix_basis] for p in rig.pose.bones});rig['source']='CC0 MPFB 2.0.18 game_engine'
sc['projection']='Fixed per-vertex camera UV, alpha/incidence blend, true 3D geometry';sc['cream_target']='#E9CFA0'
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(M/'model.blend'))
(M/'model-info.json').write_text(json.dumps({'bones':len(rig.data.bones),'projection_meshes':records,'source':'MPFB 2.0.18 CC0','painting':'Project CC BY 4.0','limitations':'Unseen cloth uses tinted generated linen from the mounted family, blended with procedural pigments; view-specific projection needs review.'},indent=2))
print('BUILT',M/'model.blend')
