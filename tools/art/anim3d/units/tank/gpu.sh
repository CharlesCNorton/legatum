#!/usr/bin/env bash
# Complete no-argument host pass, independent of the caller's working directory.
set -euo pipefail
cd "$(dirname "$0")/../../../../.."
source tools/art/anim3d/env.sh
export RENDER_ENGINE=CYCLES CYCLES_DEVICE=GPU RESOLUTION=512
export SAMPLES="${SAMPLES:-256}" ROUND="${ROUND:-4}"
[[ "$ROUND" =~ ^[a-zA-Z0-9_-]+$ ]] || { echo 'Invalid ROUND' >&2; exit 2; }
review="$ANIM_ROOT/review/3d-v2"
mkdir -p "$review"
log="$ANIM_ROOT/gpu-logs-tank-r${ROUND}.log"
status="$review/tank-gpu-status.txt"
# Direct redirection works in restricted drivers where /dev/fd process substitution fails.
exec >> "$log" 2>&1
stage=inputs
trap 'code=$?; printf "failed round=%s stage=%s exit=%s log=%s\n" "$ROUND" "$stage" "$code" "$log" > "$status"; exit "$code"' ERR
printf 'running round=%s checkout=%s\n' "$ROUND" "$PWD" > "$status"
printf '\nTank GPU round %s | checkout %s\n' "$ROUND" "$PWD"
git rev-parse HEAD
git status --short
command -v blender
for file in tank.blend tank-plain.blend clips/idle.blend clips/move.blend clips/attack.blend clips/hit.blend clips/death.blend; do
  test -s "$ANIM_ROOT/masters/tank/$file"
done
stage=metal-preflight
# Device discovery does no rendering; use a normal gated CPU startup.
BLENDER_GPU=0 CYCLES_DEVICE=CPU blender -b --disable-autoexec --factory-startup --python-exit-code 1 --python tools/art/anim3d/vehicles/gpu-preflight.py
stage=audit
tools/art/anim3d/render.sh vehicles-audit
for stage in b c details d e-idle e-move e-attack e-hit e-death g; do
  tools/art/anim3d/render.sh "vehicles-$stage"
done
stage=archive
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/vehicles/archive.py --require-512
stage=atlas
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/vehicles/deliver.py
stage=video
"$ANIM_ROOT/venv/bin/python" tools/art/anim3d/vehicles/video.py
printf 'complete round=%s GPU512/gallery256/atlas/video; visual review pending; log=%s\n' "$ROUND" "$log" > "$status"
