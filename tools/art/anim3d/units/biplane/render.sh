#!/usr/bin/env bash
set -euo pipefail
source tools/art/anim3d/env.sh
UNIT=tools/art/anim3d/units/biplane
case "${1:-}" in
 build) blender -b --disable-autoexec --python "$UNIT/scene.py" ;;
 paint) blender -b --disable-autoexec --python "$UNIT/paint.py" ;;
 audit) blender -b --disable-autoexec --python "$UNIT/audit.py" ;;
 animate) blender -b --disable-autoexec --python "$UNIT/animate.py" ;;
 *) STAGE="$1" blender -b --disable-autoexec --python "$UNIT/render.py" ;;
esac
