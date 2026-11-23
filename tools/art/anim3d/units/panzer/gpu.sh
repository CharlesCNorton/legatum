#!/usr/bin/env bash
# No arguments: complete serial host pass from repo root; never writes PASS.
set -euo pipefail
source tools/art/anim3d/env.sh
export CYCLES_DEVICE=GPU RENDER_ENGINE=CYCLES RESOLUTION=512
export SAMPLES="${SAMPLES:-128}" ROUND="${ROUND:-1}"
U=tools/art/anim3d/units/panzer
for stage in b c details d e-idle e-move e-attack e-hit e-death g; do
  "$U/run.sh" "$stage"
done
"$ANIM_ROOT/venv/bin/python" "$U/masters.py"
"$U/run.sh" audit
"$U/run.sh" pack
"$ANIM_ROOT/venv/bin/python" "$U/video.py"
