#!/usr/bin/env bash
set -euo pipefail
source tools/art/anim3d/env.sh
export CYCLES_DEVICE="${CYCLES_DEVICE:-CPU}"
if [[ "${1:-build}" == render ]]; then
  exec "$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/musketman/frame_jobs.py
fi
blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python tools/art/anim3d/units/musketman/scene.py -- "${1:-build}"
