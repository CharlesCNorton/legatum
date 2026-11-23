"""Finish the rest surface and ground the actual leather soles before projection."""
import bpy, json
from mathutils import Matrix, Vector
from math import sqrt

def refine(sc):
    rig=bpy.data.objects['Gaesatae • MPFB game_engine']
    def aim(name,direction):
        p=rig.pose.bones[name];q=p.bone.matrix_local.to_quaternion()
        mat=((q@Vector((0,1,0))).rotation_difference(direction.normalized())@q).to_matrix().to_4x4()
        mat.translation=p.head;p.matrix=mat;bpy.context.view_layer.update()
    def ankle(side,target):
        u=rig.pose.bones['thigh_'+side];l=rig.pose.bones['calf_'+side]
        a=u.head.copy();axis=target-a;length=axis.length;axis.normalize()
        along=(u.bone.length**2-l.bone.length**2+length**2)/(2*length)
        pole=Vector((target.x,-.5,.5))-a;pole=(pole-axis*pole.dot(axis)).normalized()
        knee=a+axis*along+pole*sqrt(max(0,u.bone.length**2-along**2))
        aim(u.name,knee-a);aim(l.name,target-knee)
    # Native MPFB foot orientation is independent of the braced calf tilt.
    for side in ('r','l'):
        target=rig.pose.bones['calf_'+side].tail.copy();target.y+=.30
        ankle(side,target)
        foot=rig.pose.bones['foot_'+side]
        orient=foot.bone.matrix_local.to_quaternion().to_matrix().to_4x4()
        # Turn the near toes out to recover the broad planted boot silhouette.
        orient=Matrix.Rotation(.95 if side=='l' else -.25,4,'Z')@orient
        orient.translation=foot.head.copy();foot.matrix=orient
        bpy.context.view_layer.update()
        boot=bpy.data.objects['GEO-soft leather boot '+side]
        ev=boot.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
        bottom=min((boot.matrix_world@v.co).z for v in me.vertices);ev.to_mesh_clear()
        pose=foot.matrix.copy();pose.translation.z+=.103-bottom;foot.matrix=pose
        bpy.context.view_layer.update()
    base=bpy.data.objects['GEO-stationary cream stone']
    base.scale.x=base.scale.y=.97;base.location.y=.15
    for mod in base.modifiers:
        if mod.type=='BEVEL':mod.width=.006;mod.segments=3
    # Finish geometry BEFORE recording UVs. Keep live skeletal deformation.
    for ob in list(sc.objects):
        if ob.type=='CURVE':
            bpy.ops.object.select_all(action='DESELECT');ob.select_set(True)
            bpy.context.view_layer.objects.active=ob;bpy.ops.object.convert(target='MESH')
    for ob in list(sc.objects):
        if ob.type!='MESH':continue
        bpy.ops.object.select_all(action='DESELECT');ob.select_set(True)
        bpy.context.view_layer.objects.active=ob
        if ob.data.shape_keys:
            # Freeze the current mixed macro shape; retain native skin weights.
            ob.shape_key_add(name='Frozen macro mix',from_mix=True)
            for key in list(ob.data.shape_keys.key_blocks)[:-1]:ob.shape_key_remove(key)
            ob.shape_key_remove(ob.data.shape_keys.key_blocks[0])
        for mod in list(ob.modifiers):
            if mod.type in {'SUBSURF','SOLIDIFY','BEVEL'}:
                if not mod.show_viewport or (mod.type=='SUBSURF' and mod.levels==0):
                    ob.modifiers.remove(mod);continue
                bpy.ops.object.modifier_apply(modifier=mod.name)
    # Camera-only pigment must not illuminate neighbouring skin or stone.
    sc['surface_finished']=True
    rig['neutral_pose']=json.dumps({p.name:[list(row) for row in p.matrix_basis] for p in rig.pose.bones})
