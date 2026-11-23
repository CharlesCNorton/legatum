#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/../../.."
slug="${1:?Usage: tools/art/anim3d/build.sh spearman [--preview|--model-only]}"
[[ "$slug" == spearman ]] || { echo "Only spearman is modelled" >&2; exit 2; }
mode="${2:-render}"
[[ "$mode" == render || "$mode" == --preview || "$mode" == --model-only ]] || exit 2
root="$HOME/LegatumRuns/anim-pilot"
python="${PYTHON:-$root/venv/bin/python}"
[[ -x "$python" ]] || { echo "Install Pillow in $root/venv first" >&2; exit 1; }
blender="${BLENDER:-$(command -v blender || true)}"
[[ -n "$blender" ]] || blender=/Applications/Blender.app/Contents/MacOS/Blender
mkdir -p "$root/masters/spearman-3d"
lock="$root/blender.lock"
mkdir "$lock" 2>/dev/null || { echo "Another Blender process owns $lock; retry after it finishes" >&2; exit 1; }
trap 'rmdir "$lock"' EXIT
"$python" tools/art/anim3d/paint.py
# RENDER_ENGINE=CYCLES explicitly avoids Metal in the sandbox. AUTO tries Eevee
# in a separate process, then rebuilds/renders with CPU Cycles if Eevee fails.
engine="${RENDER_ENGINE:-AUTO}"
run() { nice -n 10 "$blender" --background --factory-startup -t 4 --python-exit-code 1 --python tools/art/anim3d/model.py -- "$mode" "$1"; }
if [[ "$engine" == AUTO ]]; then
  if ! run BLENDER_EEVEE_NEXT; then echo 'Eevee unavailable; falling back to CPU Cycles' >&2; run CYCLES; fi
else run "$engine"; fi
nice -n 10 "$blender" --background --factory-startup -t 4 --python-exit-code 1 --python tools/art/anim3d/audit.py
if [[ "$mode" == render ]]; then
  "$python" tools/art/anim3d/pack.py
  "$python" tools/art/anim3d/validate.py
fi
