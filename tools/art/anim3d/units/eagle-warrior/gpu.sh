#!/usr/bin/env bash
# Run from repo root, no arguments. Driver sets ROUND; all heavy stages are serial.
set -euo pipefail
source tools/art/anim3d/env.sh
export RENDER_ENGINE=CYCLES CYCLES_DEVICE=GPU RESOLUTION=512 SAMPLES="${SAMPLES:-48}"
export STAGES=b-plain,c-textured-lit,c-details,d-rig-poses,e-idle,e-move,e-attack,e-hit,e-death
UNIT_DIR=tools/art/anim3d/units/eagle-warrior
blender -b --disable-autoexec --python-exit-code 1 --python "$UNIT_DIR/audit.py"
"$UNIT_DIR/render.sh"
"$ANIM_ROOT/venv/bin/python" "$UNIT_DIR/deliver.py" --resolution 512
"$ANIM_ROOT/venv/bin/python" "$UNIT_DIR/validate.py"
"$ANIM_ROOT/venv/bin/python" "$UNIT_DIR/mp4.py"
