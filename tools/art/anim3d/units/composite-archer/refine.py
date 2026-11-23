"""Fit full-depth geometry in the rest view, preserving native skin weights."""
import bpy, os, json, math
import numpy as np
from pathlib import Path
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view

M = Path(os.environ['ANIM_ROOT']) / 'masters/composite-archer'
bpy.ops.wm.open_mainfile(filepath=str(M / 'plain.blend'))
sc = bpy.context.scene
cam = sc.camera
rig = bpy.data.objects['RIG-composite-archer']
# Source/destination landmarks in the unchanged 256px orthographic camera.
# The fitted field changes mesh coordinates, never texture coordinates or alpha.
landmarks = [
    ((110, 44), (100, 46)), ((112, 62), (108, 60)),
    ((73, 78), (53, 81)), ((95, 80), (86, 81)),
    ((111, 80), (105, 76)), ((140, 89), (139, 92)),
    ((195, 74), (192, 82)), ((162, 16), (156, 18)),
    ((162, 137), (168, 145)), ((108, 128), (103, 125)),
    ((77, 143), (77, 144)), ((77, 185), (63, 196)),
    ((150, 163), (151, 163)), ((177, 214), (171, 204)),
    ((111, 168), (108, 169)),
]
centres = np.array([a for a, b in landmarks], dtype=float)
delta = np.array([np.subtract(b, a) for a, b in landmarks])
sigma = 25.
kernel = np.exp(-np.sum((centres[:, None] - centres[None, :]) ** 2, axis=2) / (2 * sigma ** 2))
coeff = np.linalg.solve(kernel + np.eye(len(landmarks)) * .015, delta)
right = cam.matrix_world.to_quaternion() @ Vector((1, 0, 0))
up = cam.matrix_world.to_quaternion() @ Vector((0, 1, 0))
def fit(world, name=''):
    q = world_to_camera_view(sc, cam, world)
    xy = np.array((q.x * 256, (1 - q.y) * 256))
    displacement = np.exp(-np.sum((centres - xy) ** 2, axis=1) / (2 * sigma ** 2)) @ coeff
    if 'tunic skirt' in name or 'skirt stitched' in name:
        displacement[0] -= 7 * math.exp(-((xy[0] - 75) / 22) ** 2 - ((xy[1] - 164) / 25) ** 2)
    result = world + (right * float(displacement[0]) - up * float(displacement[1])) * (cam.data.ortho_scale / 256)
    if name.startswith(('GEO-MPFB anatomical', 'GEO-soft leather boots', 'GEO-patterned trousers')) and result.z < .09:
        # Seat low foot/sole vertices on the stone along their camera rays.
        # This changes depth while retaining their fitted screen coordinates.
        ray = cam.matrix_world.to_quaternion() @ Vector((0, 0, 1))
        result += ray * ((.09 - result.z) / ray.z)
    return result

# Freeze current MPFB morphs, since shape keys otherwise override vertex edits.
body = bpy.data.objects['GEO-MPFB anatomical archer']
if body.data.shape_keys:
    mixed = body.shape_key_add(name='Frozen current anatomy', from_mix=True)
    coords = [v.co.copy() for v in mixed.data]
    body.shape_key_clear()
    for v, co in zip(body.data.vertices, coords):
        v.co = co

# Finish all rigid surfaces before projecting; retain the skinning modifier.
for o in list(sc.objects):
    if o.type not in ('CURVE', 'MESH') or 'base' in o.name:
        continue
    bpy.ops.object.select_all(action='DESELECT')
    o.select_set(True)
    bpy.context.view_layer.objects.active = o
    if o.type == 'CURVE':
        bpy.ops.object.convert(target='MESH')
    arm = next((m for m in o.modifiers if m.type == 'ARMATURE'), None)
    if not arm:
        for mod in list(o.modifiers):
            bpy.ops.object.modifier_apply(modifier=mod.name)
    states = [(m, m.show_viewport) for m in o.modifiers]
    for mod, _ in states:
        if mod.type != 'ARMATURE':
            mod.show_viewport = False
    bpy.context.view_layer.update()
    ev = o.evaluated_get(bpy.context.evaluated_depsgraph_get())
    me = ev.to_mesh()
    assert len(me.vertices) == len(o.data.vertices)
    targets = [fit(ev.matrix_world @ v.co, o.name) for v in me.vertices]
    ev.to_mesh_clear()
    transforms = {}
    if arm:
        for group in o.vertex_groups:
            if group.name in rig.pose.bones:
                p = rig.pose.bones[group.name]
                transforms[group.index] = rig.matrix_world @ p.matrix @ p.bone.matrix_local.inverted() @ rig.matrix_world.inverted() @ o.matrix_world
    for v, target in zip(o.data.vertices, targets):
        weights = [(g.weight, transforms[g.group]) for g in v.groups if g.group in transforms]
        if weights:
            total = sum(w for w, mat in weights)
            skin = Matrix([[sum(w * mat[r][c] for w, mat in weights) / total for c in range(4)] for r in range(4)])
            v.co = skin.inverted() @ target
        else:
            v.co = o.matrix_world.inverted() @ target
    for mod, state in states:
        mod.show_viewport = state
    o.data.update()

# String attachment remains anatomical after fitting. Store its actual hand-local nock.
string = bpy.data.objects['GEO-bowstring']
points = [fit(Vector(v)) for v in json.loads(string['rest_points'])]
string['rest_points'] = json.dumps([list(p) for p in points])
hand = rig.matrix_world @ rig.pose.bones['hand_r'].matrix
rig['draw_local'] = list(hand.inverted() @ points[1])
for name in ('CTRL-bow', 'CTRL-arrow'):
    ctrl = bpy.data.objects[name]
    children = [(o, o.matrix_world.copy()) for o in ctrl.children]
    matrix = ctrl.matrix_world.copy()
    matrix.translation = fit(matrix.translation)
    ctrl.matrix_world = matrix
    bpy.context.view_layer.update()
    for o, world in children:
        o.matrix_world = world

sc.view_settings.view_transform = 'Standard'
sc.view_settings.look = 'None'
for o in sc.objects:
    if o.type == 'LIGHT':
        o.data.energy *= .55
sc['round'] = 2
sc['geometry_registration'] = 'Smooth rest-view fit with inverse skin transforms; camera depth preserved'
bpy.ops.wm.save_as_mainfile(filepath=str(M / 'registered.blend'))
(M / 'registration.json').write_text(json.dumps({'landmarks': landmarks, 'method': sc['geometry_registration']}, indent=2))
print('REGISTERED_READY')
