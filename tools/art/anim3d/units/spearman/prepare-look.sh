#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../../../../.."
source tools/art/anim3d/env.sh
unit=tools/art/anim3d/units/spearman
mkdir -p "$MASTER/look"
blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python "$unit/look.py" -- "$MASTER/spearman.blend" "$MASTER/look" --mode id --res 1280
"$ANIM_ROOT/venv/bin/python" "$unit/look_textures.py" "$MASTER/spearman-source.png" "$MASTER/look/id.png" "$MASTER/look"
blender -b --disable-autoexec --factory-startup --python-exit-code 1 --gpu-backend metal --python "$unit/look.py" -- "$MASTER/spearman.blend" "$MASTER/look" --res 1280 --name light --set debug=6
"$ANIM_ROOT/venv/bin/python" "$unit/look_textures.py" "$MASTER/spearman-source.png" "$MASTER/look/id.png" "$MASTER/look" "$MASTER/look/light.png"
"$ANIM_ROOT/venv/bin/python" "$unit/look_receipt.py"
