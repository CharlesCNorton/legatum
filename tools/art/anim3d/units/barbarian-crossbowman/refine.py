"""Round-two full-depth fitting and surface finishing, before camera UVs."""
import bpy, math
from mathutils import Matrix, Vector
from bpy_extras.object_utils import world_to_camera_view

# Expand the real hood to its asymmetric draped silhouette; preserve camera depth.
right=sc.camera.matrix_world.to_quaternion()@Vector((1,0,0))
up=sc.camera.matrix_world.to_quaternion()@Vector((0,1,0))
for ob in list(sc.objects):
    if ob.type=='CURVE':
        bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
        bpy.ops.object.convert(target='MESH')
for ob in list(sc.objects):
    if ob.type!='MESH':continue
    bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
    # Apply topology-changing finishes in neutral skin space, then restore articulation.
    arms=[m for m in ob.modifiers if m.type=='ARMATURE']
    for m in arms:m.show_viewport=False
    for m in list(ob.modifiers):
        if m.type in {'SOLIDIFY','BEVEL','SUBSURF'}:
            if m.type=='SUBSURF' and m.levels==0:ob.modifiers.remove(m)
            else:bpy.ops.object.modifier_apply(modifier=m.name)
    for m in arms:m.show_viewport=True
    if ob.name.startswith(('GEO-open wool hood','GEO-hood crown','GEO-hood stitched opening')):
        inv=ob.matrix_world.inverted()
        for v in ob.data.vertices:
            w=ob.matrix_world@v.co;q=world_to_camera_view(sc,sc.camera,w);x=q.x*256;y=(1-q.y)*256
            dx=(-3.4+5*max(0,min(1,(35-y)/20)))*max(0,min(1,(138-x)/18))
            v.co=inv@(w+right*(dx*sc.camera.data.ortho_scale/256))

# Anatomical boot/toe volumes are fitted through inverse skin matrices, not image warps.
def skin_matrix(ob,v):
    weighted=Matrix(((0,0,0,0),)*4);total=0
    for g in v.groups:
        p=rig.pose.bones.get(ob.vertex_groups[g.group].name)
        if p:
            weighted+= (p.matrix@p.bone.matrix_local.inverted())*g.weight;total+=g.weight
    return weighted*(1/total) if total else Matrix.Identity(4)
for ob in [body,boots,trousers]:
    to_rig=rig.matrix_world.inverted()@ob.matrix_world
    from_rig=to_rig.inverted()
    for v in ob.data.vertices:
        if v.co.z>.90:continue
        sk=skin_matrix(ob,v);world=rig.matrix_world@sk@to_rig@v.co
        q=world_to_camera_view(sc,sc.camera,world);x=q.x*256;y=(1-q.y)*256
        blend=max(0,min(1,(y-186)/20));center=156 if x>136 else 117
        dx=(x-center)*(.70 if x>136 else .38)*blend+(3 if x>136 else 1)*blend
        dy=(4 if x>136 else 7)*blend
        dx-= (4 if x>136 else 1)*max(0,min(1,(y-132)/15))*(1-blend)
        world+=right*(dx*sc.camera.data.ortho_scale/256)-up*(dy*sc.camera.data.ortho_scale/256)
        # Seat low boot surfaces on the stone along camera rays, retaining screen position.
        forward=sc.camera.matrix_world.to_quaternion()@Vector((0,0,-1))
        if y>200:
            target_z=.055+(world.z-.10)*.72
            blend_depth=max(0,min(1,(y-200)/12));blend_depth=blend_depth*blend_depth*(3-2*blend_depth)
            world+=forward*((target_z-world.z)/forward.z)*blend_depth
        v.co=from_rig@sk.inverted()@rig.matrix_world.inverted()@world
    ob.data.update()
# Slim the case to the painted bolt quiver; keep actual rounded leather volume.
for ob in sc.objects:
    if ob.type=='MESH' and ob.name.startswith('GEO-bolt leather case'):
        if 'suspension' not in ob.name:
            for v in ob.data.vertices:v.co.x*=.68;v.co.y*=.76
        inv=ob.matrix_world.inverted()
        for v in ob.data.vertices:
            w=ob.matrix_world@v.co;q=world_to_camera_view(sc,sc.camera,w);y=(1-q.y)*256
            dy=-.30*max(0,y-113)
            v.co=inv@(w-right*(2*sc.camera.data.ortho_scale/256)-up*(dy*sc.camera.data.ortho_scale/256))
# Native body stays the original vertex count; smooth its actual skin at render time.
su=body.modifiers.new('Anatomical subdivision','SUBSURF');su.levels=1;su.render_levels=1
bpy.context.view_layer.update()
# Product lighting preserves painted illumination with a camera-only pigment branch later.
sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0
for name,power in [('Warm key',300),('Soft fill',60),('Cool rim',100)]:bpy.data.objects[name].data.energy=power
bpy.data.objects['Warm key'].data.color=(1,.96,.89)
# Keep the existing registered solid disc and apply its clean stone pigment later.
base.location.x=.018
base.location.z-=.024
