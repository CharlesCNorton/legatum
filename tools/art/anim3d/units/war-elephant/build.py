"""Original elephant sculpture, articulated equipment and two CC0 MPFB riders.

Run with the shared Blender gate. All geometry is volumetric; the painting is
frozen-camera colour on surfaces, never opacity or a camera-facing cutout.
"""
import ast
import json
import math
import os
from pathlib import Path

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Matrix, Vector

ROOT = Path(os.environ['ANIM_ROOT'])
MASTER = ROOT / 'masters/war-elephant'
ASSETS = ROOT / 'assets/war-elephant'
MASTER.mkdir(parents=True, exist_ok=True)
sin, cos, pi = math.sin, math.cos, math.pi
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)


def material(name, color, metal=0, rough=.7):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.use_fake_user = True
    m.diffuse_color = (*color, 1)
    s = m.node_tree.nodes.get('Principled BSDF')
    s.inputs['Base Color'].default_value = (*color, 1)
    s.inputs['Metallic'].default_value = metal
    s.inputs['Roughness'].default_value = rough
    n = m.node_tree.nodes.new('ShaderNodeTexNoise')
    n.inputs['Scale'].default_value = 75
    n.inputs['Detail'].default_value = 3
    bump = m.node_tree.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = .18
    bump.inputs['Distance'].default_value = .018
    m.node_tree.links.new(n.outputs['Fac'], bump.inputs['Height'])
    m.node_tree.links.new(bump.outputs['Normal'], s.inputs['Normal'])
    return m


def mesh(name, vertices, faces, mat):
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], faces)
    data.update()
    obj = bpy.data.objects.new('GEO-' + name, data)
    bpy.context.collection.objects.link(obj)
    if mat:
        data.materials.append(mat)
    for p in data.polygons:
        p.use_smooth = True
    return obj


def apply(obj, mod):
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=mod.name)


def ellipsoid(name, loc, scale, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=40, ring_count=24, location=loc)
    obj = bpy.context.object
    obj.name = 'GEO-' + name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    for p in obj.data.polygons:
        p.use_smooth = True
    return obj


def box(name, loc, scale, mat, bevel=.025):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    obj = bpy.context.object
    obj.name = 'GEO-' + name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    mod = obj.modifiers.new('Rounded timber and worn edges', 'BEVEL')
    mod.width, mod.segments = bevel, 3
    apply(obj, mod)
    return obj


def tube(name, points, radii, mat, sides=16):
    """Closed, tapered 3D sweep, with transported circular sections."""
    pts = [Vector(p) for p in points]
    verts, faces = [], []
    for j, p in enumerate(pts):
        axis = (pts[min(j+1, len(pts)-1)] - pts[max(0, j-1)]).normalized()
        u = axis.cross(Vector((0, 1, 0))).normalized()
        if u.length < .5:
            u = axis.cross(Vector((1, 0, 0))).normalized()
        v = axis.cross(u).normalized()
        r = radii[j] if isinstance(radii, list) else radii
        for i in range(sides):
            a = i * 2*pi/sides
            verts.append(tuple(p + r*(u*cos(a)+v*sin(a))))
    for j in range(len(pts)-1):
        for i in range(sides):
            a = j*sides+i
            b = j*sides+(i+1)%sides
            faces.append((a, b, b+sides, a+sides))
    faces += [tuple(reversed(range(sides))), tuple((len(pts)-1)*sides+i for i in range(sides))]
    return mesh(name, verts, faces, mat)


