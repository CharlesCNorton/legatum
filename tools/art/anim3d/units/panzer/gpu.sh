#!/usr/bin/env bash
# No arguments: complete serial host pass from repo root; never writes PASS.
set -euo pipefail
[[ $# == 0 ]] || { echo 'Run from the repository root with no arguments.' >&2; exit 2; }
source tools/art/anim3d/env.sh
export CYCLES_DEVICE=GPU RENDER_ENGINE=CYCLES RESOLUTION=512
export SAMPLES="${SAMPLES:-128}" ROUND="${ROUND:-2}"
U=tools/art/anim3d/units/panzer
# Refuse stale clips before spending time on the final render pass.
"$U/run.sh" audit
"$ANIM_ROOT/venv/bin/python" -m unittest discover -s "$U" -p 'test_*.py'
for stage in b c details d e-idle e-move e-attack e-hit e-death g; do
  "$U/run.sh" "$stage"
done
"$ANIM_ROOT/venv/bin/python" "$U/masters.py"
"$U/run.sh" pack
"$ANIM_ROOT/venv/bin/python" "$U/video.py"
"$ANIM_ROOT/venv/bin/python" - <<'PY'
import json, os
from pathlib import Path
r=Path(os.environ['ANIM_ROOT']); m=r/'masters/panzer'; review=r/'review/3d-v2'
stages=['b','c','details','d','e-idle','e-move','e-attack','e-hit','e-death','g']
for stage in stages:
    manifest=json.loads((m/'renders'/stage/'render.json').read_text())
    assert manifest['device']=='GPU' and manifest['resolution']==512, (stage, manifest)
report=json.loads((review/'panzer-validation.json').read_text())
report.update(round=os.environ['ROUND'], device='GPU', resolution=512,
              stages=stages, visual_verdict='Pending inspection; no automatic PASS')
(review/f"panzer-gpu-round{os.environ['ROUND']}.json").write_text(json.dumps(report,indent=2)+'\n')
print('GPU handoff complete; painting parity and motion still require visual review.')
PY
