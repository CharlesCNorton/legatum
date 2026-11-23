#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../.."
source tools/art/anim3d/env.sh
stage="${1:-c}"
if [[ "${UNIT:-spearman}" == horseman ]]; then exec tools/art/anim3d/mounted/render.sh "$stage"; fi
export RENDER_ENGINE="${RENDER_ENGINE:-BLENDER_EEVEE}"
if [[ "$stage" == audit ]]; then
  "$ANIM_ROOT/bin/blender-slot" -b --factory-startup --python-exit-code 1 --python tools/art/anim3d/audit.py
elif [[ "$stage" == build ]]; then
  "$ANIM_ROOT/bin/blender-slot" -b --factory-startup --python-exit-code 1 --python tools/art/anim3d/scene.py
  "$ANIM_ROOT/bin/blender-slot" -b --factory-startup --python-exit-code 1 --python tools/art/anim3d/helmet.py
elif [[ "$stage" == animate-* ]]; then
  "$ANIM_ROOT/bin/blender-slot" -b --factory-startup --python-exit-code 1 --python tools/art/anim3d/animate.py -- "${stage#animate-}"
elif [[ "$stage" == helmet ]]; then
  "$ANIM_ROOT/bin/blender-slot" -b --factory-startup --python-exit-code 1 --python tools/art/anim3d/helmet.py
elif [[ "$stage" == helmet-clips ]]; then
  "$ANIM_ROOT/bin/blender-slot" -b --factory-startup --python-exit-code 1 --python tools/art/anim3d/helmet.py -- --clips
elif [[ "$stage" == finish ]]; then
  "$ANIM_ROOT/bin/blender-slot" -b --factory-startup --python-exit-code 1 --python tools/art/anim3d/finish.py
elif [[ "$stage" == finish-clips ]]; then
  "$ANIM_ROOT/bin/blender-slot" -b --factory-startup --python-exit-code 1 --python tools/art/anim3d/finish.py -- --clips
elif [[ "$stage" == paint ]]; then
  "$ANIM_ROOT/bin/blender-slot" -b --factory-startup --python-exit-code 1 --python tools/art/anim3d/paint.py
elif [[ "$stage" == paint-clips ]]; then
  "$ANIM_ROOT/bin/blender-slot" -b --factory-startup --python-exit-code 1 --python tools/art/anim3d/paint.py -- --clips
elif [[ "$stage" == bake ]]; then
  "$ANIM_ROOT/bin/blender-slot" -b --factory-startup --python-exit-code 1 --python tools/art/anim3d/bake.py
elif [[ "$stage" == materials ]]; then
  "$ANIM_ROOT/bin/blender-slot" -b --factory-startup --python-exit-code 1 --python tools/art/anim3d/materials.py
else
  render_args=(--python tools/art/anim3d/render.py -- "$stage")
  if [[ "$RENDER_ENGINE" == BLENDER_EEVEE ]]; then render_args=(--gpu-backend metal "${render_args[@]}"); fi
  "$ANIM_ROOT/bin/blender-slot" -b --factory-startup --python-exit-code 1 "${render_args[@]}"
  "$ANIM_ROOT/venv/bin/python" tools/art/anim3d/review.py "$stage"
fi