skin = material('Elephant warm wrinkled grey', (.23, .21, .18), rough=.86)
red = material('Faded cinnabar quilted cloth', (.30, .065, .048), rough=.86)
gold = material('Worn golden braid', (.55, .33, .10), metal=1, rough=.43)
wood = material('Howdah aged honey timber', (.22, .12, .055), rough=.7)
ivory = material('Ivory tusks and linen', (.72, .62, .43), rough=.65)
rope = material('Woven rope harness', (.32, .24, .13), rough=.9)
dark = material('Eye and hair', (.018, .013, .009), rough=.55)
human_skin = material('Warm human skin', (.39, .23, .12), rough=.75)
bronze = material('Officer bronze', (.45, .29, .095), metal=1, rough=.4)
stone = material('Warm cream stone E9CFA0', (.68, .47, .25), rough=.85)

# Generated painted fills provide unseen surfaces, blended under camera colour.
for mat, kind in [(skin,'skin'),(red,'red'),(wood,'wood'),(ivory,'linen')]:
    tex=mat.node_tree.nodes.new('ShaderNodeTexImage')
    tex.image=bpy.data.images.load(str(ASSETS/f'fill-{kind}.png'));tex.image.pack()
    tex.projection='BOX';tex.projection_blend=.3
    coord=mat.node_tree.nodes.new('ShaderNodeTexCoord')
    mat.node_tree.links.new(coord.outputs['Generated'],tex.inputs['Vector'])
    bsdf=mat.node_tree.nodes.get('Principled BSDF')
    mat.node_tree.links.new(tex.outputs['Color'],bsdf.inputs['Base Color'])

# Continuous elephant skin: unioned anatomy, never a pile of visible spheres.
parts = [ellipsoid('elephant barrel', (-.30, 0, 1.63), (1.03, .58, .73), skin),
         ellipsoid('shoulder muscle', (.54, 0, 1.70), (.62, .60, .77), skin),
         ellipsoid('hindquarters', (-.99, 0, 1.50), (.50, .52, .66), skin),
         ellipsoid('skull domes', (1.02, 0, 1.97), (.51, .46, .59), skin),
         ellipsoid('cheek jaw', (1.13, 0, 1.67), (.42, .41, .35), skin)]
leg_specs = {}
for side, y in [('near', -.43), ('far', .43)]:
    for end, x in [('front', .43), ('back', -1.0)]:
        name = f'{end}.{side}'
        # The near foreleg steps slightly forward; hind legs carry the belly.
        footx = x + (.11 if end == 'front' else -.14)
        if side == 'far':
            footx += .15
        pts = [(x, y*.85, 1.58), (x-.04, y, 1.19),
               (x-.08, y, .78), (footx, y, .32), (footx, y, .18)]
        parts.append(tube(name + ' leg', pts, [.29, .25, .20, .205, .25], skin, 24))
        parts.append(ellipsoid(name + ' foot', (footx, y-.015, .22), (.28, .255, .17), skin))
        leg_specs[name] = (x, y, footx)

bpy.ops.object.select_all(action='DESELECT')
for p in parts:
    p.select_set(True)
bpy.context.view_layer.objects.active = parts[0]
bpy.ops.object.join()
body_elephant = bpy.context.object
body_elephant.name = 'GEO-Elephant continuous sculpt'
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
mod = body_elephant.modifiers.new('Union anatomical volumes', 'REMESH')
mod.mode = 'VOXEL'
mod.voxel_size = .047
apply(body_elephant, mod)
mod = body_elephant.modifiers.new('Relax skin joins', 'SMOOTH')
mod.factor, mod.iterations = .7, 5
apply(body_elephant, mod)
for p in body_elephant.data.polygons:
    p.use_smooth = True

# A dedicated elephant skeleton, with separate lower limbs and a six-joint trunk.
adata = bpy.data.armatures.new('Elephant anatomical skeleton')
erig = bpy.data.objects.new('RIG-Elephant', adata)
bpy.context.collection.objects.link(erig)
bpy.context.view_layer.objects.active = erig
erig.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')


def bone(name, head, tail, parent=None):
    b = adata.edit_bones.new(name)
    b.head, b.tail = head, tail
    if parent:
        b.parent = adata.edit_bones[parent]
    return b


