#!/bin/bash
# Host/lead only: this command renders and launches Chromium.
set -euo pipefail
cd "$(dirname "$0")/../../.."
pass="${1:?Usage: tools/art/anim/pass.sh <pass-number>}"
[[ "$pass" =~ ^[1-9][0-9]*$ ]] || { echo 'Pass must be a positive integer' >&2; exit 2; }
review="$HOME/LegatumRuns/anim-pilot/review"
out="$review/pass-$pass"
mkdir -p "$out"
for slug in spearman horseman field-cannon spartan-hoplite; do
  tools/art/anim/build.sh "$slug" "$pass"
  # Keep each completed unit's evidence even if a later unit fails.
  cp "$review/$slug.png" "$review/$slug-"*.webp "$review/$slug-pack.json" "$out/"
done
"$HOME/LegatumRuns/anim-pilot/venv/bin/python" tools/art/anim/validate.py
node tools/art/anim/capture.cjs "$pass"
echo "Now open every capture in $out/, critique it, fix, and repeat."
