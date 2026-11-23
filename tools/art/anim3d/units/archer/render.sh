#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../../../.."
source tools/art/anim3d/env.sh
stage="${1:-c}"
export RENDER_ENGINE="${RENDER_ENGINE:-CYCLES}"
args=(-b --disable-autoexec --factory-startup --python-exit-code 1)
if [[ "$RENDER_ENGINE" == BLENDER_EEVEE || "${CYCLES_DEVICE:-CPU}" == GPU ]]; then args+=(--gpu-backend metal); fi
case "$stage" in
  build|materials|bake|paint|animate|audit) blender "${args[@]}" --python "tools/art/anim3d/units/archer/$stage.py" ;;
  *) blender "${args[@]}" --python tools/art/anim3d/units/archer/render.py -- "$stage"
     "$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/archer/review.py "$stage" ;;
esac
