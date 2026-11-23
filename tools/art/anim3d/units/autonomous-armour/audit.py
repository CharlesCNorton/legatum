"""Saved-scene checks for rigid geometry, stationary ground, controls and provenance."""
import bpy,sys,json,hashlib,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import MASTER, REVIEW, SLUG, CLIPS, log, TRACK_R, MOVE_TRAVEL, ROAD_RADIUS
from bpy_extras.object_utils import world_to_camera_view
assert not (MASTER/'build-pending').exists(),'Interrupted rebuild; finish all clips before delivery'
masterhash=hashlib.sha256((MASTER/'finished.blend').read_bytes()).hexdigest();reports={}
for name,(count,fps,loop) in CLIPS.items():
    bpy.ops.wm.open_mainfile(filepath=str(MASTER/'clips'/f'{name}.blend'));sc=bpy.context.scene
    assert sc['asset']==SLUG and sc['source_sha256']==masterhash
    frames=json.loads(sc['sample_frames']);assert len(frames)==count
    base=bpy.data.objects['BASE-stationary cream stone'];assert base.parent is None
    assert not base.animation_data,'Base must not animate'
    meshes=[o for o in bpy.data.objects if o.type=='MESH'];tracks=[o for o in bpy.data.objects if 'phase' in o]
    assert len(tracks)==128 and len([o for o in bpy.data.objects if 'wheel' in o])==16
    for side in (-1,1):
        road=sorted([o for o in bpy.data.objects if o.name.startswith(f'RIG-wheel-{side}-')],key=lambda o:o.location.x)
        assert len(road)==6
        for a,b in zip(road,road[1:]):
            assert b.location.x-a.location.x>=2*ROAD_RADIUS,'Road tyres intersect'
    assert len(meshes)>300 and 'GEO-open muzzle brake' in bpy.data.objects
    poses=[];contact=[]
    shoes=[child for track in tracks for child in track.children if child.type=='MESH']
    for f in frames:
        sc.frame_set(f);bpy.context.view_layer.update()
        for o in meshes:
            assert min(abs(v) for v in o.scale)>.001,f'Unsafe tiny mesh scale: {o.name}'
        for o in tracks:
            assert .29<=o.location.z<=1.18,'Track escaped capsule'
        lowest=min((o.matrix_world @ v.co).z for o in shoes for v in o.data.vertices)
        assert .235<=lowest<=.25,f'Track contact escaped stone top: {lowest}'
        contact.append(lowest)
        root=bpy.data.objects['RIG-chassis'];assert tuple(root.location)==(0,0,0)
        poses.append({'frame':f,'turret':list(bpy.data.objects['RIG-turret'].rotation_euler),'gun':list(bpy.data.objects['RIG-gun'].location)})
    if loop:
        # Authored closure key for the cyclic body/sensor motions; track travel is periodic by shoe pitch.
        sc.frame_set(1);a=bpy.data.objects['RIG-turret'].matrix_world.copy()
        sc.frame_set(count+1);b=bpy.data.objects['RIG-turret'].matrix_world
        assert max(abs(a[i][j]-b[i][j]) for i in range(4) for j in range(4))<1e-5
    if name=='move':
        wheels=[o for o in bpy.data.objects if 'wheel' in o]
        for frame in frames:
            sc.frame_set(frame)
            phase=(frame-1)/count
            for wheel in wheels:
                radius=TRACK_R if wheel.name.startswith('RIG-sprocket') else ROAD_RADIUS
                assert abs(wheel.rotation_euler.y*radius-phase*MOVE_TRAVEL)<1e-6,'Wheel/track travel mismatch'
        sc.frame_set(1);bpy.context.view_layer.update()
        start={o.name:o.matrix_world.copy() for o in tracks}
        sc.frame_set(count+1);bpy.context.view_layer.update()
        for o in tracks:
            side=o['side'];index=round(o['phase']*64)
            expected=start[f'RIG-track-{side}-{(index+5)%64}']
            assert max(abs(o.matrix_world[i][j]-expected[i][j]) for i in range(4) for j in range(4))<1e-5,'Track loop does not close'
    sc.frame_set(1);bpy.context.view_layer.update()
    max_uv_error=0
    for o in meshes:
        uv=o.data.uv_layers.get('PaintingProjection')
        if uv is None:continue
        assert not o.modifiers,'Projection must use finished surfaces'
        assert any(n.type=='LIGHT_PATH' for n in o.data.materials[0].node_tree.nodes),'Pigment must be camera-only'
        for index in range(0,len(o.data.loops),max(1,len(o.data.loops)//20)):
            v=o.data.vertices[o.data.loops[index].vertex_index]
            p=world_to_camera_view(sc,sc.camera,o.matrix_world @ v.co)
            error=max(abs(uv.data[index].uv.x-p.x),abs(uv.data[index].uv.y-p.y))*256
            max_uv_error=max(max_uv_error,error)
    assert max_uv_error<.02,f'Frozen paint drifted {max_uv_error} pixels'
    if name=='death':assert frames[-1]==frames[-2]
    reports[name]={'meshes':len(meshes),'track_links':len(tracks),'frames':count,'poses':poses,'stationary_base':True,'safe_scales':True,'rest_uv_error_px':max_uv_error,'track_contact_z':contact}
for i in range(3):
    for mode in ['AO','curvature']:assert (MASTER/'textures/baked'/f'{i}-{mode}.png').exists()
assert len(json.loads((MASTER/'projection.json').read_text())['meshes'])>300
report={'contract':'PASS','master_sha256':masterhash,'clips':reports,'limits':'Geometry/keys audit, not a complete collision solver or visual art approval.'}
(REVIEW/f'{SLUG}-audit.json').write_text(json.dumps(report,indent=2));log('Saved-scene audit PASS: current source hashes, 128 track links, 16 wheels, stationary base, nonzero scales, loop closure keys and held death.')
print('AUDIT PASS')
