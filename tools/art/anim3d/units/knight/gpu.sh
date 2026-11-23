#!/usr/bin/env bash
# Complete no-argument lead-side pass. Always invoke from the repo root.
set -euo pipefail
[[ $# == 0 ]] || { echo 'gpu.sh takes no arguments' >&2; exit 2; }
[[ -f tools/art/anim3d/units/knight/build.py ]] || { echo 'Run from repository root' >&2; exit 2; }
source tools/art/anim3d/env.sh
export CYCLES_DEVICE=GPU RESOLUTION=512 REQUIRE_GPU=1
export ROUND="${ROUND:-2}" SAMPLES="${SAMPLES:-64}"
(( SAMPLES >= 64 )) || { echo 'Final GPU samples must be >=64' >&2; exit 2; }
UNIT_DIR=tools/art/anim3d/units/knight
KNIGHT_MASTER="$ANIM_ROOT/masters/knight"
mkdir -p "$KNIGHT_MASTER"
# A failed pass must not leave an older success receipt beside partial output.
rm -f "$KNIGHT_MASTER/validation.json" "$KNIGHT_MASTER/movie.json"
exec > >(tee "$KNIGHT_MASTER/gpu-round${ROUND}.log") 2>&1
status="$KNIGHT_MASTER/gpu-round${ROUND}-status.json"
printf '{"status":"running","round":"%s"}\n' "$ROUND" > "$status"
trap 'printf "{\"status\":\"failed\",\"round\":\"%s\"}\n" "$ROUND" > "$status"' ERR
"$ANIM_ROOT/venv/bin/python" "$UNIT_DIR/preflight.py"
# Verify Metal before any masters are overwritten; the PATH gate owns CPU/GPU slots.
blender -b --disable-autoexec --python-exit-code 1 --python "$UNIT_DIR/gpu_check.py"
"$ANIM_ROOT/venv/bin/python" "$UNIT_DIR/prepare.py"
for stage in build kit paint motion animate; do "$UNIT_DIR/run.sh" "$stage"; done
"$UNIT_DIR/run.sh" audit
STAGES=b,c,d,e-idle,e-move,e-attack,e-hit,e-death,g "$UNIT_DIR/run.sh" render
"$ANIM_ROOT/venv/bin/python" "$UNIT_DIR/delivery.py" all --resolution 512
printf '{"status":"complete","round":"%s","art_approved":false}\n' "$ROUND" > "$status"
printf 'GPU round %s complete: masters, review sheets, atlas and MP4 verified. Visual approval still required.\n' "$ROUND"
