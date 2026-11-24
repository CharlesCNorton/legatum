"""Isolated CPU A/B of the painted layer; never writes a master or final atlas.

Shader to RGB is Eevee-only. This explicitly labelled CPU proxy substitutes
an analytic sun cosine for that term (no cast shadows); Cycles still evaluates
the real AO/contact, frozen pigment and all continuity nodes. GPU acceptance
must use gpu.sh. Usage: -- LANE_DIR [rest,move,hit,death] [before,after,id] [all]
"""
import hashlib
import json
import os
import runpy
import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from kit.ab import invariant, preview_settings, render_still
from kit.look import Graph
import look


class CPUProxy(Graph):
    def lit(self, normal=None, constant_normal=None):
        if constant_normal is not None:
            return self.math('ADD', 1., 0.)
        normal = normal or self.node('ShaderNodeNewGeometry').outputs['Normal']
        direction = look.directions(bpy.context.scene)[1]
        return self.math('MAXIMUM', self.dot(normal, tuple(direction)), 0.)


def rest_contact(scene):
    """Measure the saved rest too: a passing move trace does not cover it."""
    dg = bpy.context.evaluated_depsgraph_get()

    def heights(ob):
        evaluated = ob.evaluated_get(dg)
        mesh = evaluated.to_mesh()
        values = [(evaluated.matrix_world @ v.co).z for v in mesh.vertices]
        evaluated.to_mesh_clear()
        return values

    base = next(o for o in scene.objects if o.name.startswith('Stationary cream stone'))
    top = max(heights(base))
    gaps = {side: (min(heights(scene.objects['Leather sandal sole '+side]))-top)*1000
            for side in ('l', 'r')}
    return {'stone_top_m': top, 'sole_clearance_mm': gaps,
            'within_2mm': all(abs(gap) <= 2 for gap in gaps.values())}


def main():
    args = sys.argv[sys.argv.index('--') + 1:]
    root = Path(args[0])
    clips = args[1].split(',') if len(args) > 1 else ['rest', 'move', 'hit', 'death']
    variants = args[2].split(',') if len(args) > 2 else ['before', 'after']
    out = root / 'preview'; out.mkdir(exist_ok=True)
    report = {}
    look.Graph = CPUProxy
    if clips == ['feet']:
        # Reuse the real dense contact checker, applying the same proxy after
        # it opens the clip and before it snapshots lower-leg geometry.
        @bpy.app.handlers.persistent
        def painted_feet(_):
            look.apply_scene(bpy.context.scene, 'beauty')
            look.apply_materials(bpy.context.scene, 'beauty', root/'look', dict(look.LOOK))
        bpy.app.handlers.load_post.append(painted_feet)
        os.environ['ANIM_ROOT'] = str(root)
        os.environ['CYCLES_DEVICE'] = 'CPU'
        try:
            runpy.run_path(str(Path(__file__).with_name('feet.py')), run_name='__main__')
        finally:
            bpy.app.handlers.load_post.remove(painted_feet)
        return
    for clip in clips:
        path = root/'spearman.blend' if clip == 'rest' else root/'clips'/clip/(clip+'.blend')
        bpy.ops.wm.open_mainfile(filepath=str(path))
        scene = bpy.context.scene
        contact = rest_contact(scene) if clip == 'rest' else None
        look.apply_scene(scene, 'beauty')
        receipt = preview_settings(scene)
        look.apply_materials(scene, 'beauty', root/'look', dict(look.LOOK))
        before = invariant(scene)
        samples = [scene.frame_current] if clip == 'rest' else json.loads(scene['sample_frames'])
        indices = list(range(len(samples))) if len(args) > 3 and args[3] == 'all' else {
            'rest': [0], 'idle': [0], 'attack': [4], 'move': [2, 6], 'hit': [1], 'death': [4, 7]}[clip]
        for variant in variants:
            cfg = dict(look.LOOK)
            cfg['continuity'] = 0 if variant == 'before' else 1
            if variant == 'no-contact':
                cfg['base_contact'] = cfg['base_cast'] = 0
            look.apply_materials(scene, 'id' if variant == 'id' else 'beauty', root/'look', cfg)
            assert invariant(scene) == before, 'material layer changed geometry/UVs/pose/actions/lights'
            done = {}
            for i in indices:
                target = out/f'{clip}-{i:02}-{variant}.png'
                if samples[i] in done:
                    import shutil
                    shutil.copyfile(done[samples[i]], target)
                else:
                    render_still(scene, target, samples[i])
                    done[samples[i]] = target
            scene.frame_set(samples[0] if clip != 'rest' else samples[0])
            # Restore the loaded pose for the next material-only invariant.
            before = invariant(scene)
        report[clip] = {'settings': receipt, 'source_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                        'unchanged_invariants': True, 'frames': {i: samples[i] for i in indices},
                        'proxy_limit': 'analytic sun; no cast shadow; real Cycles AO; no grade'}
        if contact is not None:
            report[clip]['rest_contact'] = contact
        (out/f'{clip}-receipt.json').write_text(json.dumps(report[clip], indent=2)+'\n')
    print('CONTINUITY_PREVIEW', json.dumps(report), flush=True)


if __name__ == '__main__':
    main()
