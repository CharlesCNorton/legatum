#!/usr/bin/env bash
# Lead/driver entry point. Only serialized host GPU renders, no hidden CPU fallback.
set -euo pipefail
cd "$(dirname "$0")/../../../../.."
source tools/art/anim3d/env.sh
export RENDER_ENGINE="${RENDER_ENGINE:-CYCLES}"
export CYCLES_DEVICE=GPU
export RESOLUTION=512
export SAMPLES="${SAMPLES:-32}"
unit=tools/art/anim3d/units/war-elephant
for stage in c d e-idle e-move e-attack e-hit e-death; do "$unit/run.sh" "$stage"; done
"$ANIM_ROOT/venv/bin/python" "$unit/deliver.py" pack
"$ANIM_ROOT/venv/bin/python" "$unit/deliver.py" validate
"$ANIM_ROOT/venv/bin/python" "$unit/deliver.py" video
