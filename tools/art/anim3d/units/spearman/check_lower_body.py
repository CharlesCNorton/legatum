"""Verify R10a anatomy isolation and unchanged source-space walk calibration.

The baseline is the preserved R9 CPU merge; ANIM_ROOT selects the candidate.
Optional --move compares all dense frames after a diagnostic or full move bake.
"""
import hashlib
import json
import os
import sys
from pathlib import Path

import bpy
from bpy_extras.object_utils import world_to_camera_view

ROOT = Path.home()/'LegatumRuns/anim-pilot'
BASE = ROOT/'lanes/spearman-r9-merge/masters/spearman-3d-v2'
MASTER = Path(os.environ['ANIM_ROOT'])/'masters/spearman-3d-v2'
OUT = Path(os.environ['ANIM_ROOT'])/'review/3d-v2'


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def snapshot(path):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    sc = bpy.context.scene
    rig = bpy.data.objects['Spearman • MPFB game_engine']
    body = bpy.data.objects['MPFB anatomical male • original topology']
    foot_vertices = {v.index: tuple(v.co) for v in body.data.vertices
                     if any(body.vertex_groups[g.group].name.startswith(('foot_', 'ball_'))
                            and g.weight > .001 for g in v.groups)}
    return {'bind': digest({b.name: [list(row) for row in b.matrix_local] for b in rig.data.bones}),
            'weights': digest([[(g.group, g.weight) for g in v.groups] for v in body.data.vertices]),
            'topology': digest([list(p.vertices) for p in body.data.polygons]),
            'body_vertices': len(body.data.vertices), 'bones': len(rig.data.bones),
            'human_feet': digest(foot_vertices), 'human_foot_vertices': len(foot_vertices),
            'soles': digest({s: [[tuple(v.co), [(g.group,g.weight) for g in v.groups]]
                                for v in bpy.data.objects['Leather sandal sole '+s].data.vertices] for s in ('l','r')}),
            'sole_landmarks': {s: [bpy.data.objects['Leather sandal sole '+s][n+'_vertex'] for n in ('heel','toe')] for s in ('l','r')},
            'upper_pose': digest({p.name: [list(row) for row in p.matrix_basis] for p in rig.pose.bones
                                  if not p.name.startswith(('thigh_', 'calf_', 'foot_', 'ball_'))}),
            'camera': digest([list(row) for row in sc.camera.matrix_world]+[[sc.camera.data.ortho_scale]]),
            'lights': digest({o.name: [list(o.location), o.data.energy, list(o.data.color)] for o in sc.objects if o.type=='LIGHT'})}


def walk(path):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    sc = bpy.context.scene
    assert sc['source_master_sha256'] == hashlib.sha256((path.parents[2]/'spearman.blend').read_bytes()).hexdigest(), 'Stale move master'
    rig = bpy.data.objects['Spearman • MPFB game_engine']
    result = {}
    welt_floor = []
    for frame in range(25, sc.frame_end+1):
        sc.frame_set(frame)
        result[frame] = {p.name: (p.matrix.to_quaternion().copy(), p.head.copy())
                         for p in rig.pose.bones if p.name.startswith(('foot_', 'ball_'))}
        for side in ('l', 'r'):
            ob = bpy.data.objects.get('Sandal welt '+side)
            if ob is None:
                continue
            evaluated = ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
            mesh = evaluated.to_mesh()
            welt_floor.append(min((ob.matrix_world @ v.co).z for v in mesh.vertices))
            evaluated.to_mesh_clear()
    return result, min(welt_floor) if welt_floor else None


def footprints():
    """Projected real sole bounds are diagnostics, never inputs to fitting."""
    sc = bpy.context.scene
    bounds = {}
    for side in ('l', 'r'):
        ob = bpy.data.objects['Leather sandal sole '+side]
        evaluated = ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh = evaluated.to_mesh()
        points = [world_to_camera_view(sc, sc.camera, ob.matrix_world @ v.co) for v in mesh.vertices]
        evaluated.to_mesh_clear()
        bounds[side] = {'xmin': min(p.x for p in points)*256,
                        'xmax': max(p.x for p in points)*256}
        bounds[side]['width_256px'] = bounds[side]['xmax']-bounds[side]['xmin']
    bounds['combined_width_256px'] = max(bounds[s]['xmax'] for s in ('l','r'))-min(bounds[s]['xmin'] for s in ('l','r'))
    return bounds


def main():
    before = snapshot(BASE/'spearman.blend')
    old_footprints = footprints()
    after = snapshot(MASTER/'spearman.blend')
    new_footprints = footprints()
    assert before == after, {k:(before[k],after[k]) for k in before if before[k]!=after[k]}
    assert after['body_vertices'] == 19158 and after['bones'] == 53
    sc = bpy.context.scene
    assert sc['spearman_lower_body_round'] == '10a'
    rig = bpy.data.objects['Spearman • MPFB game_engine']
    for side in ('l','r'):
        welt = bpy.data.objects['Sandal welt '+side]
        assert set(g.name for g in welt.vertex_groups)=={'foot_'+side,'ball_'+side}
        assert all(abs(sum(g.weight for g in v.groups)-1)<1e-5 for v in welt.data.vertices)
        ev=welt.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh=ev.to_mesh()
        lowest=min((welt.matrix_world @ v.co).z for v in mesh.vertices)
        ev.to_mesh_clear()
        assert lowest>.108, (side, lowest)
        assert (rig.pose.bones['calf_'+side].tail-rig.pose.bones['foot_'+side].head).length<1e-5
    report = {'invariants': after, 'stance': json.loads(sc['spearman_lower_body_receipt']),
              'sole_footprints': {'round9': old_footprints, 'round10a': new_footprints},
              'human_feet_soles_weights_bind_and_upper_body_unchanged': True,
              'welt_above_original_contact_plane': True}
    if '--move' in sys.argv:
        old, _ = walk(BASE/'clips/move/move.blend')
        path = MASTER/'clips/move/move.blend'
        if not path.exists():
            path=MASTER/'clips/move/move-diagnostic.blend'
        new, welt_floor = walk(path)
        assert old.keys()==new.keys()
        rotation = max(old[f][n][0].rotation_difference(new[f][n][0]).angle for f in old for n in old[f])
        translation = max((old[f][n][1]-new[f][n][1]).length for f in old for n in old[f])
        assert rotation < .001 and translation < 1e-5, (rotation, translation)
        assert welt_floor >= .104, ('New welt penetrates the stone', welt_floor)
        report['move'] = {'dense_frames': len(new), 'max_foot_ball_rotation_delta_radians': rotation,
                          'max_foot_ball_head_delta_m': translation,
                          'min_welt_z_m': welt_floor,
                          'source_space_foot_roll_preserved': True}
    (OUT/'spearman-r10a-geometry-checks.json').write_text(json.dumps(report, indent=2)+'\n')
    print('LOWER_BODY_CHECKS', json.dumps(report))


if __name__=='__main__':
    main()
