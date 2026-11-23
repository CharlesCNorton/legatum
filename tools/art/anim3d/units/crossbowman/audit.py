"""Structural source audit independent of image/atlas validation."""
import bpy,json,os,hashlib
from mathutils import Vector
from pathlib import Path
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/crossbowman';report={}
for clip,count in {'idle':8,'move':8,'attack':10,'hit':4,'death':10}.items():
    bpy.ops.wm.open_mainfile(filepath=str(M/'clips'/f'{clip}.blend'));sc=bpy.context.scene;rig=bpy.data.objects['RIG-crossbowman'];base=bpy.data.objects['GEO-stationary cream stone'];bmat=base.matrix_world.copy();assert len(rig.data.bones)>=50;assert len(bpy.data.objects['GEO-MPFB anatomical crossbowman'].data.vertices)>10000
    assert rig.animation_data.action and bpy.data.objects['CTRL-crossbow'].animation_data.action
    grip_errors=[];weapon_floor_clearances=[]
    for f in range(1,count+1):
        sc.frame_set(f);assert base.matrix_world==bmat
        weapon=bpy.data.objects['CTRL-crossbow']
        if clip!='death':
            grip=weapon.location+weapon.rotation_quaternion @ Vector((.05,.035,.04));wrist=rig.matrix_world @ rig.pose.bones['hand_r'].head;grip_errors.append((grip-wrist).length)
        for o in sc.objects:assert min(abs(v) for v in o.scale)>.0001,(clip,f,o.name)
        if clip=='death':
            floor=max((base.matrix_world @ Vector(corner)).z for corner in base.bound_box)
            dg=bpy.context.evaluated_depsgraph_get();lowest=float('inf')
            for part in weapon.children:
                if part.type!='MESH':continue
                ev=part.evaluated_get(dg);me=ev.to_mesh()
                lowest=min(lowest,min((ev.matrix_world @ v.co).z for v in me.vertices));ev.to_mesh_clear()
            weapon_floor_clearances.append(lowest-floor)
            assert lowest>=floor-.001,(clip,f,'weapon through stone',lowest,floor)
    assert sc.frame_end==count
    if grip_errors:assert max(grip_errors)<.06,(clip,'right wrist detached',max(grip_errors))
    loop_error=None
    if clip in ['idle','move']:
        def snapshot():
            return [v for o in [rig,weapon,bpy.data.objects['CTRL-pavise']] for row in o.matrix_world for v in row]+[v for p in rig.pose.bones for row in p.matrix for v in row]
        sc.frame_set(1);a=snapshot();sc.frame_set(count+1);b=snapshot();loop_error=max(abs(x-y) for x,y in zip(a,b));assert loop_error<1e-5,(clip,'loop discontinuity',loop_error)
    info=json.loads((M/'clips'/f'{clip}.json').read_text());assert info['model_sha256']==hashlib.sha256((M/'model.blend').read_bytes()).hexdigest()
    report[clip]={'frames':count,'bones':len(rig.data.bones),'stationary_base':True,'nonzero_scales':True,'max_right_wrist_error_m':max(grip_errors) if grip_errors else None,'loop_endpoint_matrix_error':loop_error}
    if weapon_floor_clearances:report[clip]['minimum_weapon_floor_clearance_m']=min(weapon_floor_clearances)
(M/'audit.json').write_text(json.dumps(report,indent=2));print('AUDIT_PASS',json.dumps(report))
