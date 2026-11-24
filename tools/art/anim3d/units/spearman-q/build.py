"""CC0 library motion on the original Quaternius base rig; no authored body poses."""
import argparse
import json
import math
import os
from pathlib import Path
import sys
import bpy
from mathutils import Matrix, Vector

ROOT = Path(os.environ.get('ANIM_ROOT', Path.home()/'LegatumRuns/anim-pilot'))
ASSETS = ROOT/'assets/spearman-q'
OUT = ROOT/'lanes/spearman-q'
MASTER = ROOT/'masters/spearman-3d-v2/spearman.blend'

def material(name, color, metal=0):
    m = bpy.data.materials.new(name); m.diffuse_color = (*color, 1); m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Metallic'].default_value = metal
    p.inputs['Roughness'].default_value = .65
    return m

def assign(o, mat):
    o.data.materials.clear(); o.data.materials.append(mat)

def import_asset(pattern):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(next(ASSETS.rglob(pattern))))
    objects = set(bpy.data.objects)-before
    rig = next(o for o in objects if o.type == 'ARMATURE')
    for o in list(objects):
        if o.name.startswith('Icosphere'):
            objects.remove(o); bpy.data.objects.remove(o, do_unlink=True)
    return rig, objects

def setup():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene; s.render.fps = 24
    body, objects = import_asset('Superhero_Male_FullBody.gltf')
    body.name = 'Quaternius Superhero male original rig'
    skin = material('Plain warm clay', (.42,.28,.18))
    for o in objects:
        if o.type == 'MESH' and o.name.startswith('SuperHero'):
            assign(o,skin)
    donors = {}; actions = {}
    for tag, filename in [('ual1','UAL1_Standard.glb'),('ual2','UAL2_Standard.glb')]:
        before = set(bpy.data.actions)
        rig, imported = import_asset(filename)
        rig.name = tag
        rig.animation_data_clear();rig.animation_data_create()
        donors[tag] = rig
        for a in set(bpy.data.actions)-before:
            a.use_fake_user = True
            key = a.name.removesuffix('.001')
            actions[(tag,key)] = a
        for o in imported:
            if o != rig:bpy.data.objects.remove(o,do_unlink=True)
        rig.hide_render = True
    body.location.z = .105
    body.animation_data_create()
    with bpy.data.libraries.load(str(MASTER),link=False) as (src,dst):
        dst.objects = ['Camera','Stationary cream stone']
    for o in dst.objects:
        bpy.context.collection.objects.link(o)
    s.camera = bpy.data.objects['Camera'];s.camera.data.dof.use_dof=False
    base=bpy.data.objects['Stationary cream stone'];base.animation_data_clear()
    base.constraints.clear();assign(base,material('Plain cream stone',(.68,.52,.32)))
    s.world=bpy.data.worlds.new('Soft studio');s.world.use_nodes=True
    s.world.node_tree.nodes['Background'].inputs[0].default_value=(.65,.65,.65,1)
    s.world.node_tree.nodes['Background'].inputs[1].default_value=.7
    for name,loc,power,size in [('Key',(-3,-4,7),450,5),('Fill',(4,-2,4),120,4)]:
        data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size
        o=bpy.data.objects.new(name,data);s.collection.objects.link(o);o.location=loc
        o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
    s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=8;s.cycles.use_denoising=True
    s.cycles.max_bounces=3;s.render.resolution_x=s.render.resolution_y=160;s.render.resolution_percentage=100
    s.render.film_transparent=True;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA'
    s.view_settings.view_transform='Standard';s.view_settings.look='None'
    s.render.use_persistent_data=True
    return s,body,donors,actions

