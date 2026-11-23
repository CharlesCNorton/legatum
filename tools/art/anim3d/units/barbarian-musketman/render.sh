#!/usr/bin/env bash
set -euo pipefail
source tools/art/anim3d/env.sh
export CYCLES_DEVICE="${CYCLES_DEVICE:-CPU}"
blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python tools/art/anim3d/units/barbarian-musketman/scene.py -- "${1:-build}"
