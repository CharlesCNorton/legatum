#!/usr/bin/env bash
# Complete host pass. Run from repo root, no arguments; ROUND comes from driver.
set -euo pipefail
source tools/art/anim3d/env.sh
export ROUND="${ROUND:-4}"
trap 'printf "%s\n" "- GPU round $ROUND failed; inspect driver output before judging this pass." >> "$REVIEW/spearman-log.md"' ERR
printf '%s\n' "- GPU round $ROUND started: full Cycles GPU pass requested." >> "$REVIEW/spearman-log.md"
export RENDER_ENGINE=CYCLES CYCLES_DEVICE=GPU CYCLES_BACKEND="${CYCLES_BACKEND:-METAL}"
export RESOLUTION=512 SAMPLES="${SAMPLES:-64}" GRADE=1
# Regenerate every clip from the current master before final renders/audit.
for clip in idle move attack hit death; do
  tools/art/anim3d/render.sh "animate-$clip"
done
# Plain geometry review uses the same calibrated camera and no texture shaders.
SPEARMAN_PLAIN=1 tools/art/anim3d/render.sh b
tools/art/anim3d/render.sh c
tools/art/anim3d/render.sh detail
tools/art/anim3d/render.sh d
for clip in idle move attack hit death; do
  tools/art/anim3d/render.sh "e-$clip"
done
tools/art/anim3d/render.sh audit
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/details.py
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/test_pipeline.py
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/spearman/delivery.py pack
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/spearman/delivery.py validate
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/units/spearman/delivery.py movie
printf '%s\n' "- GPU round $ROUND finished: all stages, masters, atlas validation and movie complete; visual review pending." >> "$REVIEW/spearman-log.md"
# PASS is a visual judgment after reviewing these outputs; never write it here.
printf '%s\n' "GPU handoff complete: spearman round $ROUND; visual review still required."
