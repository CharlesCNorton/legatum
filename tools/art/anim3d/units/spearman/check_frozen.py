"""Check the rebuilt idle/attack actions against the reviewed CPU merge.

A form/guard change rebases the old performance. Record that explicitly in the
round note; never claim the old .blend/action hashes survived such a rebuild.
This receipt ensures the host repeats the exact locally checked choreography.
"""
import json
import os
from pathlib import Path
import sys
import bpy
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from kit.ab import invariant
master = Path(os.environ['ANIM_ROOT'])/'masters/spearman-3d-v2'
expected = json.loads(Path(__file__).with_name('frozen-actions.json').read_text())
report = {}
for clip, digest in expected['actions'].items():
    bpy.ops.wm.open_mainfile(filepath=str(master/'clips'/clip/(clip+'.blend')))
    actual = invariant(bpy.context.scene)['actions']
    report[clip] = {'expected': digest, 'actual': actual, 'identical': digest == actual}
    assert digest == actual, (clip, 'CPU-reviewed performance changed', actual)
(master/'frozen-actions.json').write_text(json.dumps(report, indent=2)+'\n')
print('FROZEN_ACTIONS_OK', json.dumps(report), flush=True)
