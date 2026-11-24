#!/usr/bin/env bash
set -euo pipefail
source tools/art/anim3d/env.sh
unit=tools/art/anim3d/units/spearman-q
python3 "$unit/fetch.py"
for clip in attack idle walk hit death; do
  blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python "$unit/build.py" -- --clip "$clip"
  "$ANIM_ROOT/venv/bin/python" "$unit/package.py" "$clip"
done
blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python "$unit/verify.py"
python3 tools/art/anim3d/kit/check_imports.py
