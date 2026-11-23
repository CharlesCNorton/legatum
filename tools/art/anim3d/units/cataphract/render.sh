#!/usr/bin/env bash
set -euo pipefail
source tools/art/anim3d/env.sh
unit=tools/art/anim3d/units/cataphract
case "${1:-all}" in
 prepare) "$ANIM_ROOT/venv/bin/python" "$unit/prepare.py" ;;
 build|finish|bake|animate|audit) blender -b --disable-autoexec --python-exit-code 1 --python "$unit/$1.py" ;;
 pack) "$ANIM_ROOT/venv/bin/python" "$unit/deliver.py" ;;
 *) blender -b --disable-autoexec --python-exit-code 1 --python "$unit/render.py" -- "${1:-all}" ;;
esac
