#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../.."
# Isolated unit dispatch precedes the legacy spearman lock and defaults.
if [[ "${UNIT:-spearman}" == cavalry ]]; then
  exec tools/art/anim3d/units/cavalry/render.sh "${1:-c}"
fi
source tools/art/anim3d/env.sh
stage="${1:-c}"
lock="$ANIM_ROOT/blender-heavy.lock"
if ! mkdir "$lock" 2>/dev/null; then echo "Another Blender job owns $lock" >&2; exit 1; fi
trap 'rmdir "$lock"' EXIT
export RENDER_ENGINE="${RENDER_ENGINE:-BLENDER_EEVEE}"
if [[ "$stage" == audit ]]; then
  nice -n 10 blender -b -t 4 --factory-startup --python-exit-code 1 --python tools/art/anim3d/audit.py
elif [[ "$stage" == build ]]; then
  nice -n 10 blender -b -t 4 --factory-startup --python-exit-code 1 --python tools/art/anim3d/scene.py
  nice -n 10 blender -b -t 4 --factory-startup --python-exit-code 1 --python tools/art/anim3d/helmet.py
elif [[ "$stage" == animate-* ]]; then
  nice -n 10 blender -b -t 4 --factory-startup --python-exit-code 1 --python tools/art/anim3d/animate.py -- "${stage#animate-}"
elif [[ "$stage" == helmet ]]; then
  nice -n 10 blender -b -t 4 --factory-startup --python-exit-code 1 --python tools/art/anim3d/helmet.py
elif [[ "$stage" == helmet-clips ]]; then
  nice -n 10 blender -b -t 4 --factory-startup --python-exit-code 1 --python tools/art/anim3d/helmet.py -- --clips
elif [[ "$stage" == finish ]]; then
  nice -n 10 blender -b -t 4 --factory-startup --python-exit-code 1 --python tools/art/anim3d/finish.py
elif [[ "$stage" == finish-clips ]]; then
  nice -n 10 blender -b -t 4 --factory-startup --python-exit-code 1 --python tools/art/anim3d/finish.py -- --clips
elif [[ "$stage" == paint ]]; then
  nice -n 10 blender -b -t 4 --factory-startup --python-exit-code 1 --python tools/art/anim3d/paint.py
elif [[ "$stage" == paint-clips ]]; then
  nice -n 10 blender -b -t 4 --factory-startup --python-exit-code 1 --python tools/art/anim3d/paint.py -- --clips
elif [[ "$stage" == bake ]]; then
  nice -n 10 blender -b -t 4 --factory-startup --python-exit-code 1 --python tools/art/anim3d/bake.py
elif [[ "$stage" == materials ]]; then
  nice -n 10 blender -b -t 4 --factory-startup --python-exit-code 1 --python tools/art/anim3d/materials.py
else
  render_args=(--python tools/art/anim3d/render.py -- "$stage")
  if [[ "$RENDER_ENGINE" == BLENDER_EEVEE ]]; then render_args=(--gpu-backend metal "${render_args[@]}"); fi
  nice -n 10 blender -b -t 4 --factory-startup --python-exit-code 1 "${render_args[@]}"
  "$ANIM_ROOT/venv/bin/python" tools/art/anim3d/review.py "$stage"
fi
