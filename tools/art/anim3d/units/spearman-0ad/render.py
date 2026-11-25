"""Render the delivered GLB (never the authoring blend) with fixed map camera.

--quick renders four diagnostic poses per clip. Full run writes sprite samples
and all 36 native attack frames. Package with package.py afterwards.
"""
import bpy, sys, os, json, math
from pathlib import Path
from mathutils import Vector, Matrix
UNIT=Path(__file__).resolve().parent
ROOT=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'))
WORK=ROOT/'oad/r4';OUT=WORK/'frames';OUT.mkdir(parents=True,exist_ok=True)
QUICK='--quick' in sys.argv
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.context.scene.render.fps=30
bpy.ops.import_scene.gltf(filepath=str(UNIT/'spearman.glb'),bone_heuristic='BLENDER')
s=bpy.context.scene;s.render.fps=30
rig=next(o for o in s.objects if o.type=='ARMATURE')
meshes=[o for o in s.objects if o.type=='MESH' and not any(c.hide_render for c in o.users_collection)]
actions={a.name.split('|')[-1]:a for a in bpy.data.actions}
print('ACTIONS',list(actions),flush=True)
# Import COLOR_0 as scalar data, bypassing glTF's default RGB multiplication.
# The exported unit remains a normal lit material, with no emission or AO.
for ob in meshes:
    for mat in ob.data.materials:
        nodes=mat.node_tree.nodes;links=mat.node_tree.links
        shader=nodes.get('Principled BSDF')
        texture=next(n for n in nodes if n.type=='TEX_IMAGE')
        color=nodes.new('ShaderNodeVertexColor');color.layer_name=ob.data.color_attributes[0].name
        separate=nodes.new('ShaderNodeSeparateColor');links.new(color.outputs['Color'],separate.inputs['Color'])
        mix=nodes.new('ShaderNodeMixRGB');mix.inputs[1].default_value=(1,1,1,1)
        mix.inputs[2].default_value=(.3763,.0194,.0203,1)
        links.new(separate.outputs['Red'],mix.inputs[0])
        multiply=nodes.new('ShaderNodeMixRGB');multiply.blend_type='MULTIPLY';multiply.inputs[0].default_value=1
        links.new(texture.outputs['Color'],multiply.inputs[1]);links.new(mix.outputs[0],multiply.inputs[2])
        links.new(multiply.outputs[0],shader.inputs['Base Color'])
def pose(name,frame):
    s.frame_set(int(frame),subframe=frame%1)
    bpy.context.view_layer.update()

# Disable imported NLA: the explicitly selected action is the sole motion source.
for track in rig.animation_data.nla_tracks:track.mute=True
# Match the old game camera pitch; view from the spear arm side.
config=json.loads((UNIT/'review.json').read_text())
x,y,z=config['camera_direction_gltf']
# Camera orbit is inverse of the signed display yaw (-30 degrees). GLB stays +Z forward.
base=Matrix.Rotation(math.radians(-config['display_yaw_degrees']),3,'Z') @ Vector((x,-z,y))
direction=base.normalized()
bpy.ops.object.camera_add();camera=bpy.context.object;camera.data.type='ORTHO';s.camera=camera
camera.rotation_euler=(-direction).to_track_quat('-Z','Y').to_euler()
right=camera.rotation_euler.to_matrix() @ Vector((1,0,0));up=camera.rotation_euler.to_matrix() @ Vector((0,1,0))
worldbounds={};framing={}
# Vertex order is Blender-imported, so identify the rigid spear by its socket weight.
spear_indices={}
for o in meshes:
    group=o.vertex_groups.get("weapon_R")
    spear_indices[o.name]={v.index for v in o.data.vertices if group and any(g.group==group.index and g.weight>.999 for g in v.groups)}
