#!/usr/bin/env bash
set -euo pipefail
source tools/art/anim3d/env.sh
U=tools/art/anim3d/units/cavalry
stage="${1:?stage required}"
if [[ "$stage" =~ ^(build|materials|bake|paint|animate|audit|correct|refresh|feet)$ ]]; then
  if [[ "$stage" =~ ^(refresh|feet)$ && "${RENDER_ENGINE:-CYCLES}" == BLENDER_EEVEE ]]; then
    blender -b --disable-autoexec --gpu-backend metal --python-exit-code 1 --python "$U/$stage.py"
  else
    blender -b --disable-autoexec --python-exit-code 1 --python "$U/$stage.py"
  fi
  if [[ "$stage" == feet ]]; then "$ANIM_ROOT/venv/bin/python" "$U/feet_review.py"; fi
else
  args=(--background)
  if [[ "${RENDER_ENGINE:-CYCLES}" == BLENDER_EEVEE ]]; then args+=(--gpu-backend metal); fi
  blender --disable-autoexec "${args[@]}" --python-exit-code 1 --python "$U/render.py" -- "$stage"
  "$ANIM_ROOT/venv/bin/python" "$U/grade.py" "$stage"
  "$ANIM_ROOT/venv/bin/python" "$U/review.py" "$stage"
fi
