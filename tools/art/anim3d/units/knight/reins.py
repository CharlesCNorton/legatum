"""Deterministic solid rein curves joining the moving bit and rider's hand."""
import bpy
from mathutils import Matrix, Vector

def update_reins(frame=None):
    rig=bpy.data.objects['Rider MPFB game_engine']
    hand=rig.matrix_world @ (rig.pose.bones['hand_l'].head + rig.pose.bones['hand_l'].vector*.35)
    reins=sorted((o for o in bpy.data.objects if o.name.startswith('Slack leather rein')),key=lambda o:o.name)
    bands=sorted((o for o in bpy.data.objects if o.name.startswith('Nose band')),key=lambda o:o.name)
    errors=[]
    for index,(rein,band) in enumerate(zip(reins,bands)):
        bit=band.matrix_world @ band.data.splines[0].points[0].co.xyz
        end=hand+Vector(((-1 if index==0 else 1)*.018,0,0))
        rein.parent=None;rein.matrix_world=Matrix.Identity(4)
        spline=rein.data.splines[0]
        if len(spline.points)<17:spline.points.add(17-len(spline.points))
        rein.data.bevel_depth=.007;rein.data.bevel_resolution=3
        for i,p in enumerate(spline.points):
            t=i/(len(spline.points)-1)
            point=bit.lerp(end,t)+Vector((0,0,-.11*4*t*(1-t)))
            p.co=(*point,1)
            if frame is not None:p.keyframe_insert('co',frame=frame)
        errors.append((Vector(spline.points[0].co.xyz)-bit).length)
    return errors