bone('body', (0, 0, 1.2), (0, 0, 2.1))
bone('head', (.70, 0, 1.94), (1.35, 0, 1.94), 'body')
for name, (x, y, footx) in leg_specs.items():
    bone(name, (x, y, 1.5), (x-.06, y, .82), 'body')
    bone(name+'.lower', (x-.06, y, .82), (footx, y, .21), name)
trunk_pts = [(1.34, -.015, 2.02), (1.48, -.015, 1.72), (1.62, -.015, 1.61),
             (1.82, -.015, 1.66), (1.90, -.015, 1.90), (1.83, -.015, 2.13),
             (1.79, -.015, 2.29), (1.88, -.015, 2.30)]
for j in range(7):
    bone(f'trunk{j}', trunk_pts[j], trunk_pts[j+1], 'head' if j == 0 else f'trunk{j-1}')
for side, y in [('near', -.37), ('far', .37)]:
    bone('ear.'+side, (.80, y, 2.17), (.60, y*1.8, 1.70), 'head')
bone('tail', (-1.28, .1, 1.8), (-1.48, .12, .70), 'body')
bpy.ops.object.mode_set(mode='OBJECT')


def bind(obj, weights):
    for name in adata.bones.keys():
        obj.vertex_groups.new(name=name)
    for v in obj.data.vertices:
        for name, weight in weights(obj.matrix_world @ v.co).items():
            if weight > .00001:
                obj.vertex_groups[name].add([v.index], weight, 'REPLACE')
    mod = obj.modifiers.new('Elephant skeletal skinning', 'ARMATURE')
    mod.object = erig
    return obj


def body_weights(v):
    if v.z < 1.30:
        name = min(leg_specs, key=lambda n: (v.x-leg_specs[n][0])**2+(v.y-leg_specs[n][1])**2)
        upper = min(1, max(0, (v.z-.63)/.35))
        torso = min(1, max(0, (v.z-1.02)/.30))
        return {'body': torso, name: upper*(1-torso), name+'.lower': (1-upper)*(1-torso)}
    head = min(1, max(0, (v.x-.62)/.35))
    return {'body': 1-head, 'head': head}


bind(body_elephant, body_weights)
sub = body_elephant.modifiers.new('Smooth sculpt', 'SUBSURF')
sub.levels = sub.render_levels = 1


def attach(obj, name='body'):
    bpy.context.view_layer.update()
    world = obj.matrix_world.copy()
    obj.parent, obj.parent_type, obj.parent_bone = erig, 'BONE', name
    bpy.context.view_layer.update()
    obj.matrix_world = world
    return obj


trunk = tube('Articulated curled trunk', trunk_pts, [.29, .24, .18, .14, .12, .095, .07, .045], skin, 28)


def trunk_weights(v):
    distances = sorted(((v-Vector(p)).length, j) for j, p in enumerate(trunk_pts[:-1]))[:2]
    total = sum(1/max(.035, d)**2 for d, j in distances)
    return {f'trunk{j}': 1/max(.035, d)**2/total for d, j in distances}


