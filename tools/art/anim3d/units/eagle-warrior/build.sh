#!/usr/bin/env bash
set -euo pipefail
source tools/art/anim3d/env.sh
UNIT_DIR=tools/art/anim3d/units/eagle-warrior
"$ANIM_ROOT/venv/bin/python" "$UNIT_DIR/prepare.py"
for stage in build bake finish paint animate; do
  blender -b --disable-autoexec --python-exit-code 1 --python "$UNIT_DIR/$stage.py"
done
