#!/usr/bin/env bash
# Driver entry point: no arguments, execute from repository root.
set -euo pipefail
source tools/art/anim3d/env.sh
unit=tools/art/anim3d/units/landship
export CYCLES_DEVICE=GPU RESOLUTION=512 SAMPLES="${SAMPLES:-64}" ROUND="${ROUND:-2}"
"$ANIM_ROOT/venv/bin/python" "$unit/preflight.py" check
blender -b --disable-autoexec --python-exit-code 1 --python "$unit/audit.py"
for stage in b c d e-idle e-move e-attack e-hit e-death g; do
  "$unit/render.sh" "$stage"
done
"$ANIM_ROOT/venv/bin/python" "$unit/deliver.py" pack
"$ANIM_ROOT/venv/bin/python" "$unit/deliver.py" video
blender -b --disable-autoexec --python-exit-code 1 --python "$unit/audit.py"
"$ANIM_ROOT/venv/bin/python" "$unit/preflight.py" check
"$ANIM_ROOT/venv/bin/python" "$unit/deliver.py" gpu-check
