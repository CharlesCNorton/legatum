#!/usr/bin/env bash
set -euo pipefail
source tools/art/anim3d/env.sh
unit_dir=tools/art/anim3d/units/medjay
stage="${1:-c}"
export RENDER_ENGINE="${RENDER_ENGINE:-CYCLES}"
export CYCLES_DEVICE="${CYCLES_DEVICE:-CPU}"
args=(-b --disable-autoexec --factory-startup --python-exit-code 1)
if [[ "$RENDER_ENGINE" == BLENDER_EEVEE ]]; then args+=(--gpu-backend metal); fi
case "$stage" in
 build) "$ANIM_ROOT/venv/bin/python" "$unit_dir/prepare.py"; blender "${args[@]}" --python "$unit_dir/build.py" ;;
 finish|animate|audit|feet) blender "${args[@]}" --python "$unit_dir/$stage.py" ;;
 *) blender "${args[@]}" --python "$unit_dir/render.py" -- "$stage"; "$ANIM_ROOT/venv/bin/python" "$unit_dir/deliver.py" review "$stage" ;;
esac
