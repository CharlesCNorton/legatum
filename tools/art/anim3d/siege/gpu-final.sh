#!/usr/bin/env bash
# Backward-compatible entry point for the lead's older invocation.
set -euo pipefail
exec "$(dirname "$0")/../units/field-cannon/gpu.sh"
