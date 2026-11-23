#!/usr/bin/env bash
set -euo pipefail
source tools/art/anim3d/env.sh
unit=tools/art/anim3d/units/barbarian-archer
stage="${1:-preview}"
if [[ "$stage" == build ]]; then
  blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python "$unit/build.py"
elif [[ "$stage" == finish ]]; then
  blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python "$unit/finish.py"
elif [[ "$stage" == animate ]]; then
  blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python "$unit/animate.py"
else
  blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python "$unit/render.py" -- "$stage"
  "$ANIM_ROOT/venv/bin/python" "$unit/deliver.py" "$stage"
fi
