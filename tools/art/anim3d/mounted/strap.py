"""Fit a solid baldric to the posed linen, along the original painted path."""
import bpy
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view


def fit_baldric(scene, rig):
    old = bpy.data.objects['Leather baldric']
    material = old.data.materials[0]
    bpy.data.objects.remove(old, do_unlink=True)
    shirt = bpy.data.objects['Rider linen shirt and sleeves']
    evaluated = shirt.evaluated_get(bpy.context.evaluated_depsgraph_get())
    inverse = evaluated.matrix_world.inverted()
    camera = scene.camera
    right = camera.matrix_world.to_3x3() @ Vector((1, 0, 0))
    up = camera.matrix_world.to_3x3() @ Vector((0, 1, 0))
    direction = camera.matrix_world.to_3x3() @ Vector((0, 0, -1))
    reference = rig.matrix_world @ rig.pose.bones['spine_03'].head
    q = world_to_camera_view(scene, camera, reference)
    vertices = []
    for j in range(19):
        t = j / 18
        for edge in (-1, 1):
            x, y = 113 + 24*t + edge*1.1, 65 + 36*t
            point = reference + right*((x/256-q.x)*camera.data.ortho_scale)
            point += up*((1-y/256-q.y)*camera.data.ortho_scale)
            origin = point - direction*5
            hit, local, normal, _ = evaluated.ray_cast(inverse@origin, inverse.to_3x3()@direction)
            if not hit:
                # Short shoulder/waist overhang inherits adjacent cloth depth.
                if not vertices:
                    raise RuntimeError('Baldric starts outside the linen surface')
                local = inverse @ point
                world = point + direction*((Vector(vertices[-1])-point).dot(direction))
            else:
                world = evaluated.matrix_world@local
            vertices.append(tuple(world-direction*.006))
    faces = [(2*j, 2*j+1, 2*j+3, 2*j+2) for j in range(18)]
    mesh = bpy.data.meshes.new('Fitted leather baldric mesh')
    mesh.from_pydata(vertices, [], faces); mesh.materials.append(material)
    obj = bpy.data.objects.new('Leather baldric', mesh)
    scene.collection.objects.link(obj)
    solid = obj.modifiers.new('Real leather thickness', 'SOLIDIFY'); solid.thickness = .005
    bevel = obj.modifiers.new('Soft worn strap edges', 'BEVEL'); bevel.width = .002; bevel.segments = 3
    obj.parent = rig; obj.parent_type = 'BONE'; obj.parent_bone = 'spine_03'
    bpy.context.view_layer.update(); obj.matrix_world = Matrix.Identity(4)
    return obj
