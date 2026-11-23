"""Fit solid crossbelts to the posed coat using measured painting camera rays.
The ribbons follow real coat depth and inherit its bone transform in every clip.
No screen-space shader, flattened body or texture-coordinate warp is used.
"""
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view


def fit_crossbelts():
    scene = bpy.context.scene
    camera = scene.camera
    coat = bpy.data.objects['Tailored blue coat body']
    toward = camera.matrix_world.to_quaternion() @ Vector((0, 0, 1))
    right = camera.matrix_world.to_quaternion() @ Vector((1, 0, 0))
    up = camera.matrix_world.to_quaternion() @ Vector((0, 1, 0))
    bpy.context.view_layer.update()
    evaluated = coat.evaluated_get(bpy.context.evaluated_depsgraph_get())
    inverse = evaluated.matrix_world.inverted()
    # Use the actual front surface, including its sculpted folds, as the fitting form.
    vertices = [evaluated.matrix_world @ v.co for v in evaluated.to_mesh().vertices]
    projected = [(world_to_camera_view(scene, camera, v), v) for v in vertices]
    evaluated.to_mesh_clear()

    def surface(x, y, clearance):
        origin = camera.matrix_world.translation + right * ((x / 256 - .5) * camera.data.ortho_scale)
        origin += up * ((.5 - y / 256) * camera.data.ortho_scale)
        hit, point, normal, face = evaluated.ray_cast(inverse @ origin, inverse.to_3x3() @ -toward)
        if hit:
            return evaluated.matrix_world @ point + toward * clearance
        # The short strap ends drape beyond the coat silhouette. Preserve the depth of
        # its nearest actual surface, rather than inventing a camera-facing flat plane.
        _, nearest = min(projected, key=lambda item: (item[0].x * 256 - x)**2 + ((1-item[0].y)*256-y)**2)
        return origin + toward * (nearest-origin).dot(toward) + toward * clearance

    old = bpy.data.objects['Ivory cross belt']
    material = old.data.materials[0]
    stitch_material = bpy.data.materials['Siege exposed oak']
    for obj in list(bpy.data.objects):
        if obj.name.startswith(('Ivory cross belt', 'Ivory belt hand stitching', 'Crossbelt brass buckle', 'Crossbelt buckle pin')):
            bpy.data.objects.remove(obj, do_unlink=True)
    # Shoulder-to-waist belt beneath the longer, curved pouch belt.
    paths = [[(76, 62), (81, 68), (88, 78), (95, 88), (100, 99)],
             [(104, 65), (101, 74), (95, 83), (84, 92), (71, 100), (59, 105)]]
    for index, path in enumerate(paths):
        points = []
        for a, b in zip(path, path[1:]):
            points.extend(Vector(a).lerp(Vector(b), j / 8) for j in range(8))
        points.append(Vector(path[-1]))
        pairs = []
        for i, point in enumerate(points):
            tangent = points[min(i+1,len(points)-1)]-points[max(i-1,0)]
            side = Vector((-tangent.y,tangent.x)).normalized() * 2.1
            pairs.append([surface(*(point-side), .008+index*.008), surface(*(point+side), .008+index*.008)])
        mesh = bpy.data.meshes.new('Fitted crossbelt')
        mesh.from_pydata([coat.matrix_world.inverted() @ v for pair in pairs for v in pair], [],
                         [(2*i,2*i+1,2*i+3,2*i+2) for i in range(len(pairs)-1)])
        mesh.materials.append(material)
        obj = bpy.data.objects.new('Ivory cross belt',mesh)
        bpy.context.collection.objects.link(obj)
        obj.parent = coat
        solid = obj.modifiers.new('Leather strap thickness','SOLIDIFY');solid.thickness=.006
        bevel = obj.modifiers.new('Worn strap bevel','BEVEL');bevel.width=.0015;bevel.segments=3
        for poly in mesh.polygons:poly.use_smooth=True
        for i in range(1,len(pairs)-1,2):
            for side in (0,1):
                a = pairs[i][side].lerp(pairs[i][1-side], .1)+toward*.0035
                b = pairs[i+1][side].lerp(pairs[i+1][1-side], .1)+toward*.0035
                curve = bpy.data.curves.new('Crossbelt stitch','CURVE');curve.dimensions='3D'
                spline=curve.splines.new('POLY');spline.points.add(1)
                for p,v in zip(spline.points,(a,b)):p.co=(*(coat.matrix_world.inverted() @ v),1)
                curve.bevel_depth=.0007;curve.bevel_resolution=1;curve.materials.append(stitch_material)
                stitch=bpy.data.objects.new('Ivory belt hand stitching',curve);bpy.context.collection.objects.link(stitch);stitch.parent=coat
    # Collar facing sits above the cloth instead of being buried in the torso shell.
    curve=bpy.data.curves.new('Raised red collar facing','CURVE');curve.dimensions='3D'
    spline=curve.splines.new('POLY');path=[(82,61),(87,64),(92,66),(98,63)]
    spline.points.add(len(path)-1)
    for point,xy in zip(spline.points,path):
        point.co=(*(coat.matrix_world.inverted() @ surface(*xy,.014)),1)
    curve.bevel_depth=.010;curve.bevel_resolution=3
    curve.materials.append(bpy.data.materials['Siege vermilion facings'])
    collar=bpy.data.objects.new('Raised red collar facing',curve)
    bpy.context.collection.objects.link(collar);collar.parent=coat
    # A small solid brass belt plate occupies the actual painted waist position.
    center=surface(100,98,.025)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,location=center)
    plate=bpy.context.object;plate.name='Crossbelt brass buckle'
    plate.rotation_euler=camera.rotation_euler;plate.scale=(.025,.033,.006)
    plate.data.materials.append(bpy.data.materials['Siege bright worn bronze'])
    bpy.context.view_layer.update()
    world=plate.matrix_world.copy();plate.parent=coat;plate.matrix_basis=coat.matrix_world.inverted() @ world
    bpy.context.view_layer.update()
    scene['crossbelt_fit']='Measured source paths ray-fitted to full-depth posed coat; thick ribbons, overlapping layers, stitched edges and brass plate'
