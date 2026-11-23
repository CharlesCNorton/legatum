#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../../.."
source tools/art/anim3d/env.sh
stage="${1:-c}"
export RENDER_ENGINE="${RENDER_ENGINE:-BLENDER_EEVEE}"
# Rerender the saved masters consistently; never rebuild geometry in a delivery pass.
if [[ "$stage" == final ]]; then
  for next in c details d e-idle e-move e-attack e-hit e-death; do
    tools/art/anim3d/vehicles/render.sh "$next"
  done
  "$ANIM_ROOT/venv/bin/python" tools/art/anim3d/vehicles/deliver.py
  exec tools/art/anim3d/vehicles/render.sh audit
fi
args=(-b --disable-autoexec --factory-startup --python-exit-code 1)
case "$stage" in
  build) script=scene.py ;;
  bake) script=bake.py ;;
  paint) "$ANIM_ROOT/venv/bin/python" tools/art/anim3d/vehicles/prepare-paint.py; script=paint.py ;;
  animate) script=animate.py ;;
  audit) script=audit.py ;;
  *) script=render.py
     if [[ "$RENDER_ENGINE" == BLENDER_EEVEE || "${CYCLES_DEVICE:-CPU}" == GPU ]]; then args+=(--gpu-backend metal); fi ;;
esac
"$ANIM_ROOT/bin/blender-slot" "${args[@]}" --python "tools/art/anim3d/vehicles/$script" -- "$stage"
case "$stage" in
  b|c|details|d|e-*)
    "$ANIM_ROOT/venv/bin/python" tools/art/anim3d/vehicles/grade.py "$stage"
    "$ANIM_ROOT/venv/bin/python" tools/art/anim3d/vehicles/review.py "$stage" ;;
esac
