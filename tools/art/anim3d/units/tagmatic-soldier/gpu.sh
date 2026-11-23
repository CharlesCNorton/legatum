#!/usr/bin/env bash
# Complete host pass, no arguments; invoked from the repository root.
set -euo pipefail
cd "$(dirname "$0")/../../../../.."
source tools/art/anim3d/env.sh
export ROUND="${ROUND:-1}" RENDER_ENGINE=CYCLES CYCLES_DEVICE=GPU RESOLUTION=512 SAMPLES=48
UNIT=tools/art/anim3d/units/tagmatic-soldier
"$UNIT/render.sh" audit
for stage in b c d e-idle e-move e-attack e-hit e-death; do
 "$UNIT/render.sh" "$stage"
done
"$ANIM_ROOT/venv/bin/python" "$UNIT/deliver.py" pack
"$ANIM_ROOT/venv/bin/python" "$UNIT/deliver.py" validate
"$ANIM_ROOT/venv/bin/python" "$UNIT/deliver.py" video
printf '%s\n' "- GPU round $ROUND: all stages rendered at 512, 256 masters retained; trimmed 160 atlas validated; comparison and MP4 saved. Visual approval still required." >> "$ANIM_ROOT/review/3d-v2/tagmatic-soldier-log.md"
