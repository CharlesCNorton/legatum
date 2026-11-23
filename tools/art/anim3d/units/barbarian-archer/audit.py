"""Read saved scenes and evaluate actual weapon attachments at every output frame."""
import hashlib
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import *

source = MASTER/'master.blend'
digest = hashlib.sha256(source.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(source))
assert bpy.context.scene.get('round2_finished_projection')
body = bpy.data.objects['GEO-MPFB-anatomy']
assert body.data.shape_keys is None and len(body.vertex_groups)>50
assert len(bpy.data.objects['RIG-barbarian-archer'].data.bones)==53
for o in bpy.context.scene.objects:
    if o.type=='MESH' and o.data.uv_layers.get('PaintingUV'):
        # MPFB's helper mask only removes internal construction faces; it does
        # not displace the calibrated surface like bevel/subdivision/solidify.
        assert all(m.type=='ARMATURE' or (m.type=='MASK' and m.name=='Hide helpers')
                   for m in o.modifiers), (o.name,'unfinished projection surface')
errors = []
for name,(count,_,_) in CLIPS.items():
    bpy.ops.wm.open_mainfile(filepath=str(MASTER/(name+'.blend')))
    sc=bpy.context.scene
    assert sc['source_master_sha256']==digest
    rig=bpy.data.objects['RIG-barbarian-archer']
    if name!='attack':
        motion=json.loads((MASTER/(name+'-motion.json')).read_text())
        assert motion['source_master_sha256']==digest
        assert motion['license']=='CC0-1.0'
    bow=bpy.data.objects['GEO-Bow stave'];string=bpy.data.objects['GEO-Bowstring']
    base=bpy.data.objects['GEO-Stationary cream base'];origin=base.matrix_world.copy()
    for frame in range(1,count+1):
        sc.frame_set(frame);bpy.context.view_layer.update()
        ends=[bow.matrix_world@Vector(bow.data.splines[0].points[i].co[:3]) for i in (0,-1)]
        actual=[string.matrix_world@Vector(string.data.splines[0].points[i].co[:3]) for i in (0,-1)]
        error=max((a-b).length for a,b in zip(ends,actual))
        assert error<1e-5,(name,frame,'string/stave detached',error)
        nock=rig.matrix_world@rig.pose.bones['hand_r'].tail+Vector((.02,-.015,.012))
        assert (Vector(string.data.splines[0].points[1].co[:3])-nock).length<1e-5
        assert all(abs(base.matrix_world[r][c]-origin[r][c])<1e-7 for r in range(4) for c in range(4))
        assert all(min(abs(v) for v in o.scale)>.001 for o in sc.objects)
        errors.append(error)
    if name=='death':
        def geometry(frame):
            sc.frame_set(frame);bpy.context.view_layer.update()
            deps=bpy.context.evaluated_depsgraph_get();points=[]
            for o in sc.objects:
                if o.type=='MESH' and not o.hide_render:
                    ev=o.evaluated_get(deps);me=ev.to_mesh()
                    points.extend(ev.matrix_world@v.co for v in me.vertices)
                    ev.to_mesh_clear()
            return points
        before,after=geometry(9),geometry(10)
        assert len(before)==len(after)
        assert max((a-b).length for a,b in zip(before,after))<1e-5,'Death geometry is not held'
(MASTER/'scene-audit.json').write_text(json.dumps({'source_master_sha256':digest,'frames':40,
    'max_string_endpoint_error_m':max(errors),'stationary_base':True,'safe_scales':True,
    'scope':'Saved rig, projection surface and weapon attachments; not a full collision solver'},indent=2))
print('PASS: saved rig, finished projection surfaces, all 40 string/nock/base samples and safe scales')