def pose(body, donor, action, frame):
    donor.animation_data.action=action
    donor.animation_data.action_slot=action.slots[0]
    bpy.context.scene.frame_set(int(frame),subframe=frame-int(frame))
    matrices={}
    for p in body.pose.bones:
        if p.name.startswith('prop_'):continue
        d=donor.pose.bones[p.name]
        r=p.bone.matrix_local; dr=d.bone.matrix_local
        rot=d.matrix.to_quaternion().to_matrix()  @  dr.to_quaternion().to_matrix().transposed()  @  r.to_quaternion().to_matrix()
        if p.parent:
            par=p.parent;rest_delta=par.bone.matrix_local.inverted()  @  r.translation
            pos=matrices[par.name]  @  rest_delta
        else:pos=r.translation.copy()
        if p.name=='pelvis':
            pos += (d.matrix.translation-dr.translation)*1.035
        if p.name=='root':pos=d.matrix.translation.copy()
        m=rot.to_4x4();m.translation=pos;matrices[p.name]=m
        kwargs={'parent_matrix':matrices[p.parent.name], 'parent_matrix_local':p.parent.bone.matrix_local} if p.parent else {}
        p.matrix_basis=p.bone.convert_local_to_pose(m,r,invert=True,**kwargs)
    bpy.context.view_layer.update()

def bone_attach(obj, rig, bone, local):
    obj.parent=rig;obj.parent_type='BONE';obj.parent_bone=bone
    obj.matrix_parent_inverse=Matrix.Identity(4)
    obj.matrix_basis=Matrix.Translation((0,-rig.data.bones[bone].length,0))  @  local

