"""Original hooded brigand kit on a CC0 MPFB body; fixed painting UVs on real geometry."""
import ast, bpy, json, math, os, sys
from pathlib import Path
from mathutils import Vector, Matrix
from math import sin, cos, pi
from bpy_extras.object_utils import world_to_camera_view
ROOT=Path(os.environ['ANIM_ROOT']); M=ROOT/'masters/barbarian-crossbowman'; A=ROOT/'assets/barbarian-crossbowman'
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
body=HumanService.create_human(macro_detail_dict=macro);body.name='GEO-MPFB anatomical brigand'
bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();height=max(v.co.z for v in me.vertices)-min(v.co.z for v in me.vertices);ev.to_mesh_clear()
body.scale=(1.78/height*.88,1.78/height,1.78/height);bpy.context.view_layer.objects.active=body;body.select_set(True);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
rig=HumanService.add_builtin_rig(body,'game_engine');rig.name='RIG-barbarian-crossbowman';rig.location.z=.10
eyes_path=ROOT/'blender-user/extensions/.user/user_default/mpfb/data/eyes/high-poly/high-poly.mhclo'
eyes=HumanService.add_mhclo_asset(str(eyes_path),body,asset_type='Eyes',subdiv_levels=1,material_type='MAKESKIN');eyes.name='GEO-CC0 anatomical eyes'
# Freeze the evaluated MPFB macro mix before fitting garments; keep native topology/weights.
body.shape_key_add(name='Frozen macro anatomy',from_mix=True)
for key in list(body.data.shape_keys.key_blocks)[:-1]:body.shape_key_remove(key)
body.shape_key_remove(body.data.shape_keys.key_blocks[0])
skin=material('Skin ochre painted',(.42,.24,.13),0,.73)
linen=material('Quilted oatmeal linen',(.53,.40,.23),0,.86)
wool=material('Umber hood wool',(.12,.073,.035),0,.9)
olive=material('Olive wool trousers',(.12,.13,.055),0,.88)
leather=material('Scuffed brown leather',(.22,.105,.047),0,.72)
wood=material('Crossbow walnut',(.24,.10,.025),0,.62)
steel=material('Worn bright steel',(.43,.47,.46),1,.34)
brass=material('Brass buckle edges',(.64,.38,.12),1,.34)
string=material('Hemp bowstring',(.51,.40,.23),0,.8)
stone=material('Cream stone E9CFA0',(.815,.624,.352),0,.88)
body.data.materials.clear();body.data.materials.append(skin)
for poly in body.data.polygons:poly.use_smooth=True
# Copy body-derived garments in neutral coordinates with genuine MPFB weights.
def garment(name,pred,mat,inflate,bone_prefixes=None):
    ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
    allowed={v.index for v in me.vertices if sum(g.weight for g in v.groups if body.vertex_groups[g.group].name.startswith(bone_prefixes))>.35} if bone_prefixes else None
    polys=[p for p in me.polygons if all(pred(me.vertices[i].co) and (allowed is None or i in allowed) for i in p.vertices)]
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
trousers=garment('GEO-olive wool trousers',lambda v:.16<v.z<1.02 and abs(v.x)<.34,olive,.015)
# Closed anatomical shoe hulls bridge toe clefts instead of exposing striped
# copied toes. The existing source foot bones articulate these rigid shoes.
import bmesh
bm=bmesh.new()
ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());boot_source=ev.to_mesh()
visible_ids={i for p in boot_source.polygons for i in p.vertices}
for sign in [-1,1]:
    points=[boot_source.vertices[i] for i in visible_ids if boot_source.vertices[i].co.z<.20 and sign*boot_source.vertices[i].co.x>0]
    chunk=[bm.verts.new(v.co+v.normal*.017) for v in points]
    bmesh.ops.convex_hull(bm,input=chunk,use_existing_faces=False)
    unused=[v for v in chunk if v.is_valid and not v.link_faces]
    bmesh.ops.delete(bm,geom=unused,context='VERTS')
ev.to_mesh_clear()
bmesh.ops.triangulate(bm,faces=list(bm.faces))
bmesh.ops.subdivide_edges(bm,edges=list(bm.edges),cuts=2,use_grid_fill=True)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
me=bpy.data.meshes.new('Closed anatomical shoe surfaces');bm.to_mesh(me);bm.free()
boots=bpy.data.objects.new('GEO-leather boots',me);bpy.context.collection.objects.link(boots);boots.data.materials.append(leather);boots.parent=rig
# A leather shoe is rigid around the foot; calf weights from the anatomical
# ankle must not stretch its toe box when the shin bends during the walk.
for side in ['l','r']:boots.vertex_groups.new(name='foot_'+side)
for v in boots.data.vertices:
    boots.vertex_groups['foot_'+('l' if v.co.x>0 else 'r')].add([v.index],1,'REPLACE')
