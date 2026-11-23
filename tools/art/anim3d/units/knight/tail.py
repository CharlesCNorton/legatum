"""Authored, gravity-shaped volumetric locks anchored to the source tail root."""
import bpy, json, math
from mathutils import Matrix, Vector

def update_tail(frame=None, phase=0., moving=False):
    scene=bpy.context.scene;rig=bpy.data.objects['AnimalArmature']
    anchor=Vector(json.loads(scene['tail_root_local']))
    root=rig.matrix_world@rig.pose.bones['Tail1'].matrix@anchor
    right=scene.camera.matrix_world.to_3x3()@Vector((1,0,0))
    locks=sorted((o for o in scene.objects if o.name.startswith('Knight flowing tail lock')),key=lambda o:o.name)
    for j,ob in enumerate(locks):
        angle=j*math.tau/len(locks)
        spline=ob.data.splines[0]
        for k,p in enumerate(spline.points):
            t=k/(len(spline.points)-1)
            radius=.14*(1-.60*t)
            sway=.05*math.sin(phase*math.tau-t*2)*t if moving else .015*math.sin(phase*math.tau-t)*t
            point=root+Vector((radius*math.cos(angle)+sway,
                               .26*t+.065*math.sin(t*math.pi)+radius*math.sin(angle),
                               -.92*t+.035*math.sin(t*math.pi*2+j*.23)))
            point+=right*(.22*math.sin(t*math.pi*.72))
            point+=right*(.018*math.sin(t*math.pi*4+j*.37)*t)
            point.z=max(.125+.012*math.sin(angle),point.z)
            p.co=(*point,1)
            p.radius=max(.18,1-.72*t**2)
            if frame is not None:p.keyframe_insert('co',frame=frame)
