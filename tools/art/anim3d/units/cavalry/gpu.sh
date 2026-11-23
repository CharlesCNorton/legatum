#!/usr/bin/env bash
# Complete no-argument GPU handoff; the driver supplies ROUND.
set -euo pipefail
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
source tools/art/anim3d/env.sh
U=tools/art/anim3d/units/cavalry
export RENDER_ENGINE="${RENDER_ENGINE:-CYCLES}" CYCLES_DEVICE=GPU
export RESOLUTION=512 SAMPLES="${SAMPLES:-64}" ROUND="${ROUND:-2}"
log="$ANIM_ROOT/cavalry-gpu-round${ROUND}.log"
status="$ANIM_ROOT/review/3d-v2/cavalry-gpu-status.txt"
# Keep the driver transcript useful as well as the unit-owned detailed log.
(
# A normal pipe works in sandboxes that deny process-substitution /dev/fd.
stage=preflight
trap 'code=$?; printf "failed stage=%s exit=%s round=%s\n" "$stage" "$code" "$ROUND" > "$status"; exit "$code"' ERR
printf 'running round=%s checkout=%s\n' "$ROUND" "$PWD" > "$status"
git rev-parse HEAD
git status --short
command -v blender
[[ -f "$ANIM_ROOT/masters/cavalry/cavalry-unpainted.blend" ]] || { echo 'Missing unpainted cavalry checkpoint'; false; }
# Reject unavailable GPU before rebuilding or invalidating any final output.
if [[ "$RENDER_ENGINE" == CYCLES ]]; then
  blender -b --disable-autoexec --python-exit-code 1 --python "$U/gpu_check.py"
elif [[ "$RENDER_ENGINE" != BLENDER_EEVEE ]]; then
  echo "Unsupported GPU engine: $RENDER_ENGINE"; false
fi
stage=prepare
"$ANIM_ROOT/venv/bin/python" "$U/prepare.py"
stage=paint
"$U/render.sh" paint
stage=animate
"$U/render.sh" animate
stage=render
STAGES=b,c,c-details,d,e-idle,e-move,e-attack,e-hit,e-death "$U/render.sh" refresh
stage=look
"$ANIM_ROOT/venv/bin/python" "$U/look.py"
stage=feet
RESOLUTION=192 "$U/render.sh" feet
stage=audit
"$U/render.sh" audit
stage=pack
REQUIRE_MASTERS=1 "$ANIM_ROOT/venv/bin/python" "$U/pack.py"
stage=validate
"$ANIM_ROOT/venv/bin/python" "$U/validate.py"
stage=video
"$ANIM_ROOT/venv/bin/python" "$U/mp4.py"
printf 'complete round=%s GPU512/gallery256 atlas video; visual review pending\n' "$ROUND" > "$status"
printf '%s\n' "Round $ROUND: GPU stages, 512/256 masters, trimmed atlas, validation and MP4 complete; visual approval still required." >> "$ANIM_ROOT/review/3d-v2/cavalry-log.md"

) 2>&1 | tee -a "$log"
