"""Fit the existing painted armour to the unchanged Quaternius body and rig."""
import bpy
import numpy as np
from mathutils import Matrix,Vector


def attach_costume(body, master, bone_attach):
    before=set(bpy.data.objects)
    with bpy.data.libraries.load(str(master),link=False) as (src,dst):
        dst.objects=[n for n in src.objects if n not in ('Camera','Stationary cream stone')]
    imported=set(bpy.data.objects)-before
    for ob in imported:
        if not ob.users_collection:bpy.context.collection.objects.link(ob)
    bpy.context.view_layer.update()
    old=next(o for o in imported if o.type=='ARMATURE')
    dg=bpy.context.evaluated_depsgraph_get()
    selected=[]
    shell=next(o for o in imported if o.name.startswith('Convex bronze aspis'))
    points=np.array([tuple(shell.matrix_world @ v.co) for v in shell.data.vertices])
    center=Vector((points.min(0)+points.max(0))/2)
    _,axes=np.linalg.eigh(np.cov(points.T));normal=Vector(axes[:,0])
    if normal.y>0:normal=-normal
    flatten=normal.rotation_difference(Vector((0,-1,0))).to_matrix().to_4x4()
    placeholder=bpy.data.objects['GEO-Rigid bronze shield']
    shield_warp=Matrix.Translation(placeholder.matrix_world.translation) @ flatten @ Matrix.Translation(-center)

    for ob in imported:
        if ob.type!='MESH' or ob.hide_render:continue
        name=ob.name.lower()
        bone=ob.parent_bone
        part=None
        if ob.parent and ob.parent.name.startswith('Aspis control'):
            part='shield';bone='prop_shield_grip'
        elif ob.parent==old and bone in ('head','spine_01','spine_03','pelvis'):
            if bone=='head':part='crest' if 'horsehair' in name else 'helmet'
            elif 'pteruges' in name:part='skirt'
            elif 'crimson' in name or 'clasp' in name:part='cloak'
            elif 'belt' in name or 'baldric' in name or 'buckle' in name:part='belt'
            else:part='cuirass'
        elif name.startswith('contoured greave'):
            side=name[-1];bone='calf_'+side;part='greave_'+side
        if not part:continue
        target='Head' if bone=='head' else bone
        evaluated=ob.evaluated_get(dg)
        mesh=bpy.data.meshes.new_from_object(evaluated,preserve_all_data_layers=True,depsgraph=dg)
        item=bpy.data.objects.new('KIT '+ob.name,mesh);bpy.context.collection.objects.link(item)
        item.vertex_groups.clear()
        # Bone frames include both rigs' rest roll; the old frozen UVs stay put.
        dest=body.pose.bones[target]
        if part=='shield':
            world=shield_warp @ ob.matrix_world
            local=(body.matrix_world @ dest.matrix).inverted() @ world
            bone_attach(item,body,target,local);item['look_part']=part;selected.append(item)
            continue
        src=old.pose.bones[bone]
        rest=dest.bone.matrix_local.to_quaternion().inverted() @ src.bone.matrix_local.to_quaternion()
        rotation=dest.matrix.to_quaternion() @ rest @ src.matrix.to_quaternion().inverted()
        warp=rotation.to_matrix().to_4x4()
        warp.translation=dest.head-warp.to_3x3() @ src.head
        world=body.matrix_world @ warp @ old.matrix_world.inverted() @ ob.matrix_world
        local=(body.matrix_world @ dest.matrix).inverted() @ world
        bone_attach(item,body,target,local)
        item['look_part']=part
        selected.append(item)
    placeholder.hide_render=True
    for ob in imported:bpy.data.objects.remove(ob,do_unlink=True)
    return selected


def floor_contact(scene, count):
    """Collision-only cloth/hair corrective keys; never modify the body or props."""
    for ob in list(scene.objects):
        if ob.type!='MESH' or not ob.name.startswith('KIT ') or ob.get('look_part') not in ('crest','skirt'):continue
        corrections=[]
        for frame in range(1,count+1):
            scene.frame_set(frame);bpy.context.view_layer.update()
            world=ob.matrix_world.copy();inverse=world.inverted()
            changed={}
            for vertex in ob.data.vertices:
                point=world @ vertex.co
                if point.z<.107:
                    point.z=.107;changed[vertex.index]=inverse @ point
            if changed:
                if not ob.data.shape_keys:ob.shape_key_add(name='Basis',from_mix=False)
                key=ob.shape_key_add(name=f'Stone contact {frame:02}',from_mix=False)
                for index,point in changed.items():key.data[index].co=point
                corrections.append((frame,key))
        for target,key in corrections:
            for frame in range(1,count+1):
                key.value=float(frame==target);key.keyframe_insert('value',frame=frame)
