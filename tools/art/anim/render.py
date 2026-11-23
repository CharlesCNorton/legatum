"""Blender-only offline relief modelling, armature animation and Eevee rendering.

The camera-space relief is deliberate: one facing preserves the supplied paint,
including its three-quarter perspective. It is not an all-angle reconstruction.
All meshes are skinned to an armature, with individually articulated kit/limbs.
"""
import bpy, json, math, sys
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from units import CLIPS, UNITS
slug=sys.argv[sys.argv.index('--')+1]
PASS=int(sys.argv[sys.argv.index('--')+2])
MODEL_ONLY='--model-only' in sys.argv
HOME=Path.home()/'LegatumRuns/anim-pilot'; DEST=HOME/'masters'/slug
cfg=json.loads((DEST/'model.json').read_text())
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene; scene.render.engine='BLENDER_EEVEE'
scene.render.threads_mode='FIXED'; scene.render.threads=4
scene.render.resolution_x=256; scene.render.resolution_y=256; scene.render.resolution_percentage=100
scene.render.film_transparent=True; scene.render.image_settings.file_format='PNG'; scene.render.image_settings.color_mode='RGBA'
scene.render.image_settings.color_depth='8'; scene.render.fps=24
scene.view_settings.view_transform='Standard'; scene.view_settings.look='None'
scene.view_settings.exposure=0; scene.view_settings.gamma=1
scene.world.color=(.6,.6,.6)
if hasattr(scene,'eevee'): scene.eevee.taa_render_samples=64
bpy.ops.object.camera_add(location=(128,-1000,128))
cam=bpy.context.object; cam.rotation_euler=(Vector((128,0,128))-cam.location).to_track_quat('-Z','Y').to_euler()
cam.data.type='ORTHO'; cam.data.ortho_scale=256; scene.camera=cam
# The default far plane is 1000: it cut off the stone at depth 1015 and
# sliced the body relief. Keep the painting's exact 1:1 pixel framing.
cam.data.clip_start=.1; cam.data.clip_end=2000
# Light is available for sculpted additions. Original paint supplies the main
# upper-left soft lighting, avoiding a second set of highlights on the texture.
bpy.ops.object.light_add(type='AREA',location=(-180,-300,450)); bpy.context.object.data.energy=200; bpy.context.object.data.shape='DISK'; bpy.context.object.data.size=300

def point(p,depth=0): return (p[0],depth,256-p[1])
def material(name):
    mat=bpy.data.materials.new(name); mat.use_nodes=True
    mat.blend_method='HASHED'; mat.use_screen_refraction=False
    mat.use_transparent_shadow=False
    n=mat.node_tree.nodes; n.clear(); l=mat.node_tree.links
    out=n.new('ShaderNodeOutputMaterial'); mix=n.new('ShaderNodeMixShader'); trans=n.new('ShaderNodeBsdfTransparent'); emit=n.new('ShaderNodeEmission'); tex=n.new('ShaderNodeTexImage')
    tex.image=bpy.data.images.load(str(DEST/f'{name}.png')); tex.image.pack(); tex.interpolation='Linear'; tex.extension='CLIP'
    l.new(tex.outputs['Color'],emit.inputs['Color']); l.new(tex.outputs['Alpha'],mix.inputs[0]); l.new(trans.outputs[0],mix.inputs[1]); l.new(emit.outputs[0],mix.inputs[2]); l.new(mix.outputs[0],out.inputs['Surface'])
    return mat

# Anatomical pivot hierarchy, all bones point along world Z so local Y is up.
arm=bpy.data.armatures.new('Miniature skeleton'); rig=bpy.data.objects.new('Miniature skeleton',arm); scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active=rig; rig.select_set(True); bpy.ops.object.mode_set(mode='EDIT')
def bone(name,pivot,parent=None):
    b=arm.edit_bones.new(name); b.head=point(pivot); b.tail=Vector(b.head)+Vector((0,0,10))
    if parent: b.parent=arm.edit_bones[parent]
    return b
bone('root',cfg['root']); bone('carriage',(126,176)); bone('body',cfg['root'],'carriage' if slug=='field-cannon' else 'root')
for part in cfg['layers']: bone(part['name'],part['pivot'])
for part in cfg['layers']: arm.edit_bones[part['name']].parent=arm.edit_bones[part['parent']]
# Axle-space compression: rotate circular spoke geometry, then project it back
# to the original wheel ellipse. An image-plane rotation would rock the tyre.
wheel_ratios={'wheel_l':.44,'wheel_r':.50} if slug=='field-cannon' else {}
for part in cfg['layers']:
    if part['name'] in wheel_ratios:
        axle=bone(part['name']+'_axle',part['pivot'],'carriage')
        arm.edit_bones[part['name']].parent=axle
