#!/usr/bin/env bash
set -euo pipefail
source tools/art/anim3d/env.sh
stage="${1:-all}"
unit=tools/art/anim3d/units/stealth-fighter
if [[ "$stage" == build ]]; then
  "$ANIM_ROOT/venv/bin/python" "$unit/prepare.py"
  blender -b --disable-autoexec --python-exit-code 1 --python "$unit/scene.py"
  blender -b --disable-autoexec --python-exit-code 1 --python "$unit/bake.py"
  "$ANIM_ROOT/venv/bin/python" "$unit/deliver.py" stamp-build
elif [[ "$stage" == bake ]]; then
  blender -b --disable-autoexec --python-exit-code 1 --python "$unit/bake.py"
else
  blender -b --disable-autoexec --python-exit-code 1 --python "$unit/render.py" -- "$stage"
fi
