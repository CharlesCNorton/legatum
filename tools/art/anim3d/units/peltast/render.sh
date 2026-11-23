#!/usr/bin/env bash
set -euo pipefail
source tools/art/anim3d/env.sh
unit=tools/art/anim3d/units/peltast
stage="${1:-c}"
args=(-b --disable-autoexec --factory-startup --python-exit-code 1)
if [[ "${RENDER_ENGINE:-CYCLES}" == BLENDER_EEVEE ]]; then args+=(--gpu-backend metal); fi
case "$stage" in
 bootstrap|build|paint|animate|audit|bake|refine|feet) blender "${args[@]}" --python "$unit/$stage.py" ;;
 *) blender "${args[@]}" --python "$unit/render.py" -- "$stage"
    "$ANIM_ROOT/venv/bin/python" "$unit/post.py" "$stage" ;;
esac
