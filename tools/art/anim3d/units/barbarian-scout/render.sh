#!/usr/bin/env bash
set -euo pipefail
source tools/art/anim3d/env.sh
HERE=tools/art/anim3d/units/barbarian-scout
case "${1:-preview}" in
 build) blender -b --disable-autoexec --python-exit-code 1 --python "$HERE/build.py" ;;
 *) blender -b --disable-autoexec --python-exit-code 1 --python "$HERE/render.py" -- "$@" ;;
esac
