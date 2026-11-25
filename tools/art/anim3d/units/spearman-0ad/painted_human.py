"""Fit CC0 MPFB anatomy to the locked 0 A.D. bind pose; transfer native weights."""
import bpy,bmesh,math
import numpy as np
from mathutils import Vector
from pathlib import Path
from kit.human import create_body,freeze_macro_mix,add_rig


def replace_body(ctx):
    objects=ctx['objects'];g=ctx['g'];bones=ctx['bones'];original=ctx['original'];regions=ctx['regions'];indices=ctx['indices']
    active=ctx['active'];apply=ctx['apply'];mesh=ctx['mesh'];tube=ctx['tube']
    # Morphable source anatomy, preserved separately from the fitted delivery copy.
    body=create_body(dict(gender=1.,age=.42,muscle=1.,weight=.72,height=.42,proportions=.65),'Heroic MPFB anatomy')
    from bl_ext.user_default.mpfb.services.targetservice import TargetService
    from bl_ext.user_default.mpfb.services.locationservice import LocationService
    for side in ['l','r']:
        for target,value in [('upperarm-muscle-incr',.65),('upperarm-shoulder-muscle-incr',.45),('lowerarm-muscle-incr',.45)]:
            TargetService.load_target(body,str(Path(LocationService.get_mpfb_data('targets'))/'arms'/f'{side}-{target}.target.gz'),weight=value)
    freeze_macro_mix(body);rig=add_rig(body,'Temporary MPFB fitting rig')
    for mod in list(body.modifiers):
        if mod.type=='ARMATURE':body.modifiers.remove(mod)
        else:
            active(body);bpy.ops.object.modifier_apply(modifier=mod.name)
    inv=np.array(g.accessor(g.doc['skins'][0]['inverseBindMatrices'])).reshape(-1,4,4).transpose(0,2,1)
    target={name:Vector(np.linalg.inv(m)[:3,3]) for name,m in zip(bones,inv)}
    def convert(p):return Vector((p.x,p.z,-p.y))
    source={b.name:(convert(b.head_local),convert(b.tail_local)) for b in rig.data.bones}
    maps={}
    for side in ['l','r']:
        S=side.upper()
        for src,dst,end in [('clavicle','shoulder','arm'),('upperarm','arm','forearm'),('lowerarm','forearm','hand'),('thigh','thigh','leg'),('calf','leg','foot')]:
            maps[src+'_'+side]=(source[src+'_'+side][0],source[src+'_'+side][1],target[dst+'_'+S],target[end+'_'+S],1.12)
        palm=source['hand_'+side][0];finger=source['middle_01_'+side][0]
        maps['hand_'+side]=(palm,finger,target['hand_'+S],target['finger_'+S],1.12)
        # Common finger-frame transforms retain the spacing/anatomy of all five digits.
        for name in source:
            if name.endswith('_'+side) and name.startswith(('index_','middle_','ring_','pinky_','thumb_')):
                stage=int(name.split('_')[1])
                a,b=source['middle_0'+str(stage)+'_'+side]
                dst=target['finger_'+S] if stage==1 else target['fingertip_'+S]
                end=target['fingertip_'+S] if stage==1 else dst+Vector((-.012 if side=='l' else .012,-.010,-.006))
                maps[name]=(a,b,dst,end,.78)
    def transform(p,name):
        if name in maps:
            a,b,c,d,radial=maps[name];u=b-a;v=d-c;q=u.rotation_difference(v)
            along=(p-a).dot(u)/u.length_squared
            return c+v*along+q@((p-a)-u*along)*radial
        if name.startswith(('foot_','ball_')):
            side=name[-1];a=source['foot_'+side][0];c=target['foot_'+side.upper()]
            return c+Vector(((p.x-a.x)*.88,(p.y-a.y)*.88,(p.z-a.z)*.86))
        if name=='head':return target['head']+(p-source['head'][0])*1.06
        if name=='neck_01':
            a,b=source[name];c,d=target['neck'],target['head'];u=b-a;v=d-c
            along=(p-a).dot(u)/u.length_squared
            return c+v*along+u.rotation_difference(v)@((p-a)-u*along)
        # Broad torso under the sculpted cuirass, with its own muscle surface.
        return Vector((p.x*1.08,p.y-.070,p.z+.012))
    for v in body.data.vertices:
        p=convert(v.co);weights=[(body.vertex_groups[w.group].name,w.weight) for w in v.groups if body.vertex_groups[w.group].name in source and w.weight>1e-6]
        total=sum(w for _,w in weights)
        v.co=sum((transform(p,n)*w for n,w in weights),Vector())/total if total else transform(p,'pelvis')
    # Remove surfaces wholly concealed by armour/tunic, keeping anatomy at all joints.
    bm=bmesh.new();bm.from_mesh(body.data)
    hidden=[]
    for f in bm.faces:
        p=f.calc_center_median()
        if (.91<p.y<1.23 and abs(p.x)<.19) or (.64<p.y<.86 and abs(p.x)<.21):hidden.append(f)
    bmesh.ops.delete(bm,geom=hidden,context='FACES')
    bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(body.data);bm.free()
    # Native tunic/head donor, excluding cloak/props so back vertices cannot inherit cape weights.
    faces=[]
    for r in regions:
        if r['part'] not in {'body','Greek head'} or r['team']:continue
        for i in range(0,len(indices),3):
            face=indices[i:i+3]
            if not r['start']<=face[0]<r['start']+r['count']:continue
            if any(bones[int(j)].startswith('cape') and w>.001 for vi in face for j,w in zip(original['JOINTS_0'][vi],original['WEIGHTS_0'][vi])):continue
            faces.append(face)
    ww=[list(zip(js,ws)) for js,ws in zip(original['JOINTS_0'],original['WEIGHTS_0'])]
    donor=mesh('Weight transfer donor',original['POSITION'],faces,'skin',weights=ww)
    body.vertex_groups.clear()
    for name in bones:body.vertex_groups.new(name=name)
    active(body);mod=body.modifiers.new('Native nearest-face skin transfer','DATA_TRANSFER');mod.object=donor
    mod.use_vert_data=True;mod.data_types_verts={'VGROUP_WEIGHTS'};mod.vert_mapping='POLYINTERP_NEAREST'
    mod.layers_vgroup_select_src='ALL';mod.layers_vgroup_select_dst='NAME'
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.ops.object.vertex_group_limit_total(limit=4);bpy.ops.object.vertex_group_normalize_all(lock_active=False)
    for ob in list(objects):
        if ob['part'] in {'body','Greek head','Weight transfer donor'}:
            objects.remove(ob);bpy.data.objects.remove(ob,do_unlink=True)
    bpy.data.objects.remove(rig,do_unlink=True)
    body.name='GEO-heroicbody';body['part']='heroicbody';body['bone']='';body['team']='';body['mat']='skin'
    body.data.materials.clear();body.data.materials.append(ctx['M']['skin']);body.data.materials.append(ctx['M']['leather'])
    for f in body.data.polygons:
        f.use_smooth=True
        if f.center.y<.025:f.material_index=1
    objects.append(body)
    # Heroic helmet clearance for the anatomical head; sockets remain unchanged.
    pivot=target['head']
    for ob in objects:
        if ob['part'] in {'helmet','crest_base'}:
            for v in ob.data.vertices:
                q=v.co-pivot;v.co=pivot+Vector((q.x*1.12,q.y*1.08,q.z*1.12))
        elif ob['part']=='crest':
            for v in ob.data.vertices:v.co.y+=.019
    # Leather sandal straps follow the unchanged foot sockets.
    for side in ['L','R']:
        c=target['foot_'+side]
        for z in [.025,.075]:
            pts=[(c.x+.058*math.cos(a),.025+.033*math.sin(a),c.z+z) for a in np.linspace(0,math.pi,13)]
            tube('sandal:leather strap',pts,[.006]*13,'leather','foot_'+side,seg=6)
    print('MPFB_FITTED',len(body.data.vertices),'vertices; nearest-face native weights, maximum four',flush=True)