bind(trunk, trunk_weights)
sub = trunk.modifiers.new('Trunk organic surface', 'SUBSURF')
sub.levels = sub.render_levels = 2
for sg, side in [(-1, 'near'), (1, 'far')]:
    # Radial fan, real dished thickness, folded edge rather than an opaque plane.
    center = Vector((.78, sg*.46, 1.97))
    verts = [tuple(center)]
    outline = [(0, 0, .30), (-.23, .12, .29), (-.38, .23, .16),
               (-.40, .25, -.08), (-.26, .17, -.39), (-.04, .05, -.43), (.11, -.01, -.19)]
    for x, y, z in outline:
        verts.append(tuple(center+Vector((x, sg*y, z))))
    ear = mesh('Sculpted ear '+side, verts, [(0, i+1, (i+1)%7+1) for i in range(7)], skin)
    solid = ear.modifiers.new('Ear thickness', 'SOLIDIFY')
    solid.thickness = .065
    sub = ear.modifiers.new('Rounded ear edge', 'SUBSURF')
    sub.levels = sub.render_levels = 2
    attach(ear, 'ear.'+side)
    tusk = tube('Curved ivory tusk '+side,
                [(1.35, sg*.28, 1.67), (1.48, sg*.32, 1.43),
                 (1.73, sg*.35, 1.20), (2.01, sg*.36, 1.12), (2.12, sg*.36, 1.16)],
                [.105, .09, .062, .029, .004], ivory, 20)
    sub = tusk.modifiers.new('Polished ivory curvature', 'SUBSURF')
    sub.levels = sub.render_levels = 2
    attach(tusk, 'head')
    attach(ellipsoid('Elephant eye '+side, (1.21, sg*.397, 2.05), (.055, .025, .033), dark), 'head')
    attach(tube('Eye brow '+side, [(1.13, sg*.408, 2.09), (1.20, sg*.431, 2.105), (1.28, sg*.398, 2.08)], .027, skin), 'head')
for name, (x, y, footx) in leg_specs.items():
    for j in range(4):
        a = -.9+j*.6
        nail = ellipsoid('Toenail '+name, (footx+.23*cos(a), y+.22*sin(a), .18), (.055, .063, .055), ivory)
        attach(nail, name+'.lower')
attach(tube('Elephant tail', [(-1.25,.2,1.90),(-1.48,.20,1.43),(-1.57,.2,.95),(-1.65,.2,.76)], [.07,.055,.035,.025], skin), 'tail')
attach(ellipsoid('Tail dark tuft', (-1.65,.2,.72), (.055,.05,.14), dark), 'tail')

# Saddle cloth: a draped, folded surface with true thickness and tassels.
vs, fs = [], []
for j in range(25):
    x = -1.13+j/24*1.56
    for i in range(33):
        t = -1+i/16
        y = .65*sin(t*pi/2)
        z = 2.34-.97*abs(t)**1.55+.016*cos(i*1.6+j*.8)
        vs.append((x, y, z))
for j in range(24):
    for i in range(32):
        a = j*33+i
        fs.append((a,a+1,a+34,a+33))
cloth = mesh('Quilted elephant saddle cloth', vs, fs, red)
solid = cloth.modifiers.new('Woven cloth thickness', 'SOLIDIFY')
solid.thickness = .025
attach(cloth)
for sg in [-1,1]:
    y=sg*.666
    attach(tube('Gold cloth hem', [(-1.13,y,2.25),(-1.13,y,1.37),(.43,y,1.37),(.43,y,2.25)], .025, gold))
    for i in range(15):
        x=-1.10+i*.105
        attach(tube('Hanging golden fringe', [(x,y,1.37),(x+.007,y,1.25)], [.028,.038], rope))
    # Raised quilt stitches, visible from sides and preserving a crafted finish.
    for i in range(9):
        for j in range(5):
            x=-1.04+i*.17; z=1.47+j*.145
            attach(tube('Diamond saddle stitching',[(x,y+.012*sg,z),(x+.08,y+.012*sg,z+.07),(x+.16,y+.012*sg,z),(x+.08,y+.012*sg,z-.07),(x,y+.012*sg,z)],.006,gold))
    for x in [-1.08,.42]:
        attach(tube('Saddle leather load strap',[(x,sg*.53,2.34),(x,sg*.69,1.72),(x,sg*.59,1.17)],.046,rope))
    attach(tube('Chest rope harness',[(.57,sg*.48,1.97),(.91,sg*.54,1.30),(1.16,sg*.39,1.31)],.035,rope))

# Crown cloth over the forehead follows the head, with a raised braided edge.
vs, fs = [], []
for j in range(13):
    x=.66+j*.067
    for i in range(17):
        t=-1+i/8
        vs.append((x,.46*t,2.52-.24*t*t-.21*((x-.91)/.55)**2))
