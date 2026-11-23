"""Read back the saved poses: stationary base, contact, loop closure and safe transforms."""
import bpy, hashlib, json, os
from pathlib import Path
from math import sin, pi
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
    errors=[];snapshots=[]
    for i,f in enumerate(json.loads(sc['sample_frames'])):
        sc.frame_set(f);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
        assert base.matrix_world==initial,'Moving base'
        for ob in sc.objects:
            assert min(abs(s) for s in ob.scale)>.001,ob.name
        poses={}
        for side,sg in [('r',1),('l',-1)]:
            ob=bpy.data.objects['GEO-soft leather boot '+side];ev=ob.evaluated_get(dg);me=ev.to_mesh()
            low=min((ob.matrix_world@v.co).z for v in me.vertices);ev.to_mesh_clear()
            target=.103+(.075*max(0,sg*sin(2*pi*i/count)) if name=='move' else 0)
            if name!='death':
                error=abs(low-target);errors.append(error);assert error<.006,(name,i,side,low,target)
            poses[side]=low
        snapshots.append(poses)
    if name in ('idle','move'):
        sc.frame_set(1);bpy.context.view_layer.update();start=[p.matrix.copy() for p in rig.pose.bones]
        sc.frame_set(count+1);bpy.context.view_layer.update()
        assert max(abs(a-b) for p,m in zip(rig.pose.bones,start) for r,s in zip(p.matrix,m) for a,b in zip(r,s))<1e-4,'Loop transform mismatch'
    if name=='death':
        height=(rig.matrix_world@rig.pose.bones['head'].head).z
        assert height<.70,('Death has not settled',height)
    report[name]={'max_sole_error_m':max(errors,default=0),'frames':count,'sole_heights':snapshots}
(M/'geometry-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print('GEOMETRY_AUDIT_OK: 53-bone rig, 40 poses, sole contact, loop closure, fixed base, safe scales')
