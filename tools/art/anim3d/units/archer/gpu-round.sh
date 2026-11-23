#!/usr/bin/env bash
# Backward-compatible name for the one complete driver entry point.
set -euo pipefail
exec "$(dirname "$0")/gpu.sh"
