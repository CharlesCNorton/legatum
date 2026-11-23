#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../../../.."
source tools/art/anim3d/env.sh
export UNIT=legionary RENDER_ENGINE="${RENDER_ENGINE:-CYCLES}" CYCLES_DEVICE="${CYCLES_DEVICE:-CPU}"
stage="${1:-c}"
case "$stage" in
prepare|pack|validate) "$ANIM_ROOT/venv/bin/python" "tools/art/anim3d/units/legionary/$stage.py" ;;
build|paint|animate|audit|round) blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python "tools/art/anim3d/units/legionary/$stage.py" ;;
*) blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python tools/art/anim3d/units/legionary/render.py -- "$stage"
   "$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/legionary/review.py "$stage" ;;
esac
