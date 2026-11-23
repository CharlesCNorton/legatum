#!/usr/bin/env bash
set -euo pipefail
source tools/art/anim3d/env.sh
stage="${1:-all}"
args=(--background --disable-autoexec --python-exit-code 1)
if [[ "${RENDER_ENGINE:-CYCLES}" == BLENDER_EEVEE ]]; then args+=(--gpu-backend metal); fi
blender "${args[@]}" --python tools/art/anim3d/units/cuirassier/"${stage}".py
