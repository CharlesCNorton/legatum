#!/usr/bin/env bash
set -euo pipefail
source tools/art/anim3d/env.sh
unit=tools/art/anim3d/units/spearman-q
python3 "$unit/fetch.py"
python3 "$unit/inputs.py"
for clip in attack idle walk hit death; do
  blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python "$unit/build.py" -- --clip "$clip" --painted --build-only
  blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python "$unit/render.py" -- --clip "$clip" --samples 8
  "$ANIM_ROOT/venv/bin/python" "$unit/package.py" "$clip"
done
blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python "$unit/verify.py"
blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python "$unit/audit_contacts.py"
"$ANIM_ROOT/venv/bin/python" "$unit/atlas.py"
python3 tools/art/anim3d/kit/check_imports.py
