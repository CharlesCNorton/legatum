#!/usr/bin/env bash
set -euo pipefail
source tools/art/anim3d/env.sh
blender -b --disable-autoexec --python-exit-code 1 --python "tools/art/anim3d/units/knight/$1.py"
