#!/usr/bin/env bash
# Complete host pass. Run without arguments, from the repository root.
set -euo pipefail
source tools/art/anim3d/env.sh
export ROUND="${ROUND:-1}" RESOLUTION=512
export RENDER_ENGINE=CYCLES CYCLES_DEVICE=GPU SAMPLES="${SAMPLES:-64}"
export GPU_ARGS='--gpu-backend metal'
UNIT=tools/art/anim3d/units/fighter
for stage in b c e-idle e-move e-attack e-hit e-death; do
  "$UNIT/render.sh" "$stage"
done
"$UNIT/render.sh" audit
"$ANIM_ROOT/venv/bin/python" "$UNIT/deliver.py" pack
"$ANIM_ROOT/venv/bin/python" "$UNIT/deliver.py" movie
printf '%s\n' "- GPU round $ROUND: 512/256 masters, every stage, trimmed atlas, validation and MP4 finished. Art verdict still required." >> "$ANIM_ROOT/review/3d-v2/fighter-log.md"
