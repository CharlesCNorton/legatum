#!/usr/bin/env bash
set -euo pipefail
source tools/art/anim3d/env.sh
UNIT=tools/art/anim3d/units/byzantine-heir
case "${1:-}" in
 build) "$ANIM_ROOT/venv/bin/python" "$UNIT/prepare.py"; blender -b --disable-autoexec --python-exit-code 1 --python "$UNIT/build.py" ;;
 *) blender -b --disable-autoexec --python-exit-code 1 --python "$UNIT/render.py" -- "$@" ;;
esac
