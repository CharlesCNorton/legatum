"""Fit articulated limb landmarks along camera rays, retaining real segment lengths."""
import bpy
import json
import math
import os
from pathlib import Path
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view

M = Path(os.environ['ANIM_ROOT']) / 'masters/scout'
bpy.ops.wm.open_mainfile(filepath=str(M / 'scout-built.blend'))
sc = bpy.context.scene
rig = bpy.data.objects['Scout MPFB game_engine']
cam = sc.camera
cam.location.z = 2.9
cam.rotation_euler = (Vector((-.04, 0, .85)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
rig.location.x += .115
rig.location.z -= .045
base = bpy.data.objects['GEO-Stationary cream stone']
base.location.x += .115
bpy.context.view_layer.update()
right = cam.matrix_world.to_quaternion() @ Vector((1, 0, 0))
up = cam.matrix_world.to_quaternion() @ Vector((0, 1, 0))
ray = cam.matrix_world.to_quaternion() @ Vector((0, 0, -1))

def screen(world):
    p = world_to_camera_view(sc, cam, world)
    return Vector((p.x * 256, (1-p.y) * 256))

def on_ray(xy, near):
    delta = Vector(xy) - screen(near)
    return near + (right * delta.x - up * delta.y) * cam.data.ortho_scale / 256

def intersections(xy, centre, length):
    q = on_ray(xy, centre)
    perpendicular = q - centre
    remaining = length * length - perpendicular.length_squared
    if remaining < 0:
        raise ValueError(f'Unreachable projected landmark {xy}: {perpendicular.length} > {length}')
    offset = math.sqrt(remaining)
    return [q + ray * offset, q - ray * offset]

def aim(name, direction):
    p = rig.pose.bones[name]
    q = p.bone.matrix_local.to_quaternion()
    delta = (q @ Vector((0, 1, 0))).rotation_difference(direction.normalized())
    mat = (delta @ q).to_matrix().to_4x4()
    if 'arm_' in name: mat = mat @ Matrix.Diagonal((1, 1.17, 1, 1))
    if name=='calf_l': mat = mat @ Matrix.Diagonal((1, 1.16, 1, 1))
    mat.translation = p.head
    p.matrix = mat
    bpy.context.view_layer.update()

records = []
def limb(upper, lower, joint_xy, end_xy, prefer):
    a = rig.matrix_world @ rig.pose.bones[upper].head
    candidates = []
    for joint in intersections(joint_xy, a, rig.data.bones[upper].length * (1.17 if 'arm_' in upper else 1)):
        try:
            ends = intersections(end_xy, joint, rig.data.bones[lower].length * (1.17 if 'arm_' in lower else 1.16 if lower=='calf_l' else 1))
        except ValueError:
            continue
        for end in ends:
            candidates.append(((end-Vector(prefer)).length, joint, end))
    assert candidates, f'No reachable {upper} chain'
    _, joint, end = min(candidates, key=lambda v: v[0])
    inv = rig.matrix_world.inverted().to_3x3()
    aim(upper, inv @ (joint-a))
    aim(lower, inv @ (end-joint))
    records.append({'bone': lower, 'joint_target': joint_xy, 'end_target': end_xy,
                    'joint_actual': list(screen(rig.matrix_world @ rig.pose.bones[lower].head)),
                    'end_actual': list(screen(rig.matrix_world @ rig.pose.bones[lower].tail))})

for bone in rig.data.bones:
    if any(s in bone.name for s in ('arm_', 'hand_', 'foot_', 'ball_')): bone.inherit_scale='NONE'

# Pelvis remains fully three-dimensional; the raised knee folds forward in depth.
limb('thigh_l', 'calf_l', (188, 135), (184, 189), (.51, -.05, .22))
limb('thigh_r', 'calf_r', (130, 162), (113, 204), (-.08, -.18, .18))
aim('foot_l', Vector((.60, -.75, -.18)))
aim('foot_r', Vector((.05, -.98, -.16)))
limb('upperarm_l', 'lowerarm_l', (214, 57), (205, 29), (.65, -.16, 1.75))
aim('hand_l', Vector((-.98, -.12, -.06)))
limb('upperarm_r', 'lowerarm_r', (112, 78), (80, 94), (-.48, -.15, 1.2))
aim('hand_r', Vector((-.015, -.01, .09)))
head = rig.pose.bones['head']
head_matrix = head.matrix.copy()
head_matrix.translation += rig.matrix_world.inverted().to_3x3() @ (right*.030 + up*.020)
head.matrix = head_matrix
bpy.context.view_layer.update()

# Keep the hat a complete disc, but show its edge as in the source painting.
brim = bpy.data.objects['GEO-Travellers felt hat brim']
centre = brim.matrix_world.translation.copy()
rotation = Matrix.Rotation(1.20, 4, 'Z') @ Matrix.Rotation(-.35, 4, 'Y')
for name in ['GEO-Travellers felt hat brim', 'GEO-Hat crown']:
    ob = bpy.data.objects[name]
    ob.matrix_world = Matrix.Translation(-right*.095-up*.055) @ Matrix.Translation(centre) @ rotation @ Matrix.Translation(-centre) @ ob.matrix_world

# Keep the staff's grip, and fit its true shaft and fork to the painted direction.
hand = rig.pose.bones['hand_r']
for ob in [o for o in sc.objects if any(n in o.name for n in ('walking staff', 'Staff fork', 'Staff grain'))]:
    world = ob.matrix_world.copy()
    grip = rig.matrix_world @ hand.head
    # Source staff is a little more upright, with a short irregular fork.
    ob.matrix_world = Matrix.Translation(grip) @ Matrix.Rotation(-.07, 4, 'Y') @ Matrix.Translation(-grip) @ world

# Real anatomy contact, recorded independently of pixel registration.
body = bpy.data.objects['GEO-Scout MPFB anatomy']
bpy.context.view_layer.update()
ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
me = ev.to_mesh()
floor = min((body.matrix_world @ v.co).z for v in me.vertices)
ev.to_mesh_clear()
rig.location += ray * ((.100 - floor) / ray.z)
bpy.context.view_layer.update()

# Tailor the real skirt around the lifted thigh. Invert each blended skin matrix
# so this change remains in the bind mesh and follows the original bone weights.
tunic = bpy.data.objects['GEO-Folded short tunic']
transforms = {p.name: rig.matrix_world @ p.matrix @ p.bone.matrix_local.inverted()
              @ rig.matrix_world.inverted() @ tunic.matrix_world for p in rig.pose.bones}
for vertex in tunic.data.vertices:
    weights = [(g.weight, transforms[tunic.vertex_groups[g.group].name]) for g in vertex.groups
               if tunic.vertex_groups[g.group].name in transforms]
    skin = Matrix([[sum(w*m[i][j] for w,m in weights) for j in range(4)] for i in range(4)])
    world = skin @ vertex.co
    xy = screen(world)
    amount = max(0, min(1, (xy.y-88)/38))
    # Leftward skirt drape and a lifted right hem expose the scout's bent knee.
    fitted = (xy.x - 9*amount, xy.y - 8*amount*max(0, min(1, (xy.x-164)/25)))
    vertex.co = skin.inverted() @ on_ray(fitted, world)

# Narrow the physical cape's broad lower sweep. All shape keys receive the same
# rest-view fit, retaining their depth and their secondary-motion differences.
cloak = bpy.data.objects['GEO-Wind folded olive cloak']
points = [screen(cloak.matrix_world @ v.co) for v in cloak.data.shape_keys.key_blocks['Basis'].data]
left, right_edge = min(p.x for p in points), max(p.x for p in points)
top, bottom = min(p.y for p in points), max(p.y for p in points)
def fit_cape(co, matrix):
    world = matrix @ co
    p = screen(world)
    target = (57+(p.x-left)/(right_edge-left)*102, 62+(p.y-top)/(bottom-top)*118)
    return matrix.inverted() @ on_ray(target, world)
for key in cloak.data.shape_keys.key_blocks:
    for vertex in key.data:
        vertex.co = fit_cape(vertex.co, cloak.matrix_world)
hem = bpy.data.objects['GEO-Cloak worn hem']
for spline in hem.data.splines:
    for point in spline.points:
        point.co = (*fit_cape(point.co.xyz, hem.matrix_world), 1)

cowl = bpy.data.objects['GEO-Draped shoulder cowl']
points = [screen(cowl.matrix_world @ v.co) for v in cowl.data.vertices]
x0, x1 = min(p.x for p in points), max(p.x for p in points)
y0, y1 = min(p.y for p in points), max(p.y for p in points)
for vertex in cowl.data.vertices:
    world = cowl.matrix_world @ vertex.co
    p = screen(world)
    u=(p.x-x0)/(x1-x0);v=(p.y-y0)/(y1-y0)
    # Scarf hangs deepest below the throat, not as a horizontal collar ring.
    columns=[(0,57,61),(.20,51,64),(.42,49,70),(.62,58,80),(.80,60,82),(1,49,65)]
    for (a,hi0,lo0),(b,hi1,lo1) in zip(columns,columns[1:]):
        if a<=u<=b:
            t=(u-a)/(b-a);hi=hi0+(hi1-hi0)*t;lo=lo0+(lo1-lo0)*t
            break
    target = (125+u*67, hi+v*(lo-hi))
    vertex.co = cowl.matrix_world.inverted() @ on_ray(target, world)
# Tailor the raised-arm sleeve to the source shoulder, preserving its depth.
sleeve=bpy.data.objects['GEO-Folded sleeve l']
points=[screen(sleeve.matrix_world@v.co) for v in sleeve.data.vertices]
x0,x1=min(p.x for p in points),max(p.x for p in points)
y0,y1=min(p.y for p in points),max(p.y for p in points)
for vertex in sleeve.data.vertices:
    world=sleeve.matrix_world@vertex.co;p=screen(world)
    target=(184+(p.x-x0)/(x1-x0)*15,54+(p.y-y0)/(y1-y0)*23)
    vertex.co=sleeve.matrix_world.inverted()@on_ray(target,world)
# Pigment variation remains visible at token scale, supplementing fine bump.
stone=base.data.materials[0];n=stone.node_tree.nodes;l=stone.node_tree.links
noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=95
ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(.71,.51,.28,1);ramp.color_ramp.elements[1].color=(.92,.72,.44,1)
l.new(noise.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs[0],n.get('Principled BSDF').inputs['Base Color'])
rig['neutral_pose'] = json.dumps({p.name: [list(row) for row in p.matrix_basis] for p in rig.pose.bones})
rig['registered_targets'] = json.dumps({name: list(rig.pose.bones[name].head) for name in
    ['hand_l', 'hand_r', 'foot_l', 'foot_r', 'lowerarm_l', 'lowerarm_r', 'calf_l', 'calf_r']})
(M / 'registration.json').write_text(json.dumps({'method': 'camera-ray sphere intersections; true bone lengths',
    'pre_contact_landmarks': records, 'ground_correction_m': .100-floor,
    'camera': list(cam.location), 'note': 'Landmarks are local fits, not whole-image parity.'}, indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(M / 'scout-unpainted.blend'))
