#!/usr/bin/env bash
set -euo pipefail
source tools/art/anim3d/env.sh
export ARTILLERY_MODE="${1:-preview}"
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/artillery/prepare.py
args=(-b --disable-autoexec --factory-startup --python-exit-code 1)
if [[ "${CYCLES_DEVICE:-CPU}" == GPU ]]; then args+=(--gpu-backend metal); fi
blender "${args[@]}" --python tools/art/anim3d/units/artillery/scene.py
if [[ "$ARTILLERY_MODE" != stills ]]; then
  blender "${args[@]}" --python tools/art/anim3d/units/artillery/contact_views.py
fi
