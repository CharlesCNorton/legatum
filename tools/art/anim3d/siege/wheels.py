"""Fit complete circular wheel assemblies to the painted outer tyre silhouettes.
The mount carries toe/camber; the wheel still rolls about its local axle, with its
original radius, thickness, spokes, hubs and editable full-depth geometry intact.
"""
import math
import bpy
import numpy as np
from mathutils import Matrix, Vector
from bpy_extras.object_utils import world_to_camera_view


def fit_wheels():
    scene = bpy.context.scene
    camera = scene.camera
    gun = bpy.data.objects['Gun travel and recoil']
    records = {}
    camera_inverse = np.array(camera.matrix_world.inverted(), dtype=float)
    gun_world = np.array(gun.matrix_world, dtype=float)
    for side, target in [(-1, [94, 120, 142, 220]), (1, [166, 112, 230, 212])]:
        wheel = bpy.data.objects[f'Wheel {side}']
        # Full outer tyre, including both faces of its 105mm width.
        points = [Vector((.525*math.cos(a), y, .525*math.sin(a)))
                  for y in [-.0525, .0525]
                  for a in [i*math.tau/128 for i in range(128)]]
        original = wheel.location.copy()

        def matrix(p):
            rot = Matrix.Rotation(float(p[2]), 4, 'Z') @ Matrix.Rotation(float(p[3]), 4, 'X')
            # Rest the complete tyre on the same cream top as the original gun.
            z = .105 - min((rot @ point).z for point in points)
            return Matrix.Translation((float(p[0]), float(p[1]), z)) @ rot

        def bounds(p):
            transform = camera_inverse @ gun_world @ np.array(matrix(p), dtype=float)
            pts = np.array([(*point, 1) for point in points]) @ transform.T
            xy = np.column_stack([128+pts[:, 0]*256/camera.data.ortho_scale,
                                  128-pts[:, 1]*256/camera.data.ortho_scale])
            return np.r_[xy.min(0), xy.max(0)]

        def residual(p):
            return np.r_[bounds(p)-target, p[2:]*.6]

        p = np.array([original.x, original.y, 0., 0.])
        lo = np.array([-.1, -.75 if side < 0 else .3, -.3, -.06])
        hi = np.array([.3, -.3 if side < 0 else .75, .3, .06])
        for _ in range(60):
            r = residual(p)
            jac = np.column_stack([(residual(p+np.eye(4)[j]*1e-4)-r)/1e-4 for j in range(4)])
            delta = np.linalg.solve(jac.T @ jac+np.eye(4)*.05, -jac.T @ r)
            candidates = [p]+[np.clip(p+delta*step, lo, hi) for step in [1., .5, .2, .05]]
            best = min(candidates, key=lambda q: np.linalg.norm(residual(q)))
            if np.max(abs(best-p)) < 1e-7:
                break
            p = best
        # Coordinate refinement is stable across active extrema of the tyre bounds.
        for step in [.02, .01, .004, .001, .0002]:
            for _ in range(20):
                choices=[p]+[np.clip(p+np.eye(4)[axis]*step*sign,lo,hi) for axis in range(4) for sign in [-1,1]]
                best=min(choices,key=lambda q: np.linalg.norm(residual(q)))
                if np.max(abs(best-p))<1e-8:break
                p=best
        mount = bpy.data.objects.new(f'Wheel mounting {side}', None)
        scene.collection.objects.link(mount)
        mount.parent = gun
        mount.matrix_basis = matrix(p)
        wheel.parent = mount
        wheel.matrix_basis = Matrix.Identity(4)
        records[wheel.name] = {'target_bounds_px': target, 'actual_bounds_px': bounds(p).tolist(),
                               'mount_parameters': p.tolist(), 'radius_m': .525,
                               'method': 'complete circular tyre fit; real toe/camber mounting, unchanged wheel depth'}
    bpy.context.view_layer.update()
    # Refit the solid axle to the two real wheel centres rather than leaving it behind.
    axle = bpy.data.objects['Iron axle']
    a = bpy.data.objects['Wheel -1'].matrix_world.translation
    b = bpy.data.objects['Wheel 1'].matrix_world.translation
    direction = b-a
    z = [v.co.z for v in axle.data.vertices]
    world = Matrix.Translation((a+b)*.5) @ direction.to_track_quat('Z', 'Y').to_matrix().to_4x4()
    world = world @ Matrix.Diagonal((1, 1, direction.length/(max(z)-min(z)), 1))
    axle.matrix_world = world
    scene['wheel_fit'] = 'Full circular assemblies fitted at rest, real mounting frames preserve rolling axes'
    return records