for j in range(12):
    for i in range(16):
        a=j*17+i;fs.append((a,a+1,a+18,a+17))
cap=mesh('Red gold forehead cloth',vs,fs,red)
solid=cap.modifiers.new('Cloth thickness','SOLIDIFY');solid.thickness=.025
attach(cap,'head')
for sg in [-1,1]:
    attach(tube('Forehead golden border',[(.66+j*.067,sg*.46,2.28-.21*((.66+j*.067-.91)/.55)**2) for j in range(13)],.025,gold),'head')

# Howdah is open inside, built plank by plank, with joints, edge wear and rivets.
attach(box('Howdah floor',(-.48,0,2.51),(1.22,.98,.12),wood))
for sg in [-1,1]:
    for j in range(9):
        attach(box('Howdah individual plank',(-1.02+j*.137,sg*.48,2.76),(.128,.055,.42),wood,.012))
    for z in [2.56,2.94]:
        attach(box('Howdah horizontal rail',(-.48,sg*.52,z),(1.31,.10,.10),wood))
    for x in [-1.09,-.48,.13]:
        attach(box('Howdah reinforced post',(x,sg*.53,2.80),(.085,.105,.62),wood))
        attach(ellipsoid('Bronze post finial',(x,sg*.53,3.13),(.073,.073,.07),bronze))
        for z in [2.60,2.91]:
            attach(ellipsoid('Howdah rivet',(x,sg*.591,z),(.022,.012,.022),gold))
for x in [-1.10,.14]:
    attach(box('Howdah end wall',(x,0,2.75),(.07,.95,.40),wood))

# Match the narrower timber silhouette without flattening its depth.
bpy.context.view_layer.update()
for obj in list(bpy.context.scene.objects):
    if obj.name.startswith(('GEO-Howdah','GEO-Bronze post')):
        transform=Matrix.Translation((-.28,0,0)) @ Matrix.Diagonal((.85,1,1,1)) @ Matrix.Translation((.48,0,0))
        obj.matrix_world=transform @ obj.matrix_world

# MPFB human topology and original skin weights; no primitive human anatomy.
helpers = {'aim_bone','limb','fitted_shell'}
for node in ast.parse(Path('tools/art/anim3d/scene.py').read_text()).body:
    if isinstance(node,ast.FunctionDef) and node.name in helpers:
        exec(compile(ast.Module(body=[node],type_ignores=[]),'<MPFB helpers>','exec'))


def solid(obj, thickness):
    m=obj.modifiers.new('Clothing thickness','SOLIDIFY');m.thickness=thickness
    return obj


def bevel(obj,width):
    m=obj.modifiers.new('Clothing edge','BEVEL');m.width=width;m.segments=2
    return obj


bpy.ops.preferences.addon_enable(module='bl_ext.user_default.mpfb')
from bl_ext.user_default.mpfb.services.humanservice import HumanService
from bl_ext.user_default.mpfb.services.targetservice import TargetService

