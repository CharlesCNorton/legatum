"""Close the anatomical toe grooves with full-depth weighted leather toe boxes."""
import bpy
import bmesh
from mathutils.kdtree import KDTree


def close_toes():
    source = bpy.data.objects['GEO-Boots']
    for side, sign in [('l',1),('r',-1)]:
        vertices = [v for v in source.data.vertices if v.co.x*sign>0 and v.co.z<.125]
        assert len(vertices)>20
        bm = bmesh.new()
        for v in vertices: bm.verts.new(v.co)
        bmesh.ops.convex_hull(bm, input=list(bm.verts), use_existing_faces=False)
        loose = [v for v in bm.verts if not v.link_faces]
        if loose: bmesh.ops.delete(bm, geom=loose, context='VERTS')
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        bm.normal_update()
        for v in bm.verts: v.co += v.normal*.004
        data = bpy.data.meshes.new('Closed leather toe '+side); bm.to_mesh(data); bm.free()
        obj = bpy.data.objects.new('GEO-Boot toe cap.'+side, data)
        bpy.context.collection.objects.link(obj)
        obj.parent = source.parent
        obj.matrix_world = source.matrix_world.copy()
        obj.data.materials.append(source.data.materials[0])
        for group in source.vertex_groups: obj.vertex_groups.new(name=group.name)
        tree = KDTree(len(source.data.vertices))
        for v in source.data.vertices: tree.insert(v.co,v.index)
        tree.balance()
        for v in data.vertices:
            _, i, _ = tree.find(v.co)
            for group in source.data.vertices[i].groups:
                obj.vertex_groups[group.group].add([v.index],group.weight,'REPLACE')
        for face in data.polygons: face.use_smooth=True
        arm = obj.modifiers.new('MPFB toe box skinning','ARMATURE')
        arm.object = bpy.data.objects['RIG-barbarian-archer']
        bevel = obj.modifiers.new('Soft leather toe edge','BEVEL'); bevel.width=.006; bevel.segments=3
