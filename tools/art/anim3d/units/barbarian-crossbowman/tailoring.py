"""Transfer MPFB torso/hip skinning to the finished tunic without moving its rest surface."""
import bpy
from mathutils import Matrix
from mathutils.kdtree import KDTree

subdiv=[m for m in body.modifiers if m.type=='SUBSURF']
for m in subdiv:m.show_viewport=False
bpy.context.view_layer.update()
ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
source_weights=[[(body.vertex_groups[g.group].name,g.weight) for g in v.groups] for v in me.vertices]
kd=KDTree(len(me.vertices))
for v in me.vertices:kd.insert(ev.matrix_world@v.co,v.index)
kd.balance();ev.to_mesh_clear()
allowed={'pelvis','spine_01','spine_02','spine_03','thigh_l','thigh_r'}
for ob in list(sc.objects):
    if not ob.name.startswith(('GEO-quilted gambeson','GEO-gambeson stitched channel')):continue
    world=ob.matrix_world.copy()
    vertices=[world@v.co for v in ob.data.vertices]
    ob.parent=rig;ob.parent_type='OBJECT';ob.matrix_parent_inverse=Matrix.Identity(4);ob.matrix_basis=Matrix.Identity(4)
    for name in sorted(allowed):ob.vertex_groups.new(name=name)
    for v,w in zip(ob.data.vertices,vertices):
        weights={}
        for _,index,distance in kd.find_n(w,6):
            factor=1/max(.005,distance)**2
            for name,weight in source_weights[index]:
                if name in allowed:weights[name]=weights.get(name,0)+weight*factor
        total=sum(weights.values())
        if not total:weights={'spine_02':1};total=1
        sk=Matrix(((0,0,0,0),)*4)
        for name,weight in weights.items():
            weight/=total;p=rig.pose.bones[name]
            ob.vertex_groups[name].add([v.index],weight,'REPLACE')
            sk+=(p.matrix@p.bone.matrix_local.inverted())*weight
        v.co=sk.inverted()@rig.matrix_world.inverted()@w
    ar=ob.modifiers.new('Continuous MPFB tailored skinning','ARMATURE');ar.object=rig
    ob['attachment']='Transferred MPFB spine/pelvis/thigh skinning'
for m in subdiv:m.show_viewport=True
bpy.context.view_layer.update()
