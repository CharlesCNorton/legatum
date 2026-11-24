"""Pose-space gravity folds for the lined tunic; authored, not a cloth sim."""
import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree


def settle(sc, rig, count):
    garments=[ob for ob in sc.objects if ob.get('settle_garment')]
    sc.frame_set(1);bpy.context.view_layer.update()
    heights={}
    for ob in garments:
        ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
        heights[ob.name]=[(ev.matrix_world@v.co).z for v in me.vertices]
        ev.to_mesh_clear()
    sc.frame_set(count);bpy.context.view_layer.update()
    body=bpy.data.objects['Heir MPFB anatomy']
    ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
    skin=BVHTree.FromPolygons([ev.matrix_world@v.co for v in me.vertices],
                             [list(p.vertices) for p in me.polygons])
    ev.to_mesh_clear()
    for ob in garments:
        transforms={g.index:rig.pose.bones[g.name].matrix@rig.data.bones[g.name].matrix_local.inverted()
                    for g in ob.vertex_groups}
        key=ob.shape_key_add(name='Gravity folds over legs')
        for vertex, original_z in zip(ob.data.vertices,heights[ob.name]):
            weights=[(g.weight,transforms[g.group]) for g in vertex.groups]
            blend=Matrix([[sum(w*mat[r][c] for w,mat in weights)
                           for c in range(4)] for r in range(4)])
            transform=rig.matrix_world@blend
            point=transform@vertex.co
            amount=max(0,min(1,(1.08-original_z)/.35))
            point.z-=max(0,point.z-.125)*amount*.78
            near,normal,_,distance=skin.find_nearest(point)
            if near is not None and (point-near).dot(normal)<.008:
                point=near+normal*.009
            key.data[vertex.index].co=transform.inverted()@point
        for i in range(count):
            t=min(1,max(0,((i/(count-1))-.30)/.48))
            key.value=t*t*(3-2*t);key.keyframe_insert('value',frame=i+1)
    sc['garment_settle']='Pose-space gravity fold with evaluated anatomical surface clearance'
