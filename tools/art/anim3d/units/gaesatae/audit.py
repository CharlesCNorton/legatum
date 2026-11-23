"""Read back the saved poses: stationary base, contact, loop closure and safe transforms."""
import bpy, hashlib, json, os
from pathlib import Path
from math import atan2, degrees
from mathutils import Quaternion
M=Path(os.environ['ANIM_ROOT'])/'masters/gaesatae'
CLIPS={'idle':8,'move':8,'attack':10,'hit':4,'death':10}
report={}
source=hashlib.sha256((M/'gaesatae.blend').read_bytes()).hexdigest()
for name,count in CLIPS.items():
    bpy.ops.wm.open_mainfile(filepath=str(M/'clips'/f'{name}.blend'))
    sc=bpy.context.scene;rig=bpy.data.objects['Gaesatae • MPFB game_engine']
    assert sc['source_sha256']==source and len(rig.data.bones)==53
    base=bpy.data.objects['GEO-stationary cream stone'];initial=base.matrix_world.copy()
    assert sc.get('surface_finished')
    pants=bpy.data.objects['GEO-folded wool trousers']
    hand_groups={g.index for g in pants.vertex_groups if g.name.startswith(('hand_','index_','middle_','ring_','pinky_','thumb_'))}
    assert not any(g.group in hand_groups and g.weight>.1 for v in pants.data.vertices for g in v.groups),'Hand geometry in trouser shell'
    errors=[];snapshots=[];headings=[];toe_positions=[]
    motion=json.loads((M/'clips'/f'{name}-motion.json').read_text())
    if name!='attack':assert motion['license']=='CC0-1.0'
    for i,f in enumerate(json.loads(sc['sample_frames'])):
        sc.frame_set(f);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
        assert base.matrix_world==initial,'Moving base'
        for ob in sc.objects:
            assert min(abs(s) for s in ob.scale)>.001,ob.name
        poses={}
        for side,sg in [('r',1),('l',-1)]:
            ob=bpy.data.objects['GEO-soft leather boot '+side];ev=ob.evaluated_get(dg);me=ev.to_mesh()
            low=min((ob.matrix_world@v.co).z for v in me.vertices);ev.to_mesh_clear()
            if name=='move':
                foot=rig.pose.bones['foot_'+side];toe=rig.pose.bones['ball_'+side]
                heading=degrees(atan2((toe.head-foot.head).x,-(toe.head-foot.head).y))
                headings.append(heading)
                stance=('l' if 1<=i<=4 else 'r')
                if side==stance:assert abs(heading)<35,('Planted foot points away from travel',i,side,heading)
                expected=Quaternion(motion['target_foot_rotations'][i][side])
                angle=foot.matrix.to_quaternion().rotation_difference(expected).angle
                assert min(angle,abs(angle-6.283185307))<.01,('Foot rotation altered after retarget',i,side,angle)
            if name!='death':assert low>.096,('Foot penetrates stone',name,i,side,low)
            poses[side]=low
        if name!='death':
            error=abs(min(poses.values())-.103);errors.append(error)
            assert error<.006,('No support sole',name,i,poses)
        if name=='move':toe_positions.append({side:list(rig.matrix_world@rig.pose.bones['ball_'+side].head) for side in ['l','r']})
        snapshots.append(poses)
    if name in ('idle','move'):
        sc.frame_set(1);bpy.context.view_layer.update();start=[p.matrix.copy() for p in rig.pose.bones]
        sc.frame_set(count+1);bpy.context.view_layer.update()
        assert max(abs(a-b) for p,m in zip(rig.pose.bones,start) for r,s in zip(p.matrix,m) for a,b in zip(r,s))<1e-4,'Loop transform mismatch'
    if name=='death':
        height=(rig.matrix_world@rig.pose.bones['head'].head).z
        assert height<.70,('Death has not settled',height)
    if name=='move':
        speed=motion['contact']['virtual_ground_m_per_sample']
        residuals=[]
        for side,start,end in [('l',1,4),('r',5,7)]:
            anchor=toe_positions[start][side]
            for i in range(start,end+1):
                point=toe_positions[i][side]
                residuals.append(((point[0]-anchor[0])**2+(point[1]-anchor[1]-speed*(i-start))**2)**.5)
        assert max(residuals)<.012,('Stance sliding',residuals)
    report[name]={'foot_heading_degrees':headings,'max_stance_slip_m':max(residuals) if name=='move' else None,'max_sole_error_m':max(errors,default=0),'frames':count,'sole_heights':snapshots}
(M/'geometry-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print('GEOMETRY_AUDIT_OK: 53-bone rig, 40 poses, sole contact, loop closure, fixed base, safe scales')
