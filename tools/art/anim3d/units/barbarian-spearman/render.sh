#!/usr/bin/env bash
set -euo pipefail
source tools/art/anim3d/env.sh
TASK=tools/art/anim3d/units/barbarian-spearman
case "${1:-}" in
 build) blender -b --disable-autoexec --python-exit-code 1 --python "$TASK/build.py" ;;
 refine) blender -b --disable-autoexec --python-exit-code 1 --python "$TASK/refine.py" ;;
 paint) blender -b --disable-autoexec --python-exit-code 1 --python "$TASK/paint.py" ;;
 bake) blender -b --disable-autoexec --python-exit-code 1 --python "$TASK/bake.py" ;;
 animate) blender -b --disable-autoexec --python-exit-code 1 --python "$TASK/animate.py" ;;
 *) blender -b --disable-autoexec --python-exit-code 1 --python "$TASK/render.py" -- "$1" ;;
esac
