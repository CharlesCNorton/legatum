#!/usr/bin/env bash
# No-argument host pass. Run from the repository root; ROUND comes from the driver.
set -euo pipefail
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
source tools/art/anim3d/env.sh
U=tools/art/anim3d/units/keshig
export CYCLES_DEVICE=GPU RENDER_ENGINE=CYCLES RESOLUTION=512 SAMPLES=64 ROUND="${ROUND:-1}"
exec > >(tee -a "$ANIM_ROOT/keshig-gpu-round${ROUND}.log") 2>&1
status="$ANIM_ROOT/review/3d-v2/keshig-gpu-status.txt"
stage=preflight
trap 'code=$?; printf "failed stage=%s exit=%s\n" "$stage" "$code" > "$status"; exit "$code"' ERR
printf 'running round=%s\n' "$ROUND" > "$status"
blender -b --disable-autoexec --python-exit-code 1 --python "$U/preflight.py"
# Rebuild from this checkout so revised scripts cannot render a stale master.
stage=prepare; "$ANIM_ROOT/venv/bin/python" "$U/prepare.py"
for stage in build finish bake; do "$U/render.sh" "$stage"; done
unset CLIP_FILTER
stage=animate; "$U/render.sh" animate
stage=render; "$U/render.sh" all
stage=audit; "$U/render.sh" audit
stage=deliver; "$ANIM_ROOT/venv/bin/python" "$U/deliver.py"
stage=verify; "$ANIM_ROOT/venv/bin/python" "$U/verify.py" --gpu
printf 'complete round=%s; GPU512 and 256 masters, atlas, MP4; art approval pending\n' "$ROUND" > "$status"
