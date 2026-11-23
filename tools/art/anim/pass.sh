#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/../../.."
pass="${1:?Usage: tools/art/anim/pass.sh <pass-number>}"
for slug in spearman horseman field-cannon spartan-hoplite; do
  tools/art/anim/build.sh "$slug" "$pass"
done
"$HOME/LegatumRuns/anim-pilot/venv/bin/python" tools/art/anim/validate.py
node tools/art/anim/capture.cjs "$pass"
echo "Now open every capture in ~/LegatumRuns/anim-pilot/review/pass-$pass/, critique it, fix, and repeat."
