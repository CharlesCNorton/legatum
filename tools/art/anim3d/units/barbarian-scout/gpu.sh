#!/usr/bin/env bash
# No arguments. Run from repo root; ROUND is provided by the overnight driver.
set -euo pipefail
source tools/art/anim3d/env.sh
HERE=tools/art/anim3d/units/barbarian-scout
export ROUND="${ROUND:-1}" CYCLES_DEVICE=GPU RESOLUTION=512 SAMPLES="${SAMPLES:-64}"
# All Blender calls use the PATH gate. There is no nested process or lock.
blender -b --disable-autoexec --python-exit-code 1 --python "$HERE/audit.py"
blender -b --disable-autoexec --python-exit-code 1 --python "$HERE/render.py" -- all
"$ANIM_ROOT/venv/bin/python" "$HERE/post.py" pack
"$ANIM_ROOT/venv/bin/python" "$HERE/post.py" validate
"$ANIM_ROOT/venv/bin/python" "$HERE/post.py" video
# A successful technical pass never creates PASS: the rest comparison and motion
# must receive an actual art review first.
