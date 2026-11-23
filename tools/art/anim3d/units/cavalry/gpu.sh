#!/usr/bin/env bash
# No arguments; run from repository root. ROUND is supplied by the driver.
set -euo pipefail
source tools/art/anim3d/env.sh
U=tools/art/anim3d/units/cavalry
export RENDER_ENGINE="${RENDER_ENGINE:-CYCLES}" CYCLES_DEVICE=GPU
export RESOLUTION=512 SAMPLES="${SAMPLES:-64}" ROUND="${ROUND:-1}"
# Rebuild editable clips only if absent; source hashes prevent stale delivery.
[[ -f "$ANIM_ROOT/masters/cavalry/cavalry.blend" ]] || { echo 'Missing cavalry master: run CPU build/materials/bake/paint first.' >&2; exit 1; }
STAGES=b,c,c-details,d,e-idle,e-move,e-attack,e-hit,e-death "$U/render.sh" refresh
"$U/render.sh" audit
REQUIRE_MASTERS=1 "$ANIM_ROOT/venv/bin/python" "$U/pack.py"
"$ANIM_ROOT/venv/bin/python" "$U/validate.py"
"$ANIM_ROOT/venv/bin/python" "$U/mp4.py"
printf '%s\n' "Round $ROUND: GPU stages, 512/256 masters, trimmed atlas, validation and MP4 complete; visual approval still required." >> "$ANIM_ROOT/review/3d-v2/cavalry-log.md"
