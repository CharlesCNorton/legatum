"""Register the real articulated legs to the painting, with bone registration.

The imported glTF hoof controls are independent roots. Fit them along with their
leg chains; moving only skin vertices leaves rubbery, disconnected fetlocks.
Native source actions remain available and supply the moving poses.
"""
import json
import bpy
from mathutils import Matrix, Vector
from bpy_extras.object_utils import world_to_camera_view

# Joint centers measured in the original 256px token; support fitted in depth.
JOINTS = {
    'BackLeg.L': (103, 132), 'BackUpperLeg.L': (111, 157),
    'BackLowerLeg.L': (97, 181), 'IKBackLeg.L': (100, 203), 'FFB.L': (103, 210),
    'BackLeg.R': (89, 137), 'BackUpperLeg.R': (96, 160),
    'BackLowerLeg.R': (98, 183), 'IKBackLeg.R': (109, 208), 'FFB.R': (116, 214),
    'FrontUpperLeg.L': (169, 142), 'FrontLowerLeg.L': (180, 176),
    'IKFrontLeg.L': (190, 205), 'FF.L': (195, 212),
    'FrontUpperLeg.R': (155, 144), 'FrontLowerLeg.R': (166, 171),
    'IKFrontLeg.R': (153, 185), 'FF.R': (148, 191),
}
SEGMENTS = {
    'BackLeg.L': 'BackUpperLeg.L', 'BackUpperLeg.L': 'BackLowerLeg.L',
    'BackLowerLeg.L': 'IKBackLeg.L', 'IKBackLeg.L': 'FFB.L',
    'BackLeg.R': 'BackUpperLeg.R', 'BackUpperLeg.R': 'BackLowerLeg.R',
    'BackLowerLeg.R': 'IKBackLeg.R', 'IKBackLeg.R': 'FFB.R',
    'FrontUpperLeg.L': 'FrontLowerLeg.L', 'FrontLowerLeg.L': 'IKFrontLeg.L',
    'IKFrontLeg.L': 'FF.L', 'FrontUpperLeg.R': 'FrontLowerLeg.R',
    'FrontLowerLeg.R': 'IKFrontLeg.R', 'IKFrontLeg.R': 'FF.R',
}