for p in me.polygons:p.use_smooth=True
ar=boots.modifiers.new('Anatomical shoe weights','ARMATURE');ar.object=rig
bevel(boots,.004,3)
# Select the complete arm by native skin weights, rather than a clipped X band.
sleeves=garment('GEO-quilted sleeves',lambda v:True,linen,.027,('upperarm_','lowerarm_'))
# Pose: upright rather than spearman guard. World points account for rig elevation.
limb('upperarm_r','lowerarm_r',(-.31,-.20,1.18),(-.32,.40,1.22))
limb('upperarm_l','lowerarm_l',(.175,-.23,1.17),(.30,-.04,1.08))
aim_bone('hand_r',(0,0,-1));aim_bone('hand_l',(-.5,-.1,-.4))
for side in ['r','l']:
    for digit in ['index','middle','ring','pinky']:
        for k in [1,2,3]:
            p=rig.pose.bones[f'{digit}_{k:02d}_{side}'];p.rotation_mode='XYZ';p.rotation_euler.x=.65
# Three-quarter head orientation follows the source painting.
p=rig.pose.bones['head'];m=p.matrix.copy();pivot=m.translation.copy();m=Matrix.Rotation(.35,4,'Z')@m;m.translation=pivot;p.matrix=m;bpy.context.view_layer.update()
# Feet slightly apart, stable on the base.
limb('thigh_r','calf_r',(-.17,-.015,.10),(-.20,-.25,.48))
limb('thigh_l','calf_l',(.19,.015,.10),(.19,-.20,.48))
for side in ['l','r']:aim_bone('foot_'+side,(.04 if side=='l' else -.02,-1,0))
bpy.context.view_layer.update()
# Torso/skirt: shaped cloth with broad folds and real thickness, not a body primitive.
def cloth_rings(name,rings,mat,bone,folds=.007):
    vs=[];fs=[];N=64
    for j,(z,rx,ry) in enumerate(rings):
        for i in range(N):
            a=i*2*pi/N;f=folds*(sin(a*12+j*.4)+.3*sin(a*23))
            vs.append(((rx+f)*sin(a),-(ry+f)*cos(a),z+.008*cos(a*5)))
    for j in range(len(rings)-1):
        for i in range(N):a=j*N+i;b=j*N+(i+1)%N;fs.append((a,b,b+N,a+N))
    o=mesh(name,vs,fs,mat);solid(o,.009);bevel(o,.003);attach(o,bone);return o
cloth_rings('GEO-quilted gambeson',[(.86,.225,.16),(.98,.215,.16),(1.17,.18,.14),(1.26,.19,.15),(1.38,.21,.16),(1.49,.21,.14),(1.54,.16,.12)],linen,'spine_02')
# Stitched quilting channels: visible material relief instead of painted lines alone.
for i in range(21):
    a=-1.45+i*2.9/20;pts=[]
    for k in range(18):
        t=k/17;z=.87+.65*t;rx=.225-.045*sin(t*pi);ry=.164-.018*sin(t*pi)
        pts.append((rx*sin(a),-ry*cos(a)-.004,z))
    attach(curve('GEO-gambeson stitched channel',pts,.0015,string),'spine_02')
cloth_rings('GEO-waist leather belt',[(1.205,.192,.157),(1.245,.194,.158)],leather,'spine_02',.001)
# Buckle is a real open brass rectangle, with tongue and leather tail.
attach(curve('GEO-open belt buckle',[(.04,-.169,1.209),(.09,-.169,1.209),(.09,-.169,1.247),(.04,-.169,1.247),(.04,-.169,1.209)],.004,brass),'spine_02')
attach(curve('GEO-buckle tongue',[(.065,-.175,1.21),(.065,-.175,1.249)],.0025,brass),'spine_02')
# Shoulder cape, shaped wider at hem and raised around neck.
cloth_rings('GEO-hood shoulder cape',[(1.43,.29,.20),(1.46,.30,.19),(1.55,.245,.17),(1.62,.15,.14),(1.65,.12,.125)],wool,'spine_03',.011)
# Hood: open front cowl, elliptical rings around the actual head.
hp=rig.matrix_world@((rig.pose.bones['head'].head+rig.pose.bones['head'].tail)*.5)
print('HEAD',list(hp))
# Continuous hood: the face aperture closes over the brow into the same crown mesh.
vs=[];fs=[];N=64;J=32
for j in range(J+1):
    t=j/J; dome=max(0,(t-.65)/.35); radius=max(.035,math.sqrt(max(0,1-dome*dome)))
    z=hp.z-.13+.305*t; rx=.13*radius;ry=.145*radius
    opening=.67*(1-max(0,min(1,(t-.60)/.30)))
    for i in range(N+1):
        a=opening+(2*pi-2*opening)*i/N
        vs.append((hp.x+rx*sin(a),hp.y-ry*cos(a),z))
