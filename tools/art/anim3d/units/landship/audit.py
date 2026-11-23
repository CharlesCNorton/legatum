"""Audit the saved geometry and rig; art parity remains a visual decision."""
import bpy,bmesh,os,json,hashlib,math
from pathlib import Path
from mathutils import Vector
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/landship';REV=R/'review/3d-v2';unit=Path('tools/art/anim3d/units/landship')
for entry in json.loads((unit/'assets.lock.json').read_text())['files']:
    assert hashlib.sha256((R/entry['path']).read_bytes()).hexdigest()==entry['sha256']
bpy.ops.wm.open_mainfile(filepath=str(M/'landship.blend'));sc=bpy.context.scene
assert sum('track_distance' in o for o in sc.objects)==128
assert all(min(abs(v) for v in o.scale)>.01 for o in sc.objects if o.type=='MESH')
assert len([p for p in (M/'textures/baked').glob('*.png')])==6
# Closed hull volume, so projection cannot substitute a cutout/card.
for name in ('GEO-near_rhomboid_armour','GEO-central_armoured_hull','GEO-sponson'):
    o=bpy.data.objects[name];assert min(o.dimensions)>.15;assert len(o.data.polygons)>6
    bm=bmesh.new();bm.from_mesh(o.data)
    assert all(e.is_manifold for e in bm.edges),name+' is not a closed solid'
    bm.free()
checks={};source=hashlib.sha256((M/'landship.blend').read_bytes()).hexdigest()
for clip,n in [('idle',8),('move',8),('attack',10),('hit',4),('death',10)]:
    bpy.ops.wm.open_mainfile(filepath=str(M/'clips'/f'{clip}.blend'));sc=bpy.context.scene;assert sc['source_sha256']==source
    base=bpy.data.objects['GEO-cream_stone_base'];before=base.matrix_world.copy();minz=[]
    for frame in range(1,n+1):
        sc.frame_set(frame);bpy.context.view_layer.update();assert base.matrix_world==before
        shoes=[o for o in sc.objects if 'track_distance' in o];z=min((o.matrix_world@Vector(v)).z for o in shoes for v in o.bound_box);minz.append(z)
        assert z>=.198,('track below stone',clip,frame,z)
        assert all(min(abs(v) for v in o.scale)>.01 for o in sc.objects if o.type=='MESH')
    checks[clip]={'stationary_base':True,'minimum_track_z':min(minz)}
    if clip=='move':
        shoe=bpy.data.objects['GEO-track_near_00'];sc.frame_set(1);first=shoe.location.copy();sc.frame_set(2);assert (shoe.location-first).length>.02
        sc.frame_set(1)
        # Both closed circuits must return to the same *set* of occupied shoe poses.
        first=sorted(tuple(round(v,4) for v in o.location) for o in shoes)
        sc.frame_set(9)
        last=sorted(tuple(round(v,4) for v in o.location) for o in shoes)
        assert first==last,'track cycle geometry does not close'
    if clip=='death':
        sc.frame_set(9);end={o.name:o.matrix_world.copy() for o in sc.objects if o.type=='MESH'}
        sc.frame_set(10)
        assert all(o.matrix_world==end[o.name] for o in sc.objects if o.type=='MESH'),'unsettled death master'
result={'geometry':'PASS','closed_3d_hull':True,'track_shoes':128,'baked_maps':6,'clips':checks,'art_approval':False};(REV/'landship-audit.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
