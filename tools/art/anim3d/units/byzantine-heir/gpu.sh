#!/usr/bin/env bash
set -euo pipefail
source tools/art/anim3d/env.sh
UNIT=tools/art/anim3d/units/byzantine-heir
export CYCLES_DEVICE=GPU RESOLUTION=512 SAMPLES=48
: "${ROUND:=1}"
export ROUND
blender -b --disable-autoexec --python-exit-code 1 --gpu-backend metal --python "$UNIT/render.py" -- animate
for stage in b c e-idle e-move e-attack e-hit e-death; do
  blender -b --disable-autoexec --python-exit-code 1 --gpu-backend metal --python "$UNIT/render.py" -- "$stage"
  "$ANIM_ROOT/venv/bin/python" "$UNIT/deliver.py" review "$stage"
done
blender -b --disable-autoexec --python-exit-code 1 --python "$UNIT/audit.py"
"$ANIM_ROOT/venv/bin/python" "$UNIT/deliver.py" pack
"$ANIM_ROOT/venv/bin/python" "$UNIT/deliver.py" validate
"$ANIM_ROOT/venv/bin/python" "$UNIT/deliver.py" video
