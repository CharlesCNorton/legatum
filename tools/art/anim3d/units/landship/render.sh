#!/usr/bin/env bash
set -euo pipefail
source tools/art/anim3d/env.sh
unit=tools/art/anim3d/units/landship
case "${1:-}" in
 build) "$ANIM_ROOT/venv/bin/python" "$unit/prepare.py"; blender -b --disable-autoexec --python-exit-code 1 --python "$unit/scene.py" ;;
 bake) blender -b --disable-autoexec --python-exit-code 1 --python "$unit/bake.py" ;;
 animate) blender -b --disable-autoexec --python-exit-code 1 --python "$unit/animate.py" ;;
 *) blender -b --disable-autoexec --python-exit-code 1 --python "$unit/render.py" -- "$1"; "$ANIM_ROOT/venv/bin/python" "$unit/deliver.py" review "$1" ;;
esac
