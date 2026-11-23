#!/usr/bin/env bash
# Complete no-argument host GPU pass; CPU previews never count as GPU evidence.
set -euo pipefail
repo_root="$(cd "$(dirname "$0")/../../../../.." && pwd)"
cd "$repo_root"
source tools/art/anim3d/env.sh
export RENDER_ENGINE=CYCLES CYCLES_DEVICE=GPU RESOLUTION=512
export SAMPLES="${SAMPLES:-64}" ROUND="${ROUND:-2}"
unit_dir=tools/art/anim3d/units/phalangite
unit_master="$ANIM_ROOT/masters/phalangite"
unit_review="$ANIM_ROOT/review/3d-v2"
mkdir -p "$unit_review"
status="$unit_review/phalangite-gpu-status.txt"
receipt="$unit_review/phalangite-gpu-round${ROUND}.json"
rm -f "$receipt"
exec >> "$ANIM_ROOT/phalangite-gpu-round${ROUND}.log" 2>&1
stage=preflight
trap 'rc=$?; printf "failed round=%s stage=%s exit=%s\n" "$ROUND" "$stage" "$rc" > "$status"; exit "$rc"' ERR
printf 'running round=%s\n' "$ROUND" > "$status"
printf 'Phalangite round %s checkout %s\n' "$ROUND" "$repo_root"
git rev-parse HEAD
git status --short -- "$unit_dir"
command -v blender
test -x "$unit_dir/run.sh"
test -x "$ANIM_ROOT/venv/bin/python"
test -f "$unit_master/phalangite.blend"
test -f "$unit_master/fitted-plain.blend"
stage=animate
"$unit_dir/run.sh" animate
stage=audit
"$unit_dir/run.sh" audit
stage=render
"$unit_dir/run.sh" all
stage=gpu-master-check
"$ANIM_ROOT/venv/bin/python" "$unit_dir/deliver.py" gpu-check
stage=pack
"$ANIM_ROOT/venv/bin/python" "$unit_dir/deliver.py" pack
stage=validate
"$ANIM_ROOT/venv/bin/python" "$unit_dir/deliver.py" validate
stage=movie
"$ANIM_ROOT/venv/bin/python" "$unit_dir/deliver.py" movie
stage=receipt
"$ANIM_ROOT/venv/bin/python" "$unit_dir/deliver.py" receipt
printf 'complete round=%s; GPU512, atlas and movie verified; visual review pending\n' "$ROUND" > "$status"
