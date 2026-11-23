#!/usr/bin/env bash
# Complete lead-side pass; no arguments, run from repository root.
set -euo pipefail
source tools/art/anim3d/env.sh
export CYCLES_DEVICE=GPU RESOLUTION=512 SAMPLES=64
unit=tools/art/anim3d/units/barbarian-archer
for stage in b c d e-idle e-move e-attack e-hit e-death; do
  "$unit/run.sh" "$stage"
done
"$ANIM_ROOT/venv/bin/python" "$unit/deliver.py" pack
"$ANIM_ROOT/venv/bin/python" "$unit/deliver.py" validate
"$ANIM_ROOT/venv/bin/python" "$unit/check.py"
