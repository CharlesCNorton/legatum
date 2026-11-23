"""Structural checks and diagnostic motion bounds; does not approve the art."""
import bpy,os,json,hashlib
from pathlib import Path
from mathutils import Vector
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/barbarian-scout'
source=hashlib.sha256((M/'barbarian-scout.blend').read_bytes()).hexdigest()
counts={'idle':8,'move':8,'attack':10,'hit':4,'death':10};report={}
for name,count in counts.items():
    bpy.ops.wm.open_mainfile(filepath=str(M/'clips'/name/(name+'.blend')))
    sc=bpy.context.scene;rig=bpy.data.objects['Scout • MPFB rig'];base=bpy.data.objects['GEO-stationary-cream-base']
    assert sc.get('round2_registered'), 'Missing round-two geometry registration'
    assert not bpy.data.objects['GEO-anatomy'].data.shape_keys, 'Unfrozen shape keys'
    assert sc.camera and rig.type=='ARMATURE' and len(rig.data.bones)>=50
    assert sc['source_sha256']==source and sc['clip_count']==count
    assert sc.get('actual_bakes') and (M/'bakes.json').exists()
    assert len(bpy.data.objects['GEO-anatomy'].data.vertices)>10000
    rest=base.matrix_world.copy();poses=[];bounds=[]
    for frame in range(1,count+1):
        sc.frame_set(frame);bpy.context.view_layer.update()
        assert base.matrix_world==rest,'Moving base'
        for o in sc.objects:
            assert min(abs(v) for v in o.scale)>1e-4,(name,frame,o.name,'degenerate scale')
        if name=='attack' and 3<=frame<=7:
            haft=bpy.data.objects['GEO-axe-haft']
            grip=haft.matrix_world@Vector(haft['grip_local'])
            palm=rig.matrix_world@rig.pose.bones['hand_r'].matrix@Vector((0,.035,0))
            assert (grip-palm).length<.002,(frame,'axe grip misses palm',(grip-palm).length)
        poses.append([v for p in rig.pose.bones for row in p.matrix for v in row])
        points=[]
        for o in sc.objects:
            if o.type=='MESH' and o!=base and not o.hide_render:
                e=o.evaluated_get(bpy.context.evaluated_depsgraph_get())
                points.extend(e.matrix_world@Vector(p) for p in e.bound_box)
        bounds.append({'frame':frame,'min':[min(v[i] for v in points) for i in range(3)],'max':[max(v[i] for v in points) for i in range(3)]})
    assert any(max(abs(a-b) for a,b in zip(poses[0],p))>.001 for p in poses[1:]),'No skeletal motion'
    if name=='death':assert max(abs(a-b) for a,b in zip(poses[-1],poses[-2]))<1e-6
    if name in ('idle','move'):
        sc.frame_set(count+1);end=[v for p in rig.pose.bones for row in p.matrix for v in row]
        assert max(abs(a-b) for a,b in zip(poses[0],end))<1e-5,'Loop does not close'
    report[name]={'bones':len(rig.data.bones),'frames':count,'bounds':bounds,'stationary_base':True,'positive_scales':True}
(M/'audit.json').write_text(json.dumps({'technical_checks':'passed','art_approved':False,'notes':'Bounding boxes are conservative diagnostics, not a skin/cloth collision solver. Grounding, projection seams and hand grip require visual review.','clips':report},indent=2))
print('AUDIT_OK: anatomy, rig, bake evidence, source hashes, positive scale, stationary base, five moving clips, closed loops, held death')