for name,a in actions.items():
    rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
    lo=1e9;hi=-1e9;bounds=[1e6,1e6,-1e6,-1e6];figure_height=0
    for frame in range(round(a.frame_range[0]),round(a.frame_range[1])+1):
        pose(name,frame);dep=bpy.context.evaluated_depsgraph_get();figure_y=[]
        for o in meshes:
            ev=o.evaluated_get(dep);me=ev.to_mesh()
            for v in me.vertices:
                p=ev.matrix_world @ v.co;x=p.dot(right);y=p.dot(up)
                bounds=[min(bounds[0],x),min(bounds[1],y),max(bounds[2],x),max(bounds[3],y)]
                lo=min(lo,p.z);hi=max(hi,p.z)
                if v.index not in spear_indices[o.name]:figure_y.append(y)
            ev.to_mesh_clear()
        figure_height=max(figure_height,max(figure_y)-min(figure_y))
    worldbounds[name]=[lo,hi]
    centre=right*((bounds[0]+bounds[2])/2)+up*((bounds[1]+bounds[3])/2)
    scale=max(figure_height/config['figure_frame_fraction'],(bounds[2]-bounds[0])/config['extent_frame_fraction'],(bounds[3]-bounds[1])/config['extent_frame_fraction'])
    framing[name]={'target':list(centre),'ortho_scale':scale,'projected_bounds':bounds,'figure_fraction':figure_height/scale}
s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=12;s.cycles.use_denoising=True;s.cycles.max_bounces=2
s.render.resolution_x=320 if QUICK else 160;s.render.resolution_y=s.render.resolution_x;s.render.resolution_percentage=100
s.render.film_transparent=True;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA';s.view_settings.view_transform='Standard'
s.world.use_nodes=True;s.world.node_tree.nodes.get('Background').inputs[0].default_value=(.65,.65,.65,1);s.world.node_tree.nodes.get('Background').inputs[1].default_value=.5
for loc,energy,size in [((-3,-4,7),220,5),((4,-1,4),90,4)]:
    bpy.ops.object.light_add(type='AREA',location=loc);light=bpy.context.object;light.data.energy=energy;light.data.shape='DISK';light.data.size=size;light.rotation_euler=(Vector((0,0,1))-light.location).to_track_quat('-Z','Y').to_euler()
# Cream plane receives real-time-style lighting; no baked contact or AO.
bpy.ops.mesh.primitive_plane_add(size=200)
floor=bpy.context.object;floor.name='Review floor';floor.is_shadow_catcher=True;mat=bpy.data.materials.new('cream');mat.use_nodes=True
mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.938,.905,.807,1);mat.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=1;floor.data.materials.append(mat)
counts={'idle':12,'walk':16,'attack':18,'hit':8,'death':16}
manifest={'display_yaw_degrees':config['display_yaw_degrees'],'pitch_degrees':math.degrees(math.asin(direction.z)),'framing':framing,'bounds':worldbounds,'clips':{}}
for name,a in actions.items():
    rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
    fit=framing[name];camera.location=Vector(fit['target'])+direction*8;camera.data.ortho_scale=fit['ortho_scale']
    start,end=a.frame_range;count=4 if QUICK else counts[name]
    directory=OUT/('quick-'+name if QUICK else name);directory.mkdir(exist_ok=True)
    loop=name in {'idle','walk'}
    for i in range(count):
        f=start+(end-start)*i/(count if loop else count-1)
        pose(name,f);s.render.filepath=str(directory/f'{i:03}.png');bpy.ops.render.render(write_still=True)
    manifest['clips'][name]={'count':counts[name],'duration':(end-start)/30,'loop':loop}
    if name=='attack' and not QUICK:
        directory=OUT/'attack-fullrate';directory.mkdir(exist_ok=True)
        for i,f in enumerate(range(round(start),round(end)+1)):
            pose(name,f);s.render.filepath=str(directory/f'{i:03}.png');bpy.ops.render.render(write_still=True)
(WORK/('quick-render.json' if QUICK else 'render.json')).write_text(json.dumps(manifest,indent=2))
print('RENDER_REPORT',json.dumps(manifest),flush=True)
