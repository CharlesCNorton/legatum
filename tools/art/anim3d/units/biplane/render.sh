#!/usr/bin/env bash
set -euo pipefail
source tools/art/anim3d/env.sh
UNIT=tools/art/anim3d/units/biplane
case "${1:-}" in
 build) blender -b --disable-autoexec --python-exit-code 1 --python "$UNIT/scene.py" ;;
 register) blender -b --disable-autoexec --python-exit-code 1 --python "$UNIT/refine.py" ;;
 paint) blender -b --disable-autoexec --python-exit-code 1 --python "$UNIT/paint.py" ;;
 audit) blender -b --disable-autoexec --python-exit-code 1 --python "$UNIT/audit.py" ;;
 animate) blender -b --disable-autoexec --python-exit-code 1 --python "$UNIT/animate.py" ;;
 *) STAGE="$1" blender -b --disable-autoexec --python-exit-code 1 --python "$UNIT/render.py" ;;
esac
