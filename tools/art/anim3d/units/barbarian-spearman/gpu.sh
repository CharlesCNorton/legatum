#!/usr/bin/env bash
# Complete no-argument driver handoff; never writes an art PASS marker.
set -euo pipefail
cd "$(dirname "$0")/../../../../.."
source tools/art/anim3d/env.sh
TASK=tools/art/anim3d/units/barbarian-spearman
PY="$ANIM_ROOT/venv/bin/python"
export ROUND="${ROUND:-2}"
if [[ ! "$ROUND" =~ ^[0-9]+$ ]]; then echo "ROUND must be an integer" >&2; exit 1; fi
STATUS="$ANIM_ROOT/review/3d-v2/barbarian-spearman-gpu-status.txt"
LOG="$ANIM_ROOT/gpu-logs-barbarian-spearman-r${ROUND}.log"
printf 'GPU transcript: %s\n' "$LOG"
exec >> "$LOG" 2>&1
unset CLIP
stage=preflight
trap 'result=$?; if (( result != 0 )); then printf "failed round=%s stage=%s exit=%s\n" "$ROUND" "$stage" "$result" > "$STATUS"; fi' EXIT
printf 'running round=%s\n' "$ROUND" > "$STATUS"
printf '\nRound %s checkout %s\n' "$ROUND" "$PWD"
git rev-parse HEAD
git status --short
command -v blender
if [[ ! -f "$ANIM_ROOT/masters/barbarian-spearman/plain.blend" ]]; then echo "Missing plain master"; exit 1; fi
if [[ ! -x "$PY" ]]; then echo "Missing Pillow Python"; exit 1; fi
export RENDER_ENGINE=CYCLES CYCLES_DEVICE=GPU CYCLES_BACKEND="${CYCLES_BACKEND:-METAL}" RESOLUTION=512 SAMPLES=64
blender -b --disable-autoexec --python-exit-code 1 --python "$TASK/gpu-check.py" || exit "$?"
for stage in refine paint bake animate; do "$TASK/render.sh" "$stage" || exit "$?"; done
for stage in b c c-details d e-idle e-move e-attack e-hit e-death; do
  "$TASK/render.sh" "$stage" || exit "$?"
  "$PY" "$TASK/grade.py" "$stage" || exit "$?"
  "$PY" "$TASK/review.py" "$stage" || exit "$?"
done
stage=audit
blender -b --disable-autoexec --python-exit-code 1 --python "$TASK/audit.py" || exit "$?"
stage=pack
"$PY" "$TASK/pack.py" || exit "$?"
stage=validate
REQUIRE_GPU=1 "$PY" "$TASK/validate.py" || exit "$?"
stage=movie
"$PY" "$TASK/video.py" || exit "$?"
printf 'complete round=%s; GPU512/64, 256 masters, atlas, validation and movie; visual review pending\n' "$ROUND" > "$STATUS"
printf '%s\n' '- Full GPU stage/master/atlas/movie pass completed; fresh visual judgment still required.' >> "$ANIM_ROOT/review/3d-v2/barbarian-spearman-log.md"
