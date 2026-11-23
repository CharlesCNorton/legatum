#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../../../.."
source tools/art/anim3d/env.sh
export UNIT=settler
export RENDER_ENGINE="${RENDER_ENGINE:-CYCLES}"
export CYCLES_DEVICE="${CYCLES_DEVICE:-CPU}"
export SAMPLES="${SAMPLES:-8}"
stage="${1:-c}"
if [[ "$stage" == pack || "$stage" == validate ]]; then
  exec "$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/settler/deliver.py "$stage"
fi
args=(-b --disable-autoexec --factory-startup --python-exit-code 1)
if [[ "$RENDER_ENGINE" == BLENDER_EEVEE || "$CYCLES_DEVICE" == GPU ]]; then args+=(--gpu-backend metal); fi
exec blender "${args[@]}" --python tools/art/anim3d/units/settler/run.py -- "$stage"
