"""Solid diamond-section sabre fitted to the reference arc before projection."""
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view


def fit_blade(scene):
    blade = bpy.data.objects['GEO-sabre-blade']
    assert len(blade.data.vertices) == 100
    right = scene.camera.matrix_world.to_quaternion() @ Vector((1, 0, 0))
    up = scene.camera.matrix_world.to_quaternion() @ Vector((0, 1, 0))
    depth = right.cross(up)
    unit = scene.camera.data.ortho_scale/256
    def point(t):
        a,b,c,d = [Vector(p) for p in [(83,47),(95,29),(115,16),(132,12.5)]]
        return a*(1-t)**3+b*3*(1-t)**2*t+c*3*(1-t)*t*t+d*t**3
    for j in range(25):
        ring = list(blade.data.vertices)[j*4:j*4+4]
        world = sum((blade.matrix_world @ v.co for v in ring),Vector())/4
        q = world_to_camera_view(scene,scene.camera,world)
        t = j/24
        p = point(t)
        world += (right*(p.x-q.x*256)-up*(p.y-(1-q.y)*256))*unit
        tangent = (point(min(1,t+.01))-point(max(0,t-.01))).normalized()
        across = right*(-tangent.y)-up*tangent.x
        width = (1.0*(1-t)**.55+.05)*unit
        for v,delta in zip(ring,[across*width,depth*.003,-across*width,-depth*.003]):
            v.co = blade.matrix_world.inverted() @ (world+delta)
    blade.data.update()
