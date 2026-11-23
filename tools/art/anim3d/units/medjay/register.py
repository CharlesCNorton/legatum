"""Small depth-preserving anatomical corrections in the fixed rest camera."""
from common import *
from bpy_extras.object_utils import world_to_camera_view


def fit_anatomy(sc, body, rig):
    if body.data.shape_keys:
        bpy.context.view_layer.objects.active=body
        bpy.ops.object.shape_key_remove(all=True,apply_mix=True)
    transforms={b.name:b.matrix @ b.bone.matrix_local.inverted() for b in rig.pose.bones}
    right=sc.camera.matrix_world.to_quaternion() @ Vector((1,0,0))
    up=sc.camera.matrix_world.to_quaternion() @ Vector((0,1,0))
    unit=sc.camera.data.ortho_scale/256
    for v in body.data.vertices:
        influences=[(transforms[body.vertex_groups[g.group].name],g.weight) for g in v.groups if body.vertex_groups[g.group].name in transforms]
        total=sum(w for _,w in influences)
        if total<.001:continue
        skin=sum((m*(w/total) for m,w in influences),Matrix(((0,)*4,)*4))
        world=body.matrix_world @ (skin @ v.co)
        q=world_to_camera_view(sc,sc.camera,world);x,y=q.x*256,(1-q.y)*256
        dx=dy=0
        # Raise the actual cranial vault, tapering to zero at the jaw/neck.
        if 115<x<153 and y<57:dy=-5.5*max(0,min(1,(57-y)/27))
        # Seat the calf silhouettes under the painted knees without flattening depth.
        if 148<y<211:
            t=math.sin(math.pi*(y-148)/63)
            dx+=((3.0 if x<132 else -3.5)-.45*(x-(116 if x<132 else 149)))*t
        # Fit ankle/toe widths at fixed depth, retaining all original skin weights.
        if y>193:
            t=max(0,min(1,(y-193)/20));center=116 if x<132 else 149
            dx=((x-center)*.28+(3 if x<132 else -1.5))*t
            dy=-2*t
            if x>132 and y>207:dx+=(x-148)*.60*min(1,(y-207)/8)
        world+=right*(dx*unit)-up*(dy*unit)
        v.co=skin.inverted_safe() @ (body.matrix_world.inverted() @ world)
    body.data.update()
    # The imported eye proxy is lower than the resized human's painted sockets.
    # Fit both full eyeballs in the same posed camera space, retaining skinning.
    eyes=bpy.data.objects['Medjay anatomical eyes']
    if eyes.data.shape_keys:
        bpy.context.view_layer.objects.active=eyes
        bpy.ops.object.shape_key_remove(all=True,apply_mix=True)
    fitted=[]
    for v in eyes.data.vertices:
        influences=[(transforms[eyes.vertex_groups[g.group].name],g.weight) for g in v.groups if eyes.vertex_groups[g.group].name in transforms]
        total=sum(w for _,w in influences)
        if total<.001:continue
        skin=sum((m*(w/total) for m,w in influences),Matrix(((0,)*4,)*4))
        fitted.append((v,skin,eyes.matrix_world @ (skin @ v.co)))
    center=sum((world for _,_,world in fitted),Vector())/len(fitted)
    for v,skin,world in fitted:
        world=center+(world-center)*.68+right*(7*unit)+up*(7*unit)
        v.co=skin.inverted_safe() @ (eyes.matrix_world.inverted() @ world)
    eyes.data.update()
    sc['registration_round']=2
