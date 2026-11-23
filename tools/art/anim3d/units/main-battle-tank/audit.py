"""Geometry/motion checks; numerical evidence does not imply painting parity."""
import bpy,os,json,hashlib,math,sys
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from runninggear import route
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/main-battle-tank';records={}
source=hashlib.sha256((M/'main-battle-tank.blend').read_bytes()).hexdigest()
for clip,count in [('idle',8),('move',8),('attack',10),('hit',4),('death',10)]:
    bpy.ops.wm.open_mainfile(filepath=str(M/'clips'/f'{clip}.blend'));sc=bpy.context.scene
    assert sc['source_sha256']==source,'Stale clip source'
    samples=json.loads(sc['sample_frames']);assert len(samples)==count
    base=bpy.data.objects['Stationary cream stone base'];base_matrix=base.matrix_world.copy()
    gear=bpy.data.objects['Running gear root'];gear_matrix=gear.matrix_world.copy()
    links=[o for o in bpy.data.objects if 'track_phase' in o];wheels=[o for o in bpy.data.objects if 'wheel' in o]
    assert len(links)==124 and len(wheels)==16
    assert len([o for o in bpy.data.objects if o.type=='MESH'])>400
    routes={int(k):route(v) for k,v in json.loads(sc['track_circles']).items()}
    observed=[]
    for i,frame in enumerate(samples):
        sc.frame_set(frame);bpy.context.view_layer.update()
        assert base.matrix_world==base_matrix,'Base moves'
        assert gear.matrix_world==gear_matrix,'Running gear moves with sprung armour'
        for o in bpy.data.objects:
            if o.type=='MESH':
                assert min(abs(v) for v in o.scale)>.001,(o.name,'unsafe scale')
                assert all(math.isfinite(v) for row in o.matrix_world for v in row)
        if clip=='move':
            for o in links:
                x,z,angle=routes[o['track_side']][1](o['track_phase']+i*3/8/62)
                assert abs(o.location.x-x)<1e-5 and abs(o.location.z-z)<1e-5
            for wheel in wheels:
                expected=-i*3/8*routes[wheel['track_side']][0]/62/wheel['rolling_radius']
                assert abs(wheel.rotation_euler.y-expected)<1e-4,'Wheel/track speed mismatch'
        observed.append(tuple(bpy.data.objects['Gun recoil'].location))
    if clip=='attack':assert max(v[0] for v in observed)-min(v[0] for v in observed)>.1
    if clip=='death':assert samples[-1]==samples[-2]
    records[clip]={'samples':count,'stationary_base':True,'safe_scales':True,'links':len(links),'wheels':len(wheels),'source_sha256':source}
for i in range(3):
    for kind in ['AO','curvature']:assert (M/'textures/baked'/f'{i}-{kind}.png').stat().st_size>100
# Actual geometric grounding distances, reported separately from visual acceptance.
bpy.ops.wm.open_mainfile(filepath=str(M/'clips/move.blend'));sc=bpy.context.scene;sc.frame_set(1);bpy.context.view_layer.update()
base=bpy.data.objects['Stationary cream stone base'];normal=base.matrix_world.to_3x3()@base.data.polygons[max(range(len(base.data.polygons)),key=lambda i:base.data.polygons[i].normal.z)].normal
# The fitted mesh's dominant upper face carries the disc plane.
faces=[p for p in base.data.polygons if p.normal.z>.9];face=max(faces,key=lambda p:p.area)
normal=(base.matrix_world.to_3x3().inverted().transposed()@face.normal).normalized();plane=base.matrix_world@face.center
contacts=[]
for o in bpy.data.objects:
    if o.type=='MESH' and o.name.startswith('Forged track shoe'):
        points=[o.matrix_world@v.co for v in o.data.vertices]
        contacts.append(min((p-plane).dot(normal) for p in points))
assert abs(min(contacts))<.02, 'Track contact exceeds tolerance'
report={'technical_checks':'PASS','clips':records,'six_actual_bakes':True,'lowest_track_distance_to_base_plane':min(contacts),'note':'Grounding distance and contact sheets require visual review. No automatic art PASS.'}
(R/'review/3d-v2/main-battle-tank-audit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
