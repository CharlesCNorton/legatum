"""Saved-scene checks, separate from the manual painting-parity verdict."""
import bpy,os,json,hashlib,sys,math
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
sys.path.insert(0,str(Path(__file__).resolve().parent))
from runninggear import route
r=Path(os.environ['ANIM_ROOT']);m=r/'masters/panzer';records={}
for clip,count in [('idle',8),('move',8),('attack',10),('hit',4),('death',10)]:
    bpy.ops.wm.open_mainfile(filepath=str(m/'clips'/f'{clip}.blend'));sc=bpy.context.scene
    assert sc['source_sha256']==hashlib.sha256((m/'panzer.blend').read_bytes()).hexdigest(),'Stale animated master'
    frames=json.loads(sc['sample_frames']);assert len(frames)==count
    assert len([o for o in bpy.data.objects if o.name.startswith('Road wheel pivot')])==16
    assert len([o for o in bpy.data.objects if 'track_phase' in o])==144
    assert len([o for o in bpy.data.objects if o.name.startswith('Hull skirt plate')])==10
    base=bpy.data.objects['Stationary cream stone base'];baseline=None;bounds=[]
    for f in frames:
        sc.frame_set(f);bpy.context.view_layer.update()
        mat=tuple(v for row in base.matrix_world for v in row)
        if baseline is None:baseline=mat
        assert mat==baseline,'Base moved'
        for o in bpy.data.objects:
            if o.type!='MESH':continue
            assert min(abs(v) for v in o.scale)>.01,(o.name,'near-zero scale')
            if o.hide_render:continue
            assert len(o.data.vertices)>=8,(o.name,'flat geometry')
            for vertex in o.data.vertices:
                q=world_to_camera_view(sc,sc.camera,o.matrix_world@vertex.co);bounds.append((q.x,q.y))
    lo=[min(v[i] for v in bounds) for i in (0,1)];hi=[max(v[i] for v in bounds) for i in (0,1)]
    assert min(lo)>0 and max(hi)<1,(clip,'clips field',lo,hi)
    records[clip]={'frames':count,'stationary_base':True,'bounds':[lo,hi]}
# Physical route closure and contact velocity; rendered top/front sheets remain mandatory.
root=bpy.data.objects['Vehicle suspension root'];length,point=route(json.loads(root['route_circles']))
assert point(0)==point(1)
points=[point(i/10000) for i in range(10000)];bottom=min(p[1] for p in points)
assert abs(bottom-.27)<1e-5
contacts=[(i,p) for i,p in enumerate(points) if p[1]<bottom+1e-6]
assert all(point((i+1)/10000)[0]<p[0] for i,p in contacts[:-1])
records['mechanics']={'belt_length':length,'contact_route_z':bottom,'base_top':.23,'shoe_half_thickness':.0225,'travel_axis':'+X','contact_velocity':'-v, matching token travel +v; anchored preview uses treadmill convention','wheel_speed':'v/r','human_or_animal_motion':'not applicable'}
(r/'review/3d-v2/panzer-audit.json').write_text(json.dumps(records,indent=2));print('AUDIT PASS',records)
