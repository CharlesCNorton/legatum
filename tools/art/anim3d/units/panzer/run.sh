#!/usr/bin/env bash
set -euo pipefail
source tools/art/anim3d/env.sh
U=tools/art/anim3d/units/panzer
PY="$ANIM_ROOT/venv/bin/python"
case "${1:?stage required}" in
 build) "$PY" "$U/prepare-paint.py"; blender -b --disable-autoexec --python-exit-code 1 --python "$U/scene.py" ;;
 bake|paint|animate|audit) blender -b --disable-autoexec --python-exit-code 1 --python "$U/$1.py" ;;
 b|c|details|d|g|e-*)
   blender -b --disable-autoexec --python-exit-code 1 --python "$U/render.py" -- "$1"
   if [[ "$1" != b && "$1" != g ]]; then "$PY" "$U/grade.py" "$1"; fi
   "$PY" "$U/review.py" "$1"
   ;;
 pack) "$PY" "$U/deliver.py" ;;
 *) exit 2 ;;
esac
