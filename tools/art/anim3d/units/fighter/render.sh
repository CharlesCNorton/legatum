#!/usr/bin/env bash
set -euo pipefail
source tools/art/anim3d/env.sh
UNIT=tools/art/anim3d/units/fighter
PY="$ANIM_ROOT/venv/bin/python"
case "${1:-}" in
 build) "$PY" "$UNIT/prepare.py" || exit $?; blender -b --disable-autoexec --python-exit-code 1 --python "$UNIT/scene.py" ;;
 finish) blender -b --disable-autoexec --python-exit-code 1 --python "$UNIT/finish.py" ;;
 audit) blender -b --disable-autoexec --python-exit-code 1 --python "$UNIT/audit.py" ;;
 animate) blender -b --disable-autoexec --python-exit-code 1 --python "$UNIT/animate.py" ;;
 *) blender -b --disable-autoexec --python-exit-code 1 ${GPU_ARGS:-} --python "$UNIT/render.py" -- "${1:-c}" || exit $?; "$PY" "$UNIT/deliver.py" review "${1:-c}" ;;
esac
