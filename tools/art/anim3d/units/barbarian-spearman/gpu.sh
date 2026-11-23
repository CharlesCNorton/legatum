#!/usr/bin/env bash
# Required no-argument GPU handoff. Run from the repository root.
set -euo pipefail
source tools/art/anim3d/env.sh
TASK=tools/art/anim3d/units/barbarian-spearman
PY="$ANIM_ROOT/venv/bin/python"
export RENDER_ENGINE=CYCLES CYCLES_DEVICE=GPU RESOLUTION=512 SAMPLES=64
# Geometry/texture/rig masters are already built. Fail rather than quietly use CPU.
for stage in b c c-details d e-idle e-move e-attack e-hit e-death; do
  "$TASK/render.sh" "$stage"
  "$PY" "$TASK/grade.py" "$stage"
  "$PY" "$TASK/review.py" "$stage"
done
"$PY" "$TASK/pack.py"
"$PY" "$TASK/validate.py"
blender -b --disable-autoexec --python-exit-code 1 --python "$TASK/audit.py"
printf '%s\n' '- Full GPU stage/master/atlas pass completed; fresh visual judgment still required.' >> "$ANIM_ROOT/review/3d-v2/barbarian-spearman-log.md"
