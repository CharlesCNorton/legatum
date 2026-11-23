#!/usr/bin/env bash
set -euo pipefail
source tools/art/anim3d/env.sh
U=tools/art/anim3d/units/keshig
stage="${1:-all}"
case "$stage" in
 build|finish|bake|animate|audit) blender -b --disable-autoexec --python-exit-code 1 --python "$U/$stage.py" ;;
 *) blender -b --disable-autoexec --python-exit-code 1 --python "$U/render.py" -- "$stage" ;;
esac
