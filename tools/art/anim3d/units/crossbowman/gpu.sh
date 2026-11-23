#!/usr/bin/env bash
# One host-only no-argument entry point. The PATH gate owns all Blender scheduling.
set -euo pipefail
cd "$(dirname "$0")/../../../../.."
source tools/art/anim3d/env.sh
unit=tools/art/anim3d/units/crossbowman
export CYCLES_DEVICE=GPU RESOLUTION=512 SAMPLES="${SAMPLES:-64}" ROUND="${ROUND:-2}"
status="$REVIEW/crossbowman-gpu-status.txt"
receipt="$REVIEW/crossbowman-gpu-round${ROUND}.json"
printf 'running round %s\n' "$ROUND" > "$status"
rm -f "$receipt"
exec > "$ANIM_ROOT/gpu-logs-crossbowman-r${ROUND}.log" 2>&1
trap 'code=$?; printf "failed round %s: line %s, exit %s\n" "$ROUND" "$LINENO" "$code" > "$status"; exit "$code"' ERR
printf 'Round %s; checkout %s; Blender gate %s\n' "$ROUND" "$(git rev-parse HEAD)" "$(command -v blender)"
git status --short -- "$unit" tools/art/anim3d/PLAYBOOK.md
if [ "$SAMPLES" -lt 64 ]; then
  printf 'failed round %s: final GPU samples must be at least 64\n' "$ROUND" > "$status"
  exit 2
fi
command -v ffmpeg
command -v ffprobe
"$ANIM_ROOT/venv/bin/python" "$unit/prepare.py"
"$unit/render.sh" preflight
"$unit/render.sh" build
"$unit/render.sh" bake
"$unit/render.sh" animate
"$unit/render.sh" audit
for stage in b c d e-idle e-move e-attack e-hit e-death; do
  STAGE="$stage" "$unit/render.sh" render
  "$ANIM_ROOT/venv/bin/python" "$unit/post.py" review "$stage"
done
"$unit/render.sh" feet
"$ANIM_ROOT/venv/bin/python" "$unit/check_final.py"
"$ANIM_ROOT/venv/bin/python" "$unit/post.py" pack
"$ANIM_ROOT/venv/bin/python" "$unit/post.py" validate
"$ANIM_ROOT/venv/bin/python" "$unit/post.py" video
"$ANIM_ROOT/venv/bin/python" - <<'PY'
import json, os
from pathlib import Path
r=Path(os.environ['ANIM_ROOT']); m=r/'masters/crossbowman'
report={name:json.loads((m/(name+'.json')).read_text()) for name in ['validation','video-validation','audit','feet']}
report.update(round=os.environ['ROUND'],visual_pass=False)
(r/'review/3d-v2'/f'crossbowman-gpu-round{os.environ["ROUND"]}.json').write_text(json.dumps(report,indent=2))
PY
printf 'complete round %s: GPU512, gallery256, atlas, audit, MP4; visual review pending\n' "$ROUND" > "$status"
# Technical success never writes PASS.
