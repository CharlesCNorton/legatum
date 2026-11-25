#!/usr/bin/env bash
# Host-side handoff: Eevee needs a GPU context unavailable in the sandbox.
set -euo pipefail
source tools/art/anim3d/env.sh
unit=tools/art/anim3d/units/spearman-q
python3 tools/art/anim3d/kit/check_imports.py
python3 "$unit/inputs.py"
blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python "$unit/verify.py"
blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python "$unit/audit_contacts.py"
for clip in attack idle walk hit death; do
  blender -b --disable-autoexec --factory-startup --python-exit-code 1 --gpu-backend metal --python "$unit/render.py" -- --gpu --clip "$clip" --resolution 512
  "$ANIM_ROOT/venv/bin/python" "$unit/package.py" --gpu "$clip"
done
"$ANIM_ROOT/venv/bin/python" "$unit/atlas.py" --gpu
