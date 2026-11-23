#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../.."
source tools/art/anim3d/env.sh
stage="${1:-c}"
export RENDER_ENGINE="${RENDER_ENGINE:-BLENDER_EEVEE}"
if [[ "$stage" == audit ]]; then
  blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python tools/art/anim3d/audit.py
elif [[ "$stage" == build ]]; then
  blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python tools/art/anim3d/scene.py
  blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python tools/art/anim3d/helmet.py
elif [[ "$stage" == animate-* ]]; then
  blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python tools/art/anim3d/animate.py -- "${stage#animate-}"
elif [[ "$stage" == helmet ]]; then
  blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python tools/art/anim3d/helmet.py
elif [[ "$stage" == helmet-clips ]]; then
  blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python tools/art/anim3d/helmet.py -- --clips
elif [[ "$stage" == finish ]]; then
  blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python tools/art/anim3d/finish.py
elif [[ "$stage" == finish-clips ]]; then
  blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python tools/art/anim3d/finish.py -- --clips
elif [[ "$stage" == project ]]; then
  blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python tools/art/anim3d/project.py
elif [[ "$stage" == paint ]]; then
  blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python tools/art/anim3d/paint.py
elif [[ "$stage" == paint-clips ]]; then
  blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python tools/art/anim3d/paint.py -- --clips
elif [[ "$stage" == bake ]]; then
  blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python tools/art/anim3d/bake.py
elif [[ "$stage" == materials ]]; then
  blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python tools/art/anim3d/materials.py
else
  render_args=(--python tools/art/anim3d/render.py -- "$stage")
  if [[ "$RENDER_ENGINE" == BLENDER_EEVEE ]]; then render_args=(--gpu-backend metal "${render_args[@]}"); fi
  blender -b --disable-autoexec --factory-startup --python-exit-code 1 "${render_args[@]}"
  if [[ "$stage" != b && "${GRADE:-1}" == 1 ]]; then
    "$ANIM_ROOT/venv/bin/python" tools/art/anim3d/grade.py "$stage"
  fi
  "$ANIM_ROOT/venv/bin/python" tools/art/anim3d/review.py "$stage"
fi
