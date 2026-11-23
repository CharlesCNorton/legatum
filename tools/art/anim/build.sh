#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/../../.."
slug="${1:?Usage: tools/art/anim/build.sh <slug> [pass]}"
pass="${2:-1}"
mode="${3:-render}"
if [[ "$mode" != render && "$mode" != --model-only && "$mode" != --audit-only ]]; then echo "Expected render, --model-only, or --audit-only" >&2; exit 2; fi
root="$HOME/LegatumRuns/anim-pilot"
python="$root/venv/bin/python"
if [[ ! -x "$python" ]]; then python3 -m venv "$root/venv"; "$python" -m pip install Pillow; fi
blender="${BLENDER:-$(command -v blender || true)}"
if [[ -z "$blender" ]]; then blender=/Applications/Blender.app/Contents/MacOS/Blender; fi
# mkdir is an atomic single-renderer lock shared by worktrees and invocations.
lock="$root/blender.lock"
if ! mkdir "$lock" 2>/dev/null; then echo "Another Blender build owns $lock" >&2; exit 1; fi
trap 'rmdir "$lock"' EXIT
if [[ "$mode" == --audit-only ]]; then
  nice -n 10 "$blender" --background --factory-startup -t 4 --python-exit-code 1 --python tools/art/anim/audit_rig.py -- "$slug"
  exit
fi
"$python" tools/art/anim/prepare.py "$slug"
nice -n 10 "$blender" --background --factory-startup -t 4 --python-exit-code 1 --python tools/art/anim/render.py -- "$slug" "$pass" "$mode"
if [[ "$mode" == render ]]; then "$python" tools/art/anim/pack.py "$slug"; fi
