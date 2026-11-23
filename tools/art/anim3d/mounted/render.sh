#!/usr/bin/env bash
set -eo pipefail
cd "$(dirname "$0")/../../../.."
source tools/art/anim3d/env.sh
stage="${1:-c}"
export RENDER_ENGINE="${RENDER_ENGINE:-BLENDER_EEVEE}"
case "$stage" in
 build|materials|animate|audit|bake|paint) script="tools/art/anim3d/mounted/$stage.py"; args=();;
 *) script=tools/art/anim3d/mounted/render.py;args=(-- "$stage");;
esac
gpu=()
if [[ "$script" == */render.py && ( "$RENDER_ENGINE" == BLENDER_EEVEE || "${CYCLES_DEVICE:-CPU}" == GPU ) ]]; then gpu=(--gpu-backend metal); fi
"$ANIM_ROOT/bin/blender-slot" -b --disable-autoexec --factory-startup --python-exit-code 1 "${gpu[@]}" --python "$script" "${args[@]}"
if [[ "$script" == */render.py ]]; then "$ANIM_ROOT/venv/bin/python" tools/art/anim3d/mounted/grade.py "$stage"; "$ANIM_ROOT/venv/bin/python" tools/art/anim3d/mounted/review.py "$stage"; fi
