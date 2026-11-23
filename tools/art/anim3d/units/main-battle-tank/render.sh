#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../../../.."
source tools/art/anim3d/env.sh
stage="${1:-c}"
export RENDER_ENGINE="${RENDER_ENGINE:-BLENDER_EEVEE}"
# Rerender the saved masters consistently; never rebuild geometry in a delivery pass.
if [[ "$stage" == final ]]; then
  for next in c details d e-idle e-move e-attack e-hit e-death g; do
    tools/art/anim3d/units/main-battle-tank/render.sh "$next"
  done
  "$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/main-battle-tank/deliver.py
  exec tools/art/anim3d/units/main-battle-tank/render.sh audit
fi
args=(-b --disable-autoexec --factory-startup --python-exit-code 1)
case "$stage" in
  build) script=scene.py ;;
  refine) script=refine.py ;;
  bake) script=bake.py ;;
  paint) "$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/main-battle-tank/prepare-paint.py; script=paint.py ;;
  animate) script=animate.py ;;
  audit) script=audit.py ;;
  *) script=render.py
     if [[ "$RENDER_ENGINE" == BLENDER_EEVEE || "${CYCLES_DEVICE:-CPU}" == GPU ]]; then args+=(--gpu-backend metal); fi ;;
esac
blender "${args[@]}" --python "tools/art/anim3d/units/main-battle-tank/$script" -- "$stage"
case "$stage" in
  b|c|details|d|g|e-*)
    "$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/main-battle-tank/grade.py "$stage"
    "$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/main-battle-tank/review.py "$stage" ;;
esac