for role, seat, scale in [('Officer',(-.23,0,2.98),.78),('Mahout',(.73,-.02,2.49),.70)]:
    before=set(bpy.data.objects)
    macro=TargetService.get_default_macro_info_dict()
    macro.update(gender=1.,age=.42,muscle=.65,weight=.5,height=.46,proportions=.6)
    macro['race']={'caucasian':.15,'african':.25,'asian':.60}
    body=HumanService.create_human(macro_detail_dict=macro)
    body.name='GEO-'+role+' MPFB anatomy'
    bpy.context.view_layer.update()
    ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
    height=max(v.co.z for v in me.vertices)-min(v.co.z for v in me.vertices)
    ev.to_mesh_clear()
    body.scale=(1.72/height,)*3
    bpy.context.view_layer.objects.active=body
    bpy.ops.object.select_all(action='DESELECT');body.select_set(True)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    rig=HumanService.add_builtin_rig(body,'game_engine');rig.name='RIG-'+role+' MPFB'
    body.data.materials.clear();body.data.materials.append(human_skin)
    for p in body.data.polygons:p.use_smooth=True
    fitted_shell(role+' linen garment',lambda v:.72<v.z<1.12,ivory,.018)
    if role=='Officer':
        fitted_shell(role+' bronze cuirass',lambda v:1.04<v.z<1.43 and abs(v.x)<.24,bronze,.017)
        fitted_shell(role+' red shoulder tunic',lambda v:1.30<v.z<1.48,red,.024)
    # Seated hips, knees forward, bare lower legs hanging along the animal.
    for sg,side in [(1,'l'),(-1,'r')]:
        limb('thigh_'+side,'calf_'+side,(sg*.31,-.31,.50),(sg*.53,-.64,.93))
        limb('upperarm_'+side,'lowerarm_'+side,(sg*.25,-.39,1.06),(sg*.47,-.22,1.20))
    # Headwear is actual fitted geometry, face stays exposed.
    head=ellipsoid(role+' helmet' if role=='Officer' else role+' turban',(0,.01,1.66),(.107,.121,.115),bronze if role=='Officer' else ivory)
    bpy.context.view_layer.update();world=head.matrix_world.copy()
    head.parent=rig;head.parent_type='BONE';head.parent_bone='head';bpy.context.view_layer.update();head.matrix_world=world
    for j in range(4):
        ring=tube(role+' headwrap braid',[(.111*sin(i*2*pi/40),.01+.122*cos(i*2*pi/40),1.67+j*.018) for i in range(41)],.012,gold if role=='Officer' else ivory)
        bpy.context.view_layer.update();world=ring.matrix_world.copy()
        ring.parent=rig;ring.parent_type='BONE';ring.parent_bone='head';bpy.context.view_layer.update();ring.matrix_world=world
    # Root parent transforms the entire fitted human from +Y model convention to +X.
    group=bpy.data.objects.new('CTRL-'+role,None);bpy.context.collection.objects.link(group)
    for obj in set(bpy.data.objects)-before:
        if obj != group and obj.parent is None:
            obj.parent=group
    group.rotation_euler.z=pi/2
    group.scale=(scale,)*3
    group.location=Vector(seat)-Vector((0,0,1.0*scale))
    attach(group)

attach(tube('Mahout guiding staff',[(.93,-.30,2.55),(1.57,-.30,2.67)],.016,wood))

bpy.ops.mesh.primitive_cylinder_add(vertices=96,radius=1.48,depth=.13,location=(-.12,0,.055))
base=bpy.context.object;base.name='GEO-Stationary cream stone base';base.data.materials.append(stone)
m=base.modifiers.new('Stone eased rim','BEVEL');m.width=.045;m.segments=3;apply(base,m)

sc=bpy.context.scene
cam_data=bpy.data.cameras.new('CAM-Painting matched orthographic')
cam=bpy.data.objects.new(cam_data.name,cam_data);bpy.context.collection.objects.link(cam)
cam.location=(3,-10,4.1)
target=Vector((.19,0,1.65))
cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
cam_data.type='ORTHO';cam_data.ortho_scale=4.15;sc.camera=cam
for name,location,power,color,size in [
    ('key',(-3,-5,7),700,(1,.85,.65),5),
    ('fill',(5,-3,4),180,(.85,.9,1),4),
    ('rim',(1,4,6),450,(.7,.8,1),3)]:
    data=bpy.data.lights.new('LGT-'+name,'AREA');data.energy=power;data.color=color;data.shape='DISK';data.size=size
    obj=bpy.data.objects.new(data.name,data);bpy.context.collection.objects.link(obj);obj.location=location
    obj.rotation_euler=(Vector((0,0,1.5))-obj.location).to_track_quat('-Z','Y').to_euler()
sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs[0].default_value=(.65,.71,.8,1)
sc.world.node_tree.nodes['Background'].inputs[1].default_value=.25
sc.render.engine='CYCLES';sc.cycles.samples=4;sc.cycles.use_denoising=True
sc.render.film_transparent=True;sc.render.resolution_x=sc.render.resolution_y=512
sc.render.resolution_percentage=100
sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast'
sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA'
sc.render.image_settings.color_depth='8'
sc['unit']='war-elephant';sc['source']='Original elephant sculpture; MPFB CC0 riders; project painting'
bpy.context.view_layer.update()
erig.pose.bones['body'].location.y = .08
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(MASTER/'plain.blend'))

# Frozen-camera projection: evaluated pose coordinates, fixed UVs, facing blend.
painting=bpy.data.images.load(str(ASSETS/'painting-aligned.png'))
view=(cam.location-target).normalized()
projected=[]
for obj in list(sc.objects):
    if obj.type!='MESH' or obj==base:
        continue
    states=[(m,m.show_viewport) for m in obj.modifiers]
    for m,state in states:
        if m.type!='ARMATURE':m.show_viewport=False
    bpy.context.view_layer.update()
    ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
    assert len(me.vertices)==len(obj.data.vertices),obj.name
    coords=[];weights=[]
    for v in me.vertices:
        q=world_to_camera_view(sc,cam,ev.matrix_world@v.co)
        coords.append((q.x,q.y))
        normal=(ev.matrix_world.to_3x3().inverted().transposed()@v.normal).normalized()
        weights.append(max(0,min(1,(normal.dot(view)-.05)/.40)))
    ev.to_mesh_clear()
    for m,state in states:m.show_viewport=state
    uv=obj.data.uv_layers.new(name='Painting projection')
    attr=obj.data.color_attributes.new(name='Painting incidence',type='FLOAT_COLOR',domain='CORNER')
    for i,loop in enumerate(obj.data.loops):
        uv.data[i].uv=coords[loop.vertex_index]
        attr.data[i].color=(weights[loop.vertex_index],)*3+(1,)
    for index,old in enumerate(list(obj.data.materials)):
        mat=old.copy();mat.name=obj.name+' painted';obj.data.materials[index]=mat
        nodes=mat.node_tree.nodes;links=mat.node_tree.links;s=nodes.get('Principled BSDF')
        tex=nodes.new('ShaderNodeTexImage');tex.image=painting;tex.extension='CLIP'
        uvnode=nodes.new('ShaderNodeUVMap');uvnode.uv_map='Painting projection';links.new(uvnode.outputs[0],tex.inputs['Vector'])
        incidence=nodes.new('ShaderNodeVertexColor');incidence.layer_name='Painting incidence'
        mult=nodes.new('ShaderNodeMath');mult.operation='MULTIPLY';links.new(incidence.outputs[0],mult.inputs[0]);links.new(tex.outputs['Alpha'],mult.inputs[1])
        mix=nodes.new('ShaderNodeMixRGB');mix.inputs[1].default_value=s.inputs['Base Color'].default_value
        
        if s.inputs['Base Color'].is_linked:
            links.new(s.inputs['Base Color'].links[0].from_socket,mix.inputs[1])
        links.new(mult.outputs[0],mix.inputs[0]);links.new(tex.outputs['Color'],mix.inputs[2]);links.new(mix.outputs[0],s.inputs['Base Color'])
        links.new(mix.outputs[0],s.inputs['Emission Color']);s.inputs['Emission Strength'].default_value=.18
    projected.append(obj.name)
painting.pack()
sc['projected_meshes']=json.dumps(projected)
bpy.ops.wm.save_as_mainfile(filepath=str(MASTER/'war-elephant.blend'))
print('BUILT',len(projected),'projected meshes; original elephant rig and two MPFB riders')
