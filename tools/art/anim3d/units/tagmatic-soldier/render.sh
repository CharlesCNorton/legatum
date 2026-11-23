#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../../../.."
source tools/art/anim3d/env.sh
UNIT=tools/art/anim3d/units/tagmatic-soldier
stage="${1:-c}"
args=(-b --disable-autoexec --factory-startup --python-exit-code 1)
case "$stage" in
 build) blender "${args[@]}" --python "$UNIT/build.py" ;;
 animate) blender "${args[@]}" --python "$UNIT/animate.py" ;;
 audit) blender "${args[@]}" --python "$UNIT/audit.py" ;;
 bake) blender "${args[@]}" --python "$UNIT/bake.py" ;;
 *)
 if [[ "${RENDER_ENGINE:-CYCLES}" == BLENDER_EEVEE ]]; then args+=(--gpu-backend metal); fi
 blender "${args[@]}" --python "$UNIT/render.py" -- "$stage"
 "$ANIM_ROOT/venv/bin/python" "$UNIT/deliver.py" review "$stage"
 ;;
esac
