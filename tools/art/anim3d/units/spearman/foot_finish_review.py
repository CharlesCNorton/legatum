"""Matched R14/R15b evidence through the production look render functions.

Blender: -- proxy|beauty [rest,move,death] (default rest,move).
Host beauty is Eevee/Metal, never substituted with CPU. Outputs stay in a lane
folder; this does not overwrite masters or ship an atlas. Run the companion
foot_finish_report.py with the same mode to assemble the review and metrics.
"""
import hashlib
import json
import os
from pathlib import Path
import sys
import bpy
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import look
import foot_finish
from kit.ab import digest, invariant

R14 = dict(base_cast=.16, base_contact=.40, contact_reach=.07,
           ground_shadow=1., ground_back=.24, ground_in=.10,
           ground_depth=.18, ground_width=.26, ground_follow=0, foot_roll=0)


def geometry(scene):
    return digest({o.name: {'matrix': [list(r) for r in o.matrix_world],
        'vertices': [[list(v.co), [(g.group, g.weight) for g in v.groups]] for v in o.data.vertices],
        'uvs': {uv.name: [list(v.uv) for v in uv.data] for uv in o.data.uv_layers}}
        for o in scene.objects if o.type == 'MESH'})


def main():
    args = sys.argv[sys.argv.index('--')+1:]
    mode = args[0]
    assert mode in ('proxy', 'beauty')
    root = Path(os.environ['ANIM_ROOT'])
    master = root/'masters/spearman-3d-v2'
    out = Path(os.environ.get('FOOT_FINISH_OUTPUT', root/'lanes/spearman-r15b'))/mode
    out.mkdir(parents=True, exist_ok=True)
    clips = args[1].split(',') if len(args)>1 else ['rest', 'move']
    receipt = {'mode': mode, 'engine': 'Cycles CPU analytic proxy (no cast shadows)' if mode=='proxy' else 'Eevee Metal',
               'resolution': 256, 'samples': 8 if mode=='proxy' else 64, 'seed': 17,
               'before_overrides': R14, 'after_settings': look.LOOK,
               'code_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in
                              [Path(look.__file__), Path(foot_finish.__file__)]}, 'clips': {}}
    for clip in clips:
        path = master/'spearman.blend' if clip=='rest' else master/'clips'/clip/(clip+'.blend')
        item = {'source_sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'variants': {}}
        for variant in (('before', 'after', 'pools') if clip == 'rest' else ('before', 'after')):
            bpy.ops.wm.open_mainfile(filepath=str(path))
            sc = bpy.context.scene
            look.configure_render(sc, mode, 256, receipt['samples'])
            # Eevee and Cycles settings are identical within each A/B pair.
            sc.cycles.seed = 17
            cfg = dict(look.LOOK)
            if variant == 'before': cfg.update(R14)
            if variant == 'pools': cfg['ground_pools'] = 1
            original_geometry = geometry(sc)
            original_actions = invariant(sc)['actions']
            look.apply_materials(sc, 'beauty', master/'look', cfg)
            assert geometry(sc) == original_geometry
            assert invariant(sc)['actions'] == original_actions
            samples = [sc.frame_current] if clip=='rest' else json.loads(sc['sample_frames'])
            frames = []
            for i, frame in enumerate(samples):
                sc.frame_set(frame)
                rig = bpy.data.objects['Spearman • MPFB game_engine']
                expected = digest([[list(row) for row in b.matrix] for b in rig.pose.bones])
                report = foot_finish.update(sc)
                assert digest([[list(row) for row in b.matrix] for b in rig.pose.bones]) == expected, 'Foot finish changed pose'
                target = out/variant/clip/f'{i:02}.png'
                target.parent.mkdir(parents=True, exist_ok=True)
                look.render_frame(sc, target)
                dg = bpy.context.evaluated_depsgraph_get()
                markers = {s: list(bpy.data.objects['LOOK ankle '+s].evaluated_get(dg).matrix_world.translation) for s in 'lr'}
                if variant != 'before':
                    for side in 'lr':
                        assert max(abs(a-b) for a,b in zip(markers[side], report[side]['anchor'])) < 1e-6
                    if clip == 'rest': assert max(r['roll'] for r in report.values()) == 0, report
                frames.append({'sample': i, 'frame': frame, 'markers': markers, 'feet': report})
            item['variants'][variant] = {'effective_settings': {k:v for k,v in cfg.items() if not k.startswith('_')}, 'frames': frames, 'geometry_weights_uvs_pose_actions_unchanged': True}
        receipt['clips'][clip] = item
        (out/'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print('FOOT_FINISH_AB_READY', out)

if __name__ == '__main__': main()
