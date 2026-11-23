#!/usr/bin/env bash
# Complete driver handoff, invoked without arguments from any directory.
set -euo pipefail
cd "$(dirname "$0")/../../../../.."
source tools/art/anim3d/env.sh
export ROUND="${ROUND:-3}"
export ANIM_MASTER="${ANIM_MASTER:-$ANIM_ROOT/masters/spartan-hoplite/round4-3d}"
export UNIT=spartan-hoplite RENDER_ENGINE=CYCLES CYCLES_DEVICE=GPU RESOLUTION=512 SAMPLES=64
unit=tools/art/anim3d/units/spartan-hoplite
status="$ANIM_ROOT/review/3d-v2/spartan-hoplite-gpu-status.txt"
log="$ANIM_ROOT/spartan-hoplite-gpu-round${ROUND}.log"
exec > >(tee "$log") 2>&1
stage=preflight
trap 'echo "interrupted round=$ROUND stage=$stage exit=130" > "$status"; exit 130' INT
trap 'echo "terminated round=$ROUND stage=$stage exit=143" > "$status"; exit 143' TERM
trap 'code=$?; echo "failed round=$ROUND stage=$stage exit=$code" > "$status"; exit "$code"' ERR
printf 'running round=%s\n' "$ROUND" > "$status"
printf 'checkout=%s\n' "$PWD"
git rev-parse HEAD
git status --short
command -v blender
test -f "$ANIM_MASTER/unpainted.blend"
command -v ffmpeg
command -v ffprobe
for stage in gpu-check refine check-scene all-clips audit b all-renders feet verify-gpu pack validate video; do
  printf 'running round=%s stage=%s\n' "$ROUND" "$stage" > "$status"
  "$unit/render.sh" "$stage"
done
printf 'complete round=%s GPU512/64; atlas/video validated; pending visual review\n' "$ROUND" > "$status"
