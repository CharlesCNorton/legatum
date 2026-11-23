#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../../../.."
source tools/art/anim3d/env.sh
unit=tools/art/anim3d/units/war-elephant
stage="${1:-c}"
case "$stage" in
  build|animate|audit) script="$unit/$stage.py"; args=() ;;
  *) script="$unit/render.py"; args=(-- "$stage") ;;
esac
gpu=()
if [[ "${RENDER_ENGINE:-CYCLES}" == BLENDER_EEVEE ]]; then gpu=(--gpu-backend metal); fi
"$ANIM_ROOT/bin/blender-slot" -b --disable-autoexec --factory-startup --python-exit-code 1 ${gpu[@]+"${gpu[@]}"} --python "$script" ${args[@]+"${args[@]}"}
case "$stage" in
  build|animate|audit) ;;
  *) "$ANIM_ROOT/venv/bin/python" "$unit/deliver.py" review "$stage" ;;
esac
