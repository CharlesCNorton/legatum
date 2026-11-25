"""Render the delivered GLB (never the authoring blend) with fixed map camera.

--quick renders four diagnostic poses per clip. Full run writes sprite samples
and all 36 native attack frames. Package with package.py afterwards.
"""
import bpy, sys, os, json, math
from pathlib import Path
from mathutils import Vector, Matrix
UNIT=Path(__file__).resolve().parent
ROOT=Path(os.environ.get('ANIM_ROOT',Path.home()/'LegatumRuns/anim-pilot'))
ROUND='painted-r1'
WORK=ROOT/'lanes/spearman-0ad-painted-r1';OUT=WORK/'frames';OUT.mkdir(parents=True,exist_ok=True)
QUICK='--quick' in sys.argv
STILLS='--stills' in sys.argv
MAP_ONLY='--map-only' in sys.argv
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.context.scene.render.fps=30
bpy.ops.import_scene.gltf(filepath=str(UNIT/'spearman.glb'),bone_heuristic='BLENDER')
s=bpy.context.scene;s.render.fps=30
rig=next(o for o in s.objects if o.type=='ARMATURE')
meshes=[o for o in s.objects if o.type=='MESH' and o.name=='spearman_LOD0']
lod1=next(o for o in s.objects if o.type=='MESH' and o.name=='spearman_LOD1')
for o in s.objects:
    if o.type=='MESH' and o.name not in {m.name for m in meshes}:o.hide_render=True;o.hide_set(True)
actions={a.name.split('|')[-1]:a for a in bpy.data.actions}
if os.environ.get('ANIM_CLIPS'):
    actions={n:a for n,a in actions.items() if n in os.environ['ANIM_CLIPS'].split(',')}
print('ACTIONS',list(actions),flush=True)
# Import COLOR_0 as scalar data, bypassing glTF's default RGB multiplication.
# The exported unit remains a normal lit material, with no emission or AO.
for ob in meshes:
    for mat in ob.data.materials:
        nodes=mat.node_tree.nodes;links=mat.node_tree.links
        shader=nodes.get('Principled BSDF')
        texture=next(n for n in nodes if n.type=='TEX_IMAGE' and 'basecolor' in n.image.name.lower())
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
if os.environ.get('ANIM_SHARED_FIT'):
    # A/B clips share one fixed camera; pose differences cannot be zoom/recentre.
    b=[min(v['projected_bounds'][i] for v in framing.values()) for i in (0,1)]
    b += [max(v['projected_bounds'][i] for v in framing.values()) for i in (2,3)]
    scale=max(*(v['ortho_scale'] for v in framing.values()),(b[2]-b[0])/config['extent_frame_fraction'],(b[3]-b[1])/config['extent_frame_fraction'])
    centre=right*((b[0]+b[2])/2)+up*((b[1]+b[3])/2)
    for fit in framing.values():
        fit['figure_fraction']*=fit['ortho_scale']/scale
        fit.update(target=list(centre),ortho_scale=scale)
s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=16 if STILLS else 8;s.cycles.use_denoising=True;s.cycles.max_bounces=2
s.render.resolution_x=512 if STILLS else 320 if QUICK else 160;s.render.resolution_y=s.render.resolution_x;s.render.resolution_percentage=100
s.render.film_transparent=True;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA';s.view_settings.view_transform='AgX'
s.world.use_nodes=True
wn=s.world.node_tree.nodes;wl=s.world.node_tree.links
env=wn.new('ShaderNodeTexEnvironment');env.image=bpy.data.images.load(str(UNIT.parents[1]/'viewer/studio_small_09_1k.hdr'))
wl.new(env.outputs['Color'],wn.get('Background').inputs[0]);wn.get('Background').inputs[1].default_value=.35
for loc,energy,size,col in [((-3,-4,6),350,4,(1,.83,.65)),((3,2,4),250,3,(.63,.78,1))]:
    bpy.ops.object.light_add(type='AREA',location=loc);light=bpy.context.object;light.data.energy=energy;light.data.shape='DISK';light.data.size=size;light.data.color=col;light.rotation_euler=(Vector((0,0,1))-light.location).to_track_quat('-Z','Y').to_euler()
