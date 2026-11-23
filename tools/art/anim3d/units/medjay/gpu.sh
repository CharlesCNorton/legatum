#!/usr/bin/env bash
# No arguments; run from repo root. Host driver provides ROUND.
set -euo pipefail
source tools/art/anim3d/env.sh
export ROUND="${ROUND:-2}"
unit_dir=tools/art/anim3d/units/medjay
log="$ANIM_ROOT/gpu-logs-medjay-r${ROUND}.log"
status="$ANIM_ROOT/review/3d-v2/medjay-gpu-status.txt"
receipt="$ANIM_ROOT/masters/medjay/gpu-round${ROUND}.json"
mkdir -p "$(dirname "$status")"
exec >> "$log" 2>&1
stage=preflight
trap 'rc=$?; echo "failed stage=$stage exit=$rc" > "$status"; exit "$rc"' ERR
rm -f "$receipt"
echo "running round=$ROUND checkout=$PWD" > "$status"
date -u
git rev-parse HEAD
git status --short -- tools/art/anim3d/units/medjay
command -v blender
python3 "$unit_dir/gpu_check.py" --inputs-only
export RENDER_ENGINE=CYCLES CYCLES_DEVICE=GPU RESOLUTION=512
export SAMPLES="${SAMPLES:-64}"
if (( SAMPLES < 64 )); then echo 'GPU finals require SAMPLES >= 64'; false; fi
for stage in b c c-details d e-idle e-move e-attack e-hit e-death; do
 "$unit_dir/render.sh" "$stage"
done
stage=verify-gpu-masters
"$ANIM_ROOT/venv/bin/python" "$unit_dir/gpu_check.py"
stage=audit
"$unit_dir/render.sh" audit
stage=pack
"$ANIM_ROOT/venv/bin/python" "$unit_dir/deliver.py" pack
stage=validate
"$ANIM_ROOT/venv/bin/python" "$unit_dir/deliver.py" validate
stage=video
"$ANIM_ROOT/venv/bin/python" "$unit_dir/deliver.py" video
stage=receipt
"$ANIM_ROOT/venv/bin/python" - <<'PY'
import hashlib,json,os
from pathlib import Path
m=Path(os.environ['ANIM_ROOT'])/'masters/medjay'
p=json.loads((m/'pack.json').read_text())
receipt={'round':os.environ['ROUND'],'device':'GPU','resolution':512,'master_sha256':hashlib.sha256((m/'medjay.blend').read_bytes()).hexdigest(),'bytes':p['bytes'],'quality':p['quality'],'art_approved':False}
(m/f"gpu-round{os.environ['ROUND']}.json").write_text(json.dumps(receipt,indent=2)+'\n')
PY
echo "complete round=$ROUND; pending visual review" > "$status"