def fit_stance(scene):
    arm = bpy.data.objects['AnimalArmature']
    original = {p.name: arm.matrix_world @ p.matrix for p in arm.pose.bones}
    right = scene.camera.matrix_world.to_quaternion() @ Vector((1, 0, 0))
    up = scene.camera.matrix_world.to_quaternion() @ Vector((0, 1, 0))
    unit = scene.camera.data.ortho_scale / 256
    # Broaden native anatomy around its own joints before the pose fit. Small
    # radial changes preserve the limb axis and the original continuous topology.
    horse = bpy.data.objects['Horse']
    to_arm = arm.matrix_world.inverted() @ horse.matrix_world
    transforms = {p.name: to_arm.inverted() @ p.matrix @ p.bone.matrix_local.inverted() @ to_arm
                  for p in arm.pose.bones}
    # Imported control origins need not coincide with the visible skin joint.
    # Locate actual joints from shared weights on the evaluated rest mesh.
    evaluated = horse.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ v.co for v in mesh.vertices]
    evaluated.to_mesh_clear()
    weights_by_vertex = [{horse.vertex_groups[g.group].name: g.weight for g in v.groups}
                         for v in horse.data.vertices]
    anchors = {}
    for name in JOINTS:
        if name.startswith('BackLeg.'):
            parent = name.replace('BackLeg.', 'BackShoulder.')
        elif name.startswith('FrontUpperLeg.'):
            parent = name.replace('FrontUpperLeg.', 'FrontShoulder.')
        else:
            parent = next(n for n, child in SEGMENTS.items() if child == name)
        weights = [min(w.get(parent, 0), w.get(name, 0)) for w in weights_by_vertex]
        total = sum(weights)
        assert total > .01, f'No skin boundary for {parent} / {name}'
        anchors[name] = sum((p*w for p, w in zip(points, weights)), Vector())/total
    print('REGISTERED_SKIN_JOINTS', {n: tuple(round(v,3) for v in p) for n,p in anchors.items()})
    for v in horse.data.vertices:
        weights = {horse.vertex_groups[g.group].name: g.weight for g in v.groups
                   if horse.vertex_groups[g.group].name in transforms}
        total = sum(weights.values())
        skin = sum((transforms[n]*(w/total) for n, w in weights.items()),
                   Matrix(((0,)*4,)*4)) if total else Matrix.Identity(4)
        world = horse.matrix_world @ (skin @ v.co)
        delta = Vector()
        for name, weight in weights.items():
            if name not in SEGMENTS or name.startswith('IK'):
                continue
            a = anchors[name]
            b = anchors[SEGMENTS[name]]
            axis = (b-a).normalized()
            radial = world-a-axis*(world-a).dot(axis)
            amount = .45 if 'Lower' in name else .28
            delta += radial*(amount*weight)
        v.co = skin.inverted_safe() @ (horse.matrix_world.inverted() @ (world+delta))
    horse.data.update()
    targets = {}
    for name, (x, y) in JOINTS.items():
        w = anchors[name]
        q = world_to_camera_view(scene, scene.camera, w)
        targets[name] = w + (right*(x-q.x*256)-up*(y-(1-q.y)*256))*unit
    def apply_targets():
        # Pair independent hoof roots by shared skin weights, not screen proximity.
        for name in JOINTS:
            old = original[name]
            transform = Matrix.Identity(4)
            if name in SEGMENTS:
                child = SEGMENTS[name]
                src = anchors[child]-anchors[name]
                dst = targets[child]-targets[name]
                # Stretch only along the limb, preserving its cross-sectional area.
                axis = src.normalized()
                stretch = Matrix.Identity(3)
                ratio = dst.length/src.length
                for i in range(3):
                    for j in range(3):
                        stretch[i][j] += (ratio-1)*axis[i]*axis[j]
                transform = (src.rotation_difference(dst).to_matrix() @ stretch).to_4x4()
            fitted = Matrix.Translation(targets[name]) @ transform @ Matrix.Translation(-anchors[name]) @ old
            arm.pose.bones[name].matrix = arm.matrix_world.inverted() @ fitted
            bpy.context.view_layer.update()
    # Fit support in depth while preserving every painted screen-space joint.
    # The old mesh-only correction stretched tendons and left death's first
    # sample below the stone, causing the whole body to pop upward.
    support = {'FF.L': ('IKFrontLeg.L', .112), 'FFB.L': ('IKBackLeg.L', .112),
               'FFB.R': ('IKBackLeg.R', .112), 'FF.R': ('IKFrontLeg.R', .38)}
    depth = right.cross(up)
    for iteration in range(3):
        apply_targets()
        evaluated = horse.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh = evaluated.to_mesh()
        for foot, (control, height) in support.items():
            group = horse.vertex_groups[foot].index
            ids = [v.index for v in horse.data.vertices
                   if any(g.group == group and g.weight > .5 for g in v.groups)]
            sole = min((evaluated.matrix_world @ mesh.vertices[i].co).z for i in ids)
            shift = depth*((height-sole)/depth.z)
            targets[foot] += shift
            targets[control] += shift
        evaluated.to_mesh_clear()
    apply_targets()
    # Freeze the calibrated rest pose as an ordinary editable action.
    for p in arm.pose.bones:
        p.rotation_mode = 'QUATERNION'
        for prop in ('location', 'rotation_quaternion', 'scale'):
            p.keyframe_insert(prop, frame=0)
    arm['registered_stance'] = json.dumps({n: [list(row) for row in arm.pose.bones[n].matrix_basis] for n in JOINTS})
    scene['stance_method'] = 'Full-depth joint registration; independent glTF hoof roots included; native source motion retained'
