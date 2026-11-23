#!/usr/bin/env bash
# Complete no-argument host pass. Fail explicitly if the host has no Metal GPU.
set -euo pipefail
cd "$(dirname "$0")/../../../../.."
source tools/art/anim3d/env.sh
UNIT=tools/art/anim3d/units/biplane
export ROUND="${ROUND:-2}" CYCLES_DEVICE=GPU RESOLUTION=512 SAMPLES="${SAMPLES:-64}" REQUIRE_GPU=1
PY="$ANIM_ROOT/venv/bin/python"
STATUS="$ANIM_ROOT/review/3d-v2/biplane-gpu-status.txt"
RECEIPT="$ANIM_ROOT/review/3d-v2/biplane-gpu-round${ROUND}.json"
LOG="$ANIM_ROOT/gpu-logs-biplane-r${ROUND}.log"
# Direct append works even when the overnight driver already redirects to LOG.
exec >> "$LOG" 2>&1
stage=preflight
trap 'rc=$?; printf "round=%s failed stage=%s exit=%s\n" "$ROUND" "$stage" "$rc" > "$STATUS"; exit "$rc"' ERR
printf 'round=%s running\n' "$ROUND" > "$STATUS"
rm -f "$RECEIPT" "$ANIM_ROOT/review/3d-v2/biplane-PASS"
printf 'Biplane round %s GPU handoff\n' "$ROUND"
git rev-parse HEAD
git status --short
command -v blender
"$PY" "$UNIT/preflight.py"
# The first render performs a real device check; no silent CPU fallback.
# Recreate clips from the current master so driver restarts cannot use stale rigs.
stage=animate
CYCLES_DEVICE=CPU "$UNIT/render.sh" animate
stage=audit
CYCLES_DEVICE=CPU "$UNIT/render.sh" audit
for stage in b c d g e-idle e-move e-attack e-hit e-death; do
  "$UNIT/render.sh" "$stage"
  "$PY" "$UNIT/review.py" "$stage"
done
stage=gpu-provenance
"$PY" "$UNIT/preflight.py" --gpu
stage=delivery
"$PY" "$UNIT/deliver.py"
stage=validation
"$PY" "$UNIT/check.py"
stage=receipt
"$PY" - <<'PY'
import json,os,hashlib
from pathlib import Path
r=Path(os.environ['ANIM_ROOT']);m=r/'masters/biplane'
record={'round':os.environ['ROUND'],'gpu_stages_verified':True,'visual_approval':False,
        'master_sha256':hashlib.sha256((m/'biplane.blend').read_bytes()).hexdigest(),
        'delivery':json.loads((m/'validation.json').read_text()),
        'video':json.loads((m/'video-validation.json').read_text()),
        'geometry':json.loads((m/'geometry-audit.json').read_text())}
(r/'review/3d-v2'/f"biplane-gpu-round{os.environ['ROUND']}.json").write_text(json.dumps(record,indent=2))
PY
printf 'round=%s complete; GPU512, atlas and movie verified; visual review pending\n' "$ROUND" > "$STATUS"
