"""Audit geometry, articulated movement, bakes and planted terminal wreck."""
import bpy,os,json,math,sys
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
sys.path.insert(0,str(Path(__file__).resolve().parent))
from runninggear import route
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/tank';results={}
for clip,count in [('idle',8),('move',8),('attack',10),('hit',4),('death',10)]:
    bpy.ops.wm.open_mainfile(filepath=str(M/'clips'/f'{clip}.blend'));sc=bpy.context.scene
    samples=json.loads(sc['sample_frames']);assert len(samples)==count
    routes={int(side):route(circles) for side,circles in json.loads(sc['track_circles']).items()}
    assert sc.view_settings.view_transform=='Standard'
    for material in bpy.data.materials:
        if 'painted projection' in material.name:
            assert any(n.type=='LIGHT_PATH' for n in material.node_tree.nodes), 'Missing camera-only pigment'
    base=bpy.data.objects['Stationary cream stone base'];base_initial=base.matrix_world.copy()
    links=[o for o in bpy.data.objects if 'track_phase' in o];wheels=[o for o in bpy.data.objects if 'wheel' in o]
    assert len(links)==124 and len(wheels)==16
    assert all(o.type=='MESH' for o in [bpy.data.objects['Sloped upper hull'],bpy.data.objects['Rounded cast turret']])
    root=bpy.data.objects['Vehicle suspension root'];turret=bpy.data.objects['Turret traverse'];gun=bpy.data.objects['Gun recoil']
    assert turret.parent==root and gun.parent==turret
    light_frame=bpy.data.objects['Wheel illumination frame']
    assert light_frame.parent==root and not light_frame.animation_data
    light_local=light_frame.matrix_local.copy()
    separated=[o for o in bpy.data.objects if o.type=='MESH' and o.parent in wheels
               and not o.name.startswith('Sprocket tooth')]
    assert separated and all(o.data.materials[0].get('wheel_light_separated') for o in separated)
    # At the authored rest transform the fixed field must match frozen UVs.
    # A wrong parent inverse otherwise changes every wheel's rest-pose colour.
    sc.frame_set(1);bpy.context.view_layer.update()
    if clip!='move':
        for obj in separated:
            world=obj.matrix_world@obj.data.vertices[0].co
            uv=world_to_camera_view(sc,sc.camera,world)
            fixed=light_frame.matrix_world.inverted()@world
            assert abs(fixed.x/sc.camera.data.ortho_scale+.5-uv.x)<1e-5
            assert abs(fixed.y/sc.camera.data.ortho_scale+.5-uv.y)<1e-5
    positions=[];wheel_angles=[];gun_positions=[];ground=[]
    for f in samples:
        sc.frame_set(f);bpy.context.view_layer.update();assert base.matrix_world==base_initial
        error=max(abs(light_frame.matrix_local[r][c]-light_local[r][c])
                  for r in range(4) for c in range(4))
        assert error<1e-5,('Broad wheel lighting must not spin',error)
        positions.append(tuple(links[0].location));wheel_angles.append(wheels[0].rotation_euler.y);gun_positions.append(gun.location.x)
        # Track link centre minus its shoe half-thickness at the lowest contact.
        ground.append(min((o.matrix_world.translation.z-.028) for o in links))
        assert all(o.hide_render or min(o.scale)>0.005 for o in bpy.data.objects if 'effect' in o), 'Visible effect has degenerate scale'
    assert min(ground)>.17 and max(ground)<.30,(clip,ground)
    if clip=='move':
        assert len(set(positions))==8 and len(set(wheel_angles))==8
        for i,f in enumerate(samples):
            sc.frame_set(f)
            for wheel in wheels:
                length=routes[wheel['track_side']][0]
                expected=-i*3/8*length/62/wheel['rolling_radius']
                assert abs(wheel.rotation_euler.y-expected)<1e-5, 'Wheel/track speed mismatch'
    if clip=='attack':assert max(gun_positions)-min(gun_positions)>.16
    if clip=='death':assert samples[-1]==samples[-2] and ground[-1]<.26
    results[clip]={'samples':samples,'track_contact_z':ground,'stationary_base':True,'links':len(links),'wheel_pivots':len(wheels)}
manifest=json.loads((M/'textures/baked/manifest.json').read_text());assert len(manifest)==3
for entry in manifest:
    for mode in ['AO','curvature']:assert Path(entry[mode]).exists()
(R/'review/3d-v2/tank-audit.json').write_text(json.dumps(results,indent=2));print('PASS: true geometry, 124 track links, 16 wheel pivots, recoil, six bakes, planted samples and stationary base')
