"""Saved-scene checks for rigid geometry, stationary ground, controls and provenance."""
import bpy,sys,json,hashlib,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import MASTER, REVIEW, SLUG, CLIPS, log
masterhash=hashlib.sha256((MASTER/'finished.blend').read_bytes()).hexdigest();reports={}
for name,(count,fps,loop) in CLIPS.items():
    bpy.ops.wm.open_mainfile(filepath=str(MASTER/'clips'/f'{name}.blend'));sc=bpy.context.scene
    assert sc['asset']==SLUG and sc['source_sha256']==masterhash
    frames=json.loads(sc['sample_frames']);assert len(frames)==count
    base=bpy.data.objects['BASE-stationary cream stone'];assert base.parent is None
    assert not base.animation_data,'Base must not animate'
    meshes=[o for o in bpy.data.objects if o.type=='MESH'];tracks=[o for o in bpy.data.objects if 'phase' in o]
    assert len(tracks)==128 and len([o for o in bpy.data.objects if 'wheel' in o])==18
    assert len(meshes)>300 and 'GEO-open muzzle brake' in bpy.data.objects
    poses=[]
    for f in frames:
        sc.frame_set(f);bpy.context.view_layer.update()
        for o in meshes:
            assert min(abs(v) for v in o.scale)>.001,f'Unsafe tiny mesh scale: {o.name}'
        for o in tracks:
            assert .28<=o.location.z<=1.16,'Track escaped capsule'
        root=bpy.data.objects['RIG-chassis'];assert tuple(root.location)==(0,0,0)
        poses.append({'frame':f,'turret':list(bpy.data.objects['RIG-turret'].rotation_euler),'gun':list(bpy.data.objects['RIG-gun'].location)})
    if loop:
        # Authored closure key for the cyclic body/sensor motions; track travel is periodic by shoe pitch.
        sc.frame_set(1);a=bpy.data.objects['RIG-turret'].matrix_world.copy()
        sc.frame_set(count+1);b=bpy.data.objects['RIG-turret'].matrix_world
        assert max(abs(a[i][j]-b[i][j]) for i in range(4) for j in range(4))<1e-5
    if name=='death':assert frames[-1]==frames[-2]
    reports[name]={'meshes':len(meshes),'track_links':len(tracks),'frames':count,'poses':poses,'stationary_base':True,'safe_scales':True}
for i in range(3):
    for mode in ['AO','curvature']:assert (MASTER/'textures/baked'/f'{i}-{mode}.png').exists()
assert len(json.loads((MASTER/'projection.json').read_text())['meshes'])>300
report={'contract':'PASS','master_sha256':masterhash,'clips':reports,'limits':'Geometry/keys audit, not a complete collision solver or visual art approval.'}
(REVIEW/f'{SLUG}-audit.json').write_text(json.dumps(report,indent=2));log('Saved-scene audit PASS: current source hashes, 128 track links, 18 wheels, stationary base, nonzero scales, loop closure keys and held death.')
print('AUDIT PASS')
