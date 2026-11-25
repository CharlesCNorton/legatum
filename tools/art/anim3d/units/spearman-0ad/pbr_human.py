"""CC0 MPFB anatomy fitted to the frozen 0 A.D. rest pose, then weight transfer.

The temporary MPFB rig is only a fitting guide. It is never exported or animated.
"""
import bpy, bmesh
from mathutils import Vector
from pathlib import Path
from kit.human import create_body, freeze_macro_mix, add_rig


def build(mesh, mod, material, parts, old, indices, source, bones, work):
    human=create_body({'gender':1.,'muscle':1.,'weight':.72,'height':.55,'age':.35},'GEO-CC0 muscular anatomy')
    freeze_macro_mix(human);guide=add_rig(human,'CC0 fitting guide')
    # Remove MakeHuman's non-rendering fitting helper surfaces before decimation.
    bpy.context.view_layer.objects.active=human
    for modifier in list(human.modifiers):
        if modifier.type=='MASK':bpy.ops.object.modifier_apply(modifier=modifier.name)
    worlds=source.worlds(None,0)
    dest={name:Vector(worlds[source.doc['skins'][0]['joints'][i]][12:15]) for name,i in bones.items()}
    def convert(v):return Vector((v.x,v.z,-v.y))
    mapping={'pelvis':('hip','spine'),'spine_01':('spine','spine1'),
             'spine_02':('spine1','chest'),'spine_03':('chest','neck'),
             'neck_01':('neck','head'),'head':('head',None)}
    for side in ('l','r'):
        s=side.upper()
        for a,b,c in [('clavicle','shoulder','arm'),('upperarm','arm','forearm'),
                      ('lowerarm','forearm','hand'),('hand','hand','finger'),
                      ('thigh','thigh','leg'),('calf','leg','foot'),('foot','foot',None),('ball','foot',None)]:
            mapping[a+'_'+side]=(b+'_'+s,c+'_'+s if c else None)
    transforms={}
    for bone in guide.data.bones:
        name=bone.name
        if name=='Root':continue
        a=convert(bone.head_local);b=convert(bone.tail_local)
        if name in mapping:
            first,last=mapping[name];target=dest[first]
            if last:end=dest[last]
            elif first=='head':end=target+Vector((0,.19,0))
            else:end=target+Vector((0,-.025,.15))
            if name=='spine_03':b=convert(guide.data.bones['neck_01'].head_local)
            # Hand guide has a tiny palm bone; use the actual metacarpal span.
            if name.startswith('hand_'):b=convert(guide.data.bones['middle_01_'+name[-1]].head_local)
            if name.startswith('ball_'):
                a=convert(guide.data.bones['foot_'+name[-1]].head_local);b=convert(guide.data.bones['ball_'+name[-1]].tail_local)
        else:
            side=name[-1].upper();first='finger_'+side
            target=dest[first];end=dest['fingertip_'+side]
            # All five source fingers keep separate offsets around the grip.
            family=name.split('_')[0]
            offsets={'index':.025,'middle':.008,'ring':-.010,'pinky':-.025,'thumb':.038}
            target=target+Vector((offsets.get(family,0)*(1 if side=='L' else -1),.013 if family=='thumb' else 0,.014 if family=='thumb' else 0))
            end=end+(target-dest[first])
            a=convert(guide.data.bones[family+'_01_'+name[-1]].head_local)
            b=convert(guide.data.bones[family+'_03_'+name[-1]].tail_local)
        axis=b-a;target_axis=end-target
        rotation=axis.rotation_difference(target_axis)
        scale=target_axis.length/axis.length
        radial_scale=1.38 if name.startswith('upperarm') else 1.30 if name.startswith('lowerarm') else 1.14 if name.startswith(('thigh','calf')) else 1.10
        transforms[name]=(a,target,axis.normalized(),rotation,scale,radial_scale)
    for vertex in human.data.vertices:
        p=convert(vertex.co);result=Vector();total=0
        for w in vertex.groups:
            name=human.vertex_groups[w.group].name
            if name not in transforms:continue
            a,target,axis,rotation,length_scale,radial_scale=transforms[name]
            delta=p-a;along=axis*delta.dot(axis)
            q=target+rotation@(along*length_scale+(delta-along)*radial_scale)
            result+=q*w.weight;total+=w.weight
        vertex.co=result/total if total else Vector((p.x,p.y*1.05,p.z))
    # Transfer the approved native weights by nearest triangle interpolation.
    for modifier in list(human.modifiers):human.modifiers.remove(modifier)
    human.parent=None;human.matrix_world.identity();human.vertex_groups.clear()
    body_ids={i for r in source.doc['meshes'][0]['extras']['vertex_regions'] if r['part']=='body' and not r['team'] for i in range(r['start'],r['start']+r['count']) if not any(int(j) in (4,5,6) and w>.1 for j,w in zip(old['JOINTS_0'][i],old['WEIGHTS_0'][i]))}
    faces=[indices[i:i+3] for i in range(0,len(indices),3) if all(j in body_ids for j in indices[i:i+3])]
    donor=mesh('weight transfer donor',old['POSITION'],faces,material('skin','body'),weights=[{int(j):w for j,w in zip(js,ws) if w>0} for js,ws in zip(old['JOINTS_0'],old['WEIGHTS_0'])])
    bpy.context.view_layer.objects.active=human
    transfer=human.modifiers.new('Native nearest face weights','DATA_TRANSFER');transfer.object=donor;transfer.use_vert_data=True;transfer.data_types_verts={'VGROUP_WEIGHTS'};transfer.vert_mapping='POLYINTERP_NEAREST';transfer.layers_vgroup_select_src='ALL';transfer.layers_vgroup_select_dst='NAME'
    bpy.ops.object.datalayout_transfer(modifier=transfer.name)
    bpy.ops.object.modifier_apply(modifier=transfer.name)
    # Seat the larger CC0 foot around the approved sandal footprint, without
    # changing ankle pose or yaw. This is a rest-shape fit, not an animation edit.
    for v in human.data.vertices:
        foot=sum(w.weight for w in v.groups if human.vertex_groups[w.group].name in ('j25','j28'))
        v.co.z+=.040*foot
    # The native body donor ends at the neck; the rigid original head was a
    # separate prop. Complete that missing transfer surface with its same bone.
    for v in human.data.vertices:
        if v.co.y>1.49:
            for group in human.vertex_groups:group.remove([v.index])
            human.vertex_groups['j8'].add([v.index],1,'REPLACE')
    bpy.ops.object.vertex_group_limit_total(limit=4);bpy.ops.object.vertex_group_normalize_all(lock_active=False)
    parts.remove(donor);bpy.data.objects.remove(donor,do_unlink=True);bpy.data.objects.remove(guide,do_unlink=True)
    human.data.materials.clear();human.data.materials.append(material('skin','body'))
    for p in human.data.polygons:p.material_index=0;p.use_smooth=True
    bpy.data.libraries.write(str(work/'cc0-fitted-anatomy.blend'),{human},fake_user=True)
    # Hidden torso / head detail cannot spend the game budget. The entire sculpt
    # is retained in the separate source blend; visible anatomy gets 2500 tris.
    bm=bmesh.new();bm.from_mesh(human.data)
    hidden=[f for f in bm.faces if all(.70<v.co.y<1.27 and abs(v.co.x)<.20 for v in f.verts)]
    bmesh.ops.delete(bm,geom=hidden,context='FACES');bm.to_mesh(human.data);bm.free()
    human.data.calc_loop_triangles();mod(human,'DECIMATE',ratio=min(1,2400/len(human.data.loop_triangles)))
    parts.append(human)
    return human