def props(body, clip='attack'):
    bronze=material('Plain bronze',(.38,.21,.065),.55)
    wood=material('Plain ash wood',(.23,.12,.045))
    # A non-deforming grip follows the forearm. No body bone is moved.
    bpy.context.view_layer.objects.active=body;body.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    b=body.data.edit_bones.new('prop_shield_grip');b.parent=body.data.edit_bones['lowerarm_l']
    b.head=b.parent.head;b.tail=b.parent.tail;b.roll=b.parent.roll;b.use_deform=False
    b=body.data.edit_bones.new('prop_spear_grip');b.parent=body.data.edit_bones['hand_r']
    b.head=b.parent.head;b.tail=b.parent.tail;b.roll=b.parent.roll;b.use_deform=False
    bpy.ops.object.mode_set(mode='OBJECT');bpy.context.view_layer.update()
    # Fit a static socket in each clip's entry pose; no per-frame prop correction.
    fore=body.pose.bones['lowerarm_l'];hand=body.pose.bones['hand_l']
    center=body.matrix_world  @  ((fore.head+hand.head)*.5)+Vector((-.03,-.14,-.10))
    if clip!='attack':
        center.y=min(fore.head.y,hand.head.y)-.14;center.z=1.18
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=16,radius=1,location=center)
    shield=bpy.context.object;shield.name='GEO-Rigid bronze shield';shield.scale=(.36,.055,.36)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);assign(shield,bronze)
    local=(body.matrix_world  @  body.pose.bones['prop_shield_grip'].matrix).inverted()  @  shield.matrix_world
    bone_attach(shield,body,'prop_shield_grip',local)
    # Attack uses a forward grip; carry/reaction clips use an upright entry grip.
    grip=Matrix.Translation((0,.055,-.022))  @  Matrix.Rotation(math.pi/2,4,'Z')
    if clip!='attack':
        # Fixed carry socket: shaft upright at entry, then follows the source hand.
        world=Matrix.Identity(4);world.translation=body.matrix_world  @  (body.pose.bones['hand_r'].matrix  @  Vector((0,.055,-.022)))
        world=world  @  Matrix.Rotation(-math.pi/2,4,'Y')
        grip=(body.matrix_world  @  body.pose.bones['prop_spear_grip'].matrix).inverted()  @  world
    bpy.ops.mesh.primitive_cylinder_add(vertices=12,radius=.018,depth=1.705)
    spear=bpy.context.object;spear.name='GEO-Rigid spear shaft';assign(spear,wood)
    local=grip  @  Matrix.Translation((.0075,0,0))  @  Matrix.Rotation(math.pi/2,4,'Y')
    bone_attach(spear,body,'prop_spear_grip',local)
    verts=[(1.425,0,0),(1.22,.075,0),(1.08,0,0),(1.22,-.075,0),(1.22,0,.022),(1.22,0,-.022)]
    verts=[(x-.22,y,z) for x,y,z in verts]
    faces=[(0,1,4),(1,2,4),(2,3,4),(3,0,4),(1,0,5),(2,1,5),(3,2,5),(0,3,5)]
    mesh=bpy.data.meshes.new('Leaf head');mesh.from_pydata(verts,[],faces);mesh.update()
    head=bpy.data.objects.new('GEO-Rigid spear leaf',mesh);bpy.context.collection.objects.link(head);assign(head,bronze)
    bone_attach(head,body,'prop_spear_grip',grip)
    return [shield,spear,head]

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--probe',action='store_true');parser.add_argument('--clip',default='attack')
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    clips = {
        'attack': ('ual1', 'Punch_Cross', 16, 14, False),
        'idle': ('ual2', 'Idle_Shield_Loop', 12, 4, True),
        'walk': ('ual2', 'Walk_Carry_Loop', 12, 6, True),
        'hit': ('ual1', 'Hit_Chest', 8, 12, False),
        'death': ('ual1', 'Death01', 14, 4, False),
    }
    s,body,donors,actions=setup()
    tag,name,*_=clips[args.clip]
    pose(body,donors[tag],actions[tag,name],0)
    rigid=props(body,args.clip)
    if args.probe:
        for tag,name in [('ual1','Punch_Cross'),('ual2','Idle_Shield_Loop'),('ual2','Walk_Carry_Loop'),('ual1','Death01')]:
            a=actions[tag,name];folder=OUT/'probe'/name;folder.mkdir(parents=True,exist_ok=True)
            for i in range(5):
                pose(body,donors[tag],a,a.frame_range[1]*i/4)
                s.render.filepath=str(folder/f'{i:02}.png');bpy.ops.render.render(write_still=True)
        return
    tag,name,count,fps,loop = clips[args.clip]
    source=actions[tag,name]; end=float(source.frame_range[1])
    samples=[end*i/(count if loop else count-1) for i in range(count)]
    if args.clip in ('death','hit'):samples=[min(end,i*24/fps) for i in range(count)]
    poses=[]
    for f in samples:
        pose(body,donors[tag],source,f)
        poses.append({p.name:(p.location.copy(),p.rotation_quaternion.copy()) for p in body.pose.bones if not p.name.startswith('prop_')})
    baked=bpy.data.actions.new('spearman-q-'+args.clip);body.animation_data.action=baked
    for i,values in enumerate(poses,1):
        for name,(loc,quat) in values.items():
            p=body.pose.bones[name];p.rotation_mode='QUATERNION';p.location=loc;p.rotation_quaternion=quat
            p.keyframe_insert('location',frame=i);p.keyframe_insert('rotation_quaternion',frame=i)
    s.render.fps=fps;s.frame_start=1;s.frame_end=count
    folder=OUT/'frames'/args.clip;folder.mkdir(parents=True,exist_ok=True)
    masters=OUT/'masters';masters.mkdir(parents=True,exist_ok=True)
    s.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath=str(masters/(args.clip+'.blend')))
    distances={o.name:[] for o in rigid}
    for i in range(1,count+1):
        s.frame_set(i);bpy.context.view_layer.update()
        for o in rigid:
            assert len(o.vertex_groups)==0 and o.data.shape_keys is None
            assert not any(m.type=='ARMATURE' for m in o.modifiers)
            v=o.data.vertices
            distances[o.name].append((o.matrix_world @ v[0].co-o.matrix_world @ v[len(v)//2].co).length)
        s.render.filepath=str(folder/f'{i-1:02}.png');bpy.ops.render.render(write_still=True)
    audit={name:max(ds)-min(ds) for name,ds in distances.items()}
    assert max(audit.values())<1e-5,audit
    receipt={'clip':args.clip,'library':tag,'action':source.name,'frames':count,'fps':fps,'source_samples_24fps':samples,
             'rigid_distance_variation_m':audit,'camera_matrix':[list(r) for r in s.camera.matrix_world],
             'ortho_scale':s.camera.data.ortho_scale,'body_pose':'Rest-space rotation transfer only; no hand-authored body keys',
             'source_duration_seconds':end/24,'output_duration_seconds':count/fps}
    (folder/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')

if __name__=='__main__':main()
