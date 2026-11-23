"""Rest-pose sculpture in camera coordinates, retaining depth and skin weights.

A smooth 3D displacement (constant along the view axis) registers anatomical
landmarks; it is baked into bind vertices, not applied to moving screen pixels.
The rig and all depth remain real. Subsequent motion uses the original weights.
"""
import bpy
import numpy as np
from mathutils import Matrix, Vector
from bpy_extras.object_utils import world_to_camera_view

class Registration:
    def __init__(self, scene, landmarks, radius=28):
        self.scene = scene
        self.radius = radius
        self.points = np.array([a for a,b in landmarks], dtype=float)
        delta = np.array([np.subtract(b,a) for a,b in landmarks])
        distance = ((self.points[:,None,:]-self.points[None,:,:])**2).sum(axis=2)
        self.weights = np.linalg.solve(np.exp(-distance/(2*radius**2)) + np.eye(len(delta))*.035, delta)
        self.right = scene.camera.matrix_world.to_3x3() @ Vector((1,0,0))
        self.up = scene.camera.matrix_world.to_3x3() @ Vector((0,1,0))
        self.scale = scene.camera.data.ortho_scale/256

    def world(self, world):
        q = world_to_camera_view(self.scene,self.scene.camera,world)
        point = np.array([q.x*256,(1-q.y)*256])
        kernel = np.exp(-((self.points-point)**2).sum(axis=1)/(2*self.radius**2))
        dx,dy = kernel @ self.weights
        return world + self.right*(float(dx)*self.scale) - self.up*(float(dy)*self.scale)

    def object(self, obj):
        arm = next((m.object for m in obj.modifiers if m.type=='ARMATURE'), None)
        if arm:
            transforms = {g.index:arm.pose.bones[g.name].matrix @ arm.data.bones[g.name].matrix_local.inverted()
                          for g in obj.vertex_groups if g.name in arm.pose.bones}
            for v in obj.data.vertices:
                groups = [(g.weight,transforms[g.group]) for g in v.groups if g.group in transforms and g.weight>0]
                if not groups: continue
                total=sum(w for w,m in groups)
                deform=Matrix([[sum(w*m[r][c] for w,m in groups)/total for c in range(4)] for r in range(4)])
                transform=arm.matrix_world @ deform @ arm.matrix_world.inverted() @ obj.matrix_world
                v.co=transform.inverted() @ self.world(transform @ v.co)
            obj.data.update()
        else:
            inv=obj.matrix_world.inverted()
            if obj.type=='MESH':
                for v in obj.data.vertices: v.co=inv@self.world(obj.matrix_world@v.co)
                obj.data.update()
            elif obj.type=='CURVE':
                for spline in obj.data.splines:
                    for p in spline.points:
                        p.co=(*(inv@self.world(obj.matrix_world@p.co.xyz)),1)