bpy.ops.object.mode_set(mode='OBJECT')
for p in rig.pose.bones: p.rotation_mode='XYZ'

def mesh_layer(name,bone_name,depth):
    # A mid-poly relief rather than a single card: a rounded shallow surface,
    # subdivided for subsequent weight painting and projection adjustments.
    step=8; verts=[]; faces=[]
    for y in range(0,257,step):
        for x in range(0,257,step):
            relief=-1.2*math.sin(math.pi*x/256)*math.sin(math.pi*y/256) if name!='base' else 0
            projected_x=x
            if name in wheel_ratios:
                cx=next(p['pivot'][0] for p in cfg['layers'] if p['name']==name)
                projected_x=cx+(x-cx)/wheel_ratios[name]
            verts.append((projected_x,depth+relief,256-y))
    side=33
    for y in range(32):
        for x in range(32):
            i=y*side+x; faces.append((i,i+1,i+side+1,i+side))
    mesh=bpy.data.meshes.new(name); mesh.from_pydata(verts,[],faces); mesh.update()
    obj=bpy.data.objects.new(name,mesh); scene.collection.objects.link(obj); obj.data.materials.append(material(name))
    uv=mesh.uv_layers.new(name='Painting projection')
    for poly in mesh.polygons:
        for li in poly.loop_indices:
            idx=mesh.loops[li].vertex_index
            uv.data[li].uv=((idx%33)*step/256,1-(idx//33)*step/256)
    if bone_name:
        group=obj.vertex_groups.new(name=bone_name); group.add(list(range(len(verts))),1,'REPLACE')
        mod=obj.modifiers.new('Armature','ARMATURE'); mod.object=rig
    return obj
mesh_layer('base',None,15)
mesh_layer('body','body',1)
# Same source pixel ownership means the layer order cannot duplicate outlines.
for i,part in enumerate(reversed(cfg['layers'])): mesh_layer(part['name'],part['name'],-3-i*.35)

# Smoke is a restrained, soft irregular puff; no emissive blast or ground plane.
smokes=[]
if slug=='field-cannon':
    for i in range(5):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=8,radius=1,location=(221,-20,116))
        ob=bpy.context.object; ob.name=f'Muzzle smoke {i}'; mat=bpy.data.materials.new(ob.name); mat.use_nodes=True
        n=mat.node_tree.nodes; n.clear(); l=mat.node_tree.links
        out=n.new('ShaderNodeOutputMaterial'); mix=n.new('ShaderNodeMixShader'); trans=n.new('ShaderNodeBsdfTransparent'); em=n.new('ShaderNodeEmission'); lw=n.new('ShaderNodeLayerWeight'); mul=n.new('ShaderNodeMath'); mul.operation='MULTIPLY'; mul.inputs[1].default_value=.36
        em.inputs[0].default_value=(.62,.59,.52,1); l.new(lw.outputs['Facing'],mul.inputs[0]); l.new(mul.outputs[0],mix.inputs[0]); l.new(trans.outputs[0],mix.inputs[1]); l.new(em.outputs[0],mix.inputs[2]); l.new(mix.outputs[0],out.inputs[0]); ob.data.materials.append(mat); smokes.append(ob)

def pose(name,dx=0,dy=0,angle=0,sx=1,sy=1):
    if name not in rig.pose.bones: return
    b=rig.pose.bones[name]; b.location=(dx,-dy,0); b.rotation_euler=(0,0,-math.radians(angle)); b.scale=(sx,sy,1)

def smooth(t): return t*t*(3-2*t)
def animate(clip,i,n):
    for b in rig.pose.bones: b.location=(0,0,0); b.rotation_euler=(0,0,0); b.scale=(1,1,1)
    for wheel,ratio in wheel_ratios.items(): pose(wheel+'_axle',sx=ratio)
    t=i/(n-1); cycle=math.tau*i/n; s=math.sin(cycle); c=math.cos(cycle)
    horse=slug=='horseman'; cannon=slug=='field-cannon'
    if clip=='idle':
        pose('body',dx=.65*s,dy=-1.4*s,angle=.6*s)
        pose('head',angle=.55*s); pose('rider',dy=-.5*s,angle=.5*s)
        pose('spear',angle=.65*s); pose('tail',angle=2*s)
        if cannon: pose('crew',dy=-.6*s,angle=.3*s)
    elif clip=='move':
        pose('body',dy=-1.8*(1-math.cos(2*cycle)),angle=1.3*s)
        stride=13 if horse else 12
        pose('leg_l',angle=stride*s,dy=-max(0,s)*5)
        pose('leg_r',angle=-stride*s,dy=-max(0,-s)*5)
        pose('leg_back',angle=-stride*s); pose('leg_front',angle=stride*s)
        pose('rider',dy=-1.5*(1-c),angle=-2*s); pose('horse_head',angle=2*s); pose('tail',angle=5*s)
        pose('shield',angle=-1.8*s); pose('spear',angle=2.4*s)
        if cannon:
            pose('crew',dx=1.3*s,dy=-(1-c),angle=3)
            pose('carriage',dx=1.2*s,dy=-.5*(1-c))
            pose('wheel_l',angle=360*i/n); pose('wheel_r',angle=360*i/n)
    elif clip=='attack':
        # Anticipation -> fast strike -> weighted recovery; final pose is neutral.
        a=[0,-.12,-.2,.7,1,.94,.72,.35,.10,0][i]
        if cannon:
            pose('barrel',dx=-6*max(0,a),dy=-1*max(0,a)); pose('carriage',dx=-1.8*max(0,a))
            pose('crew',angle=-4*max(0,a)); pose('ramrod',angle=-3*max(0,a))
        else:
            pose('body',dx=5*a,dy=2*a,angle=5*a)
            pose('spear',angle=(38 if slug=='spartan-hoplite' else 48)*a)
            pose('shield',angle=-7*a); pose('head',angle=-3*a)
            pose('leg_l',angle=-3*a); pose('leg_r',angle=4*a)
            if horse:
                pose('rider',angle=9*a,dx=2*a); pose('horse_head',angle=6*a)
                pose('leg_front',angle=-12*a); pose('leg_back',angle=8*a)
    elif clip=='hit':
        a=[0,1,.45,0][i]; pose('body',dx=-3*a,angle=-5*a); pose('head',angle=-6*a); pose('shield',angle=5*a)
        if cannon: pose('crew',angle=-6*a)
    elif clip=='death':
        # Two-frame settle holds the exact final pose; stone has no animation.
        u=smooth(min(1,max(0,(t-.1)/.7)))
        if cannon:
            pose('root',dx=-10*u,dy=76*u,angle=-68*u,sx=1-.25*u,sy=1-.38*u)
        else:
            pose('root',dx=-3*u,dy=(22 if horse else 44)*u,angle=-69*u,sx=1-.22*u,sy=1-.45*u)
            pose('spear',angle=-18*u); pose('shield',angle=12*u); pose('head',angle=-10*u)
            pose('leg_l',angle=18*u); pose('leg_r',angle=-12*u)
            pose('rider',angle=-20*u); pose('horse_head',angle=-10*u)
    for j,ob in enumerate(smokes):
        q=(i-3)/6 if clip=='attack' and i>=3 else -1
        size=(2+j*.6+q*5) if 0<=q<.84 else .001
        ob.scale=(size,size*.7,size*.72); ob.location=(219+q*12+j*1.5,-20-j,116+q*14+j*2)
        ob.keyframe_insert('scale'); ob.keyframe_insert('location')
    for b in rig.pose.bones:
        b.keyframe_insert('location'); b.keyframe_insert('rotation_euler'); b.keyframe_insert('scale')

frame=1; shots=[]
for clip,(n,fps,loop) in CLIPS.items():
    marker=scene.timeline_markers.new(clip,frame=frame)
    for i in range(n):
        scene.frame_set(frame); animate(clip,i,n); shots.append((frame,clip,i)); frame+=1
scene.frame_start=1; scene.frame_end=frame-1
rig['source']=f'app/src/assets/units/{slug}-256.png'; rig['technique']='Camera-projected articulated relief, one facing'; rig['pass']=PASS
scene.render.use_file_extension=True
bpy.ops.wm.save_as_mainfile(filepath=str(DEST/f'{slug}.blend'))
if MODEL_ONLY:
    print(f'MODEL ONLY {slug}: armature and {len(shots)} poses saved; no renders produced')
    sys.exit(0)
for frame,clip,i in shots:
    scene.frame_set(frame); out=DEST/'frames'/clip; out.mkdir(parents=True,exist_ok=True)
    scene.render.filepath=str(out/f'{i:02}.png'); bpy.ops.render.render(write_still=True)
print(f'FINISHED {slug}: {len(shots)} Eevee frames, pass {PASS}')
