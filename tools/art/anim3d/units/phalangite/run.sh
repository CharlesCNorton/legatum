#!/usr/bin/env bash
set -euo pipefail
source tools/art/anim3d/env.sh
unit_dir=tools/art/anim3d/units/phalangite
stage="${1:-c}"
if [[ "$stage" == build ]]; then
  "$ANIM_ROOT/venv/bin/python" "$unit_dir/prepare.py"
  blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python "$unit_dir/build.py"
elif [[ "$stage" == finish ]]; then
  blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python "$unit_dir/finish.py"
elif [[ "$stage" == audit ]]; then
  blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python "$unit_dir/audit.py"
elif [[ "$stage" == animate ]]; then
  blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python "$unit_dir/animate.py"
else
  if [[ "${RENDER_ENGINE:-CYCLES}" == BLENDER_EEVEE ]]; then
    blender -b --disable-autoexec --factory-startup --gpu-backend metal --python-exit-code 1 --python "$unit_dir/render.py" -- "$stage"
  else
    blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python "$unit_dir/render.py" -- "$stage"
  fi
fi
