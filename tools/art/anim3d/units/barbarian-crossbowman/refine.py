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
        if v.co.z>.40:continue
        sk=skin_matrix(ob,v);world=rig.matrix_world@sk@to_rig@v.co
        q=world_to_camera_view(sc,sc.camera,world);x=q.x*256;y=(1-q.y)*256
        blend=max(0,min(1,(y-186)/20));center=156 if x>136 else 117
        dx=(x-center)*.32*blend+(2 if x>136 else 1)*blend
        dy=(1 if x>136 else 4)*blend
        world+=right*(dx*sc.camera.data.ortho_scale/256)-up*(dy*sc.camera.data.ortho_scale/256)
        # Seat low boot surfaces on the stone along camera rays, retaining screen position.
        forward=sc.camera.matrix_world.to_quaternion()@Vector((0,0,-1))
        if y>204:
            target_z=.082+(world.z-.10)*.72
            world+=forward*((target_z-world.z)/forward.z)
        v.co=from_rig@sk.inverted()@rig.matrix_world.inverted()@world
    ob.data.update()
# Native body stays the original vertex count; smooth its actual skin at render time.
su=body.modifiers.new('Anatomical subdivision','SUBSURF');su.levels=1;su.render_levels=1
bpy.context.view_layer.update()
# Product lighting preserves painted illumination with a camera-only pigment branch later.
sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.view_settings.exposure=0
for name,power in [('Warm key',300),('Soft fill',60),('Cool rim',100)]:bpy.data.objects[name].data.energy=power
bpy.data.objects['Warm key'].data.color=(1,.96,.89)
# The stone remains physical: no painted feet or shadows remain after a foot lifts.
base.location.x=.018
stone.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.89,.64,.39,1)

# Camera-only cream pigment, with live cavity/contact shading; never a figure projection.
n=stone.node_tree.nodes;l=stone.node_tree.links;s=n.get('Principled BSDF');out=n.get('Material Output')
geo=n.new('ShaderNodeNewGeometry');sep=n.new('ShaderNodeSeparateXYZ');l.new(geo.outputs['Normal'],sep.inputs[0])
mix=n.new('ShaderNodeMixRGB');mix.inputs[1].default_value=(.80,.45,.23,1);mix.inputs[2].default_value=(1.14,.81,.55,1);l.new(sep.outputs['Z'],mix.inputs[0])
ao=n.new('ShaderNodeAmbientOcclusion');ao.inputs['Distance'].default_value=.07
shade=n.new('ShaderNodeMixRGB');shade.blend_type='MULTIPLY';shade.inputs[0].default_value=.30;l.new(mix.outputs[0],shade.inputs[1]);l.new(ao.outputs['Color'],shade.inputs[2])
pigment=n.new('ShaderNodeBsdfPrincipled');pigment.name='Camera stone pigment';pigment.inputs['Base Color'].default_value=(0,0,0,1);pigment.inputs['Specular IOR Level'].default_value=0;pigment.inputs['Emission Strength'].default_value=1;l.new(shade.outputs[0],pigment.inputs['Emission Color'])
ray=n.new('ShaderNodeLightPath');weight=n.new('ShaderNodeMath');weight.operation='MULTIPLY';weight.inputs[1].default_value=.85;l.new(ray.outputs['Is Camera Ray'],weight.inputs[0])
blend=n.new('ShaderNodeMixShader');l.new(weight.outputs[0],blend.inputs[0]);l.new(s.outputs[0],blend.inputs[1]);l.new(pigment.outputs[0],blend.inputs[2]);l.new(blend.outputs[0],out.inputs['Surface'])
