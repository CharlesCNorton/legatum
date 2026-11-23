"""Fit full-depth geometry in the fixed rest view; never warp projected UVs."""
import bpy, json
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view


def finish_and_fit(master):
    sc=bpy.context.scene; cam=sc.camera
    cam.location=(.45,-7,3.0)
    cam.rotation_euler=(Vector((0,0,.88))-cam.location).to_track_quat('-Z','Y').to_euler()
    bpy.context.view_layer.update()
    # Bake only static macro shape keys, retaining original anatomy and skin weights.
    for ob in list(sc.objects):
        if ob.type=='CURVE':
            bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob;bpy.ops.object.convert(target='MESH')
        if ob.type!='MESH':continue
        if 'MPFB' in ob.name and ob.data.shape_keys:
            ob.shape_key_add(name='Frozen macro mix',from_mix=True)
            for key in list(ob.data.shape_keys.key_blocks)[:-1]:ob.shape_key_remove(key)
            ob.shape_key_remove(ob.data.shape_keys.key_blocks[0])
        # Rigid finished surfaces must own the projection, not their coarse cages.
        if not ob.data.shape_keys and not any(m.type=='ARMATURE' for m in ob.modifiers):
            bpy.context.view_layer.objects.active=ob
            for mod in list(ob.modifiers):
                if mod.type in {'SOLIDIFY','BEVEL','SUBSURF'}:
                    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.context.view_layer.update()
    right=cam.matrix_world.to_quaternion() @ Vector((1,0,0));up=cam.matrix_world.to_quaternion() @ Vector((0,1,0));unit=cam.data.ortho_scale/256
    records=[]
    def coords(ob):
        return [world_to_camera_view(sc,cam,ob.matrix_world @ v.co) for v in ob.data.vertices]
    def fit_group(prefixes, target):
        obs=[o for o in sc.objects if o.type=='MESH' and any(o.name.startswith('GEO-'+p) for p in prefixes)]
        points=[c for o in obs for c in coords(o)]
        if not points:return
        box=[min(c.x for c in points)*256,(1-max(c.y for c in points))*256,max(c.x for c in points)*256,(1-min(c.y for c in points))*256]
        l,t,r,b=target
        for ob in obs:
            inv=ob.matrix_world.inverted()
            for i,c in enumerate(coords(ob)):
                x=c.x*256;y=(1-c.y)*256
                xx=l+(x-box[0])/(box[2]-box[0])*(r-l);yy=t+(y-box[1])/(box[3]-box[1])*(b-t)
                delta=inv.to_3x3() @ (right*((xx-x)*unit)+up*((y-yy)*unit))
                if ob.data.shape_keys:
                    for key in ob.data.shape_keys.key_blocks:key.data[i].co+=delta
                else:ob.data.vertices[i].co+=delta
            ob.data.update()
        records.append({'objects':[o.name for o in obs],'before':box,'target':target,'method':'Camera-plane mesh fitting, unchanged depth and bone attachment'})
    fit_group(['full length linen skirt'],(99,87,167,198))
    fit_group(['olive diagonal overdrape'],(110,90,172,184))
    fit_group(['rust shawl shoulder folds'],(96,48,169,83))
    fit_group(['rust shawl long fringed tail','shawl fringe'],(148,62,187,166))
    fit_group(['gathered linen bodice'],(107,58,158,102))
    fit_group(['hood','open linen hood'],(109,12,154,66))
    fit_group(['chestnut hair cap','wavy temple lock'],(122,15,148,57))
    fit_group(['ochre traveller pack','pack woven rib'],(158,74,186,112))
    fit_group(['rolled wool blanket','blanket visible spiral'],(157,48,188,75))
    fit_group(['leather belt'],(116,87,150,98))
    fit_group(['knotted belt tail'],(137,91,153,142))
    fit_group(['pack strap','strap saddle stitch'],(140,51,165,108))
    fit_group(['brass shawl pin','pin concentric relief'],(137,55,144,62))
    fit_group(['folded sleeve upperarm r'],(96,72,115,98))
    fit_group(['folded sleeve lowerarm r'],(92,81,110,104))
    fit_group(['folded sleeve upperarm l'],(149,65,170,94))
    fit_group(['folded sleeve lowerarm l'],(145,73,168,97))
    # Fit the weighted head via the inverse blended bone transform. Body remains 3D.
    body=bpy.data.objects['GEO-MPFB female traveller'];rig=bpy.data.objects['RIG-Settler MPFB']
    transforms={g.index:rig.matrix_world @ rig.pose.bones[g.name].matrix @ rig.data.bones[g.name].matrix_local.inverted() @ rig.matrix_world.inverted() @ body.matrix_world for g in body.vertex_groups if g.name in rig.pose.bones}
    selected=[]
    for v in body.data.vertices:
        weights=[(g.weight,transforms[g.group]) for g in v.groups if g.group in transforms]
        total=sum(w for w,m in weights)
        if not total:continue
        mat=Matrix([[sum(w*m[r][c] for w,m in weights)/total for c in range(4)] for r in range(4)])
        pos=mat @ v.co
        if pos.z>1.56:
            c=world_to_camera_view(sc,cam,pos);selected.append((v,mat,pos,c.x*256,(1-c.y)*256))
    box=[min(v[3] for v in selected),min(v[4] for v in selected),max(v[3] for v in selected),max(v[4] for v in selected)]
    for v,mat,pos,x,y in selected:
        xx=124+(x-box[0])/(box[2]-box[0])*25;yy=18+(y-box[1])/(box[3]-box[1])*37
        v.co=mat.inverted() @ (pos+right*((xx-x)*unit)+up*((y-yy)*unit))
    body.data.update()
    base=bpy.data.objects['GEO-stationary cream base'];base.location.y+=.20
    # Standard clothing-body culling: retain the full editable body and weights.
    # Torso and upper legs are enclosed by complete opaque bodice/skirt meshes.
    group=body.vertex_groups['Visible outside opaque robe'];group.remove(list(range(len(body.data.vertices))))
    names={g.index:g.name for g in body.vertex_groups}
    visible=[]
    for v in body.data.vertices:
        arm_weight=sum(g.weight for g in v.groups if any(k in names[g.group] for k in ['upperarm','lowerarm','hand','clavicle','index','middle','ring','pinky','thumb']))
        if v.co.z<.31 or v.co.z>1.50 or arm_weight>.35:visible.append(v.index)
    group.add(visible,1,'REPLACE')
    # Softer product light and a display transform appropriate to painted illumination.
    sc.view_settings.view_transform='Standard';sc.view_settings.look='None'
    for ob in sc.objects:
        if ob.type=='LIGHT':ob.data.energy*=.55
    (master/'registration.json').write_text(json.dumps(records,indent=2))
