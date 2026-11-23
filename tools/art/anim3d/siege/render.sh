#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../../.."
source tools/art/anim3d/env.sh
stage="${1:-c}"
export RENDER_ENGINE="${RENDER_ENGINE:-BLENDER_EEVEE}"
args=(-b --disable-autoexec --factory-startup --python-exit-code 1)
if [[ "$stage" == build ]]; then
  blender "${args[@]}" --python tools/art/anim3d/siege/scene.py
elif [[ "$stage" == register || "$stage" == finish || "$stage" == paint || "$stage" == materials || "$stage" == bake || "$stage" == animate || "$stage" == audit ]]; then
  blender "${args[@]}" --python "tools/art/anim3d/siege/$stage.py"
elif [[ "$stage" == pack || "$stage" == validate ]]; then
  "$ANIM_ROOT/venv/bin/python" "tools/art/anim3d/siege/$stage.py"
else
  if [[ "$RENDER_ENGINE" == BLENDER_EEVEE ]]; then args+=(--gpu-backend metal); fi
  blender "${args[@]}" --python tools/art/anim3d/siege/render.py -- "$stage"
  "$ANIM_ROOT/venv/bin/python" tools/art/anim3d/siege/review.py "$stage"
fi
