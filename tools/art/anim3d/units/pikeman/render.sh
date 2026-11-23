#!/usr/bin/env bash
set -euo pipefail
source tools/art/anim3d/env.sh
args=(-b --disable-autoexec --python-exit-code 1)
if [[ ${RENDER_ENGINE:-CYCLES} != CYCLES || ${CYCLES_DEVICE:-CPU} == GPU ]]; then args+=(--gpu-backend metal); fi
blender "${args[@]}" --python tools/art/anim3d/units/pikeman/render.py
