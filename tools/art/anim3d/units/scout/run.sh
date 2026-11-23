#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../../../.."
source tools/art/anim3d/env.sh
stage="${1:-round}"
if [[ "$stage" == prepare || "$stage" == pack || "$stage" == validate ]]; then
  exec "$ANIM_ROOT/venv/bin/python" "tools/art/anim3d/units/scout/$stage.py"
fi
export RENDER_ENGINE="${RENDER_ENGINE:-CYCLES}"
export CYCLES_DEVICE="${CYCLES_DEVICE:-CPU}"
args=(-b --disable-autoexec --factory-startup --python-exit-code 1)
if [[ "$RENDER_ENGINE" == BLENDER_EEVEE ]]; then args+=(--gpu-backend metal); fi
exec blender "${args[@]}" --python tools/art/anim3d/units/scout/pipeline.py -- "$stage"