for j in range(J):
    for i in range(N):
        a=j*(N+1)+i;fs.append((a,a+1,a+N+2,a+N+1))
fs.append(tuple(J*(N+1)+i for i in range(N,-1,-1)))
hood=mesh('GEO-open wool hood',vs,fs,wool);solid(hood,.009)
su=hood.modifiers.new('Soft hood folds','SUBSURF');su.levels=1;attach(hood,'head')
for edge in [0,N]:
    attach(curve('GEO-hood stitched opening',[vs[j*(N+1)+edge] for j in range(29)],.003,wool),'head')
# Modelled moustache/beard, not paint on a flat face.
for sg in [-1,1]:
    attach(curve('GEO-moustache',[(hp.x+sg*.006,hp.y-.088,hp.z-.022),(hp.x+sg*.025,hp.y-.09,hp.z-.025),(hp.x+sg*.042,hp.y-.081,hp.z-.041)],.008,leather),'head')
# Crossbow: stock vertical at rest, steel prod across the lower shins, real string and stirrup.
weapon=bpy.data.objects.new('CTRL-crossbow',None);bpy.context.collection.objects.link(weapon);weapon.location=(-.275,-.26,1.17)
def weaponize(o):
    bpy.context.view_layer.update();w=o.matrix_world.copy();o.parent=weapon;o.matrix_world=w;return o
def box(name,loc,scale,mat):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(mat);bevel(o,.006,3);return o
weaponize(box('GEO-crossbow walnut tiller',(-.275,-.26,.67),(.057,.062,1.05),wood))
weaponize(box('GEO-crossbow trigger mechanism',(-.275,-.30,1.21),(.068,.018,.10),steel))
weaponize(curve('GEO-steel bow prod',[(-.61,-.28,.40),(-.53,-.25,.34),(-.41,-.245,.28),(-.275,-.24,.26),(-.14,-.245,.28),(-.02,-.25,.34),(.06,-.28,.40)],.013,steel))
weaponize(curve('GEO-taut bowstring',[(-.61,-.28,.40),(-.275,-.305,.40),(.06,-.28,.40)],.0027,string))
weaponize(curve('GEO-steel foot stirrup',[(-.31,-.26,.21),(-.325,-.26,.11),(-.225,-.26,.11),(-.24,-.26,.21)],.009,steel))
weaponize(curve('GEO-loaded bolt',[(-.275,-.30,.97),(-.275,-.30,.39)],.004,wood))
for z in [.3,.72,1.02]:weaponize(box('GEO-stock steel band',(-.275,-.26,z),(.063,.067,.021),steel))
for z in [.78,.81,.84,.87]:weaponize(curve('GEO-stock binding', [(-.305,-.30,z),(-.245,-.30,z)],.0025,string))
weapon.location.z+=.14
weapon.location.x+=.04
# Side bolt case, leather straps, brass studs.
case=cloth_rings('GEO-bolt leather case',[(.72,.063,.051),(1.01,.063,.051)],leather,'pelvis',.001)
case.location.x+=.27
for label,lo,hi in [('top band',.972,1.014),('bottom seam',.72,.737)]:
    band=cloth_rings('GEO-bolt leather case '+label,[(lo,.068,.055),(hi,.068,.055)],leather,'pelvis',.001)
    band.location.x+=.27