# Cream plane receives real-time-style lighting; no baked contact or AO.
bpy.ops.mesh.primitive_plane_add(size=200)
floor=bpy.context.object;floor.name='Review floor';floor.is_shadow_catcher=True;mat=bpy.data.materials.new('cream');mat.use_nodes=True
mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.938,.905,.807,1);mat.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=1;floor.data.materials.append(mat)
# Game sampling rates; retain GLB time rather than stretching clips to old frame counts.
fps={'idle':4,'walk':6,'attack':14,'hit':12,'death':4}
counts={name:max(1,math.ceil((a.frame_range[1]-a.frame_range[0])/30*fps[name]-1e-6)) for name,a in actions.items()}
manifest={'display_yaw_degrees':config['display_yaw_degrees'],'pitch_degrees':math.degrees(math.asin(direction.z)),'framing':framing,'bounds':worldbounds,'clips':{}}
for name,a in actions.items():
    if STILLS and name!='idle':continue
    if MAP_ONLY and name not in {'idle','attack'}:continue
    rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
    fit=framing[name];camera.location=Vector(fit['target'])+direction*8;camera.data.ortho_scale=fit['ortho_scale']
    start,end=a.frame_range;count=1 if STILLS else 4 if QUICK else counts[name]
    directory=OUT/('still-'+name if STILLS else 'quick-'+name if QUICK else name);directory.mkdir(exist_ok=True)
    loop=name in {'idle','walk'}
    for i in range(count):
        if MAP_ONLY and i not in {'idle':[0],'attack':[0,4,8,12]}[name]:continue
        f=start if STILLS else start+(end-start)*i/(count if loop else count-1) if QUICK else min(end,start+i/fps[name]*30)
        pose(name,f);s.render.filepath=str(directory/f'{i:03}.png')
        if not MAP_ONLY:bpy.ops.render.render(write_still=True)
        if not QUICK and not STILLS and i in {'idle':[0],'attack':[0,4,8,12]}.get(name,[]):
            # Same GLB, pose and lighting; maximum figure height exactly 48 px
            # on a 160 px canvas. This is a fresh render, not a thumbnail crop.
            tiny=OUT/('map48-'+name);tiny.mkdir(exist_ok=True)
            camera.data.ortho_scale=fit['ortho_scale']*fit['figure_fraction']/(48/160)
            s.render.filepath=str(tiny/f'{i:03}.png')
            meshes[0].hide_render=True;lod1.hide_render=False;lod1.hide_set(False)
            bpy.ops.render.render(write_still=True)
            meshes[0].hide_render=False;lod1.hide_render=True;lod1.hide_set(True)
            camera.data.ortho_scale=fit['ortho_scale']
    manifest['clips'][name]={'count':counts[name],'duration':(end-start)/30,'loop':loop,'fps':fps[name]}
    if (name=='attack' or os.environ.get('ANIM_FULLRATE') and name=='hit') and not QUICK and not STILLS and not MAP_ONLY:
        directory=OUT/(name+'-fullrate');directory.mkdir(exist_ok=True)
        for i,f in enumerate(range(round(start),round(end)+1)):
            pose(name,f);s.render.filepath=str(directory/f'{i:03}.png')
        if not MAP_ONLY:bpy.ops.render.render(write_still=True)
(WORK/('map-render.json' if MAP_ONLY else 'quick-render.json' if QUICK else 'render.json')).write_text(json.dumps(manifest,indent=2))
print('RENDER_REPORT',json.dumps(manifest),flush=True)

if STILLS:
    # Detail crops use the evaluated delivered LOD0. No authoring mesh substitution.
    ob=meshes[0]
    for label,group,extent in [('shield','shield_arm',.99),('helmet','helmet',.46),('crest','helmet',.59)]:
        dep=bpy.context.evaluated_depsgraph_get();ev=ob.evaluated_get(dep);me=ev.to_mesh()
        vg=ob.vertex_groups.get(group);pts=[ev.matrix_world @ v.co for v in me.vertices if any(g.group==vg.index and g.weight>.99 for g in v.groups)]
        ev.to_mesh_clear()
        lo=Vector(tuple(min(v[k] for v in pts) for k in range(3)));hi=Vector(tuple(max(v[k] for v in pts) for k in range(3)));c=(lo+hi)/2
        if label=='helmet':c.z-=.14
        if label=='crest':c.z+=.065
        camera.location=c+direction*8;camera.data.ortho_scale=extent;s.render.filepath=str(OUT/(label+'-close.png'));bpy.ops.render.render(write_still=True)
