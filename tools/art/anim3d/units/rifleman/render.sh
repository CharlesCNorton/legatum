#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../../../.."
source tools/art/anim3d/env.sh
export CYCLES_DEVICE="${CYCLES_DEVICE:-CPU}" RESOLUTION="${RESOLUTION:-256}" SAMPLES="${SAMPLES:-8}"
unit=tools/art/anim3d/units/rifleman
stage="${1:-preview}"
case "$stage" in
 build) "$ANIM_ROOT/venv/bin/python" "$unit/prepare.py"; blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python "$unit/scene.py" -- build ;;
 pack) "$ANIM_ROOT/venv/bin/python" "$unit/finish.py" ;;
 *) blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python "$unit/scene.py" -- "$stage" ;;
esac