strap=curve('GEO-bolt leather case suspension',[(.24,-.025,1.21),(.28,-.035,1.10),(.29,-.053,1.00)],.009,leather);attach(strap,'pelvis')
for i in range(5):attach(curve('GEO-spare bolt',[(.25+i*.011,.02,.87),(.25+i*.011,.02,1.13)],.0035,wood),'pelvis')
# Shift figure to the painting's right-biased silhouette.
rig.location.x+=.065
weapon.location.x+=.005
weapon.scale.z=1.10
# Cream base is stationary for all poses.
bpy.ops.mesh.primitive_cylinder_add(vertices=96,radius=.52,depth=.075,location=(0,0,.0375));base=bpy.context.object;base.name='GEO-stationary cream stone';base.data.materials.append(stone);bevel(base,.012,3)
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=8;sc.cycles.use_denoising=True
sc.render.resolution_x=sc.render.resolution_y=256;sc.render.resolution_percentage=100;sc.render.film_transparent=True;sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA'
sc.world.color=(.15,.15,.15);sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast';sc.view_settings.exposure=.25
bpy.ops.object.camera_add(location=(0,-7,2.95));sc.camera=bpy.context.object;sc.camera.name='CAM-painting';sc.camera.data.type='ORTHO';sc.camera.data.ortho_scale=2.28;sc.camera.rotation_euler=(Vector((0,0,.90))-sc.camera.location).to_track_quat('-Z','Y').to_euler()
for name,loc,power,size,col in [('Warm key',(-3,-4,6),550,3,(1,.89,.72)),('Soft fill',(3,-3,3),140,4,(.85,.91,1)),('Cool rim',(2,3,4),360,2,(.73,.85,1))]:
    bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name=name;o.data.energy=power;o.data.size=size;o.data.color=col;o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
# Finish geometry before sampling frozen camera UVs.
import runpy
runpy.run_path('tools/art/anim3d/units/barbarian-crossbowman/refine.py',init_globals=globals())
runpy.run_path('tools/art/anim3d/units/barbarian-crossbowman/tailoring.py',init_globals=globals())
# Covered anatomy must not poke through the rigid leather shoe during rollover.
covered=body.vertex_groups.new(name='Covered inside leather shoes')
covered.add([v.index for v in body.data.vertices if v.co.z<.21],1,'REPLACE')
mask=body.modifiers.new('Anatomical feet enclosed by shoes','MASK');mask.vertex_group=covered.name;mask.invert_vertex_group=True
bpy.ops.wm.save_as_mainfile(filepath=str(M/'plain.blend'))
runpy.run_path('tools/art/anim3d/units/barbarian-crossbowman/fills.py',init_globals=globals())
# Fine grain, weave, pointiness edge wear and AO cavities are physical shader detail.
for mat in [skin,linen,wool,olive,leather,wood,steel,brass,stone]:
    n=mat.node_tree.nodes;l=mat.node_tree.links;s=n.get('Principled BSDF')
    tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=170 if mat in [linen,wool,olive] else 95;tex.inputs['Detail'].default_value=3
    bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.18;bump.inputs['Distance'].default_value=.003;l.new(tex.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],s.inputs['Normal'])
    ao=n.new('ShaderNodeAmbientOcclusion');ao.inputs['Distance'].default_value=.08
    mix=n.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=.3;mix.inputs[1].default_value=s.inputs['Base Color'].default_value;
    if s.inputs['Base Color'].is_linked:l.new(s.inputs['Base Color'].links[0].from_socket,mix.inputs[1])
    l.new(ao.outputs['Color'],mix.inputs[2]);l.new(mix.outputs[0],s.inputs['Base Color'])
    if mat in [steel,brass]:
        geo=n.new('ShaderNodeNewGeometry');r=n.new('ShaderNodeMapRange');r.inputs['From Min'].default_value=.35;r.inputs['From Max'].default_value=.6;r.inputs['To Min'].default_value=.65;r.inputs['To Max'].default_value=.23;l.new(geo.outputs['Pointiness'],r.inputs['Value']);l.new(r.outputs[0],s.inputs['Roughness'])
# Calibrate projection on the finished surfaces, never the unfinished cage.
records=runpy.run_path('tools/art/anim3d/units/barbarian-crossbowman/project.py',init_globals=globals())['records']
rig['neutral']=json.dumps({p.name:[list(row) for row in p.matrix_basis] for p in rig.pose.bones});rig['source']='CC0 MPFB 2.0.18 game_engine'
sc['projection']='Fixed per-vertex camera UV, alpha/incidence blend, true 3D geometry';sc['cream_target']='#E9CFA0'
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(M/'model.blend'))
(M/'model-info.json').write_text(json.dumps({'bones':len(rig.data.bones),'projection_meshes':records,'source':'MPFB 2.0.18 CC0','painting':'Project CC BY 4.0','limitations':'Generated linen, leather and skin fill unseen surfaces; generated clean stone plate on solid disc with live contact AO. View-specific projection needs review.'},indent=2))
print('BUILT',M/'model.blend')
