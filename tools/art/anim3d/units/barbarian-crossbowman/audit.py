"""Structural source audit independent of image/atlas validation."""
import bpy,json,os,hashlib
from pathlib import Path
from mathutils import Vector
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/barbarian-crossbowman';report={}
for clip,count in {'idle':8,'move':8,'attack':10,'hit':4,'death':10}.items():
    bpy.ops.wm.open_mainfile(filepath=str(M/'clips'/f'{clip}.blend'));sc=bpy.context.scene;rig=bpy.data.objects['RIG-barbarian-crossbowman'];base=bpy.data.objects['GEO-stationary cream stone'];bmat=base.matrix_world.copy();assert len(rig.data.bones)>=50;assert len(bpy.data.objects['GEO-MPFB anatomical brigand'].data.vertices)>10000
    body=bpy.data.objects['GEO-MPFB anatomical brigand'];assert not body.data.shape_keys,'Unfrozen macro anatomy'
    assert sc.view_settings.view_transform=='Standard'
    for o in sc.objects:
        if o.type=='MESH' and o!=base and o.name!='GEO-CC0 anatomical eyes':
            assert o.data.uv_layers.get('Painting fixed UV'),o.name
            for mat in o.data.materials:
                assert mat.node_tree.nodes.get('Camera painted pigment'),o.name
                assert any(n.type=='LIGHT_PATH' for n in mat.node_tree.nodes),o.name
    max_grip=0
    assert rig.animation_data.action and bpy.data.objects['CTRL-crossbow'].animation_data.action
    for f in range(1,count+1):
        sc.frame_set(f);assert base.matrix_world==bmat
        if clip in ['idle','move','attack']:
            weapon=bpy.data.objects['CTRL-crossbow'];expected=weapon.matrix_world@Vector(weapon['grip_local']);actual=rig.matrix_world@rig.pose.bones['hand_r'].head;max_grip=max(max_grip,(expected-actual).length)
        for o in sc.objects:assert min(abs(v) for v in o.scale)>.0001,(clip,f,o.name)
    assert max_grip<.002,(clip,'wrist/stock grip error',max_grip)
    assert sc.frame_end==count
    info=json.loads((M/'clips'/f'{clip}.json').read_text());assert info['model_sha256']==hashlib.sha256((M/'model.blend').read_bytes()).hexdigest()
    report[clip]={'frames':count,'bones':len(rig.data.bones),'stationary_base':True,'nonzero_scales':True,'max_wrist_grip_error_m':max_grip,'finished_projection':True}
(M/'audit.json').write_text(json.dumps(report,indent=2));print('AUDIT_PASS',json.dumps(report))
