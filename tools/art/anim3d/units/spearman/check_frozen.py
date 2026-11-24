"""Refuse drift in the approved idle/attack actions after any host rebuild."""
import json
import os
from pathlib import Path
import sys
import bpy
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from kit.ab import invariant

EXPECTED = {
    'idle': '057f5cef51f6b2199b5834af980f67b1920b0e954f12b50f63d875298dcda227',
    'attack': '667d83498c04185fb13b1142c58274ef864aec7ae5222f07f73360d9d5168a6e',
}
master = Path(os.environ['ANIM_ROOT'])/'masters/spearman-3d-v2'
report = {}
for clip, expected in EXPECTED.items():
    bpy.ops.wm.open_mainfile(filepath=str(master/'clips'/clip/(clip+'.blend')))
    actual = invariant(bpy.context.scene)['actions']
    report[clip] = {'expected':expected, 'actual':actual, 'identical':actual == expected}
    assert actual == expected, (clip, 'approved performance changed', actual)
(master/'frozen-actions.json').write_text(json.dumps(report,indent=2)+'\n')
print('FROZEN_ACTIONS_OK', json.dumps(report), flush=True)
