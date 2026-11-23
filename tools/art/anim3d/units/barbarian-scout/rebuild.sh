#!/usr/bin/env bash
set -euo pipefail
source tools/art/anim3d/env.sh
HERE=tools/art/anim3d/units/barbarian-scout
"$ANIM_ROOT/venv/bin/python" "$HERE/prepare.py"
for stage in build refine texture bake animate; do
  blender -b --disable-autoexec --python-exit-code 1 --python "$HERE/$stage.py"
  printf 'Completed %s stage.\n' "$stage" >> "$ANIM_ROOT/review/3d-v2/barbarian-scout-log.md"
done
