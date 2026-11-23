#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../../../.."
source tools/art/anim3d/env.sh
export CYCLES_DEVICE=GPU RESOLUTION=512 SAMPLES="${SAMPLES:-48}"
python="$ANIM_ROOT/venv/bin/python"
"$python" tools/art/anim3d/units/arquebusier/prepare.py
blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python tools/art/anim3d/units/arquebusier/scene.py -- render
blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python tools/art/anim3d/units/arquebusier/audit.py
"$python" tools/art/anim3d/units/arquebusier/finish.py
