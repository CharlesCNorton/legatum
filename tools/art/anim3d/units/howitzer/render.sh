#!/usr/bin/env bash
set -euo pipefail
source tools/art/anim3d/env.sh
export HOWITZER_MODE="${1:-preview}"
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/howitzer/prepare.py
args=(-b --disable-autoexec --factory-startup --python-exit-code 1)
if [[ "${CYCLES_DEVICE:-CPU}" == GPU ]]; then args+=(--gpu-backend metal); fi
blender "${args[@]}" --python tools/art/anim3d/units/howitzer/scene.py
