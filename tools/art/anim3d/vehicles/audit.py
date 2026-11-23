"""Audit geometry, articulated movement, bakes and planted terminal wreck."""
import bpy,os,json,math
from pathlib import Path
from mathutils import Vector
R=Path(os.environ['ANIM_ROOT']);M=R/'masters/tank';results={}
for clip,count in [('idle',8),('move',8),('attack',10),('hit',4),('death',10)]:
    bpy.ops.wm.open_mainfile(filepath=str(M/'clips'/f'{clip}.blend'));sc=bpy.context.scene
    samples=json.loads(sc['sample_frames']);assert len(samples)==count
    base=bpy.data.objects['Stationary cream stone base'];base_initial=base.matrix_world.copy()
    links=[o for o in bpy.data.objects if 'track_phase' in o];wheels=[o for o in bpy.data.objects if 'wheel' in o]
    assert len(links)==124 and len(wheels)==16
    assert all(o.type=='MESH' for o in [bpy.data.objects['Sloped upper hull'],bpy.data.objects['Rounded cast turret']])
    root=bpy.data.objects['Vehicle suspension root'];turret=bpy.data.objects['Turret traverse'];gun=bpy.data.objects['Gun recoil']
    assert turret.parent==root and gun.parent==turret
    positions=[];wheel_angles=[];gun_positions=[];ground=[]
    for f in samples:
        sc.frame_set(f);bpy.context.view_layer.update();assert base.matrix_world==base_initial
        positions.append(tuple(links[0].location));wheel_angles.append(wheels[0].rotation_euler.y);gun_positions.append(gun.location.x)
        # Track link centre minus its shoe half-thickness at the lowest contact.
        ground.append(min((o.matrix_world.translation.z-.028) for o in links))
        assert all(o.hide_render or min(o.scale)>0.005 for o in bpy.data.objects if 'effect' in o), 'Visible effect has degenerate scale'
    assert min(ground)>.17 and max(ground)<.30,(clip,ground)
    if clip=='move':assert len(set(positions))==8 and len(set(wheel_angles))==8
    if clip=='attack':assert max(gun_positions)-min(gun_positions)>.16
    if clip=='death':assert samples[-1]==samples[-2] and ground[-1]<.26
    results[clip]={'samples':samples,'track_contact_z':ground,'stationary_base':True,'links':len(links),'wheel_pivots':len(wheels)}
manifest=json.loads((M/'textures/baked/manifest.json').read_text());assert len(manifest)==3
for entry in manifest:
    for mode in ['AO','curvature']:assert Path(entry[mode]).exists()
(R/'review/3d-v2/tank-audit.json').write_text(json.dumps(results,indent=2));print('PASS: true geometry, 124 track links, 16 wheel pivots, recoil, six bakes, planted samples and stationary base')
